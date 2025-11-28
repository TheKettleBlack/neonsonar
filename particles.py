import pygame

class Particle(pygame.sprite.Sprite):
    def __init__(self, groups, pos, color, direction, speed, lifetime=60):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.color = color
        self.direction = (
            direction.normalize() 
            if direction.length() != 0 
            else pygame.math.Vector2(0, -1)
        )
        self.speed = speed
        self.lifetime = lifetime
        self.age = 0
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (4, 4), 4)
        self.rect = self.image.get_rect(center=pos)
    def update(self):
        self.pos += self.direction * self.speed
        self.rect.center = self.pos
        self.age += 1
        alpha = max(0, 255 * (1 - self.age / self.lifetime))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (*self.color[:3], int(alpha)), (4, 4), 4)
        if alpha <= 0:
            self.kill()
