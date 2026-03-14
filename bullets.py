import pygame

BULLET_W, BULLET_H = 10, 40

class Bullet:

    def __init__(self, owner, x, y, vy, ay, jy, color, w=BULLET_W, h=BULLET_H):
        self.owner = owner

        self.x = x
        self.y = y

        self.w = w
        self.h = h

        self.vy = vy
        self.ay = ay
        self.jy = jy

        self.alive = True

        self.color = color

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)
    
