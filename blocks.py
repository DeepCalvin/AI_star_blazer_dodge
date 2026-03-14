import pygame

class Block:

    def __init__(self, x, y, w, h, vy, ay, jy, shoot_cooldown, color):
        self.x = x
        self.y = y

        self.w = w
        self.h = h

        self.vy = vy # Vertical speed
        self.ay = ay # Vertical acc
        self.jy = jy # Vertical jerk

        self.shoot_cooldown = shoot_cooldown
        self.time_since_last_shot = 0

        self.alive = True

        self.color = color

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)
    

    