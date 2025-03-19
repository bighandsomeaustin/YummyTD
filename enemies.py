import pygame
import math
import game_tools


class Enemy:
    def __init__(self, position, health, money, speed, image_path, path=game_tools.house_path):
        self.position = position  # (x, y) tuple
        self.health = health
        self.money = money
        self.speed = speed
        self.path = path  # List of (x, y) points the enemy follows
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.img_death = pygame.image.load("assets/splatter.png").convert_alpha()
        self.size = self.rect.size  # Width and height of the enemy
        self.current_target = 0  # Current target index in the path
        self.is_alive = True
        self.sfx_splat = pygame.mixer.Sound("assets/splat_sfx.mp3")

    def move(self):
        # Move towards the next point in the path
        if self.current_target < len(self.path):
            target_x, target_y = self.path[self.current_target]
            dx = target_x - self.position[0]
            dy = target_y - self.position[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance == 0:  # Avoid division by zero
                return

            # Calculate normalized direction vector
            direction_x = dx / distance
            direction_y = dy / distance

            # Move enemy by speed in the direction of the target
            self.position = (
                self.position[0] + direction_x * self.speed,
                self.position[1] + direction_y * self.speed
            )
            self.rect.center = self.position

            # Rotate the enemy to face the target
            self.update_orientation(direction_x, direction_y)

            # Check if the enemy reached the target
            if distance <= self.speed:
                self.current_target += 1

        # If the enemy has reached the end of the path
        if self.current_target >= len(self.path):
            self.is_alive = False  # Mark as no longer active (escaped)
            game_tools.user_health -= self.health

    def update_orientation(self, direction_x, direction_y):
        """Rotate the image to face the movement direction."""
        # Calculate angle in radians and convert to degrees
        angle = math.degrees(math.atan2(-direction_y, direction_x))  # Flip y-axis for Pygame
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            game_tools.money += self.money

    def render(self, screen):
        # Draw the enemy on the screen
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        if not self.is_alive:
            screen.blit(self.img_death, self.rect.topleft)
            # Optionally, draw the health bar
            # pygame.draw.rect(screen, (255, 0, 0), (*self.rect.topleft, self.size[0], 5))
            # pygame.draw.rect(
            #     screen,
            #     (0, 255, 0),
            #     (*self.rect.topleft, self.size[0] * (self.health / 100), 5)
            # )


class AntEnemy(Enemy):
    def __init__(self, position, health=1, money=5, speed=1, image_path="assets/ant_base.png"):
        super().__init__(position, health, money, speed, image_path)


class HornetEnemy(Enemy):
    def __init__(self, position, health=3, money=10, speed=2, image_path="assets/hornet_base.png"):
        super().__init__(position, health, money, speed, image_path)
