import pygame
import math
import game_tools

class Tower:
    def __init__(self, position, radius, weapon, damage, image_path, projectile_image, shoot_interval, speed, cost):
        self.position = position  # (x, y) tuple
        self.radius = radius # Tower Range
        self.angle = 0  # Default orientation
        self.weapon = weapon # Projectile
        self.damage = damage
        self.speed = speed
        self.cost = cost
        self.sell_amt = int(cost / 2)
        self.image = pygame.image.load(image_path).convert_alpha()
        self.original_image = self.image
        self.rect = self.image.get_rect(center=position)
        self.target = None  # Current target (e.g., enemy)
        self.projectiles = []  # List to manage active projectiles
        self.projectile_image = projectile_image  # Path to the projectile image
        self.shoot_interval = shoot_interval  # Interval in milliseconds
        self.last_shot_time = 0  # Tracks the last time the tower shot
        self.curr_top_upgrade = 0  # Tracks top upgrade status
        self.curr_bottom_upgrade = 0  # tracks bottom upgrade status
        self.penetration = False

    def update(self, enemies):
        # global last_time_sfx
        self.target = None
        potential_targets = []
        for enemy in enemies:
            distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                 (enemy.position[1] - self.position[1]) ** 2)
            if distance <= self.radius:
                potential_targets.append((distance, enemy))

        # Sort enemies by distance
        potential_targets.sort(key=lambda x: x[0])

        # Assign an enemy that is not already targeted by another tower
        for _, enemy in potential_targets:
            if not any(tower.target == enemy for tower in game_tools.towers if tower != self and not isinstance(tower, game_tools.RatTent)):
                self.target = enemy
                break  # Stop once a unique target is found

        # If all enemies are already targeted, pick the closest one
        if self.target is None and potential_targets:
            self.target = potential_targets[0][1]

        # Rotate towards the target if one is found
        if self.target:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]
            self.angle = math.degrees(math.atan2(-dy, dx))  # Negative for correct orientation
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(center=self.position)

        # Update all projectiles
        for projectile in self.projectiles[:]:
            projectile.move()
            if projectile.hit:  # Check if the projectile has hit the target
                if self.target is not None and self.target.is_alive:  # Apply damage if the target is still alive
                    self.target.take_damage(self.damage)
                if not self.penetration:
                    self.projectiles.remove(projectile)
                if self.penetration:
                    projectile.penetration -= 1
                    if projectile.penetration == 0:
                        self.projectiles.remove(projectile)

    def render(self, screen):
        # Draw the tower
        screen.blit(self.image, self.rect.topleft)
        # Optionally draw the radius for debugging
        # pygame.draw.circle(screen, (0, 255, 0), self.position, self.radius, 1)

        # Render all projectiles
        for projectile in self.projectiles:
            projectile.render(screen)

    def shoot(self, *args):
        # Shoot a projectile if enough time has passed since the last shot
        current_time = pygame.time.get_ticks()
        if self.target and current_time - self.last_shot_time >= self.shoot_interval:
            projectile = game_tools.Projectile(
                position=self.position,
                target=self.target,
                speed=self.speed,  # Speed of the projectile
                damage=self.damage,
                image_path=self.projectile_image
            )
            if self.penetration:
                projectile.penetration = self.damage - round((self.damage / 2))
            self.projectiles.append(projectile)
            self.last_shot_time = current_time

class MrCheese(Tower):
    def __init__(self, position, radius=100, weapon="Cheese", damage=1, image_path="assets/base_rat.png", projectile_image="assets/projectile_cheese.png", shoot_interval=1000, speed=10, cost=150):
        super().__init__(position, radius, weapon, damage, image_path, projectile_image, shoot_interval, speed, cost)
        self.sfx_squeak = pygame.mixer.Sound("assets/mouse-squeak.mp3")

    def update(self, enemies):
        super().update(enemies)
        current_time = pygame.time.get_ticks()
        if current_time - game_tools.last_time_sfx >= 15000:
            self.sfx_squeak.play()
            pygame.mixer.Sound("assets/mouse-squeak.mp3").play()
            game_tools.last_time_sfx = current_time

class RatTent(Tower):
    def __init__(self, position, radius=50, weapon="Recruit", health=1, damage=1, image_path="assets/base_camp.png", projectile_image="assets/rat_recruit.png", shoot_interval=2000, speed=1, cost=500):
        super().__init__(position, radius, weapon, damage, image_path, projectile_image, shoot_interval, speed, cost)
        self.health = health

    def update(self, enemies):
        pass

    def shoot(self, enemies):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_interval and game_tools.RoundFlag:
            recruit_entity = game_tools.RecruitEntity(self.position, 1, 1, game_tools.recruit_path, 1, self.projectile_image)
            closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
            distance = ((closest_spawn_point[0] - self.position[0]) ** 2 + (closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
            if distance <= self.radius:
                recruit = game_tools.RecruitEntity(
                    position=closest_spawn_point,
                    health=self.health,
                    speed=self.speed,
                    path=game_tools.recruit_path,
                    damage=self.damage,
                    image_path=self.projectile_image
                )
                self.projectiles.append(recruit)
                self.last_shot_time = current_time

        for recruit in self.projectiles[:]:
            recruit.update(enemies)
            if not recruit.is_alive:
                self.projectiles.remove(recruit)
            if not game_tools.RoundFlag:
                self.projectiles.remove(recruit)
