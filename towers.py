import math
import game_tools
import pygame


class Tower:
    # sfx_squeak = pygame.mixer.Sound("assets/mouse-squeak.mp3")

    def __init__(self, position, radius, weapon, damage, image_path, projectile_image,
                 speed, cost, shoot_interval=1000):
        self.position = position  # (x, y) tuple
        self.speed = speed
        self.radius = radius
        self.weapon = weapon
        self.damage = damage
        self.image = pygame.image.load(image_path).convert_alpha()
        self.original_image = self.image
        self.rect = self.image.get_rect(center=position)
        self.angle = 0  # Default orientation
        self.target = None  # Current target (e.g., enemy)
        self.projectiles = []  # List to manage active projectiles
        self.projectile_image = projectile_image  # Path to the projectile image
        self.shoot_interval = shoot_interval  # Interval in milliseconds
        self.last_shot_time = 0  # Tracks the last time the tower shot
        self.curr_top_upgrade = 0  # Tracks top upgrade status
        self.curr_bottom_upgrade = 0  # tracks bottom upgrade status
        self.penetration = False
        self.cost = cost
        self.sell_amt = int(cost / 2)

    def update(self, enemies):
        self.target = None
        potential_targets = []
        # Gather all enemies within range
        for enemy in enemies:
            distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                 (enemy.position[1] - self.position[1]) ** 2)
            if distance <= self.radius:
                potential_targets.append((distance, enemy))

        # Sort enemies by distance
        potential_targets.sort(key=lambda x: x[0])

        # Assign an enemy that is not already targeted by another tower
        for _, enemy in potential_targets:
            if not any(tower.target == enemy for tower in game_tools.towers if tower != self
            and not isinstance(tower, game_tools.RatTent)):
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
    def __init__(self, position, radius, weapon, damage, image_path,
                 projectile_image, speed=10, cost=150, shoot_interval=1000):
        super().__init__(position, radius, weapon, damage, image_path, projectile_image, speed, cost, shoot_interval)

    def update(self, enemies):
        super().update(enemies)

    def render(self, screen):
        super().render(screen)

    def shoot(self, enemies):
        super().shoot(enemies)


class RatTent(Tower):
    def __init__(self, position, radius=50, weapon="Recruit", health=1, damage=1, image_path="assets/base_camp.png",
                 projectile_image="assets/rat_recruit.png", speed=1, cost=650, shoot_interval=2000):
        super().__init__(position, radius, weapon, damage, image_path, projectile_image, speed, cost, shoot_interval)
        self.health = health

    def update(self, enemies):
        pass

    def shoot(self, enemies):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_interval and game_tools.RoundFlag:
            recruit_entity = game_tools.RecruitEntity(self.position, 1, 1,
                                                      game_tools.recruit_path, 1, self.projectile_image)
            closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
            distance = ((closest_spawn_point[0] - self.position[0]) ** 2 +
                        (closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
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


class Ozbourne(Tower):
    def __init__(self, position, radius=100, weapon="guitar", damage=1, riff_blast_radius=75,
                 image_path="assets/alfredo_ozbourne_base.png",
                 projectile_image="assets/alfredo_ozbourne_amplifier.png",
                 riff_interval=4000, cost=500, speed=1):
        super().__init__(position, radius, weapon, damage, image_path, projectile_image, speed, cost, riff_interval)
        self.riff_interval = riff_interval  # Interval in milliseconds
        self.riff_blast_radius = riff_blast_radius  # Blast effect radius
        self.last_blast_time = 0  # Tracks last time the tower blasted
        self.blast_active = False
        self.blast_animation_timer = 0
        self.blast_duration = 1165  # Duration of the blast effect in ms
        self.blast_radius = 0  # Expanding effect
        self.max_blast_radius = self.riff_blast_radius  # Maximum visual blast size
        self.riff_count = 0
        self.damage_default = self.damage
        self.riff_sfx = pygame.mixer.Sound("assets/riff1.mp3")

    def update(self, enemies):
        current_time = pygame.time.get_ticks()

        # Check if enough time has passed to trigger a blast
        if current_time - self.last_blast_time >= self.riff_interval:
            # Check if any enemies are in range
            for enemy in enemies:
                distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                     (enemy.position[1] - self.position[1]) ** 2)
                if distance <= self.radius:
                    self.shoot(enemies)
                    break  # Stop checking once a blast is triggered
                else:
                    self.riff_count = 0
                    self.riff_sfx.stop()
                    self.damage = 1

        # Handle blast animation timing
        if self.blast_active:
            self.blast_animation_timer += pygame.time.get_ticks() - self.last_blast_time
            self.blast_radius += (self.max_blast_radius / self.blast_duration) * (
                        pygame.time.get_ticks() - self.last_blast_time)

            if self.blast_animation_timer >= self.blast_duration:
                self.blast_active = False
                self.blast_radius = 0  # Reset blast visual

        if not game_tools.RoundFlag:
            self.damage = 1
            self.riff_sfx.stop()
            self.riff_count = 0

    def shoot(self, enemies):
        """Triggers an AoE attack damaging enemies in range."""
        if self.curr_bottom_upgrade < 1:
            self.riff_sfx.play()
        elif self.curr_bottom_upgrade >= 1:
            self.riff_count += 1
            if self.riff_count == 1:
                self.riff_sfx.play()
            elif self.riff_count >= 88:
                self.riff_count = 0
            self.damage += (self.riff_count * .1)

        self.last_blast_time = pygame.time.get_ticks()
        self.blast_active = True
        self.blast_animation_timer = 0
        self.blast_radius = 0  # Reset the expanding effect

        # Apply damage to enemies within blast radius
        for enemy in enemies:
            distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                 (enemy.position[1] - self.position[1]) ** 2)
            if distance <= self.riff_blast_radius:
                enemy.take_damage(self.damage)

    def render(self, screen):
        # Draw the tower
        screen.blit(self.image, self.rect.topleft)
        # Render the blast effect
        if self.blast_active:
            # Normalize damage scale between 0 (default) and 1 (fully red)
            normalized_damage = int((self.damage - 1) / (9.8 - 1))  # Scale between 1 and 4.25

            # Ensure normalized_damage is clamped between 0 and 1
            normalized_damage = max(0, min(1, normalized_damage))

            # Interpolate color from (255, 200, 100) to (255, 0, 0)
            r = 255  # Always stays at max
            g = int(200 * (1 - normalized_damage))  # Decreases with damage
            b = int(100 * (1 - normalized_damage))  # Decreases with damage

            pygame.draw.circle(
                screen,
                (r, g, b),  # RGB without alpha (pygame doesn't support alpha in draw functions)
                self.position,
                int(self.blast_radius),
                2  # Thin outline
            )
# towers