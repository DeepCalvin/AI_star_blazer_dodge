import pygame

class Agent:

    def __init__(self, x, y, vx=0, ax=0, owner="AI", w=25, h=25, color=(0, 0, 255)):
        self.x = x
        self.y = y

        self.vx = vx
        self.ax = ax

        self.owner = owner

        self.w = w
        self.h = h

        self.alive = True

        self.color = color

        # Evolutionary stats
        self.time_alive = 0
        self.fitness = 0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)