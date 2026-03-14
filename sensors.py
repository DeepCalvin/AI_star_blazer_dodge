# Functions to help calculate features and stuff

# Calculate threat_score, which is calculated x_factor / (t_hit + eps)
# t_hit is the TTC
# And when we pass top k threat features, that top k threats are sorted by threat_score


# Block: __init__(self, x, y, w, h, vy, ay, jy, shoot_cooldown, color)
# Bullet: __init__(self, owner, x, y, vy, ay, jy, color, w=BULLET_W, h=BULLET_H)
class Threat():

    def __init__(self, x, y, w, h, vy, ay, jy, threat_type, valid=True, source=None):
        self.source = source

        self.x = x
        self.y = y

        self.w = w
        self.h = h

        self.vy = vy
        self.ay = ay
        self.jy = jy

        self.threat_type = threat_type # "block" or "bullet" or "none"
        self.valid = bool(valid)

        self.cx = self.x + self.w * 0.5
        self.cy = self.y + self.h * 0.5

        # For later (may add more)
        self.TTC = None
        self.overlap = 0 # boolean overlap
        self.gap = 0 # gap
        self.score = 0 # threat score


# Gather threat into list of object with normalized information
def collect_threat(bullet_list: list, block_list: list) -> list:
    threats = []

    for bullet in bullet_list:
        new_threat = Threat(
            x=bullet.x,
            y=bullet.y,

            w=bullet.w,
            h=bullet.h,

            vy=bullet.vy,
            ay=bullet.ay,
            jy=bullet.jy,

            threat_type="bullet",
            source=bullet
        )
        threats.append(new_threat)

    for block in block_list:
        new_threat = Threat(
            x=block.x,
            y=block.y,

            w=block.w,
            h=block.h,

            vy=block.vy,
            ay=block.ay,
            jy=block.jy,

            threat_type="block",
            source=block
        )
        threats.append(new_threat)

    return threats

# Calculate TTC using formula
def _y_at(t: float, y0: float, vy0: float, ay0: float, jy: float) -> float:
    return y0 + vy0 * t + 0.5 * ay0 * (t**2) + (1.0 / 6.0) * jy * (t**3)

# Calculate time to reach y
def time_to_reach_y(y0: float, vy0: float, ay0: float, jy: float, y_target: float,
                    t_max: float = 2.0, iters: int = 25) -> float | None:
    """
    Returns the smallest t in [0, t_max] such that y(t) >= y_target
    If it won't reach by t_max, returns None

    Our falling block is monotomic so y(t) can be calculated
    """
    # Already at / through the target
    if y0 >= y_target:
        return 0.0

    # If object doesn't reach y_target by t_max, it's not urgent and therefore ignore
    if _y_at(t_max, y0, vy0, ay0, jy) < y_target:
        return None

    # Binary search to find approximate time of impact
    # This solution is actually, I think, really smart cuz idk how to solve cubic :sob:
    low = 0.0
    high = t_max

    for _ in range(iters):
        mid = (low + high) * 0.5

        # Over
        if _y_at(mid, y0, vy0, ay0, jy) >= y_target:
            high = mid

        # Under
        else:
            low = mid

    return high

# Calculate X gap and whether it overlaps
def x_gap_and_overlap(agent_x: float, agent_w: float, obj_x: float, obj_w: float) -> tuple[float, int]:
    """
    Return gap_px as 0 if they overlap (no gap), or the distance between edges
    Return overalp: bool 0 or 1 to represent whether they overlap
    """
    agent_left = agent_x
    agent_right = agent_x + agent_w
    obj_left = obj_x
    obj_right = obj_x + obj_w

    # Check for overlap
    if not (obj_right < agent_left or obj_left > agent_right):
        overlap = 1
    else:
        overlap = 0

    # Return if overlap
    if overlap:
        return 0.0, 1

    # If not overlap, return gap between edges
    if obj_right < agent_left:
        return float(agent_left - obj_right), 0
    else:
        return float(obj_left - agent_right), 0
    

# Calculate X factor from gap
def x_factor(gap_px: float) -> float:
    """
    gap_px + 1 to prevent division by zero obv
    
    The reason to do this is because x_factor is later gonna be plugged into that formula
    X_factor / TTC

    X_factor is small and TTC increase, threat_score should be small, because threat is horizontally far from agent, and far from impact
    X_factor is big and TTC is small, threat_score should be big, becuase threat is horizontally close from agent, and close to impact

    Hence X_factor should be small if gap is large, and large is gap is small

    But also, the gap_px + 1 is because if gap_px = 0, it means threat and agent overlap, so X_factor is 1

    1 indicating max threat, it's scaling
    """

    return 1 / (gap_px + 1)

# Calculate threat_score
def threat_score(agent, threat: Threat, t_max: float = 2.0, eps: float = 1e-3) -> float:
    """
    Score = x_factor / (t_hit + eps)
    If no hit within t_max => 0, eps is to prevent zero division error
    """

    if not threat.valid:
        threat.TTC = None
        threat.score = 0
        return 0

    # danger line: when threat's bottom reach agent's top
    y_target = float(agent.y) - threat.h

    t_hit = time_to_reach_y(threat.y, threat.vy, threat.ay, threat.jy, y_target, t_max=t_max)
    threat.TTC = t_hit

    gap, overlap = x_gap_and_overlap(agent.x, agent.w, threat.x, threat.w)
    threat.gap = gap
    threat.overlap = overlap

    # Too far away, not taken into account
    if t_hit is None:
        threat.score = 0
        return 0

    xf = x_factor(gap)
    score = xf / (t_hit + eps)
    threat.score = score
    return score

# Pad invalid threat
def pad_invalid_threats(threats: list[Threat], k: int) -> list[Threat]:
    """
    Pads with invalid threats so length becomes k
    because sometimes, there are fewer threats than k, but NN have a fixed structure
    """

    while len(threats) < k:
        threats.append(Threat(0, 0, 0, 0, 0, 0, 0, threat_type="none", valid=False))

    return threats[:k]

# Sort threat list
def sort_threat_list(agent, bullets: list, blocks: list, k: int, t_max: float = 2.0) -> list[Threat]:
    """
    Returns top-k threats sorted by score desc, padded with invalid threats
    """

    threats = collect_threat(bullets, blocks)

    # Calculate threat_score
    for threat in threats:
        threat_score(agent, threat, t_max=t_max)

    # Filter
    threats = [threat for threat in threats if threat.score > 0.0]

    # sort desc
    threats.sort(key=lambda threat: threat.score, reverse=True)

    # pad
    return pad_invalid_threats(threats, k)

def _clamp(x: float, low: float, high: float) -> float:
    if x < low:
        return low
    if x > high:
        return high
    return x


def build_observation(agent, bullets: list, blocks: list, k: int, WIDTH: float, HEIGHT: float, TMAX: float = 2.0,
                        VY_NORM: float = 1000,
                        AY_NORM: float = 3000,
                        JY_NORM: float = 1500,
                        VX_NORM: float = 1000
) -> list[float]:
    
    # Those xx_NORM are just constants (which I will tune) used to normalize values

    """
    Build a fixed size observation vector of self-features + (k * threat-features)

    Self-features:
    - agent_x_norm
    - agent_vx_norm
    - left_wall_dist_norm
    - right_wall_dist_norm
    - agent_width_norm

    Threat-features:
    - is_bullet
    - is_valid
    - dx_norm
    - dy_norm
    - overlap
    - gap_norm
    - t_hit_norm
    - w_norm
    - vy_norm
    - ay_norm
    - jy_norm
    """

    obs = [] # List of floats

    # Self-features
    obs.append(agent.x / WIDTH) # agent_x_norm
    obs.append(_clamp(agent.vx / VX_NORM, -1.0, 1.0)) # agent_vx_norm

    left_wall_dist = agent.x
    right_wall_dist = WIDTH - (agent.x + agent.w)

    obs.append(_clamp(left_wall_dist / WIDTH, 0.0, 1.0)) # left_wall_dist_norm
    obs.append(_clamp(right_wall_dist / WIDTH, 0.0, 1.0)) # right_wall_dist_norm
    obs.append(_clamp(agent.w / WIDTH, 0.0, 1.0)) # agent_width_norm

    # Top k threats
    top_threats = sort_threat_list(agent, bullets, blocks, k, t_max=TMAX)

    agent_cx = agent.x + agent.w * 0.5

    for threat in top_threats:

        # Type
        is_bullet = 1.0 if threat.threat_type == "bullet" else 0.0
        is_valid  = 1.0 if threat.valid else 0.0


        # If invalid threat
        if not threat.valid:
            
            # Pad with zeros (except the two flags)
            obs.extend([is_bullet, is_valid, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
            continue

        # Relative pos
        dx_norm = _clamp((threat.cx - agent_cx) / WIDTH, -1, 1)
        dy_norm = _clamp((agent.y - threat.y) / HEIGHT, -1, 1)

        overlap = float(threat.overlap)
        gap_norm = _clamp(threat.gap / WIDTH, 0, 1)

        # TTC normalized
        if threat.TTC is None:
            t_hit_norm = 1
        else:
            t_hit_norm = _clamp(threat.TTC / TMAX, 0, 1)

        w_norm = _clamp(threat.w / WIDTH, 0, 1)

        vy_norm = _clamp(threat.vy / VY_NORM, -1, 1)
        ay_norm = _clamp(threat.ay / AY_NORM, -1, 1)
        jy_norm = _clamp(threat.jy / JY_NORM, -1, 1)

        obs.extend([
            is_bullet,
            is_valid,
            dx_norm,
            dy_norm,
            overlap,
            gap_norm,
            t_hit_norm,
            w_norm,
            vy_norm,
            ay_norm,
            jy_norm
        ])

    return obs


