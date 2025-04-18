import pygame
import math
import random
import game_tools
import game_stats


class Enemy:
    def __init__(self, position, health, speed, path, image_path, money):
        if position:
            self.position = position
        self.health = health
        self.money = money
        self.speed = speed
        self.path = path
        self.original_image = game_tools.load_image(image_path)
        self.sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
        self.img_death = game_tools.load_image("assets/splatter.png")
        self.image = self.original_image
        if position:
            self.rect = self.image.get_rect(center=position)
        if position:
            self.size = self.rect.size
            self.is_alive = True
        self.current_target = 0
        # game_tools.global_impact_particles = []  # New: Particle storage

    def move(self):
        if self.current_target < len(self.path):
            target_x, target_y = self.path[self.current_target]
            dx = target_x - self.position[0]
            dy = target_y - self.position[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance == 0:
                return
            direction_x = dx / distance
            direction_y = dy / distance
            self.position = (
                self.position[0] + direction_x * self.speed,
                self.position[1] + direction_y * self.speed
            )
            self.rect.center = self.position
            self.update_orientation(direction_x, direction_y)
            if distance <= self.speed:
                self.current_target += 1
        if self.current_target >= len(self.path):
            self.is_alive = False
            game_tools.user_health -= self.health

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def show_damage_indicator(self, damage):
        # Create a damage text surface using a shared font.
        font = pygame.font.SysFont("impact", 20, bold=False)
        text_surface = font.render(f"{damage:.1f}", True, (255, 0, 0))
        text_surface.set_alpha(128)

        angle_deg = random.uniform(-45, 45)
        angle_rad = math.radians(angle_deg)

        # Speed magnitude
        speed = random.uniform(.5, 2)

        # Convert polar to cartesian velocity
        vel_x = math.sin(angle_rad) * speed
        vel_y = -math.cos(angle_rad) * speed  # negative because up is -y in Pygame

        # Set up the indicator's properties.
        indicator = {
            'surface': text_surface,
            'pos': list(self.rect.center) + [0, -20],  # starting at the enemy's center
            'vel': [vel_x, vel_y],
            'lifetime': random.randint(100, 250),  # milliseconds
            'start_time': pygame.time.get_ticks()
        }
        if len(game_tools.global_damage_indicators) < game_tools.MAX_INDICATORS:
            game_tools.global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        self.health -= damage
        self.show_damage_indicator(damage)
        game_tools.spawn_shard(
            pos=self.position,
            color=(255, 255, 255),
            count=4,
            speed=3,
            radius_range=(1, 3),
            lifetime_range=(100, 600)
        )
        if self.health <= 0:
            self.is_alive = False
            game_stats.global_kill_total["count"] += 1
            self.sfx_splat.play()
            game_tools.money += self.money

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)

    def spawn_shards(self, count=5):
        for _ in range(count):
            game_tools.spawn_shard(self.position, count=5)

    def update_shards(self, screen, color):
        current_time = pygame.time.get_ticks()
        for shard in game_tools.global_impact_particles[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                game_tools.global_impact_particles.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (color, alpha)
                shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))


class AntEnemy(Enemy):
    def __init__(self, position, health, speed, path, image_path, money=2):
        super().__init__(position, health, speed, path, image_path, money)

    def update_shards(self, screen, color=(255, 255, 255)):
        super().update_shards(screen, color)

class BeetleEnemy(Enemy):
    def __init__(self, position, path, image_path="assets/beetle_base.png", health=6, speed=0.5, money=10):
        """
        Initialize a BeetleEnemy.
        :param position: Starting (x, y) tuple.
        :param path: List of waypoints (tuples) to follow.
        """
        super().__init__(position, health, speed, path, image_path, money)
        # Movement properties
        self.position = position
        self.path = path
        self.current_target = 1  # start toward the second point
        self.speed = 0.5  # Half as fast as the Ant (which moves at 1)

        # Health and armor properties
        self.base_health = 6  # Health after armor is gone
        self.health = self.base_health
        self.total_armor_layers = 3  # Three layers of armor
        self.current_armor_layer = self.total_armor_layers
        self.current_layer_health = 5  # Each armor layer has 5 health

        # Load images
        self.base_image = game_tools.load_image("assets/beetle_base.png")
        self.image = self.base_image
        self.original_image = self.image

        # Set up rect for positioning/collision
        self.rect = self.image.get_rect(center=self.position)

        self.is_alive = True

        # Load sound effects
        self.armor_hit_sound = game_tools.load_sound("assets/armor_hit.mp3")
        self.armor_break_sound = game_tools.load_sound("assets/armor_break.mp3")

        # Shard effect properties for armor break
        # game_tools.global_impact_particles = []  # List to store shard particles

    def move(self):
        """
        Move the beetle along its predefined path.
        """
        if self.current_target < len(self.path):
            target_point = self.path[self.current_target]
            dx = target_point[0] - self.position[0]
            dy = target_point[1] - self.position[1]
            distance = math.hypot(dx, dy)
            if distance == 0:
                return
            direction_x = dx / distance
            direction_y = dy / distance
            self.position = (
                self.position[0] + direction_x * self.speed,
                self.position[1] + direction_y * self.speed
            )
            self.rect.center = self.position
            self.update_orientation(direction_x, direction_y)
            if distance <= self.speed:
                self.current_target += 1
        else:
            # Reached the end of the path; mark as not alive
            game_tools.user_health -= self.base_health + self.total_armor_layers * self.current_layer_health
            self.is_alive = False

    def spawn_shards(self, count=5):
        """
        Spawn a burst of shards to simulate armor breaking.
        Each shard is represented as a dictionary with position, velocity, lifetime, and start_time.
        """
        for _ in range(count):
            game_tools.spawn_shard(self.position, count=5)

    def update_shards(self, screen, color=(255, 255, 255)):
        super().update_shards(screen, color)

    def render(self, screen: pygame.Surface):
        """
        Render the beetle on the given screen along with shard particles if any.
        """
        screen.blit(self.image, self.rect.topleft)

    def take_damage(self, damage, projectile=None):
        """
        Process incoming damage. If the projectile has an attribute armor_break,
        remove all armor instantly and spawn shards. Otherwise, apply damage to armor first.
        """
        # Check if the projectile has the armor_break attribute
        if projectile is not None and getattr(projectile, "armor_break", False):
            # Play the armor break sound only if there is still armor
            if self.current_armor_layer > 0:
                self.armor_break_sound.play()

            # Spawn shards effect
            self.spawn_shards(count=5)

            # Instantly remove all armor layers
            self.current_armor_layer = 0
            self.current_layer_health = 0

            # Update the image to final damage state
            self.original_image = game_tools.load_image("assets/beetle_damage3.png")
            self.image = self.original_image

            # Apply full damage to base health
            self.health -= damage
            self.show_damage_indicator(damage)
            if self.health <= 0:
                self.is_alive = False
                game_stats.global_kill_total["count"] += 1
                game_tools.money += 10
            return  # Exit immediately to prevent normal armor processing

        # For every hit, play the armor hit sound if armor is present
        if self.current_armor_layer > 0:
            self.armor_hit_sound.play()

        # Normal damage processing (when not armor_break)
        if self.current_armor_layer > 0:
            self.current_layer_health -= damage
            self.show_damage_indicator(damage)
            if self.current_layer_health <= 0:
                overflow = -self.current_layer_health
                self.current_armor_layer -= 1

                # Spawn shards effect on armor layer break
                self.spawn_shards(count=5)

                # If breaking the last armor layer, play the armor break sound
                if self.current_armor_layer == 0:
                    self.armor_break_sound.play()

                # Update the image based on armor remaining
                if self.current_armor_layer == 2:
                    self.original_image = game_tools.load_image("assets/beetle_damage1.png")
                elif self.current_armor_layer == 1:
                    self.original_image = game_tools.load_image("assets/beetle_damage2.png")
                elif self.current_armor_layer == 0:
                    self.original_image = game_tools.load_image("assets/beetle_damage3.png")
                self.image = self.original_image

                # Reset armor health unless all armor is broken
                if self.current_armor_layer > 0:
                    self.current_layer_health = 5

                # If there is overflow damage after breaking armor, apply it to health
                if self.current_armor_layer == 0 and overflow > 0:
                    self.health -= overflow
                    self.show_damage_indicator(damage)
        else:
            # No armor remains; apply damage directly to base health.
            self.health -= damage
            self.show_damage_indicator(damage)

        if self.health <= 0:
            self.is_alive = False
            game_stats.global_kill_total["count"] += 1
            game_tools.money += 10


class HornetEnemy(Enemy):
    def __init__(self, position, health, speed, path, image_path, money=4):
        super().__init__(position, health, speed, path, image_path, money)

    def update_shards(self, screen, color=(255, 255, 255)):
        super().update_shards(screen, color)

class SpiderEnemy(Enemy):
    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")

    def __init__(self, position, path, health=5, speed=1.5, image_path="assets/spider_frames/spider0.png", money=6):
        super().__init__(position, health, speed, path, image_path, money)
        self.frames = ["assets/spider_frames/spider0.png", "assets/spider_frames/spider1.png",
                       "assets/spider_frames/spider2.png", "assets/spider_frames/spider3.png",
                       "assets/spider_frames/spider4.png"]
        self.current_frame = 0
        self.frame_duration = 175  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        # game_tools.global_impact_particles = []  # NEW: Particle storage

    def take_damage(self, damage, projectile=None):
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()  # NEW: Create particles on hit
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            game_tools.money += self.money
            game_stats.global_kill_total["count"] += 1

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_tools.game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = game_tools.load_image(self.frames[self.current_frame])
            self.original_image = game_tools.load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

    def update_shards(self, screen, color=(255, 255, 255)):
        super().update_shards(screen, color)

    def move(self):
        super().move()
        self.update_animation()


class FireflyEnemy(Enemy):
    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")
    MAX_RADIUS = 75
    MIN_RADIUS = 0
    BASE_COLOR = (247, 217, 59)

    def __init__(self, position, path, health=20, speed=1, image_path="assets/firefly_frames/firefly0.png", money=10):
        super().__init__(position, health, speed, path, image_path, money)
        self.position = position
        self.health = 20
        self.money = 10
        self.speed = 1
        self.path = path
        self.frames = ["assets/firefly_frames/firefly0.png", "assets/firefly_frames/firefly1.png",
                       "assets/firefly_frames/firefly2.png", "assets/firefly_frames/firefly3.png",
                       "assets/firefly_frames/firefly4.png", "assets/firefly_frames/firefly5.png",
                       "assets/firefly_frames/firefly6.png"]
        self.current_frame = 0
        self.frame_duration = 75  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        self.original_image = game_tools.load_image("assets/firefly_frames/firefly0.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        # game_tools.global_impact_particles = []  # NEW: Particle storage
        self.health = 20
        self.initial_health = self.health  # Store for healing cap
        self.affected_enemies = []
        self.protected_enemies = {}  # Track enemy: last_health
        self.last_heal_time = pygame.time.get_ticks()
        self.glow_layers = [
            {'base_radius': 45, 'current_radius': 0, 'alpha': 0, 'speed': 2.5},
            {'base_radius': 55, 'current_radius': 0, 'alpha': 0, 'speed': 2.0},
            {'base_radius': 65, 'current_radius': 0, 'alpha': 0, 'speed': 1.5}
        ]
        self.max_glow_radius = max(l['base_radius'] for l in self.glow_layers) + 10
        self.base_health = self.health  # Used for radius calculation

        # Glow properties
        self.glow_phase = 0
        self.glow_surface = pygame.Surface((self.MAX_RADIUS * 2, self.MAX_RADIUS * 2), pygame.SRCALPHA)
        self.glow_rect = self.glow_surface.get_rect()

    def get_current_radius(self):
        """Calculate radius based on current health"""
        health_ratio = max(0, self.health) / self.base_health
        ratio_clamped = min(health_ratio, 1.0)  # clamp to max 1.0
        return self.MIN_RADIUS + (self.MAX_RADIUS - self.MIN_RADIUS) * ratio_clamped

    def update_heal_effect(self, enemies):
        current_radius = self.get_current_radius()
        current_time = pygame.time.get_ticks()

        # Update protected enemies list
        new_protected = [
            enemy for enemy in enemies
            if enemy.is_alive
               and not isinstance(enemy, FireflyEnemy)
               and math.dist(self.position, enemy.position) <= current_radius
        ]

        # Check for damage reflection
        for enemy in new_protected:
            # Initialize tracking for new enemies
            if enemy not in self.protected_enemies:
                self.protected_enemies[enemy] = enemy.health

            # Calculate damage taken since last frame
            damage_taken = self.protected_enemies[enemy] - enemy.health
            if damage_taken > 0:
                # Apply reflected damage to self
                self.health -= damage_taken * 0.5
                self.create_reflection_effect()

            # Update stored health
            self.protected_enemies[enemy] = enemy.health

        # Clean up dead/out-of-range enemies
        for enemy in list(self.protected_enemies.keys()):
            if enemy not in new_protected or not enemy.is_alive:
                del self.protected_enemies[enemy]

        # Update affected enemies list
        self.affected_enemies = [
            enemy for enemy in enemies
            if enemy.is_alive
               and not isinstance(enemy, FireflyEnemy)
               and math.dist(self.position, enemy.position) <= current_radius
        ]

        # Healing and protection logic
        if current_time - self.last_heal_time >= 750:
            self.last_heal_time = current_time
            for enemy in self.affected_enemies:
                enemy.health = max(enemy.health, 0.5)
                enemy.health += 1
        else:
            for enemy in self.affected_enemies:
                enemy.health = max(enemy.health, 0.5)

    def create_reflection_effect(self):
        # Visual feedback for damage reflection
        for _ in range(2):
            particle = {
                'pos': list(self.position),
                'vel': [random.uniform(-2, 2), random.uniform(-2, 2)],
                'lifetime': random.randint(200, 400),
                'start_time': pygame.time.get_ticks(),
                'color': (255, 0, 0),  # Red particles for damage reflection
                'radius': random.randint(1, 2)
            }
            game_tools.global_impact_particles.append(particle)

    def update_glow_animation(self):
        """Update glow animation based on health and phase"""
        self.glow_phase += 0.05
        if self.glow_phase > 2 * math.pi:
            self.glow_phase -= 2 * math.pi

    def render_glow(self, screen):
        current_radius = self.get_current_radius()
        self.glow_surface.fill((0, 0, 0, 0))

        # Core glow
        core_alpha = int(80 + math.sin(self.glow_phase) * 40)
        pygame.draw.circle(
            self.glow_surface,
            (*self.BASE_COLOR, core_alpha),
            (current_radius, current_radius),
            int(current_radius * 0.8 + math.sin(self.glow_phase) * 3)
        )

        # Pulse effect
        pulse_radius = current_radius * 1.2
        pulse_alpha = int(40 + math.sin(self.glow_phase + 1) * 20)
        pygame.draw.circle(
            self.glow_surface,
            (*self.BASE_COLOR, pulse_alpha),
            (current_radius, current_radius),
            int(pulse_radius + math.sin(self.glow_phase + 0.5) * 5),
            width=3
        )

        # Outer aura
        aura_radius = current_radius * 1.5
        aura_alpha = int(20 + math.sin(self.glow_phase + 2) * 10)
        pygame.draw.circle(
            self.glow_surface,
            (*self.BASE_COLOR, aura_alpha),
            (current_radius, current_radius),
            int(aura_radius),
            width=2
        )

        # Position and draw
        screen.blit(self.glow_surface, (
            self.position[0] - current_radius,
            self.position[1] - current_radius
        ))

    def update_shards(self, screen, color=(247, 217, 59)):
        super().update_shards(screen, color)

    def take_damage(self, damage, projectile=None):
        original_health = self.health
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()

        # Prevent negative health
        self.health = max(self.health, 0)

        # Visual feedback when taking damage
        if original_health != self.health:
            self.create_protection_effect()

        if self.health <= 0:
            self.protected_enemies.clear()
            self.is_alive = False
            self.sfx_splat.play()
            game_tools.money += self.money
            game_stats.global_kill_total["count"] += 1

    def create_protection_effect(self):
        # Create shield burst effect
        for _ in range(5):
            particle = {
                'pos': list(self.position),
                'vel': [random.uniform(-3, 3), random.uniform(-3, 3)],
                'lifetime': random.randint(300, 600),
                'start_time': pygame.time.get_ticks(),
                'color': (247, 217, 59),
                'radius': random.randint(2, 4)
            }
            game_tools.global_impact_particles.append(particle)

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_tools.game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = game_tools.load_image(self.frames[self.current_frame])
            self.original_image = game_tools.load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

class DragonflyEnemy(Enemy):
    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")

    def __init__(self, position, path, health=3, speed=3, image_path="assets/dragonfly_frames/dragonfly0.png", money=10):
        super().__init__(position, health, speed, path, image_path, money)
        self.frames = ["assets/dragonfly_frames/dragonfly0.png", "assets/dragonfly_frames/dragonfly1.png",
                       "assets/dragonfly_frames/dragonfly2.png", "assets/dragonfly_frames/dragonfly3.png"]
        self.current_frame = 0
        self.frame_duration = 75  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        # game_tools.global_impact_particles = []  # NEW: Particle storage

    def move(self):
        self.update_animation()
        super().move()

    def take_damage(self, damage, projectile=None):
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()  # NEW: Create particles on hit
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            game_tools.money += self.money
            game_stats.global_kill_total["count"] += 1

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_tools.game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = game_tools.load_image(self.frames[self.current_frame])
            self.original_image = game_tools.load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time


class MantisBoss(Enemy):
    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")

    def __init__(self, position, path, health=250, speed=.15, image_path="assets/mantis_frames/mantis0.png", money=10):
        super().__init__(position, health, speed, path, image_path, money)
        self.radius = 250
        self.frames = []
        for i in range(0, 15):
            self.frames.append(f"assets/mantis_frames/mantis{i}.png")
        self.current_frame = 0
        self.frame_duration = 125  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        self.target = None
        self.shoot_interval = 15000
        self.shoot_sound = game_tools.load_sound("assets/mantis_shoot.mp3")
        self.last_shot_time = 0
        self.projectiles = []

    def move(self):
        self.update_animation()

        # === Targeting ===
        self.target = None
        potential_targets = []
        for enemy in game_tools.towers:
            distance = math.hypot(enemy.position[0] - self.position[0],
                                  enemy.position[1] - self.position[1])
            if distance <= self.radius:
                potential_targets.append((distance, enemy))
        potential_targets.sort(key=lambda x: x[0])
        if potential_targets:
            self.target = potential_targets[0][1]

        if self.target:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]
            angle = math.degrees(math.atan2(-dy, dx))
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.position)
            self.shoot()

        # === Process Projectiles ===
        for projectile in self.projectiles[:]:
            projectile.move()
            for enemy in game_tools.towers:
                enemy_center = enemy.rect.center
                dist = math.hypot(projectile.position[0] - enemy_center[0],
                                  projectile.position[1] - enemy_center[1])
                if dist < enemy.rect.width / 2:
                    projectile.hit = True
                    game_tools.spawn_shard(projectile.position, color=(105, 160, 25), count=25)
                    if hasattr(enemy, "shoot_interval"):
                        game_tools.apply_mantis_debuff(enemy)
            if projectile.hit:
                self.projectiles.remove(projectile)
        super().move()

    def shoot(self):
        scaled_interval = self.shoot_interval / game_tools.game_speed_multiplier
        if self.target and pygame.time.get_ticks() - self.last_shot_time >= scaled_interval:
            self.shoot_sound.play()
            proj = game_tools.Projectile(self.position, self.target, speed=5, damage=0, image_path="assets/mantis_ball.png")
            self.projectiles.append(proj)
            self.last_shot_time = pygame.time.get_ticks()

    def take_damage(self, damage, projectile=None):
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()  # NEW: Create particles on hit
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            game_tools.money += 10
            game_stats.global_kill_total["count"] += 1

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_tools.game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = game_tools.load_image(self.frames[self.current_frame])
            self.original_image = game_tools.load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

    def render(self, screen):
        super().render(screen)
        for projectile in self.projectiles:
            projectile.render(screen)


class TermiteEnemy(Enemy):

    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")

    def __init__(self, path, position=None, health=1, speed=1, image_path="assets/termite.png", money=4):
        """
        Initializes the TermiteEnemy.
        :param path: A list of (x, y) tuples representing the enemy's path.
        :param position: Optional starting position; if None, uses the first point in the path.
        """
        if position is None:
            super().__init__(path[0], health, speed, path, image_path, money)
            self.current_target = 1
        else:
            super().__init__(position, health, speed, path, image_path, money)
            # Find the closest point in the path to the given position.
            closest_dist = float('inf')
            closest_index = 0
            for i, point in enumerate(path):
                dist = math.hypot(position[0] - point[0], position[1] - point[1])
                if dist < closest_dist:
                    closest_dist = dist
                    closest_index = i
            if closest_index + 1 < len(path):
                self.current_target = closest_index + 1
            else:
                self.current_target = closest_index
        self.rotated_image = self.image  # Will be updated with rotation.

        # Use virtual time (real ticks * game_tools.game_speed_multiplier) for burrow timing.
        self.next_burrow_time = 0
        self.is_burrowed = False
        self.burrow_start_time = 0
        self.burrow_duration = 1000  # Duration in virtual ms

    def move(self):
        """Moves normally along the path."""
        if self.is_burrowed:
            if pygame.time.get_ticks() - self.burrow_start_time >= self.burrow_duration:
                self.finish_burrow()
                self.is_burrowed = False
        else:
            if pygame.time.get_ticks() >= self.next_burrow_time:
                self.start_burrow()

        super().move()

        if self.is_burrowed:
            game_tools.spawn_shard(self.position, color=(139, 69, 19), count=1)

    def start_burrow(self):
        """
        Initiates the burrow:
          - Plays the pop sound.
          - Spawns brown particles at the current location.
          - Sets the termite as burrowed and chooses a random virtual burrow duration (1000–3000 ms).
        """
        dig_sfx = game_tools.load_sound("assets/dig.mp3")
        dig_sfx.play()
        game_tools.spawn_shard(self.position, color=(139, 69, 19), count=10)
        self.is_burrowed = True
        self.burrow_start_time = pygame.time.get_ticks()
        self.burrow_duration = random.randint(1500, 5500) / game_tools.game_speed_multiplier
        self.speed = random.uniform(.1, 1.0)

    def finish_burrow(self):
        """
        Finishes burrowing:
          - Advances the termite five waypoints ahead. If that index equals the path end,
            reappear at the last point before the final.
          - Spawns particles at the new location.
          - Resets burrow state and sets the next burrow virtual time.
        """
        pop_sound = game_tools.load_sound("assets/pop.mp3")
        pop_sound.play()
        game_tools.spawn_shard(self.position, color=(139, 69, 19), count=10)
        self.is_burrowed = False
        self.next_burrow_time = pygame.time.get_ticks() + random.randint(4000, 8000) / game_tools.game_speed_multiplier
        self.speed = 1

    def take_damage(self, amount, projectile=None):
        """
        Reduces health by amount, shows a damage indicator, and if health falls to zero,
        increments the global kill count and awards money.
        """
        if self.is_burrowed:
            return
        self.health -= amount
        self.show_damage_indicator(amount)
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            self.sfx_splat.play()
            game_tools.spawn_shard(self.position)
            import game_stats  # Ensure game_stats is imported
            game_stats.global_kill_total["count"] += 1
            game_tools.money += 4

    def render(self, screen):
        """
        Draws the termite on the screen only if it is not burrowed.
        """
        if not self.is_burrowed:
            super().render(screen)


class DungBeetleBoss(Enemy):
    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")
    sfx_squeak = game_tools.load_sound("assets/dungbeetle_squeak.mp3")
    sfx_shield = game_tools.load_sound("assets/dungbeetle_shield.mp3")
    sfx_death = game_tools.load_sound("assets/dungbeetle_death.mp3")

    def __init__(self, position, path, health=175, speed=.15, image_path="assets/dungbeetle_frames/dung0.png", money=100):
        super().__init__(position, health, speed, path, image_path, money)
        self.frames = ["assets/dungbeetle_frames/dung0.png", "assets/dungbeetle_frames/dung1.png",
                       "assets/dungbeetle_frames/dung2.png", "assets/dungbeetle_frames/dung3.png",
                       "assets/dungbeetle_frames/dung4.png", "assets/dungbeetle_frames/dung5.png",
                       "assets/dungbeetle_frames/dung6.png", "assets/dungbeetle_frames/dung7.png",
                       "assets/dungbeetle_frames/dung8.png", "assets/dungbeetle_frames/dung9.png",
                       "assets/dungbeetle_frames/dung10.png"]
        self.current_frame = 0
        self.frame_duration = 250  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        # game_tools.global_impact_particles = []  # for hit/blue particle effects

        # Squeak timer: play squeak sound every random interval (3000-10000ms)
        self.next_squeak_time = pygame.time.get_ticks() + random.randint(2000, 5000)

        # Health threshold for triggering shield effects every 10 points lost.
        self.next_threshold = self.health - 60

        # For trailing particles when health is below 10
        self.trail_particles = []

    def move(self):
        current_time = pygame.time.get_ticks()
        self.update_animation()

        # Squeak sound logic.
        if current_time >= self.next_squeak_time:
            self.sfx_squeak.play()
            self.next_squeak_time = current_time + random.randint(3000, 10000)

        # Low health boost: if health below 10, speed increases and trail particles spawn.
        if self.health < 10:
            self.speed = 1.5
            self.spawn_trail_particle()

        # Movement along the path.
        super().move()

        # Update trail particles.
        self.update_trail_particles()

    def spawn_trail_particle(self):
        # Create a subtle blue trail particle when health is low.
        particle = {
            'pos': [self.position[0], self.position[1]],
            'vel': [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)],
            'lifetime': random.randint(300, 600),
            'start_time': pygame.time.get_ticks(),
            'radius': random.randint(2, 4)
        }
        self.trail_particles.append(particle)

    def update_trail_particles(self):
        current_time = pygame.time.get_ticks()
        for particle in self.trail_particles[:]:
            elapsed = current_time - particle['start_time']
            if elapsed > particle['lifetime']:
                self.trail_particles.remove(particle)
            else:
                particle['pos'][0] += particle['vel'][0]
                particle['pos'][1] += particle['vel'][1]
                # Update alpha for a smooth fading effect.
                alpha = max(0, 255 - int((elapsed / particle['lifetime']) * 255))
                particle['color'] = (0, 0, 255, alpha)

    def spawn_shards(self, count=2):
        super().spawn_shards(count)

    def spawn_blue_particles(self, count=30):
        # Spawn a cool, refined radial blue particle effect.
        # Particles are smaller and fade smoothly.
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            particle = {
                'pos': [self.position[0], self.position[1]],
                'vel': [math.cos(angle) * speed, math.sin(angle) * speed],
                'lifetime': random.randint(400, 800),
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3),
                'color': (0, 0, 255)  # Blue particles.
            }
            game_tools.global_impact_particles.append(particle)

    def update_shards(self, screen, color=None):
        current_time = pygame.time.get_ticks()
        for shard in game_tools.global_impact_particles[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                game_tools.global_impact_particles.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                # Use particle's color with fading alpha.
                color = (*shard['color'][:3], alpha) if 'color' in shard else (255, 255, 255, alpha)
                shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

    def take_damage(self, damage, projectile=None):
        prev_health = self.health
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()  # Standard shards on hit

        # When health drops by every 10 points, trigger special effects.
        while self.health <= self.next_threshold and self.next_threshold > 0:
            self.sfx_shield.play()
            self.spawn_blue_particles(count=30)  # Cool, refined blue radial effect
            # Spawn 5 roaches instead of beetles.
            for _ in range(2):
                offset_x = random.randint(-20, 20)
                offset_y = random.randint(-20, 20)
                spawn_pos = (self.position[0] + offset_x, self.position[1] + offset_y)
                # Instantiate a RoachMinionEnemy that uses the boss's current target.
                new_beetle = BeetleEnemy(spawn_pos, self.path)
                new_beetle.current_target = self.current_target  # Make it follow the boss's next point
                new_beetle.speed = random.uniform(1, 1.5)
                game_tools.enemies.append(new_beetle)
            self.next_threshold -= 35

        # Upon death, spawn 10 roaches with 2 health.
        if self.health <= 0 and self.is_alive:
            self.is_alive = False
            for _ in range(5):
                offset_x = random.randint(-30, 30)
                offset_y = random.randint(-30, 30)
                spawn_pos = (self.position[0] + offset_x, self.position[1] + offset_y)
                new_beetle = BeetleEnemy(spawn_pos, self.path)
                new_beetle.current_target = self.current_target  # Make it follow the boss's next point
                new_beetle.speed = random.uniform(1, 1.5)
                game_tools.enemies.append(new_beetle)
            self.sfx_death.play()
            game_tools.money += 100
            game_stats.global_kill_total["count"] += 1

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_tools.game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = game_tools.load_image(self.frames[self.current_frame])
            self.original_image = game_tools.load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

    def render(self, screen):
        super().render(screen)
        # Render trail particles (with refined blue effect)
        for particle in self.trail_particles:
            elapsed = pygame.time.get_ticks() - particle['start_time']
            alpha = max(0, 255 - int((elapsed / particle['lifetime']) * 255))
            trail_surface = pygame.Surface((particle['radius'] * 2, particle['radius'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (0, 0, 255, alpha), (particle['radius'], particle['radius']),
                               particle['radius'])
            screen.blit(trail_surface, (particle['pos'][0], particle['pos'][1]))


class RoachQueenEnemy(Enemy):
    def __init__(self, position, path, health=30, speed=0.5, image_path="assets/roach_queen.png", money=15):
        super().__init__(position, health, speed, path, image_path, money)
        self.current_target = 0
        # Multiplication timing
        self.spawn_time = pygame.time.get_ticks()
        self.last_multiply_time = self.spawn_time + 500  # First multiply after 500ms
        self.multiply_interval = 12000  # Starts at 4000ms, decreases by 500ms down to 500ms
        self.has_multiplied_initially = False
        self.total_spawned = 2
        # For spawn animation particles
        self.spawn_particles = []

        # Multiplication logic
        current_time = pygame.time.get_ticks()
        if not self.has_multiplied_initially and current_time - self.spawn_time >= 500 / game_tools.game_speed_multiplier:
            self.multiply()
            self.has_multiplied_initially = True
            self.last_multiply_time = current_time
        elif current_time - self.last_multiply_time >= self.multiply_interval / game_tools.game_speed_multiplier:
            self.multiply()
            self.last_multiply_time = current_time
            self.multiply_interval = max(2000, self.multiply_interval - 500)

        self.update_spawn_particles()

    def multiply(self):
        # Play multiplication sound and create animation particles.
        game_tools.load_sound("assets/roach_multiply.mp3").play()
        self.create_spawn_particles()
        # Determine the forward direction based on the next waypoint.
        if self.current_target < len(self.path):
            target = self.path[self.current_target]
            dx = target - self.position[0] if isinstance(target, (int, float)) else target[0] - self.position[0]
            dy = target - self.position[1] if isinstance(target, (int, float)) else target[1] - self.position[1]
            distance = math.hypot(dx, dy)
            if distance != 0:
                direction_x = dx / distance
                direction_y = dy / distance
            else:
                direction_x, direction_y = 1, 0
        else:
            direction_x, direction_y = 1, 0

        # Base spawn position: in front of the queen by a random offset (10-40)
        forward_offset = random.randint(20, 40)
        base_spawn_x = self.position[0] + forward_offset * direction_x
        base_spawn_y = self.position[1] + forward_offset * direction_y

        # Spawn two roach minions; pass the queen's current_target so they continue forward.
        for _ in range(self.total_spawned):
            x_offset = random.randint(-16, 16)
            y_offset = random.randint(-16, 16)
            offset_path = [(x + x_offset, y + y_offset) for (x, y) in self.path]
            spawn_x = base_spawn_x + x_offset
            spawn_y = base_spawn_y + y_offset  # For simplicity; adjust if desired.
            new_speed = random.uniform(1.5, 3.0)
            # Pass the current_target so the minion starts moving toward the same next waypoint.
            roach = RoachMinionEnemy((spawn_x, spawn_y), self.health / 10, offset_path, new_speed,
                                     current_target=self.current_target)
            game_tools.enemies.append(roach)
        self.total_spawned += 2
        if self.total_spawned > 10:
            self.total_spawned = 10

    def create_spawn_particles(self):
        # Create a burst of particles for the multiplication animation.
        for _ in range(8):
            particle = {
                'pos': [self.position[0], self.position[1]],
                'vel': [random.uniform(-3, 3), random.uniform(-3, 3)],
                'lifetime': random.randint(200, 400),
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(2, 4)
            }
            self.spawn_particles.append(particle)

    def update_spawn_particles(self):
        current_time = pygame.time.get_ticks()
        for particle in self.spawn_particles[:]:
            elapsed = current_time - particle['start_time']
            if elapsed > particle['lifetime']:
                self.spawn_particles.remove(particle)
            else:
                particle['pos'][0] += particle['vel'][0]
                particle['pos'][1] += particle['vel'][1]

    def render_spawn_particles(self, screen):
        current_time = pygame.time.get_ticks()
        for particle in self.spawn_particles:
            elapsed = current_time - particle['start_time']
            if elapsed < particle['lifetime']:
                alpha = max(0, 255 - int((elapsed / particle['lifetime']) * 255))
                color = (255, 255, 0, alpha)
                part_surface = pygame.Surface((particle['radius'] * 2, particle['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(part_surface, color, (particle['radius'], particle['radius']), particle['radius'])
                screen.blit(part_surface, (particle['pos'][0], particle['pos'][1]))

    def take_damage(self, damage, projectile=None):
        self.health -= damage
        self.show_damage_indicator(damage)
        if self.health <= 0:
            self.is_alive = False
            game_tools.load_sound("assets/splat_sfx.mp3").play()
            game_tools.money += 15
            game_stats.global_kill_total["count"] += 1

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(game_tools.load_image("assets/splatter.png"), self.rect.topleft)
        self.render_spawn_particles(screen)


# ------------------------------------------------------------
# RoachMinionEnemy class (adjusted to use queen's current_target)
# ------------------------------------------------------------
class RoachMinionEnemy(Enemy):
    def __init__(self, position, health, path, speed, current_target=0, image_path="assets/roach.png", money=3):
        super().__init__(position, health, speed, path, image_path, money)
        self.current_target = current_target  # Start from the queen's target
        # game_tools.global_impact_particles = []  # For particle effects if needed

    def take_damage(self, damage, projectile=None):
        self.health -= damage
        self.show_damage_indicator(damage)
        if self.health <= 0:
            self.is_alive = False
            game_tools.money += self.money
            game_stats.global_kill_total["count"] += 1
            game_tools.load_sound("assets/splat_sfx.mp3").play()

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(game_tools.load_image("assets/splatter.png"), self.rect.topleft)

class CentipedeEnemy(Enemy):
    """
    A composite enemy consisting of:
      - Head (health=6)
      - Several Link segments (each with health=2)
      - Tail (health=3)
    Movement is fluid: each segment follows the one ahead with a smoothing delay.
    Damage is applied to any non-head segment (links or tail) when hit – the head is only damaged after all
    other segments are destroyed. Additionally, when a link is destroyed, a burst of particle shards is spawned,
    similar to the beetle enemy’s armor-break effect. When segments are removed, the remaining segments are
    repositioned so that they remain in contact (i.e. no gaps appear).
    """
    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")

    class Segment:
        def __init__(self, role, health, image, position):
            self.role = role  # "head", "link", or "tail"
            self.health = health
            self.image = image
            self.position = position  # (x, y)
            self.angle = 0  # in degrees; 0 means "facing up"
            self.alive = True
            self.death_time = None  # time when the segment died
            self.rect = self.image.get_rect(center=position)

        def update_rect(self):
            self.rect = self.image.get_rect(center=self.position)

    def __init__(self, position, path, links=6, speed=1, health=6, image_path="assets/centipede_head.png", money=10):
        """
        :param position: Starting position (tuple)
        :param path: List of points (tuples) for the centipede head to follow.
        :param links: Number of link segments between the head and tail.
        """
        super().__init__(None, health, speed, path, image_path, money)
        self.current_target = 0  # Index in the path for head movement
        self.base_speed = self.speed
        self.links = links

        # Load images
        head_img = game_tools.load_image("assets/centipede_head.png")
        link_img = game_tools.load_image("assets/centipede_link.png")
        tail_img = game_tools.load_image("assets/centipede_tail.png")

        # Calculate desired gap distances for smooth connectivity between segments.
        self.gap_distances = []
        gap_head_link = (head_img.get_height() / 4) + (link_img.get_height() / 4)
        self.gap_distances.append(gap_head_link)
        for _ in range(self.links - 1):
            gap_link_link = link_img.get_height() / 4
            self.gap_distances.append(gap_link_link)
        gap_link_tail = (link_img.get_height() / 4) + (tail_img.get_height() / 4)
        self.gap_distances.append(gap_link_tail)

        # Create segments: head, links, and tail.
        self.segments = []
        self.segments.append(self.Segment("head", 3, head_img, position))
        for _ in range(self.links):
            self.segments.append(self.Segment("link", 2, link_img, position))
        self.segments.append(self.Segment("tail", 3, tail_img, position))

        # Initialize shard particles list.
        # global_impact_particles = []

    def spawn_shards(self, count=10):
        global global_impact_particles
        """
        Spawn a burst of shard particles to simulate a link breaking.
        """
        for _ in range(count):
            game_tools.spawn_shard(self.position, count=5)

    def update_shards(self, screen):
        """
        Update and render shard particles.
        """
        current_time = pygame.time.get_ticks()
        for shard in global_impact_particles[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                global_impact_particles.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (255, 255, 255, alpha)
                shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

    def update(self):
        """
        Update the centipede:
          - Move the head along its path.
          - Smoothly update each following segment to trail its predecessor.
          - Adjust speed based on remaining non-head segments.
          - If the centipede reaches the end of its path, subtract health from the user.
        """

        # Adjust speed based on number of alive non-head segments.
        non_head_alive = sum(1 for seg in self.segments[1:] if seg.alive)
        if non_head_alive >= 4:
            self.speed = 1
        elif non_head_alive > 0:
            self.speed = 1.5
        else:
            self.speed = 2

        # Move the head along the path.
        head = self.segments[0]
        if self.current_target < len(self.path):
            target_point = self.path[self.current_target]
            dx = target_point[0] - head.position[0]
            dy = target_point[1] - head.position[1]
            distance = math.hypot(dx, dy)
            if distance:
                dir_x = dx / distance
                dir_y = dy / distance
                move_dist = self.speed
                new_x = head.position[0] + dir_x * move_dist
                new_y = head.position[1] + dir_y * move_dist
                head.position = (new_x, new_y)
                head.angle = math.degrees(math.atan2(dir_x, -dir_y))
                head.update_rect()
                if distance <= move_dist:
                    self.current_target += 1
        else:
            # If the head reaches the end of the path, subtract remaining health from the user.
            tot_health = sum(1 for seg in self.segments[1:] if seg.alive)
            game_tools.user_health -= int(head.health + tot_health * 2)
            self.segments.clear()
            return

        # Smoothly update each following segment.
        alpha = 0.2  # smoothing factor
        for i in range(1, len(self.segments)):
            prev_seg = self.segments[i - 1]
            seg = self.segments[i]
            desired_gap = self.gap_distances[i - 1]
            vec_x = prev_seg.position[0] - seg.position[0]
            vec_y = prev_seg.position[1] - seg.position[1]
            dist = math.hypot(vec_x, vec_y)
            if dist:
                dir_x = vec_x / dist
                dir_y = vec_y / dist
                target_x = prev_seg.position[0] - desired_gap * dir_x
                target_y = prev_seg.position[1] - desired_gap * dir_y
                new_x = seg.position[0] + alpha * (target_x - seg.position[0])
                new_y = seg.position[1] + alpha * (target_y - seg.position[1])
                seg.position = (new_x, new_y)
                desired_angle = math.degrees(math.atan2(dir_x, -dir_y))
                seg.angle += alpha * (((desired_angle - seg.angle + 180) % 360) - 180)
                seg.update_rect()

    def move(self):
        """
        Alias for update, allowing external calls to move the enemy.
        """
        self.update()

    def show_damage_indicator(self, damage):
        # Create a damage text surface using a shared font.
        font = pygame.font.SysFont("impact", 20, bold=False)
        text_surface = font.render(f"{damage:.1f}", True, (255, 0, 0))
        text_surface.set_alpha(128)

        angle_deg = random.uniform(-45, 45)
        angle_rad = math.radians(angle_deg)

        # Speed magnitude
        speed = random.uniform(.5, 2)

        # Convert polar to cartesian velocity
        vel_x = math.sin(angle_rad) * speed
        vel_y = -math.cos(angle_rad) * speed  # negative because up is -y in Pygame

        # Set up the indicator's properties.
        indicator = {
            'surface': text_surface,
            'pos': list(self.rect.center) + [0, -20],  # starting at the enemy's center
            'vel': [vel_x, vel_y],
            'lifetime': random.randint(100, 250),  # milliseconds
            'start_time': pygame.time.get_ticks()
        }
        if len(game_tools.global_damage_indicators) < game_tools.MAX_INDICATORS:
            game_tools.global_damage_indicators.append(indicator)

    def take_damage(self, damage, hit_position=None, projectile=None, area_center=None, area_radius=0):
        global money
        """
        Apply incoming damage:
          - If a projectile is provided and its explosive flag is True, then set default explosion parameters.
          - If area_center and area_radius (or those set via an explosive projectile) are provided,
            apply damage to every non-head segment whose center is within the explosion radius.
          - Else if hit_position is provided, apply damage to the non-head segment closest to that point.
          - Otherwise, when no extra parameters are provided, assume a radial (area) damage effect
            and apply damage to every non-head segment.
          - Damage to the head is applied only once all non-head segments are destroyed.
        """
        # Check for explosive projectile.
        if projectile is not None and getattr(projectile, "explosive", False):
            if area_center is None:
                area_center = projectile.position
            if area_radius == 0:
                area_radius = getattr(projectile, "explosion_radius", 50)

        # Radial (area) damage branch.
        if area_center is not None and area_radius > 0:
            any_hit = False
            for seg in self.segments[1:][:]:
                if seg.alive:
                    seg_center = seg.rect.center
                    tolerance = seg.rect.width * 0.5
                    if math.hypot(seg_center[0] - area_center[0],
                                  seg_center[1] - area_center[1]) <= area_radius + tolerance:
                        seg.health -= damage
                        self.show_damage_indicator(damage)
                        any_hit = True
                        if seg.health <= 0:
                            seg.alive = False
                            seg.death_time = pygame.time.get_ticks()
                            self.spawn_shards(count=10)
                            self.remove_segment(seg)
            if any_hit:
                return
            # If no non-head segments were hit, apply damage to the head.
            head = self.segments[0]
            head.health -= damage
            self.show_damage_indicator(damage)
            if head.health <= 0:
                head.alive = False
                game_tools.money += 10
                game_stats.global_kill_total["count"] += 1
                head.death_time = pygame.time.get_ticks()
            return

        # Damage by hit position branch.
        if hit_position is not None:
            try:
                hp = (float(hit_position[0]), float(hit_position[1]))
            except (TypeError, ValueError):
                return
            candidates = [seg for seg in self.segments[1:] if seg.alive and seg.rect.collidepoint(hp)]
            if candidates:
                seg = min(candidates, key=lambda s: math.hypot(s.rect.centerx - hp[0], s.rect.centery - hp[1]))
                seg.health -= damage
                self.show_damage_indicator(damage)
                if seg.health <= 0:
                    seg.alive = False
                    seg.death_time = pygame.time.get_ticks()
                    self.spawn_shards(count=10)
                    self.remove_segment(seg)
                return
            return

        # Fallback: if no parameters, apply damage to furthest alive non-head segment
        for seg in reversed(self.segments[1:]):
            if seg.alive:
                seg.health -= damage
                self.show_damage_indicator(damage)
                if seg.health <= 0:
                    seg.alive = False
                    seg.death_time = pygame.time.get_ticks()
                    self.spawn_shards(count=10)
                    self.remove_segment(seg)
                return  # Exit after damaging one segment

        # If no non-head segments are alive, apply damage to the head.
        head = self.segments[0]
        head.health -= damage
        self.show_damage_indicator(damage)
        if head.health <= 0:
            head.alive = False
            game_tools.money += 10
            game_stats.global_kill_total["count"] += 1
            head.death_time = pygame.time.get_ticks()

    def remove_segment(self, seg):
        """
        Remove a destroyed segment and recalculate gap distances so that the remaining segments remain connected.
        """
        if seg in self.segments:
            self.segments.remove(seg)
            head_img = game_tools.load_image("assets/centipede_head.png")
            link_img = game_tools.load_image("assets/centipede_link.png")
            tail_img = game_tools.load_image("assets/centipede_tail.png")
            new_gaps = []
            if len(self.segments) > 1:
                new_gaps.append((head_img.get_height() / 4) + (link_img.get_height() / 4))
                for _ in range(len(self.segments) - 2):
                    new_gaps.append(link_img.get_height() / 4)
                new_gaps.append((link_img.get_height() / 4) + (tail_img.get_height() / 4))
            self.gap_distances = new_gaps

    @property
    def rect(self):
        """
        Returns the union of the hitboxes for all alive non-head segments,
        or the head's rect if no non-head segments are alive.
        """
        if not self.segments:
            return pygame.Rect(0, 0, 0, 0)
        alive_rects = [seg.rect for seg in self.segments[1:] if seg.alive]
        if alive_rects:
            union_rect = alive_rects[0].copy()
            for r in alive_rects[1:]:
                union_rect.union_ip(r)
            return union_rect
        return self.segments[0].rect

    @property
    def position(self):
        """
        Returns the center of the union of all alive non-head segments,
        or the head's position if no non-head segments are alive.
        This allows towers to target any part of the centipede body.
        """
        alive_rects = [seg.rect for seg in self.segments[1:] if seg.alive]
        if not self.segments:
            return 0, 0  # or self.last_known_position, or something safe
        if alive_rects:
            union_rect = alive_rects[0].copy()
            for r in alive_rects[1:]:
                union_rect.union_ip(r)
            return union_rect.center
        return self.segments[0].position

    @property
    def is_alive(self):
        """
        Returns True if any segment is still alive.
        """
        return any(seg.alive for seg in self.segments)

    def render(self, screen: pygame.Surface):
        """
        Render each segment (applying rotation and flipping as needed).
        Also, render a splatter effect for segments that have recently died and update shard particles.
        """
        current_time = pygame.time.get_ticks()
        SPLATTER_DURATION = 100  # Duration in milliseconds to show splatter effect

        for seg in self.segments:
            if seg.alive:
                rotated_image = pygame.transform.rotate(seg.image, seg.angle)
                rotated_image = pygame.transform.flip(rotated_image, True, False)
                rect = rotated_image.get_rect(center=seg.position)
                screen.blit(rotated_image, rect.topleft)
            elif seg.death_time and current_time - seg.death_time <= SPLATTER_DURATION:
                rotated_splatter = pygame.transform.rotate(self.img_death, seg.angle)
                rotated_splatter = pygame.transform.flip(rotated_splatter, True, False)
                rect = rotated_splatter.get_rect(center=seg.position)
                screen.blit(rotated_splatter, rect.topleft)
        # self.update_shards(screen)

class MillipedeBoss(Enemy):
    """
    A composite enemy consisting of:
      - Head (health=6)
      - Several Link segments (each with health=2)
      - Tail (health=3)
    Movement is fluid: each segment follows the one ahead with a smoothing delay.
    Damage is applied to any non-head segment (links or tail) when hit – the head is only damaged after all
    other segments are destroyed. Additionally, when a link is destroyed, a burst of particle shards is spawned,
    similar to the beetle enemy’s armor-break effect. When segments are removed, the remaining segments are
    repositioned so that they remain in contact (i.e. no gaps appear).
    """
    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")

    class Segment:
        def __init__(self, role, health, image, position):
            self.role = role  # "head", "link", or "tail"
            self.health = health
            self.image = image
            self.frames_head = ["assets/centipede_boss/head0.png", "assets/centipede_boss/head1.png",
                                "assets/centipede_boss/head2.png", "assets/centipede_boss/head3.png",]
            self.frames_link = ["assets/centipede_boss/link0.png", "assets/centipede_boss/link1.png",
                                "assets/centipede_boss/link2.png", "assets/centipede_boss/link3.png", ]
            self.frames_tail = ["assets/centipede_boss/tail0.png", "assets/centipede_boss/tail1.png",
                                "assets/centipede_boss/tail2.png", "assets/centipede_boss/tail3.png", ]
            self.current_frame = 0
            self.frame_duration = 50  # milliseconds per frame
            self.last_frame_update = pygame.time.get_ticks()
            self.position = position  # (x, y)
            self.angle = 0  # in degrees; 0 means "facing up"
            self.alive = True
            self.death_time = None  # time when the segment died
            self.rect = self.image.get_rect(center=position)

        def update_rect(self):
            self.rect = self.image.get_rect(center=self.position)

        def update_animation(self, segment):
            current_time = pygame.time.get_ticks()
            if current_time - self.last_frame_update >= self.frame_duration / game_tools.game_speed_multiplier:
                self.current_frame = (self.current_frame + 1) % len(segment)
                self.image = game_tools.load_image(segment[self.current_frame])
                self.last_frame_update = current_time

    def __init__(self, position, path, links=6, health=30, speed=.35, image_path="assets/centipede_boss/head0.png", money=10):
        """
        :param position: Starting position (tuple)
        :param path: List of points (tuples) for the centipede head to follow.
        :param links: Number of link segments between the head and tail.
        """
        super().__init__(None, health, speed, path, image_path, money)
        self.current_target = 0  # Index in the path for head movement
        self.base_speed = self.speed
        self.links = links
        self.sfx_channel = pygame.mixer.Channel(3)
        self.millipede_sfx = game_tools.load_sound("assets/centipede_crawl.mp3")
        self.sfx_playing = False

        # Load images
        head_img = game_tools.load_image("assets/centipede_boss/head0.png")
        link_img = game_tools.load_image("assets/centipede_boss/link0.png")
        tail_img = game_tools.load_image("assets/centipede_boss/tail0.png")

        # Calculate desired gap distances for smooth connectivity between segments.
        self.gap_distances = []
        gap_head_link = (head_img.get_height() / 4) + (link_img.get_height() / 4)
        self.gap_distances.append(gap_head_link)
        for _ in range(self.links - 1):
            gap_link_link = link_img.get_height() / 4
            self.gap_distances.append(gap_link_link)
        gap_link_tail = (link_img.get_height() / 4) + (tail_img.get_height() / 4)
        self.gap_distances.append(gap_link_tail)

        # Create segments: head, links, and tail.
        self.segments = []
        self.segments.append(self.Segment("head", 18, head_img, position))
        for _ in range(self.links):
            self.segments.append(self.Segment("link", 12, link_img, position))
        self.segments.append(self.Segment("tail", 18, tail_img, position))

        # Initialize shard particles list.
        # game_tools.global_impact_particles = []

    def spawn_shards(self, count=10):
        super().spawn_shards(count)

    def update_shards(self, screen, color=(255, 255, 255)):
        """
        Update and render shard particles.
        """
        current_time = pygame.time.get_ticks()
        for shard in game_tools.global_impact_particles[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                game_tools.global_impact_particles.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (color, alpha)
                shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

    def update(self):
        """
        Update the centipede:
          - Move the head along its path.
          - Smoothly update each following segment to trail its predecessor.
          - Adjust speed based on remaining non-head segments.
          - If the centipede reaches the end of its path, subtract health from the user.
        """
        if not self.sfx_playing:
            self.sfx_channel.play(self.millipede_sfx, loops=-1)
            self.sfx_playing = True
        # Adjust speed based on number of alive non-head segments.
        non_head_alive = sum(1 for seg in self.segments[1:] if seg.alive)
        if non_head_alive >= 8:
            self.speed = .75
        elif non_head_alive > 6:
            self.speed = 1
        elif non_head_alive > 3:
            self.speed = 1.5
        else:
            self.speed = 1.75

        # Move the head along the path.
        head = self.segments[0]
        if self.current_target < len(self.path):
            target_point = self.path[self.current_target]
            dx = target_point[0] - head.position[0]
            dy = target_point[1] - head.position[1]
            distance = math.hypot(dx, dy)
            if distance:
                dir_x = dx / distance
                dir_y = dy / distance
                move_dist = self.speed
                new_x = head.position[0] + dir_x * move_dist
                new_y = head.position[1] + dir_y * move_dist
                head.position = (new_x, new_y)
                head.angle = math.degrees(math.atan2(dir_x, -dir_y))
                head.update_rect()
                if distance <= move_dist:
                    self.current_target += 1
        else:
            # If the head reaches the end of the path, subtract remaining health from the user.
            tot_health = sum(1 for seg in self.segments[1:] if seg.alive)
            game_tools.user_health -= 99
            self.segments.clear()
            self.sfx_channel.stop()
            self.sfx_playing = False
            return

        # Smoothly update each following segment.
        alpha = 0.2  # smoothing factor
        for i in range(1, len(self.segments)):
            prev_seg = self.segments[i - 1]
            seg = self.segments[i]
            desired_gap = self.gap_distances[i - 1]
            vec_x = prev_seg.position[0] - seg.position[0]
            vec_y = prev_seg.position[1] - seg.position[1]
            dist = math.hypot(vec_x, vec_y)
            if dist:
                dir_x = vec_x / dist
                dir_y = vec_y / dist
                target_x = prev_seg.position[0] - desired_gap * dir_x
                target_y = prev_seg.position[1] - desired_gap * dir_y
                new_x = seg.position[0] + alpha * (target_x - seg.position[0])
                new_y = seg.position[1] + alpha * (target_y - seg.position[1])
                seg.position = (new_x, new_y)
                desired_angle = math.degrees(math.atan2(dir_x, -dir_y))
                seg.angle += alpha * (((desired_angle - seg.angle + 180) % 360) - 180)
                seg.update_rect()

    def move(self):
        """
        Alias for update, allowing external calls to move the enemy.
        """
        self.update()

    def take_damage(self, damage, hit_position=None, projectile=None, area_center=None, area_radius=0):
        """
        Apply incoming damage:
          - If a projectile is provided and its explosive flag is True, then set default explosion parameters.
          - If area_center and area_radius (or those set via an explosive projectile) are provided,
            apply damage to every non-head segment whose center is within the explosion radius.
          - Else if hit_position is provided, apply damage to the non-head segment closest to that point.
          - Otherwise, when no extra parameters are provided, assume a radial (area) damage effect
            and apply damage to every non-head segment.
          - Damage to the head is applied only once all non-head segments are destroyed.
        """
        # Check for explosive projectile.
        if projectile is not None and getattr(projectile, "explosive", False):
            if area_center is None:
                area_center = projectile.position
            if area_radius == 0:
                area_radius = getattr(projectile, "explosion_radius", 0)

        # Radial (area) damage branch.
        if area_center is not None and area_radius > 0:
            any_hit = False
            for seg in self.segments[1:][:]:
                if seg.alive:
                    seg_center = seg.rect.center
                    tolerance = seg.rect.width * 0.5
                    if math.hypot(seg_center[0] - area_center[0],
                                  seg_center[1] - area_center[1]) <= area_radius + tolerance:
                        seg.health -= damage / 2
                        self.show_damage_indicator(damage)
                        any_hit = True
                        if seg.health <= 0:
                            seg.alive = False
                            seg.death_time = pygame.time.get_ticks()
                            self.spawn_shards(count=10)
                            self.remove_segment(seg)
            if any_hit:
                return
            # If no non-head segments were hit, apply damage to the head.
            head = self.segments[0]
            head.health -= damage
            self.show_damage_indicator(damage)
            if head.health <= 0:
                head.alive = False
                game_tools.money += 200
                game_stats.global_kill_total["count"] += 1
                head.death_time = pygame.time.get_ticks()
                self.sfx_channel.stop()
                self.sfx_playing = False
            return

        # Damage by hit position branch.
        if hit_position is not None:
            try:
                hp = (float(hit_position[0]), float(hit_position[1]))
            except (TypeError, ValueError):
                return
            candidates = [seg for seg in self.segments[1:] if seg.alive and seg.rect.collidepoint(hp)]
            if candidates:
                seg = min(candidates, key=lambda s: math.hypot(s.rect.centerx - hp[0], s.rect.centery - hp[1]))
                seg.health -= damage
                self.show_damage_indicator(damage)
                if seg.health <= 0:
                    seg.alive = False
                    seg.death_time = pygame.time.get_ticks()
                    self.spawn_shards(count=10)
                    self.remove_segment(seg)
                return
            return

        # Fallback: if no parameters, apply damage to furthest alive non-head segment
        for seg in reversed(self.segments[1:]):
            if seg.alive:
                seg.health -= damage
                self.show_damage_indicator(damage)
                if seg.health <= 0:
                    seg.alive = False
                    seg.death_time = pygame.time.get_ticks()
                    self.spawn_shards(count=10)
                    self.remove_segment(seg)
                return  # Exit after damaging one segment

        # If no non-head segments are alive, apply damage to the head.
        head = self.segments[0]
        head.health -= damage
        self.show_damage_indicator(damage)
        if head.health <= 0:
            head.alive = False
            game_tools.money += self.money
            game_stats.global_kill_total["count"] += 1
            head.death_time = pygame.time.get_ticks()
            self.sfx_channel.stop()
            self.sfx_playing = False

    def remove_segment(self, seg):
        """
        Remove a destroyed segment and recalculate gap distances so that the remaining segments remain connected.
        """
        if seg in self.segments:
            self.segments.remove(seg)
            head_img = game_tools.load_image("assets/centipede_boss/head0.png")
            link_img = game_tools.load_image("assets/centipede_boss/link0.png")
            tail_img = game_tools.load_image("assets/centipede_boss/tail0.png")
            new_gaps = []
            if len(self.segments) > 1:
                new_gaps.append((head_img.get_height() / 4) + (link_img.get_height() / 4))
                for _ in range(len(self.segments) - 2):
                    new_gaps.append(link_img.get_height() / 4)
                new_gaps.append((link_img.get_height() / 4) + (tail_img.get_height() / 4))
            self.gap_distances = new_gaps

    @property
    def rect(self):
        """
        Returns the union of the hitboxes for all alive non-head segments,
        or the head's rect if no non-head segments are alive.
        """
        if not self.segments:
            return pygame.Rect(0, 0, 0, 0)
        alive_rects = [seg.rect for seg in self.segments[1:] if seg.alive]
        if alive_rects:
            union_rect = alive_rects[0].copy()
            for r in alive_rects[1:]:
                union_rect.union_ip(r)
            return union_rect
        return self.segments[0].rect

    @property
    def position(self):
        """
        Returns the center of the union of all alive non-head segments,
        or the head's position if no non-head segments are alive.
        This allows towers to target any part of the centipede body.
        """
        alive_rects = [seg.rect for seg in self.segments[1:] if seg.alive]
        if not self.segments:
            return 0, 0  # or self.last_known_position, or something safe
        if alive_rects:
            union_rect = alive_rects[0].copy()
            for r in alive_rects[1:]:
                union_rect.union_ip(r)
            return union_rect.center
        return self.segments[0].position

    @property
    def is_alive(self):
        """
        Returns True if any segment is still alive.
        """
        return any(seg.alive for seg in self.segments)

    def render(self, screen: pygame.Surface):
        """
        Render each segment (applying rotation and flipping as needed).
        Also, render a splatter effect for segments that have recently died and update shard particles.
        """
        current_time = pygame.time.get_ticks()
        SPLATTER_DURATION = 100  # Duration in milliseconds to show splatter effect

        for seg in self.segments:
            if seg.alive:
                if seg.role == "head":
                    seg.update_animation(seg.frames_head)
                elif seg.role == "link":
                    seg.update_animation(seg.frames_link)
                elif seg.role == "tail":
                    seg.update_animation(seg.frames_tail)
                rotated_image = pygame.transform.rotate(seg.image, seg.angle)
                rotated_image = pygame.transform.flip(rotated_image, True, False)
                rect = rotated_image.get_rect(center=seg.position)
                screen.blit(rotated_image, rect.topleft)
            elif seg.death_time and current_time - seg.death_time <= SPLATTER_DURATION:
                rotated_splatter = pygame.transform.rotate(self.img_death, seg.angle)
                rotated_splatter = pygame.transform.flip(rotated_splatter, True, False)
                rect = rotated_splatter.get_rect(center=seg.position)
                screen.blit(rotated_splatter, rect.topleft)
        # self.update_shards(screen)