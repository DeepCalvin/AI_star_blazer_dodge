import random
import pygame
from blocks import Block

def get_color(name: str) -> tuple:
    color_dict = {
        "white": (255, 255, 255),
        'orange': (255,127,80), # bullets
        "yellow": (255, 255, 0), # blocks
        "light_blue": (173, 216, 230) # ai_agent color
    }

    return color_dict[name] if name in color_dict else (0, 0, 0)



def spawn_block(block_list: list, screen_width: int, difficulty: float):

    # Width
    W_MIN, W_MAX = 100, 150
    w = random.randint(W_MIN, W_MAX)
    
    # Height
    H_MIN, H_MAX = 100, 150
    h = random.randint(H_MIN, H_MAX)

    # Spawn position (x)
    X_MIN, X_MAX = 0, screen_width-w
    x_pos = random.randint(X_MIN, X_MAX)

    # Vertical vel
    VY_MIN, VY_MAX = 200, 300
    vy = random.randint(VY_MIN, VY_MAX)
    vy = int(vy * (1 + difficulty))

    # Vertical acc
    AY_MIN, AY_MAX = 275, 325
    ay = random.randint(AY_MIN, AY_MAX)
    ay = int(ay * (1 + difficulty))

    # Vertical jerk
    J_MIN, J_MAX = 100, 150
    jy = random.randint(J_MIN, J_MAX)
    jy = int(jy * (1 + difficulty))

    # Shoot cooldown
    CD_MIN, CD_MAX = 0.6, 1.8
    cd = random.uniform(CD_MIN, CD_MAX)
    cd = cd / (1 + 0.4 * difficulty)
    cd = max(0.25, cd)

    # Spawn position (y)
    y_pos = -h

    # Spawn loop
    MAX_TRIES = 200
    TOP_ZONE_Y = 200
    for _ in range(MAX_TRIES):

        test_rect = pygame.Rect(x_pos, y_pos, w, h)
        collision = False

        for block in block_list:
            if block.y > TOP_ZONE_Y:
                continue

            if test_rect.colliderect(block.rect):
                collision = True
                break

        if not collision:
            return Block(x_pos, y_pos, w, h, vy, ay, jy, cd, color=get_color("yellow"))

    return None


