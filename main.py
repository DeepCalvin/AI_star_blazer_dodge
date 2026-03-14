import pygame
import sys
from utils import get_color, spawn_block
import random
from bullets import Bullet, BULLET_W, BULLET_H
from agents import Agent
from brain import ContinuousMLPBrain, evolve_next_generation
from sensors import build_observation, sort_threat_list


pygame.init()

# Screen settings
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Neuro Dodge Sandbox")
clock = pygame.time.Clock()

# Difficulty scaling
difficulty = 0.0
DIFFICULTY_STEP = 0.01
# Update once every 10 seconds to prevent any jerk variable from updating every frame (cuz it makes me feel safe hehe)
DIFFICULTY_INTERVAL = 10
difficulty_timer = 0

# Observation constant
K_THREATS = 5
OBS_LEN = 5 + K_THREATS * 11

ELITE_COUNT = 5
MUT_RATE = 0.10
MUT_SCALE = 0.12
TOURNAMENT_K = 5





# instances list
blocks = []
bullets = []
ai_agents = []

# Spawn timer
spawn_timer = 0.0
next_spawn_time = random.uniform(2.0, 4.0)

# Text
font = pygame.font.SysFont(None, 36)

# Initialize agent
player = Agent(x=WIDTH//2, y=HEIGHT-80, owner="PLAYER")

ACCEL = 5000 # ps/s^2
FRICTION = 3750 # px/s^2
MAX_VX = 900 # px/s
SIDE_MARGIN = 100 # px

# GENERATIONS
GEN = 1
AI_POP = 50


# DEBUGGING TOOLS
DEBUG_AGENT_INDEX = random.randint(0, AI_POP-1) # highlight random AI to see its topk features
DEBUG_SHOW_TOPK = True
debug_agent_ref = None # will store an Agent object (or None)


# Debug agent
def pick_debug_agent(ai_agents, preferred_index=0, prev=None):
    """
    Always returns an alive agent if any exist

    Priority:
      1. prev, AKA previous, AI agent from previous frame (if still alive)
      2. preferred_index (if alive)
      3. first alive agent
    """
    alive = [agent for agent in ai_agents if agent.alive]

    if not alive:
        return None

    if prev is not None and prev.alive:
        return prev

    if 0 <= preferred_index < len(ai_agents):
        candidate = ai_agents[preferred_index]
        if candidate.alive:
            return candidate

    return max(alive, key=lambda agent: agent.fitness)


# Spawn AI population
def spawn_ai_population(brains=None):
    agents = []
    for i in range(AI_POP):
        x = random.randint(SIDE_MARGIN, WIDTH - SIDE_MARGIN - 25)
        ai_agent = Agent(x=x, y=HEIGHT-80, owner="AI", color=get_color("light_blue"))

        if brains is None:
            ai_agent.brain = ContinuousMLPBrain.create(input_dim=OBS_LEN)
        else:
            ai_agent.brain = brains[i]

        agents.append(ai_agent)
    return agents


# Reset generaiton func
def reset_gen():
    global blocks, bullets, spawn_timer, next_spawn_time, difficulty, ai_agents, GEN, difficulty_timer

    GEN += 1

    blocks = []
    bullets = []

    spawn_timer = 0
    next_spawn_time = random.uniform(2.0, 4.0)

    difficulty = 0
    difficulty_timer = 0

    player.alive = True
    player.x = WIDTH // 2
    player.vx = 0
    player.ax = 0

    ai_agents = spawn_ai_population()

# Init gen 1
ai_agents = spawn_ai_population()

running = True
while running:
    dt = clock.tick(60) / 1000 # number of seconds since last frame

    # EVENTS
    for event in pygame.event.get():

        # QUIT
        if event.type == pygame.QUIT:
            running = False
        # KEY
        if event.type == pygame.KEYDOWN:
            # ESC
            if event.key == pygame.K_ESCAPE:
                running = False

    keys = pygame.key.get_pressed()

    player.ax = 0.0
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player.ax = -ACCEL
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player.ax = ACCEL


    # Restart when all AI dead
    if not any(ai_agent.alive for ai_agent in ai_agents):

        # Evolve from previous generation
        old_brains = [ai_agent.brain for ai_agent in ai_agents]
        old_fitness = [ai_agent.fitness for ai_agent in ai_agents]

        print("GEN", GEN, "best fitness:", max(old_fitness), "avg:", sum(old_fitness)/len(old_fitness))

        new_brains = evolve_next_generation(
            brains=old_brains,
            fitness=old_fitness,
            pop_size=AI_POP,
            elite_count=ELITE_COUNT,
            mutation_rate=MUT_RATE,
            mutation_scale=MUT_SCALE,
            tournament_k=TOURNAMENT_K,
        )

        reset_gen()
        ai_agents = spawn_ai_population(new_brains)
        continue



    # Spawn blocks
    spawn_timer += dt
    if spawn_timer >= next_spawn_time:
        
        # Reset
        spawn_timer = 0

        base_min, base_max = 0.5, 0.8
        min_interval = max(0.15, base_min - 0.08 * difficulty)
        max_interval = max(0.25, base_max - 0.10 * difficulty)
        next_spawn_time = random.uniform(min_interval, max_interval)
        
        # Spawn
        base_low, base_high = 2, 5
        extra = int(difficulty * 1.2)
        spawn_amount = random.randint(base_low, base_high + extra)

        for i in range(spawn_amount):
            new_block = spawn_block(blocks, WIDTH, difficulty)
            if new_block is not None:
                blocks.append(new_block)


    # Fill screen
    screen.fill(get_color("white"))

    # UPDATE

    # Scale difficulty
    difficulty_timer += dt

    if difficulty_timer >= DIFFICULTY_INTERVAL:
        difficulty += DIFFICULTY_STEP

        # Reset
        difficulty_timer = 0


    # Update block
    for block in blocks:

        if block.time_since_last_shot >= block.shoot_cooldown:

            # Spawn bullet

            bullet_x = block.x + block.w // 2 - BULLET_W // 2
            bullet_y = block.y + block.h

            bullet = Bullet(owner=block, x=bullet_x, y=bullet_y, w=BULLET_W, h=BULLET_H, vy=block.vy * 1.5, ay=block.ay * 1.5, jy=block.jy * 1.5, color=get_color("orange"))

            bullets.append(bullet)

            # Reset
            block.time_since_last_shot = 0.0

        block.ay += block.jy * dt
        block.vy += block.ay * dt
        block.y  += block.vy * dt
        block.time_since_last_shot += dt

    # Update bullet
    for bullet in bullets:
        bullet.ay += bullet.jy * dt
        bullet.vy += bullet.ay * dt
        bullet.y  += bullet.vy * dt

    # Update player
    if player.alive:
        # Update vel
        player.vx += player.ax * dt

        # Friction
        if player.ax == 0.0:
            if player.vx > 0:
                player.vx = max(0.0, player.vx - FRICTION * dt)
            elif player.vx < 0:
                player.vx = min(0.0, player.vx + FRICTION * dt)

        # Update pos
        player.vx = max(-MAX_VX, min(MAX_VX, player.vx))
        player.x += player.vx * dt

        # Clamp side wall pos (to prevent wall camp)
        if player.x < SIDE_MARGIN:
            player.x = SIDE_MARGIN
            player.vx = 0
        elif player.x > WIDTH - player.w - SIDE_MARGIN:
            player.x = WIDTH - player.w - SIDE_MARGIN
            player.vx = 0

    for ai_agent in ai_agents:

        if not ai_agent.alive:
            continue


        # FITNESS CONTROl
        ai_agent.time_alive += dt

        # Fitness measured in how long agent survives
        ai_agent.fitness = ai_agent.time_alive

        # Wall camp penalty
        EDGE_ZONE = 300
        PENALTY_RATE = 10 # penalty per second for wall hug

        left_dist = ai_agent.x
        right_dist = WIDTH - (ai_agent.x + ai_agent.w)
        edge_dist = min(left_dist, right_dist)

        # If AI close to edge
        if edge_dist < EDGE_ZONE:

            # Deeper into edge zone -> stronger penalty
            edge_strength = (EDGE_ZONE - edge_dist) / EDGE_ZONE
            ai_agent.fitness -= PENALTY_RATE * edge_strength * dt

        # Give center bonus
        CENTER_BONUS_RATE = 0.3 # Rewards / sec

        center_x = WIDTH * 0.5
        agent_cx = ai_agent.x + ai_agent.w * 0.5

        dist_center = abs(agent_cx - center_x) / (WIDTH * 0.5)
        ai_agent.fitness += (1.0 - dist_center) * CENTER_BONUS_RATE * dt

        # Movement rewarding
        MOVEMENT_BONUS = 0.5
        ai_agent.fitness += abs(ai_agent.vx) / MAX_VX * MOVEMENT_BONUS * dt



        # NEURAL NET CONTROL
        obs = build_observation(ai_agent, bullets, blocks, K_THREATS, WIDTH, HEIGHT)
        u = ai_agent.brain.forward(obs) # u in [-1, 1]
        ai_agent.ax = u * ACCEL # continuous acceleration


        # Update vel
        ai_agent.vx += ai_agent.ax * dt

        # Friction
        if ai_agent.ax == 0.0:
            if ai_agent.vx > 0:
                ai_agent.vx = max(0.0, ai_agent.vx - FRICTION * dt)
            elif ai_agent.vx < 0:
                ai_agent.vx = min(0.0, ai_agent.vx + FRICTION * dt)

        # Update pos
        ai_agent.vx = max(-MAX_VX, min(MAX_VX, ai_agent.vx))
        ai_agent.x += ai_agent.vx * dt

        # Clamp side wall pos (to prevent wall camp)
        if ai_agent.x < SIDE_MARGIN:
            ai_agent.x = SIDE_MARGIN
            ai_agent.vx = 0
        elif ai_agent.x > WIDTH - ai_agent.w - SIDE_MARGIN:
            ai_agent.x = WIDTH - ai_agent.w - SIDE_MARGIN
            ai_agent.vx = 0


    # COLLISION CHECK dAWG
    for block in blocks:
        if player.alive and player.rect.colliderect(block.rect):
            player.alive = False

        for ai_agent in ai_agents:
            if ai_agent.alive and ai_agent.rect.colliderect(block.rect):
                ai_agent.alive = False

    for bullet in bullets:
        if player.alive and player.rect.colliderect(bullet.rect):
            player.alive = False

        for ai_agent in ai_agents:
            if ai_agent.alive and ai_agent.rect.colliderect(bullet.rect):
                ai_agent.alive = False

    # Remove bullets from screen
    blocks = [b for b in blocks if (b.y < HEIGHT + b.h and b.alive)]
    bullets = [b for b in bullets if (b.y < HEIGHT + b.h and b.alive)]


    # DRAW
    for block in blocks:
        pygame.draw.rect(screen, block.color, block.rect)

    for bullet in bullets:
        pygame.draw.rect(screen, bullet.color, bullet.rect)

    for ai_agent in ai_agents:
        if ai_agent.alive:
            pygame.draw.rect(screen, ai_agent.color, ai_agent.rect)

    if player.alive:
        pygame.draw.rect(screen, player.color, player.rect)

    if DEBUG_SHOW_TOPK:
        debug_agent_ref = pick_debug_agent(ai_agents, preferred_index=DEBUG_AGENT_INDEX, prev=debug_agent_ref)

        if debug_agent_ref is not None:

            debug = debug_agent_ref
            topk = sort_threat_list(debug, bullets, blocks, K_THREATS, t_max=2.0)

            # highlight the agent
            pygame.draw.rect(screen, (255, 255, 0), (debug.x, debug.y, debug.w, debug.h), 3)

            # highlight agent's top k threat
            for i, threat in enumerate(topk):
                
                if not threat.valid or threat.source is None:
                    continue

                obj = threat.source
                pygame.draw.rect(screen, (255, 0, 255), (obj.x, obj.y, obj.w, obj.h), 4)

                # rank label
                rank_text = font.render(str(i+1), True, (255, 255, 255))
                screen.blit(rank_text, (obj.x, obj.y - 18))



    # Status
    alive_count = sum(ai_agent.alive for ai_agent in ai_agents)
    text = font.render(
        f"GEN: {GEN} | diff: {difficulty:.2f} | AI alive: {alive_count}",
        True,
        (0, 0, 0)
    )
    screen.blit(text, (20, 20))


    # Update
    pygame.display.flip()

pygame.quit()
sys.exit()