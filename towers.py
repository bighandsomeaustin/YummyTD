import pygame
from pygame import mixer
import math
import random
import game_tools
import enemies


class Tower:
    sfx_squeak = game_tools.load_sound("assets/mouse-squeak.mp3")

    def __init__(self, position, radius, damage, image_path, projectile_image, shoot_interval, color, weapon=None):
        self.image_path = image_path
        self.image = game_tools.load_image(self.image_path)
        self.position = position
        self.radius = radius
        self.weapon = weapon
        self.damage = damage
        self.original_image = game_tools.load_image(self.image_path)
        self.rect = self.image.get_rect(center=position)
        self.angle = 0
        self.target = None
        self.projectiles = []
        self.projectile_image = projectile_image
        self.penetration = False
        self.shoot_interval = shoot_interval
        self.last_shot_time = 0
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.impact_shards = []  # Changed from particles to shards

    def update(self, enemies):
        self.target = None
        closest_distance = self.radius
        potential_targets = []
        current_time = pygame.time.get_ticks()
        if current_time - game_tools.last_time_sfx >= 15000:
            self.sfx_squeak.play()
            game_tools.last_time_sfx = current_time
        for enemy in enemies:
            distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                 (enemy.position[1] - self.position[1]) ** 2)
            if distance <= self.radius:
                potential_targets.append((distance, enemy))
        potential_targets.sort(key=lambda x: x[0])
        for _, enemy in potential_targets:
            if not any(tower.target == enemy for tower in towers if
                       tower != self and not isinstance(tower, RatTent) and not isinstance(tower, Ozbourne)
                       and not isinstance(tower, RatBank) and not isinstance(tower, WizardTower)
                       and not isinstance(tower, CheeseBeacon) and not isinstance(tower, MortarStrike)):
                self.target = enemy
                break
        if self.target is None and potential_targets:
            self.target = potential_targets[0][1]
        if self.target:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]
            self.angle = math.degrees(math.atan2(-dy, dx))
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(center=self.position)
        for projectile in self.projectiles[:]:
            projectile.move()
            if projectile.hit:
                if self.target is not None and self.target.is_alive:
                    self._create_impact_shards(projectile.position, color=(255, 255, 255))
                    self.target.take_damage(self.damage)
                if not self.penetration:
                    self.projectiles.remove(projectile)
                if self.penetration:
                    projectile.penetration -= 1
                    if projectile.penetration == 0:
                        self.projectiles.remove(projectile)
        self._update_impact_shards()

    def _create_impact_shards(self, position, color):
        """Create tower-themed impact shards"""
        for _ in range(8):
            self.impact_shards.append({
                'pos': list(position),
                'vel': [random.uniform(-5, 5), random.uniform(-5, 5)],
                'lifetime': random.randint(50, 300),  # Shorter lifetime than firefly
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3),  # Smaller than firefly shards
                'color': color  # tower's color
            })

    def _update_impact_shards(self):
        """Update shard positions and lifetimes"""
        current_time = pygame.time.get_ticks()
        for shard in self.impact_shards[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                self.impact_shards.remove(shard)
            else:
                # Add gravity effect
                shard['vel'][1] += 0.3
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
        for projectile in self.projectiles:
            projectile.render(screen)

        # Draw impact shards
        current_time = pygame.time.get_ticks()
        for shard in self.impact_shards:
            elapsed = current_time - shard['start_time']
            alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))

            # Create shard surface with rotation
            angle = elapsed * 0.3  # Rotate over time
            shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)

            # Draw angled rectangle as shard
            rotated_surface = pygame.transform.rotate(shard_surface, angle)
            pygame.draw.rect(
                rotated_surface,
                (*shard['color'], alpha),
                (0, 0, shard['radius'], shard['radius'] * 2)
            )

            screen.blit(rotated_surface, shard['pos'])

    def shoot(self):
        scaled_interval = self.shoot_interval / game_tools.game_speed_multiplier
        if self.target and self.target.is_alive:  # Add target validation
            if pygame.time.get_ticks() - self.last_shot_time >= scaled_interval:
                projectile = game_tools.Projectile(
                    position=self.position,
                    target=self.target,
                    speed=10 * game_tools.game_speed_multiplier,  # Scaled projectile speed
                    damage=self.damage,
                    image_path=self.projectile_image
                )
                if self.penetration:
                    projectile.penetration = 4
                self.projectiles.append(projectile)
                self.last_shot_time = pygame.time.get_ticks()


class RatTent(Tower):
    def __init__(self, position, radius=50, damage=1, recruit_health=1, recruit_speed=1, recruit_image="assets/rat_recruit.png", image_path="assets/base_camp.png",
                 spawn_interval=3000):
        super().__init__(position, radius, damage, image_path, recruit_image, spawn_interval)
        self.health = recruit_health
        self.speed = recruit_speed
        self.freak_last_spawn_time = 0
        self.sell_amt = 325
        self.horn_sfx = game_tools.load_sound("assets/battle_horn.mp3")
        self.freak_sfx = game_tools.load_sound("assets/freak-squeak.mp3")
        self.freak_death = game_tools.load_sound("assets/freak_death.mp3")

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
        for recruit in self.projectiles:
            recruit.render(screen)

    def update(self, enemies):
        scaled_interval = self.shoot_interval / game_tools.game_speed_multiplier
        if self.curr_top_upgrade > 0:
            self.spawn_interval = 1500
        # use default spawning
        if self.curr_top_upgrade < 2:
            if pygame.time.get_ticks() - self.last_shot_time >= scaled_interval and RoundFlag:
                recruit_entity = game_tools.RecruitEntity(self.position, 1, 1, game_tools.recruit_path, 1, self.projectile_image)
                closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
                distance = ((closest_spawn_point[0] - self.position[0]) ** 2 + (
                        closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
                if distance <= self.radius:
                    recruit = game_tools.RecruitEntity(
                        position=closest_spawn_point,
                        health=self.health,
                        speed=self.speed,
                        path=game_tools.recruit_path,
                        damage=self.damage,
                        image_path=self.projectile_image,
                    )
                    if self.curr_top_upgrade > 0:
                        recruit.speed = 2
                    if self.curr_bottom_upgrade > 1:
                        recruit.health = 2
                    self.projectiles.append(recruit)
                    self.last_shot_time = pygame.time.get_ticks()

        # ARMY RELEASE!
        if self.curr_top_upgrade == 2 and self.curr_bottom_upgrade < 2:
            if pygame.time.get_ticks() - self.last_shot_time >= (scaled_interval * 10) and RoundFlag:
                self.horn_sfx.play()
                recruit_entity = game_tools.RecruitEntity(self.position, 1, 1, game_tools.recruit_path, 1, self.projectile_image)
                closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
                distance = ((closest_spawn_point[0] - self.position[0]) ** 2 + (
                        closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
                if distance <= self.radius:
                    for _ in range(60):
                        offset_path = [(x + random.randint(-16, 16), y + random.randint(-8, 8)) for (x, y) in game_tools.recruit_path]
                        recruit = game_tools.RecruitEntity(
                            position=(closest_spawn_point[0] + random.randint(-16, 16), closest_spawn_point[1] + random.randint(-16, 16)),
                            health=self.health / 2,
                            speed=self.speed,
                            path=offset_path,
                            damage=self.damage / 2,
                            image_path="assets/recruit_army.png"
                        )
                        self.projectiles.append(recruit)
                        self.last_spawn_time = pygame.time.get_ticks()

        # RELEASE A FREAK!!
        if self.curr_bottom_upgrade > 1 and self.curr_top_upgrade < 2:
            if pygame.time.get_ticks() - self.freak_last_spawn_time >= (scaled_interval * 5) and RoundFlag:
                self.freak_sfx.play()
                recruit_entity = game_tools.RecruitEntity(self.position, 1, 1, game_tools.recruit_path, 1, self.projectile_image)
                closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
                distance = ((closest_spawn_point[0] - self.position[0]) ** 2 + (
                        closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
                if distance <= self.radius:
                    recruit = game_tools.RecruitEntity(
                        position=closest_spawn_point,
                        health=10,
                        speed=.5,
                        path=game_tools.recruit_path,
                        damage=3,
                        image_path="assets/freak_recruit_frames/freak0.png"
                    )
                    recruit.buff = True
                    self.projectiles.append(recruit)
                    self.freak_last_spawn_time = pygame.time.get_ticks()

        for recruit in self.projectiles[:]:
            recruit.update(enemies)
            if not recruit.is_alive and recruit is not None:
                if recruit.buff:
                    self.freak_death.play()
                self.projectiles.remove(recruit)
            if not RoundFlag and recruit is not None:
                self.projectiles.remove(recruit)


class MrCheese(Tower):
    sfx_squeak = game_tools.load_sound("assets/mouse-squeak.mp3")

    def __init__(self, position, radius, weapon, damage, image_path, projectile_image, shoot_interval=1500):
        super().__init__(position, radius, weapon, damage, image_path, projectile_image, shoot_interval)


class Ratman(Tower):
    sfx_squeak = game_tools.load_sound("assets/mouse-squeak.mp3")

    def __init__(self, position, radius=150, weapon='cheese', damage=1, image_path=None, projectile_image=None,
                 shoot_interval=500):
        super().__init__(position, radius, weapon, damage, image_path, projectile_image, shoot_interval)
        self.curr_top_upgrade = 2
        self.curr_bottom_upgrade = 2
        self.sell_amt = 1300
        self.robo = False
        self.get_upgrades()

    def get_upgrades(self):
        # Super Radius
        if self.curr_top_upgrade == 1:
            self.radius = 225
            if self.curr_bottom_upgrade == 0:
                self.image_path = "assets/ratman+supervision.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
            elif self.curr_bottom_upgrade == 1:
                self.image_path = "assets/ratman+fondue.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
            elif self.curr_bottom_upgrade == 2:
                self.image_path = "assets/ratman+plasma.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
        # Super Speed
        elif self.curr_top_upgrade == 2:
            self.shoot_interval = 250
            self.radius = 225
            if self.curr_bottom_upgrade == 0:
                self.image_path = "assets/ratman+superspeed.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
            elif self.curr_bottom_upgrade == 1:
                self.image_path = "assets/ratman+fondue+superspeed.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
            elif self.curr_bottom_upgrade == 2:
                self.image_path = "assets/ratman+plasma+speed.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
        # RoboRat
        elif self.curr_top_upgrade == 3 and self.curr_bottom_upgrade < 3:
            self.robo = True
            self.shoot_interval = 250
            self.radius = 225
            self.image_path = "assets/ratman+roborat.png"
            self.image = game_tools.load_image(self.image_path)
            self.original_image = game_tools.load_image(self.image_path)
        # Fondue
        if self.curr_bottom_upgrade == 1:
            self.weapon = 'fondue'
            self.damage = 4
            self.projectile_image = "assets/fondue.png"
            if self.curr_top_upgrade == 0:
                self.image_path = "assets/ratman+fondue.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
            elif self.curr_top_upgrade == 1:
                self.image_path = "assets/ratman+fondue.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
            elif self.curr_top_upgrade == 2:
                self.image_path = "assets/ratman+fondue+superspeed.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
        # Plasmatic Provolone
        elif self.curr_bottom_upgrade == 2:
            self.weapon = 'plasma'
            self.damage = 6
            self.projectile_image = "assets/plasma_proj.png"
            if self.curr_top_upgrade == 0:
                self.image_path = "assets/ratman+plasma.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
            elif self.curr_top_upgrade == 1:
                self.image_path = "assets/ratman+plasma.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
            elif self.curr_top_upgrade == 2:
                self.image_path = "assets/ratman+plasma+speed.png"
                self.image = game_tools.load_image(self.image_path)
                self.original_image = game_tools.load_image(self.image_path)
        # Cheese God
        elif self.curr_bottom_upgrade == 3 and self.curr_top_upgrade < 3:
            self.weapon = 'god'
            self.damage = 8
            self.shoot_interval = 125
            self.projectile_image = "assets/cheesegod_proj.png"
            self.image_path = "assets/ratman+cheesegod.png"
            self.image = game_tools.load_image(self.image_path)
            self.original_image = game_tools.load_image(self.image_path)

    def update(self, enemies):
        global last_time_sfx, RoundFlag
        self.target = None
        potential_targets = []
        current_time = pygame.time.get_ticks()

        if current_time - last_time_sfx >= 10000:
            self.sfx_squeak.play()
            last_time_sfx = current_time

        for enemy in enemies:
            distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                 (enemy.position[1] - self.position[1]) ** 2)
            if distance <= self.radius:
                potential_targets.append((distance, enemy))

        potential_targets.sort(key=lambda x: x[0])
        for _, enemy in potential_targets:
            if not any(tower.target == enemy for tower in towers if
                       tower != self and not isinstance(tower, RatTent) and not isinstance(tower, Ozbourne)
                       and not isinstance(tower, RatBank) and not isinstance(tower, WizardTower)
                       and not isinstance(tower, CheeseBeacon) and not isinstance(tower, MortarStrike)):
                self.target = enemy
                break
        if self.target is None and potential_targets:
            self.target = potential_targets[0][1]
        if self.target:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]
            self.angle = math.degrees(math.atan2(-dy, dx))
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(center=self.position)

        for projectile in self.projectiles[:]:
            projectile.move()
            # For "god" projectiles, wait at least 50ms before checking collisions.
            threshold = 50 if self.weapon == 'god' else 0
            if pygame.time.get_ticks() - projectile.spawn_time >= threshold:
                for enemy in enemies:
                    enemy_center = enemy.rect.center
                    dist = math.hypot(projectile.position[0] - enemy_center[0],
                                      projectile.position[1] - enemy_center[1])
                    if dist < enemy.rect.width / 2:
                        projectile.hit = True
                        break  # Once hit, no need to check further

            if projectile.hit:
                if self.target is not None and self.target.is_alive:
                    self._create_impact_shards(projectile.position)
                    self.target.take_damage(self.damage)
                self.projectiles.remove(projectile)
        self._update_impact_shards()

    def _create_impact_shards(self, position, color=(255, 245, 200)):
        super()._create_impact_shards(position, color)

    def _update_impact_shards(self):
        super()._update_impact_shards()

    def render(self, screen):
        super().render(screen)

    def shoot(self):
        # how fast we’re allowed to fire
        interval = self.shoot_interval / game_tools.game_speed_multiplier
        if not self.target or not self.target.is_alive:
            return

        now = pygame.time.get_ticks()
        if now - self.last_shot_time < interval:
            return
        self.last_shot_time = now

        bx, by = self.position
        tx, ty = self.target.position

        # Always rotate the sprite toward the center‑to‑target line:
        dx0, dy0 = tx - bx, ty - by
        # -- rotate sprite (degrees)
        self.angle = math.degrees(math.atan2(-dy0, dx0))
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.position)

        # Precompute the raw radian angle
        ang_rad = math.atan2(dy0, dx0)
        # Also compute it in degrees for CommandoProjectile
        ang_deg = math.degrees(ang_rad)

        if not self.robo:
            # ——— classic single‑barrel shot ———
            if self.weapon == 'cheese':
                proj = game_tools.Projectile(
                    position=self.position,
                    target=self.target,
                    speed=10,
                    damage=self.damage,
                    image_path=self.projectile_image
                )
                proj.vx = math.cos(ang_rad) * proj.speed
                proj.vy = math.sin(ang_rad) * proj.speed

            elif self.weapon == 'fondue':
                proj = game_tools.Projectile(
                    position=self.position,
                    target=self.target,
                    speed=5,
                    damage=self.damage,
                    image_path=self.projectile_image
                )
                proj.vx = math.cos(ang_rad) * proj.speed
                proj.vy = math.sin(ang_rad) * proj.speed

            elif self.weapon in ('plasma', 'god'):
                # Fix A: pass degrees instead of radians
                proj = CommandoProjectile(
                    position=self.position,
                    angle=ang_deg,
                    radius=(10 if self.weapon == 'plasma' else 15),
                    color=((67, 201, 245) if self.weapon == 'plasma' else (245, 235, 67)),
                    speed=5,
                    damage=self.damage,
                    piercing=True,
                    image_path=self.projectile_image
                )
                # OR Fix B: override its velocity to match the raw vector
                proj.velocity = [math.cos(ang_rad) * proj.speed,
                                 math.sin(ang_rad) * proj.speed]

            proj.spawn_time = now
            self.projectiles.append(proj)

        else:
            # ——— RoboRat: two‑barrel shot from y±15px ———
            for sign in (-1, +1):
                arm_offset = 15
                ox, oy = bx + sign * arm_offset, by
                dx, dy = tx - ox, ty - oy
                arm_rad = math.atan2(dy, dx)
                arm_deg = math.degrees(arm_rad)

                if self.weapon == 'cheese':
                    proj = game_tools.Projectile(
                        position=(ox, oy),
                        target=self.target,
                        speed=10,
                        damage=self.damage,
                        image_path=self.projectile_image
                    )
                    proj.vx = math.cos(arm_rad) * proj.speed
                    proj.vy = math.sin(arm_rad) * proj.speed

                elif self.weapon == 'fondue':
                    proj = game_tools.Projectile(
                        position=(ox, oy),
                        target=self.target,
                        speed=5,
                        damage=self.damage,
                        image_path=self.projectile_image
                    )
                    proj.vx = math.cos(arm_rad) * proj.speed
                    proj.vy = math.sin(arm_rad) * proj.speed

                else:  # plasma or god
                    # Fix A for robo‑arms as well
                    proj = CommandoProjectile(
                        position=(ox, oy),
                        angle=arm_deg,
                        radius=(10 if self.weapon == 'plasma' else 15),
                        color=((67, 201, 245) if self.weapon == 'plasma' else (245, 235, 67)),
                        speed=5,
                        damage=self.damage,
                        piercing=True,
                        image_path=self.projectile_image
                    )
                    # Or Fix B override:
                    proj.velocity = [math.cos(arm_rad) * proj.speed,
                                     math.sin(arm_rad) * proj.speed]

                proj.spawn_time = now
                self.projectiles.append(proj)


class MortarStrike:
    """
    Mortar Strike tower: places a target marker that can be moved when selected.
    Fires a mortar to the target every 6500ms, causing an explosion (radius 75, damage 2, armor_break).
    Upgrade at curr_top_upgrade == 3 spawns 5 smaller explosions around the circumference.
    """
    EXPLOSION_DURATION = 250  # ms

    def __init__(self, position, image_path=None):
        self.position = position
        # Base sprite (tower icon)
        self.original_image = game_tools.load_image(image_path or "assets/mortar_base.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        # Rotation angle
        self.angle = 0
        self.radius = 0
        # Target marker image and position
        self.target_image = game_tools.load_image("assets/strike.png")
        self.target_pos = list(position)
        self.dragging = False
        self.is_selected = False
        # Firing
        self.shoot_interval = 6500  # ms
        self.last_shot_time = 0
        # Damage
        self.damage = 3
        # Upgrade
        self.curr_top_upgrade = 3
        self.curr_bottom_upgrade = 0
        # Explosion schedule
        self.explosions = []
        # Sell value
        self.sell_amt = 375

    def update(self, enemies):
        now = pygame.time.get_ticks()
        # Shooting
        if now - self.last_shot_time >= self.shoot_interval / game_tools.game_speed_multiplier:
            self.last_shot_time = now
            # spawn main explosion
            self._spawn_explosion(self.target_pos, 75, self.damage, enemies)
            if self.curr_top_upgrade == 3:
                for i in range(5):
                    angle = i * (2 * math.pi / 5)
                    ox = self.target_pos[0] + math.cos(angle) * 75
                    oy = self.target_pos[1] + math.sin(angle) * 75
                    self._spawn_explosion((ox, oy), 100 * 0.33, self.damage * 0.33, enemies)
        # Cleanup old explosions
        self.explosions = [e for e in self.explosions
                           if pygame.time.get_ticks() - e['start'] < self.EXPLOSION_DURATION]

    def _spawn_explosion(self, pos, radius, dmg, enemies):
        if not RoundFlag:
            return
        class ExplosiveProjectile:
            armor_break = True
            explosive   = True
        # Damage
        for enemy in enemies:
            ex, ey = enemy.rect.center
            if math.hypot(ex - pos[0], ey - pos[1]) <= radius + enemy.rect.width/2:
                enemy.take_damage(dmg, ExplosiveProjectile())
        # Sound
        game_tools.load_sound("assets/explosion_sfx.mp3").play()
        # Create particles
        parts = []
        for _ in range(20):
            a = random.uniform(0, 2*math.pi)
            mag = random.uniform(radius*0.3, radius*0.7)
            parts.append({
                'pos': [pos[0], pos[1]],
                'vel': [math.cos(a)*mag, math.sin(a)*mag],
                'life': self.EXPLOSION_DURATION
            })
        # Schedule explosion
        self.explosions.append({ 'pos':pos, 'radius':radius, 'start':pygame.time.get_ticks(), 'particles':parts })

    def render(self, screen):
        # Rotate turret toward target
        dx = self.target_pos[0] - self.position[0]
        dy = self.target_pos[1] - self.position[1]
        self.angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.position)
        # Draw tower
        screen.blit(self.image, self.rect.topleft)
        # Draw target only when selected
        if getattr(self, 'is_selected', False):
            mouse = pygame.mouse.get_pos()
            pressed = pygame.mouse.get_pressed()[0]
            if self.dragging:
                if not pressed:
                    self.dragging = False
                else:
                    self.target_pos = list(mouse)
            else:
                marker_rect = self.target_image.get_rect(center=self.target_pos)
                if marker_rect.collidepoint(mouse) and pressed:
                    self.dragging = True
            screen.blit(self.target_image, self.target_image.get_rect(center=self.target_pos))
        # Draw explosions
        now = pygame.time.get_ticks()
        for exp in self.explosions[:]:
            elapsed = now - exp['start']
            if elapsed > self.EXPLOSION_DURATION:
                self.explosions.remove(exp)
                continue
            p = elapsed / self.EXPLOSION_DURATION
            alpha = int(255*(1-p))
            # flash + ring
            fr = exp['radius']*(0.5+0.5*p)
            surf = pygame.Surface((fr*2, fr*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,200,50,alpha//2),(fr,fr),int(fr))
            pygame.draw.circle(surf, (255,100,0,alpha),(fr,fr),int(exp['radius']),3)
            screen.blit(surf,(exp['pos'][0]-fr, exp['pos'][1]-fr))
            # particles
            for part in exp['particles'][:]:
                t = elapsed/part['life']
                if t>=1:
                    exp['particles'].remove(part)
                    continue
                part['pos'][0] += part['vel'][0]*(1/60)*game_tools.game_speed_multiplier
                part['pos'][1] += part['vel'][1]*(1/60)*game_tools.game_speed_multiplier
                pa = int(alpha*(1-t))
                pygame.draw.circle(screen,(255,220,100,pa),
                                   (int(part['pos'][0]),int(part['pos'][1])),
                                   max(1,int(exp['radius']*0.05*(1-t))))

    def shoot(self):
        pass


class ImportTruck:
    def __init__(self, position, path, health):
        self.position = position
        self.speed = 0.75
        self.health = health
        self.path = path
        self.original_image = game_tools.load_image("assets/import_truck.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True

    def move(self):
        global user_health
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
            user_health += self.health

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)


class RatBank:
    def __init__(self, position, image_path):
        self.position = position
        self.image_path = "assets/rat_bank.png"
        self.image = game_tools.load_image(self.image_path)
        self.rect = self.image.get_rect(center=position)
        self.radius = 0
        # Investment properties
        self.interest_rate = 1.03  # Base interest rate (3% per round)
        self.cash_invested = 0  # Total cash invested by the user
        self.cash_generated = 0  # Interest generated on the invested cash
        self.stock_value = 0  # Calculated as 10% of total towers’ sell_amt
        self.investment_window_open = False
        self.open_new_investment = False
        self.open_withdraw_window = False
        # Loan properties (unlocked with the Cheese Fargo HQ upgrade)
        self.loan_amount = 0  # Outstanding loan balance
        self.loan_payment = 0  # Payment due each round for the active loan
        self.loan_type = None  # Either "provoloan" or "briefund"
        self.provoloan = 5000
        self.provoloan_payment = 285
        self.provoloanFlag = False
        self.briefund = 10000
        self.briefund_payment = 720
        self.briefundFlag = False
        # cheese imports flags
        self.dutch = True
        self.polish = True
        self.french = True
        self.sfx_horn = game_tools.load_sound("assets/truck_honk.mp3")
        # Upgrade flags
        self.curr_top_upgrade = 0  # For interest rate improvement (Cheese Fargo upgrade)
        self.curr_bottom_upgrade = 0  # For loan functionality (Cheese Fargo HQ upgrade)
        self.invested_round = game_tools.current_wave  # Round tracking for investment updates
        self.curr_round = game_tools.current_wave
        self.sell_amt = 350
        self.RepoFlag = False
        self.user_text = ""
        # NEW: Instance-level flag for selection (used for showing the invest button)
        self.is_selected = False
        self.trucks = []

    def update_user_text(self, event):
        # Only process input if this bank's investment window is open.
        if not self.investment_window_open:
            return False
        global money
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.user_text = self.user_text[:-1]
            elif event.unicode.isdigit():
                new_text = self.user_text + event.unicode
                if int(new_text) <= money:
                    self.user_text = new_text
            elif event.key == pygame.K_RETURN:
                if self.user_text:
                    self.cash_invested += int(self.user_text)
                    money -= int(self.user_text)
                    self.user_text = ""  # Clear input after entry
                    self.open_new_investment = False
        return False

    def investment_interface(self, scrn: pygame.Surface):
        """
        Displays the investment window.
        This window shows:
          - Cash Invested
          - Cash Generated (Interest)
          - Stock Value (10% of total towers' sell_amt)
          - Buttons for deposit/withdraw actions and loan handling.
        """
        global money, UpgradeFlag
        investment_bg = game_tools.load_image("assets/investment_window.png")
        investment_bg_no_loans = game_tools.load_image("assets/investment_window_no_loans.png")
        investment_no_prov = game_tools.load_image("assets/investment_window_provoloan_unavail.png")
        investment_no_brie = game_tools.load_image("assets/investment_window_briefund_unavail.png")
        investment_both_unavail = game_tools.load_image("assets/investment_window_both_unavail.png")
        investment_imports = game_tools.load_image("assets/investment_window_imports.png")
        french = game_tools.load_image("assets/french_avail.png")
        french_unavail = game_tools.load_image("assets/french_unavail.png")
        polish = game_tools.load_image("assets/polish_avail.png")
        polish_unavail = game_tools.load_image("assets/polish_unavail.png")
        dutch = game_tools.load_image("assets/dutch_avail.png")
        dutch_unavail = game_tools.load_image("assets/dutch_unavail.png")
        import_select = game_tools.load_image("assets/import_select.png")
        add_investment = game_tools.load_image("assets/enter_investment_window.png")
        withdraw_window = game_tools.load_image("assets/withdraw_window.png")
        select_loan = game_tools.load_image("assets/loan_highlight.png")
        mouse = pygame.mouse.get_pos()

        # Calculate stock price based on total towers' sell_amt
        sell_sum = 0
        for tower in towers:
            sell_sum += tower.sell_amt

        if self.curr_bottom_upgrade < 1:
            self.stock_value = int(sell_sum * 0.01)
        elif self.curr_bottom_upgrade >= 1:
            self.stock_value = (int(sell_sum * 0.01)) * 2

        font = pygame.font.SysFont("arial", 20)
        text_invested = font.render(f"${self.cash_invested}", True, (255, 255, 255))
        text_generated = font.render(f"${self.cash_generated}", True, (255, 255, 255))
        text_stock = font.render(f"${self.stock_value} per share", True, (255, 255, 255))
        text_payment = font.render(f"${self.loan_payment}", True, (255, 255, 255))
        font_invest = pygame.font.SysFont("arial", 16)

        # Choose the appropriate background based on loan upgrade state
        if self.curr_bottom_upgrade < 2 and self.curr_top_upgrade < 2:
            scrn.blit(investment_bg_no_loans, (0, 0))
        elif self.curr_bottom_upgrade > 1:
            if self.briefundFlag and self.provoloanFlag:
                scrn.blit(investment_both_unavail, (0, 0))
            elif self.provoloanFlag:
                scrn.blit(investment_no_prov, (0, 0))
            elif self.briefundFlag:
                scrn.blit(investment_no_brie, (0, 0))
            else:
                scrn.blit(investment_bg, (0, 0))

        elif self.curr_top_upgrade > 1:
            scrn.blit(investment_imports, (0, 0))
            if self.french:
                scrn.blit(french, (483, 406))
            else:
                scrn.blit(french_unavail, (483, 406))
            if self.polish:
                scrn.blit(polish, (592, 406))
            else:
                scrn.blit(polish_unavail, (592, 406))
            if self.dutch:
                scrn.blit(dutch, (704, 406))
            else:
                scrn.blit(dutch_unavail, (704, 406))

        if self.curr_bottom_upgrade > 1:
            scrn.blit(text_payment, (662, 413))

        scrn.blit(text_invested, (644, 264))
        scrn.blit(text_generated, (654, 300))
        scrn.blit(text_stock, (624, 337))

        # Close button for the investment window;
        # also reset the selection so the invest button won't reappear.
        if 799 <= mouse[0] <= 799 + 11 and 212 <= mouse[1] <= 212 + 15:
            if game_tools.detect_single_click():
                self.investment_window_open = False
                self.is_selected = False

        # '+' button to open the new investment input
        if 746 <= mouse[0] <= 746 + 22 and 264 <= mouse[1] <= 264 + 23:
            if game_tools.detect_single_click():
                self.open_new_investment = True

        # New investment input interface
        if self.open_new_investment:
            if not (746 <= mouse[0] <= 746 + 22 and 264 <= mouse[1] <= 264 + 23):
                if game_tools.detect_single_click():
                    self.open_new_investment = False
            self.open_withdraw_window = False  # Close withdraw if open
            scrn.blit(add_investment, (771, 262))
            user_text_display = font_invest.render(self.user_text, True, (255, 255, 255))
            scrn.blit(user_text_display, (802, 285))

        # Withdraw button handling
        if 748 <= mouse[0] <= 748 + 20 and 302 <= mouse[1] <= 302 + 22:
            if game_tools.detect_single_click():
                self.open_withdraw_window = True

        if self.open_withdraw_window:
            self.open_new_investment = False
            scrn.blit(withdraw_window, (769, 297))
            if not (774 <= mouse[0] <= 774 + 141 and 301 <= mouse[1] <= 320 + 17):
                if game_tools.detect_single_click():
                    self.open_withdraw_window = False
            if 774 <= mouse[0] <= 774 + 141 and 301 <= mouse[1] <= 301 + 17:
                if game_tools.detect_single_click():
                    money += self.cash_generated
                    self.invested_round = game_tools.current_wave
                    self.cash_generated = 0
                    self.open_withdraw_window = False
            if 774 <= mouse[0] <= 744 + 141 and 320 <= mouse[1] <= 320 + 17:
                if game_tools.detect_single_click():
                    money += (self.cash_generated + self.cash_invested)
                    self.invested_round = game_tools.current_wave
                    self.cash_generated = 0
                    self.cash_invested = 0
                    self.open_withdraw_window = False

        # Import handling
        if self.curr_top_upgrade > 1:
            # France
            if 484 <= mouse[0] <= 484 + 90 and 407 <= mouse[1] <= 407 + 62 and self.french:
                scrn.blit(import_select, (484, 407))
                if game_tools.detect_single_click():
                    if money >= 200:
                        self.french = False
                        money -= 200
                        self.send_import(10)
            # Poland
            if 595 <= mouse[0] <= 595 + 90 and 407 <= mouse[1] <= 407 + 62 and self.polish:
                scrn.blit(import_select, (593, 407))
                if game_tools.detect_single_click():
                    if money >= 1000:
                        self.polish = False
                        money -= 1000
                        self.send_import(60)
            # Netherlands
            if 707 <= mouse[0] <= 707 + 90 and 407 <= mouse[1] <= 407 + 62 and self.dutch:
                scrn.blit(import_select, (705, 407))
                if game_tools.detect_single_click():
                    if money >= 2000:
                        self.dutch = False
                        money -= 2000
                        self.send_import(150)

        # Loan handling (Cheese Fargo upgrades)
        if self.curr_bottom_upgrade > 1:
            if 507 <= mouse[0] <= 507 + 133 and 441 <= mouse[1] <= 441 + 64 and not self.provoloanFlag:
                scrn.blit(select_loan, (507, 441))
                if game_tools.detect_single_click():
                    money += self.provoloan
                    self.loan_payment += self.provoloan_payment
                    self.loan_amount += (self.provoloan * 1.14)
                    self.provoloanFlag = True
            if 639 <= mouse[0] <= 639 + 133 and 441 <= mouse[1] <= 441 + 64 and not self.briefundFlag:
                scrn.blit(select_loan, (639, 441))
                if game_tools.detect_single_click():
                    money += self.briefund
                    self.loan_payment += self.briefund_payment
                    self.loan_amount += (self.briefund * 1.07)
                    self.briefundFlag = True

    def send_import(self, health_amt):
        spawn_pos = (238 + random.randint(-16, 16), 500)
        offset_path = [(x + random.randint(-8, 8), y) for (x, y) in game_tools.house_path]
        self.sfx_horn.play()
        self.trucks.append(ImportTruck(spawn_pos, offset_path, health_amt))

    def update_trucks(self, scrn):
        for truck in self.trucks:
            if truck.is_alive:
                truck.move()
                truck.render(scrn)
            else:
                self.trucks.remove(truck)

    def process_interest(self):
        global money
        """
        Called at the end of each round to apply interest to the invested cash,
        update cash_generated, and recalculate the stock value.
        """
        self.curr_round = game_tools.current_wave
        round_diff = self.curr_round - self.invested_round
        self.cash_generated += int((self.cash_invested + self.cash_generated) *
                                   (self.interest_rate - 1))

        if self.curr_bottom_upgrade < 1:
            self.cash_generated += (100 + self.stock_value)
        elif self.curr_bottom_upgrade >= 1:
            self.cash_generated += (200 + self.stock_value)

    def reset_imports(self):
        self.polish = True
        self.french = True
        self.dutch = True

    def process_loan_payment(self):
        """
        At the start of each round, processes the loan payment.
        If the user cannot cover the payment, repossesses towers (excluding banks)
        to cover the deficit.
        """
        global money, towers
        if self.loan_amount > 0:
            if money >= self.loan_payment:
                money -= self.loan_payment
                self.loan_amount -= self.loan_payment
                if self.loan_amount < 0:
                    self.loan_amount = 0
            else:
                deficit = self.loan_payment - money
                sorted_towers = sorted(towers, key=lambda t: t.sell_amt)
                repossessed_value = 0
                towers_to_remove = []
                for tower in sorted_towers:
                    if not isinstance(tower, RatBank):
                        if repossessed_value < deficit:
                            repossessed_value += tower.sell_amt
                            towers_to_remove.append(tower)
                        else:
                            break
                for tower in towers_to_remove:
                    towers.remove(tower)
                self.loan_amount -= self.loan_payment
                self.RepoFlag = True
                if self.loan_amount < 0:
                    self.loan_amount = 0
                    self.provoloanFlag = False
                    self.briefundFlag = False

    def render(self, scrn: pygame.Surface):
        global UpgradeFlag
        mouse = pygame.mouse.get_pos()
        invest_btn = game_tools.load_image("assets/invest_box.png")
        repossessed_window = game_tools.load_image("assets/repossessed_window.png")
        scrn.blit(self.image, self.rect.topleft)

        # If this bank is selected and its investment window is not open, show its invest button.
        if self.is_selected and not self.investment_window_open:
            if self.curr_bottom_upgrade < 2:
                scrn.blit(invest_btn, (self.position[0] - 22, self.position[1] + 45))
                if (self.position[0] - 22 <= mouse[0] <= self.position[0] - 22 + 46 and
                        self.position[1] + 45 <= mouse[1] <= self.position[1] + 45 + 14):
                    if game_tools.detect_single_click():
                        self.investment_window_open = True
                        UpgradeFlag = False
                        self.is_selected = False
            else:
                scrn.blit(invest_btn, (self.position[0] - 22, self.position[1] + 45 + 59))
                if (self.position[0] - 22 <= mouse[0] <= self.position[0] - 22 + 46 and
                        self.position[1] + 45 + 59 <= mouse[1] <= self.position[1] + 45 + 14 + 59):
                    if game_tools.detect_single_click():
                        self.investment_window_open = True
                        self.is_selected = False
                        UpgradeFlag = False

        # If the bank is selected but a click occurs outside its area, clear the selection
        # so the invest button disappears.
        if self.is_selected and not self.investment_window_open:
            # Check if the mouse click is outside the bank's rect (you can fine-tune this as needed)
            if game_tools.detect_single_click() and not self.rect.collidepoint(mouse):
                self.is_selected = False

        if self.RepoFlag:
            scrn.blit(repossessed_window, (403, 317))
            if 728 <= mouse[0] <= 728 + 12 and 323 <= mouse[1] <= 323 + 10:
                if game_tools.detect_single_click():
                    self.RepoFlag = False

        if self.investment_window_open:
            self.investment_interface(scrn)

        if self.curr_top_upgrade > 1:
            self.update_trucks(scrn)

        # self.process_interest()


# New projectile class for Cheddar Commando using pygame drawing for bullets
class CommandoProjectile:
    def __init__(self, position, angle, speed, damage, radius=5, color=(255, 255, 0), piercing=False, image_path=None):
        self.position = list(position)  # Ensure mutability for movement
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.image = game_tools.load_image(image_path) if image_path else None
        self.radius = radius  # bullet radius for drawing
        self.penetration = 5  # Add penetration counter
        self.target = None
        self.hit = False
        self.piercing = piercing
        self.explosive = False
        self.armor_break = False
        self.homing = False
        self.color = color

        # Calculate velocity based on angle
        rad = math.radians(angle)
        self.velocity = [speed * math.cos(rad), -speed * math.sin(rad)]

    def update_velocity(self):
        if self.target is not None:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.velocity = [dx / dist * self.speed, dy / dist * self.speed]
            else:
                self.velocity = [0, 0]
        else:
            self.velocity = [0, 0]

    def move(self):
        if self.homing:
            self.update_velocity()
        """Update projectile movement."""
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

        # Destroy projectile if it leaves screen bounds
        if not (0 <= self.position[0] <= 1280 and 0 <= self.position[1] <= 720):
            self.hit = True

    def render(self, screen):
        """Draw projectile."""
        if self.image is not None:
            screen.blit(self.image, (self.position[0], self.position[1]))
        else:
            pygame.draw.circle(screen, self.color, (int(self.position[0]), int(self.position[1])), self.radius)


class CheddarCommando:
    def __init__(self, position, radius=75, damage=1, shoot_interval=800, reload_time=4000):
        self.image_path = "assets/base_soldier.png"
        self.image = game_tools.load_image(self.image_path)
        self.position = position
        self.radius = radius
        self.damage = damage
        self.explosion_sfx = game_tools.load_sound("assets/explosion_sfx.mp3")
        self.original_image = game_tools.load_image(self.image_path)
        self.rect = self.image.get_rect(center=position)
        self.target = None
        self.projectiles = []
        self.shoot_interval = shoot_interval
        self.last_shot_time = 0
        self.shot_count = 0
        self.reload_time = reload_time
        self.is_reloading = False
        self.has_fired = False  # Tracks whether the unit has fired at least once
        # Explosion properties (for debugging, explosion radius set to 100)
        self.explosion_active = False
        self.explosion_damage = 0.25
        self.explosion_pos = (0, 0)
        self.explosion_animation_timer = 0
        self.explosion_duration = 50  # Explosion lasts 50ms
        self.max_explosion_radius = 25  # Explosion damage radius (debug value; adjust as needed)
        self.explosion_radius = 0  # Animated explosion radius
        self.last_explosion_update = 0  # For delta time tracking
        self.reloadFlag = False
        self.reload_start_time = 0

        # Upgrade levels (externally modified)
        # Top upgrade: 0 (base), 1, 2; Bottom upgrade: 0 (base), 1 (explosive rounds)
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.sell_amt = 125

        # Load sounds
        self.sound_path = "assets/pistol_shoot.mp3"
        self.shoot_sound = game_tools.load_sound(self.sound_path)
        self.reload_path = "assets/commando_reload.mp3"
        self.regame_tools.load_sound = game_tools.load_sound(self.reload_path)

    def update(self, enemies):
        """Update targeting, projectiles, explosion animation, and reload state."""

        # Reset ammo when round ends
        if not RoundFlag:
            self.shot_count = 0

        # === Targeting ===
        self.target = None
        potential_targets = []
        if not self.is_reloading:
            for enemy in enemies:
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

        # === Explosion Animation (optimized) ===
        if self.explosion_active:
            current_time = pygame.time.get_ticks()
            if self.last_explosion_update == 0:
                self.last_explosion_update = current_time
            delta = current_time - self.last_explosion_update
            self.last_explosion_update = current_time
            self.explosion_animation_timer += delta
            self.explosion_radius += (self.max_explosion_radius / self.explosion_duration) * delta
            if self.explosion_animation_timer >= self.explosion_duration:
                self.explosion_active = False
                self.explosion_radius = 0

        # === Process Projectiles ===
        for projectile in self.projectiles[:]:
            projectile.move()
            for enemy in enemies:
                enemy_center = enemy.rect.center
                dist = math.hypot(projectile.position[0] - enemy_center[0],
                                  projectile.position[1] - enemy_center[1])
                if dist < enemy.rect.width / 2:
                    enemy.take_damage(projectile.damage, projectile=projectile)
                    if projectile.explosive and not self.explosion_active:
                        self.explosion_pos = enemy.rect.center
                        self.explosion(enemies)
                        self.explosion_sfx.play()
                    projectile.hit = True
                    if not projectile.piercing:
                        break
            if projectile.hit:
                if not projectile.piercing:
                    self.projectiles.remove(projectile)
                else:
                    projectile.penetration -= 1
                    if projectile.penetration <= 0:
                        self.projectiles.remove(projectile)

        # === Reload Handling ===
        if self.is_reloading:
            scaled_reload = self.reload_time / game_tools.game_speed_multiplier
            if pygame.time.get_ticks() - self.reload_start_time >= scaled_reload:
                self.is_reloading = False
                self.shot_count = 0

    def explosion(self, enemies):
        """
        Trigger an explosion that immediately deals damage to all enemies within
        the fixed explosion radius (including those partially overlapping), then
        starts the explosion animation.
        """
        self.explosion_active = True
        self.explosion_animation_timer = 0
        self.explosion_radius = self.max_explosion_radius  # Immediate damage radius
        self.last_explosion_update = pygame.time.get_ticks()

        class ExplosiveProjectile:
            armor_break = True
            explosive = True

        for enemy in enemies:
            enemy_center = enemy.rect.center
            dist = math.hypot(enemy_center[0] - self.explosion_pos[0],
                              enemy_center[1] - self.explosion_pos[1])

            if dist <= self.max_explosion_radius + enemy.rect.width / 2:
                self.explosion_damage = 0.25
                if isinstance(enemy, enemies.BeetleEnemy):
                    # Pass dummy projectile to force armor break
                    enemy.take_damage(self.explosion_damage, ExplosiveProjectile())
                else:
                    enemy.take_damage(self.explosion_damage)

    def render(self, screen):
        """Render the tower, its projectiles, explosion animation, and reloading graphic."""
        screen.blit(self.image, self.rect.topleft)
        for projectile in self.projectiles:
            projectile.render(screen)
        if self.explosion_active:
            pygame.draw.circle(screen, (255, 165, 0),
                               (int(self.explosion_pos[0]), int(self.explosion_pos[1])),
                               int(self.explosion_radius), 2)
        # Restore original reloading graphic: a progress bar drawn above the tower.
        if self.is_reloading:
            scaled_reload = self.reload_time / game_tools.game_speed_multiplier
            progress = (pygame.time.get_ticks() - self.reload_start_time) / scaled_reload
            if progress > 1:
                progress = 1
            bar_width = self.rect.width
            bar_height = 5
            bar_x = self.rect.left
            bar_y = self.rect.top - bar_height - 2
            # Draw the background bar (red)
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # Draw the progress (green)
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))

    def shoot(self):
        global RoundFlag
        """Fire projectiles toward the target, applying upgrade effects."""
        current_time = pygame.time.get_ticks()
        scaled_interval = self.shoot_interval / game_tools.game_speed_multiplier
        if self.target and not self.is_reloading and pygame.time.get_ticks() - self.last_shot_time >= scaled_interval:
            self.shoot_sound.play()
            self.has_fired = True
            # If top upgrade is active, fire a spread shot
            if self.curr_top_upgrade > 1:
                spread_angles = [-20, -10, 0, 10, 20]
                for offset in spread_angles:
                    dx = self.target.position[0] - self.position[0]
                    dy = self.target.position[1] - self.position[1]
                    angle = math.degrees(math.atan2(-dy, dx))
                    proj = CommandoProjectile(self.position, angle + offset, speed=20, damage=self.damage)
                    if self.curr_bottom_upgrade >= 1:
                        scaled_interval /= 2
                        proj.explosive = True
                        proj.armor_break = True
                        proj.penetration = 3
                        proj.damage = self.damage
                    if self.curr_top_upgrade >= 1:
                        proj.piercing = True
                    self.projectiles.append(proj)
            else:
                dx = self.target.position[0] - self.position[0]
                dy = self.target.position[1] - self.position[1]
                angle = math.degrees(math.atan2(-dy, dx))
                proj = CommandoProjectile(self.position, angle, speed=20, damage=self.damage)
                if self.curr_bottom_upgrade >= 1:
                    proj.explosive = True
                    proj.armor_break = True
                if self.curr_top_upgrade >= 1:
                    proj.piercing = True
                self.projectiles.append(proj)

            self.last_shot_time = pygame.time.get_ticks()
            self.shot_count += 1  # Increment shot count

            # DEBUG: Print statements to check values
            print(f"Bottom Upgrade: {self.curr_bottom_upgrade}, Shot Count: {self.shot_count}")

            # **Force immediate reload for explosive rounds**
            if self.curr_bottom_upgrade == 1:
                print("Reloading after one shot (Explosive Rounds Active)")
                self.is_reloading = True
                self.reload_start_time = pygame.time.get_ticks()
                self.regame_tools.load_sound.play()
                self.shot_count = 0  # Reset shot count IMMEDIATELY to prevent standard reload logic

            # **Standard Reload Logic**
            elif self.curr_top_upgrade > 1 and self.shot_count >= 7:
                self.is_reloading = True
                self.reload_start_time = pygame.time.get_ticks()
                self.regame_tools.load_sound.play()
            elif self.curr_bottom_upgrade > 1 and self.shot_count >= 6:
                self.is_reloading = True
                self.reload_start_time = pygame.time.get_ticks()
                self.regame_tools.load_sound.play()
            elif self.shot_count >= 12:
                self.is_reloading = True
                self.reload_start_time = pygame.time.get_ticks()
                self.regame_tools.load_sound.play()


class RatFrost:
    sfx_frost = game_tools.load_sound("assets/frost_sfx.mp3")
    sfx_freeze = game_tools.load_sound("assets/slow_sfx.mp3")

    def __init__(self, position):
        self.position = position
        self.base_image = game_tools.load_image("assets/base_frost.png")
        self.image = self.base_image
        self.rect = self.image.get_rect(center=position)
        self.sell_amt = 100
        self.angle = 0

        # Base stats
        self.radius = 75
        self.slow_multiplier = 0.75
        self.radius_image = game_tools.load_image("assets/frost_freeze_radius_75.png")
        self.projectiles = []
        self.snowball_interval = 1500
        self.last_shot = 0
        self.last_freeze_time = 0

        # Upgrades
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.active_enemies = set()  # For damage-over-time tracking
        self.damage_timer = 0

        # Visual effects
        self.aura_surface = pygame.Surface((150, 150), pygame.SRCALPHA)
        self.trail_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
        self._create_aura_texture()

        # Lazily import enemy classes when an instance is created.
        self.immune_classes, self.vulnerable_classes = self._get_enemy_classes()

        # Define a fixed attack range for firing & slowing enemies.
        self.attack_range = self.radius

    def _get_enemy_classes(self):
        from game_tools import (AntEnemy, CentipedeEnemy, DungBeetleBoss, BeetleEnemy, RoachMinionEnemy,
                                RoachQueenEnemy, HornetEnemy,
                                FireflyEnemy, DragonflyEnemy)
        immune = (CentipedeEnemy, DungBeetleBoss,
                  RoachQueenEnemy)
        vulnerable = (HornetEnemy, FireflyEnemy, DragonflyEnemy, AntEnemy, DragonflyEnemy, RoachMinionEnemy, BeetleEnemy)
        return immune, vulnerable

    def _create_aura_texture(self):
        for r in range(75, 0, -1):
            alpha = int(50 * (1 - r / 75))
            pygame.draw.circle(self.aura_surface, (203, 239, 248, alpha), (75, 75), r, 2)

    def update(self, enemies):
        if self.curr_bottom_upgrade > 0:
            self.radius = 100
            self.attack_range = self.radius
        # Find the closest enemy within the attack range.
        closest = None
        min_dist = float('inf')
        for enemy in enemies:
            if isinstance(enemy, self.immune_classes):
                continue
            dx = enemy.position[0] - self.position[0]
            dy = enemy.position[1] - self.position[1]
            dist = math.hypot(dx, dy)
            if dist < min_dist:
                min_dist = dist
                closest = enemy

        # Only target if enemy is within the attack range.
        if closest and math.hypot(closest.position[0]-self.position[0],
                                  closest.position[1]-self.position[1]) <= self.attack_range \
                and self.curr_top_upgrade > 1:
            dx = closest.position[0] - self.position[0]
            dy = closest.position[1] - self.position[1]
            self.angle = math.degrees(math.atan2(-dy, dx))
            self.image = pygame.transform.rotate(self.base_image, self.angle)
            self.rect = self.image.get_rect(center=self.position)

        current_time = pygame.time.get_ticks()
        tower_slow = 0.65 if self.curr_bottom_upgrade >= 2 else 0.8

        self.active_enemies.clear()
        vulnerable_hit = False
        for enemy in enemies:
            if isinstance(enemy, self.immune_classes):
                continue

            # Initialize enemy properties if needed.
            if not hasattr(enemy, "base_speed"):
                enemy.base_speed = enemy.speed
            if not hasattr(enemy, "freeze_multiplier"):
                enemy.freeze_multiplier = 1.0

            # Reset enemy speed to its base.
            enemy.speed = enemy.base_speed

            dx = enemy.position[0] - self.position[0]
            dy = enemy.position[1] - self.position[1]
            if math.hypot(dx, dy) <= self.attack_range:
                self.active_enemies.add(enemy)
                # Apply tower slow combined with any accumulated freeze.
                effective_multiplier = tower_slow * enemy.freeze_multiplier
                enemy.speed = enemy.base_speed * effective_multiplier

                if isinstance(enemy, self.vulnerable_classes):
                    enemy.speed = max(enemy.speed * tower_slow, .25)
                    vulnerable_hit = True

                if self.curr_bottom_upgrade >= 3 and current_time - self.damage_timer >= 1000:
                    enemy.take_damage(0.25)

        # Play freeze SFX every 6000 ms if at least one vulnerable enemy is in range.
        if vulnerable_hit and (current_time - self.last_freeze_time >= 6000):
            self.last_freeze_time = current_time
            self.sfx_freeze.play()

        if self.curr_bottom_upgrade >= 3 and current_time - self.damage_timer >= 1000:
            self.damage_timer = current_time

        # Fire snowballs only if the closest enemy is within the attack range.
        if self.curr_top_upgrade >= 1 and closest:
            if math.hypot(closest.position[0]-self.position[0],
                          closest.position[1]-self.position[1]) <= self.attack_range + 100:
                if current_time - self.last_shot >= self._get_fire_interval():
                    self._fire_snowball(closest)
                    self.last_shot = current_time

        # Update projectiles.
        # If a projectile has collided and its collision timer has expired, remove it.
        for proj in self.projectiles[:]:
            proj.update()
            if proj.collided and (current_time - proj.collision_time >= 500):
                self.projectiles.remove(proj)
            elif not proj.collided and proj.check_collision(enemies):
                # When collision is detected, play the frost sfx.
                self.sfx_frost.play()

    def _get_fire_interval(self):
        if self.curr_top_upgrade >= 3:
            return 750 / game_tools.game_speed_multiplier
        if self.curr_top_upgrade >= 1:
            return 1500 / game_tools.game_speed_multiplier
        return float('inf')

    def _fire_snowball(self, target_enemy):
        proj = FrostProjectile(
            start_pos=self.position,
            target=target_enemy,
            speed=15,
            slow_amount=0.25 if self.curr_top_upgrade < 2 else 0.35,
            damage=1 if self.curr_top_upgrade >= 2 else 0
        )
        self.projectiles.append(proj)

    def shoot(self):
        pass

    def target(self):
        pass

    def render(self, screen):
        # Render the frost aura.
        if self.curr_bottom_upgrade < 1:
            radius_img = "assets/frost_freeze_radius_75.png"
        elif self.radius > 75:
            radius_img = "assets/frost_freeze_radius_100.png"
        if self.curr_bottom_upgrade < 1:
            screen.blit(game_tools.load_image(radius_img), (self.position[0] - 75, self.position[1] - 75))
        else:
            screen.blit(game_tools.load_image(radius_img), (self.position[0] - 100, self.position[1] - 100))
        # Render the tower.
        screen.blit(self.image, self.rect.topleft)
        # Render all projectiles.
        for proj in self.projectiles:
            proj.render(screen)


class FrostProjectile:
    def __init__(self, start_pos, target, speed, slow_amount, damage):
        self.position = list(start_pos)
        self.speed = speed
        self.slow = slow_amount
        self.damage = damage
        self.trail = []
        self.target = target  # Reference to the enemy target.
        self.collided = False
        self.collision_time = None

        # Set initial velocity toward the target.
        self.update_velocity()

        # Visual properties.
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255, 200), (4, 4), 4)
        self.impact_particles = []

    def update_velocity(self):
        if self.target is not None:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.velocity = [dx / dist * self.speed, dy / dist * self.speed]
            else:
                self.velocity = [0, 0]
        else:
            self.velocity = [0, 0]

    def update(self):
        # Recalculate velocity for homing.
        self.update_velocity()
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

        # Manage trail.
        self.trail.append(list(self.position))
        if len(self.trail) > 15:
            self.trail.pop(0)

    def check_collision(self, enemies):
        if self.collided:
            return False  # Already processed collision.
        for enemy in enemies:
            if math.hypot(enemy.position[0] - self.position[0],
                          enemy.position[1] - self.position[1]) < 20:
                if not hasattr(enemy, "freeze_multiplier"):
                    enemy.freeze_multiplier = 1.0
                # Stack the freeze effect.
                enemy.freeze_multiplier = max(enemy.freeze_multiplier * (1 - self.slow), 0.15)
                if self.damage > 0:
                    enemy.take_damage(self.damage)
                self._create_impact_effect()
                self.collided = True
                self.collision_time = pygame.time.get_ticks()
                return True
        return False

    def _create_impact_effect(self):
        # Create 8 impact particles.
        for _ in range(8):
            self.impact_particles.append({
                "pos": list(self.position),
                "vel": [random.uniform(-2, 2), random.uniform(-2, 2)],
                "life": 1000
            })

    def render(self, screen):
        # Render the trail.
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            pygame.draw.circle(screen, (255, 255, 255, alpha), pos, int(3 * (i / len(self.trail))))
        # Render the projectile if it hasn't collided.
        if not self.collided:
            screen.blit(self.image, (self.position[0] - 4, self.position[1] - 4))
        # Render impact particles.
        for p in self.impact_particles[:]:
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["life"] -= 20
            alpha = int(255 * (p["life"] / 1000))
            pygame.draw.circle(screen, (230, 250, 255, alpha),
                               (int(p["pos"][0]), int(p["pos"][1])),
                               max(1, int(3 * (p["life"] / 1000))))
            if p["life"] <= 0:
                self.impact_particles.remove(p)



class RatSniper:
    def __init__(self, position, shoot_interval=6500, damage=6):
        self.position = position
        self.damage = damage
        self.shoot_interval = shoot_interval  # default milliseconds between shots
        self.last_shot_time = 0
        self.projectiles = []
        self.target = None
        self.radius = 0
        self.image_path = "assets/sniper_base.png"
        self.image_path_shoot = "assets/sniper_base_shoot.png"
        # Load both the base turret image and the firing image.
        self.base_image = game_tools.load_image(self.image_path)
        self.shoot_image = game_tools.load_image(self.image_path_shoot)
        # Start with the base image.
        self.image = self.base_image
        self.original_image = self.base_image
        self.rect = self.image.get_rect(center=position)
        self.angle = 0  # current rotation angle

        # Firing state variables.
        self.firing = False
        self.firing_timer = 0  # time when the turret started firing

        # Upgrade attributes; set these externally as needed.
        self.curr_bottom_upgrade = 0  # valid values: 0, 1, 2, or 3.
        self.curr_top_upgrade = 0  # valid values: 0, 1, 2, or 3.

        # RatSniper has infinite range.
        self.shoot_sound = game_tools.load_sound("assets/sniper_shoot.mp3")
        self.sell_amt = 175

    def select_target(self, enemies):
        """
        Select a target from the list of enemies.
        Prioritize CentipedeEnemy regardless of health.
        If none are found, select an enemy that has a health attribute and is still alive (health > 0).
        """
        centipedes = [enemy for enemy in enemies if isinstance(enemy, enemies.CentipedeEnemy)]
        if centipedes:
            return centipedes[0]

        alive_enemies = [enemy for enemy in enemies if hasattr(enemy, 'health') and enemy.health > 0]
        if not alive_enemies:
            return None
        return max(alive_enemies, key=lambda e: e.health)

    def update(self, enemies):
        current_time = pygame.time.get_ticks()
        # Determine effective shooting interval based on curr_bottom_upgrade.
        if self.curr_bottom_upgrade == 1:
            effective_interval = 2000
        elif self.curr_bottom_upgrade > 1:
            effective_interval = 1000
        else:
            effective_interval = self.shoot_interval

        # Scale the effective interval by game_tools.game_speed_multiplier.
        scaled_interval = effective_interval / game_tools.game_speed_multiplier

        self.target = self.select_target(enemies)

        if self.target:
            # Rotate toward the target.
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]
            self.angle = math.degrees(math.atan2(-dy, dx))

            # Use the firing image for 50ms after firing; otherwise use base image.
            if self.firing and current_time - self.firing_timer < 50:
                self.original_image = self.shoot_image
            else:
                self.firing = False
                self.original_image = self.base_image

            self.image = pygame.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(center=self.position)

            # Fire only if enough time has passed.
            if current_time - self.last_shot_time >= scaled_interval:
                self.shoot(current_time)

        # Process projectile movement and collision.
        for projectile in self.projectiles[:]:
            if projectile.target is not None and not projectile.target.is_alive:
                self.projectiles.remove(projectile)
                continue
            projectile.move()

            if not (0 <= projectile.position[0] <= 1280 and 0 <= projectile.position[1] <= 720):
                self.projectiles.remove(projectile)
                continue

            # Check collision with enemies.
            for enemy in enemies:
                if hasattr(enemy, 'health') and enemy.health <= 0:
                    continue

                dist = math.hypot(projectile.position[0] - enemy.rect.centerx,
                                  projectile.position[1] - enemy.rect.centery)

                if dist < enemy.rect.width / 2:
                    # Determine primary damage.
                    if self.curr_top_upgrade == 2:
                        primary_damage = 15
                    else:
                        primary_damage = projectile.damage
                    enemy.take_damage(primary_damage, projectile=projectile)
                    self.create_impact_effect(projectile.position)

                    # Apply top-upgrade secondary effects.
                    if self.curr_top_upgrade == 1:
                        self.apply_secondary_damage(enemy, projectile.damage * 0.7, num_targets=1, enemies=enemies)
                    elif self.curr_top_upgrade == 3:
                        self.apply_secondary_damage(enemy, projectile.damage * 0.5, num_targets=4, enemies=enemies)

                    projectile.hit = True
                    break

            if projectile.hit and projectile in self.projectiles:
                self.projectiles.remove(projectile)

    def shoot(self, current_time):
        """
        Fire a projectile if the target is valid.
        Switches to the firing image for 50ms.
        """
        if hasattr(self.target, 'health') and self.target.health <= 0:
            return

        self.firing = True
        self.firing_timer = current_time
        self.shoot_sound.play()

        # Create a projectile with a speed of 150.
        proj = CommandoProjectile(self.position, self.angle, speed=50, damage=self.damage)
        proj.radius = 5
        proj.target = self.target
        # If curr_bottom_upgrade equals 3, add the armor_break attribute.
        if self.curr_bottom_upgrade == 3:
            proj.armor_break = True
        proj.homing = True

        self.projectiles.append(proj)
        self.last_shot_time = current_time

    def apply_secondary_damage(self, main_enemy, secondary_damage, num_targets, enemies):
        """
        Applies secondary damage to enemies behind the main_enemy.
        Considers enemies aligned with the projectile's travel direction (from the main enemy's center)
        within a tolerance. Applies damage to up to num_targets enemies.
        """
        angle_rad = math.radians(self.angle)
        vx, vy = math.cos(angle_rad), -math.sin(angle_rad)
        main_center = main_enemy.rect.center
        candidates = []
        for enemy in enemies:
            if enemy == main_enemy:
                continue
            if not hasattr(enemy, 'rect'):
                continue
            enemy_center = enemy.rect.center
            dx = enemy_center[0] - main_center[0]
            dy = enemy_center[1] - main_center[1]
            proj = dx * vx + dy * vy
            distance_sq = dx ** 2 + dy ** 2
            perp_sq = distance_sq - proj ** 2
            perp = math.sqrt(perp_sq) if perp_sq > 0 else 0
            if proj > 0 and perp < 30:
                candidates.append((proj, enemy))
        candidates.sort(key=lambda x: x[0])
        for i in range(min(num_targets, len(candidates))):
            enemy = candidates[i][1]
            enemy.take_damage(secondary_damage)

    def create_impact_effect(self, position):
        """
        Create a shards-like impact effect at the given position.
        Spawns several small particles radiating outwards that fade over time.
        """
        num_particles = 5
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            particle = {
                'pos': [position[0], position[1]],
                'vel': [math.cos(angle) * speed, math.sin(angle) * speed],
                'lifetime': random.randint(200, 400),
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3),
                'color': (200, 200, 200)  # Light gray.
            }
            game_tools.global_impact_particles.append(particle)

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
        for projectile in self.projectiles:
            projectile.render(screen)


class WizardTower:
    sfx_zap = game_tools.load_sound("assets/zap_sfx.mp3")
    sfx_explosion = game_tools.load_sound("assets/explosion_sfx.mp3")

    def __init__(self, position):
        self.image_path = "assets/wizard_base.png"
        self.position = position
        self.base_image = game_tools.load_image(self.image_path)
        self.original_image = self.base_image
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=position)
        self.radius = 100
        self.damage = 2
        self.attack_speed = 2.0
        self.target = None
        self.orb_count = 4
        self.orb_speed = 0.25
        self.fire_interval = 2500
        self.recharge_time = 3000
        self.last_fire_time = 0
        self.orbs = []
        self.lightning_interval = 2000
        self.last_lightning_time = 0
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.sell_amt = 200
        self.explosive_orbs = False
        self.currRound = False
        self.lightning_chain = 5
        self.lightning_damage = [self.damage, self.damage, self.damage / 2, self.damage / 2, self.damage / 2]
        self.lightning_targets = []
        self.orb_angles = [i * (360 / self.orb_count) for i in range(self.orb_count)]
        self.target_angle = 0
        self.current_angle = 0
        self.rotation_speed = 5
        self.orb_respawn_timers = {}
        self._init_orbs()
        self.last_frame_time = pygame.time.get_ticks()
        self.explosion_particles = []

    class OrbProjectile:
        def __init__(self, parent, angle, orbit_radius=40):
            self.parent = parent
            self.angle = angle
            self.orbit_radius = self.parent.radius / 2
            self.speed = 0.25
            self.damage = parent.damage
            self.image = game_tools.load_image("assets/orb_projectile.png")
            self.rect = self.image.get_rect()
            self.attacking = False
            self.target = None
            self.attack_speed = parent.attack_speed
            self.explosive = False
            self.armor_break = False
            self.initial_velocity = [0, 0]
            self.spark_particles = []
            self.orbit_offset = (0, 0)
            self.world_pos = parent.position
            self.position = self.world_pos
            self.alive = True
            self.last_update = pygame.time.get_ticks()
            self.particles = []

        class OrbParticle:
            def __init__(self, position):
                self.position = list(position)
                self.life = 250
                self.max_life = self.life
                self.start_time = pygame.time.get_ticks()
                angle = random.uniform(0, 2 * math.pi)
                self.velocity = [math.cos(angle) * 2, math.sin(angle) * 2]

            def update(self):
                dt = pygame.time.get_ticks() - self.start_time
                self.life = self.max_life - dt
                self.position[0] += self.velocity[0]
                self.position[1] += self.velocity[1]

            def render(self, screen, color=None):
                alpha = max(0, int(255 * (self.life / self.max_life)))
                surface = pygame.Surface((4, 4), pygame.SRCALPHA)
                if color is not None:
                    surface.fill((255, 69, 0, alpha))
                else:
                    surface.fill((255, 255, 255, alpha))
                screen.blit(surface, (self.position[0], self.position[1]))

        def update_orbit(self):
            if self.alive and not self.attacking:
                current_time = pygame.time.get_ticks()
                delta = (current_time - self.last_update) * game_tools.game_speed_multiplier
                self.last_update = current_time

                self.angle = (self.angle + self.speed * delta / 16) % 360
                rad = math.radians(self.angle)
                self.orbit_offset = (
                    math.cos(rad) * self.orbit_radius,
                    math.sin(rad) * self.orbit_radius
                )
                self.world_pos = (
                    self.parent.position[0] + self.orbit_offset[0],
                    self.parent.position[1] + self.orbit_offset[1]
                )
                self.rect.center = self.world_pos
                self.initial_velocity = [
                    math.cos(rad) * self.speed * 1,
                    math.sin(rad) * self.speed * 1
                ]

        def launch(self, target):
            self.attacking = True
            self.target = target
            self.world_pos = self.rect.center
            self.last_update = pygame.time.get_ticks()

        def update_attack(self, enemies):
            if self.attacking and self.alive:
                current_time = pygame.time.get_ticks()
                delta = (current_time - self.last_update) * game_tools.game_speed_multiplier
                self.last_update = current_time

                if self.target and self.target.is_alive:
                    dx = self.target.position[0] - self.world_pos[0]
                    dy = self.target.position[1] - self.world_pos[1]
                    distance = math.hypot(dx, dy)

                    if distance > 0:
                        self.initial_velocity[0] += (dx / distance) * 0.15 * delta / 16
                        self.initial_velocity[1] += (dy / distance) * 0.15 * delta / 16

                        self.world_pos = (
                            self.world_pos[0] + self.initial_velocity[0] * self.attack_speed * delta / 16,
                            self.world_pos[1] + self.initial_velocity[1] * self.attack_speed * delta / 16
                        )
                        self.rect.center = self.world_pos

                        if random.random() < 0.5:
                            self.spark_particles.append({
                                'pos': list(self.world_pos),
                                'vel': [
                                    -self.initial_velocity[0] * 0.3 + random.uniform(-0.5, 0.5),
                                    -self.initial_velocity[1] * 0.3 + random.uniform(-0.5, 0.5)
                                ],
                                'life': random.randint(100, 200),
                                'start': pygame.time.get_ticks()
                            })

                    for enemy in enemies:
                        if enemy.is_alive and self.rect.colliderect(enemy.rect):
                            self.on_impact(enemies)
                            self.alive = False
                            break  # Found first collision

                    if self.rect.colliderect(self.target.rect) and self.alive:
                        self.on_impact(enemies)
                else:
                    self.alive = False

        def on_impact(self, enemies):
            self.target.take_damage(self.damage, projectile=self)
            if self.explosive:
                self.create_explosion(enemies)
                self.parent.sfx_explosion.play()

            # Add respawn timer even if explosive
            self.parent.orb_respawn_timers[self.angle] = pygame.time.get_ticks()

            self.spawn_particles(self.world_pos)
            self.alive = False

        def spawn_particles(self, position):
            for _ in range(10):
                self.particles.append(self.OrbParticle(position))

        def create_explosion(self, enemies):
            explosion_pos = self.rect.center
            explosion_radius = 35

            # Spawn explosion particles
            for _ in range(15):
                self.spark_particles.append({
                    'pos': list(explosion_pos),
                    'vel': [random.uniform(-8, 8), random.uniform(-8, 8)],
                    'life': random.randint(100, 1000),
                    'start': pygame.time.get_ticks()
                })

            # Damage enemies with armor break
            for enemy in enemies:
                distance = math.hypot(enemy.position[0] - explosion_pos[0],
                                      enemy.position[1] - explosion_pos[1])
                if distance <= explosion_radius + enemy.rect.width / 2:
                    enemy.take_damage(2, projectile=self)

        def render_sparks(self, screen):
            current_time = pygame.time.get_ticks()
            for spark in self.spark_particles[:]:
                if current_time - spark['start'] > spark['life']:
                    self.spark_particles.remove(spark)
                else:
                    alpha = 255 - int((current_time - spark['start']) / spark['life'] * 255)
                    pygame.draw.circle(screen, (255, 255, 100, alpha),
                                       (int(spark['pos'][0]), int(spark['pos'][1])), 2)

        def render(self, screen):
            if self.alive:
                screen.blit(self.image, self.rect.topleft)
                self.render_sparks(screen)

    class LightningBolt:
        def __init__(self, start_pos, targets, damages):
            self.segments = []
            self.fork_particles = []
            self.duration = 250
            self.start_time = pygame.time.get_ticks()

            prev_pos = start_pos
            for i, target in enumerate(targets[:len(damages)]):
                new_pos = target.rect.center
                self.segments.append({
                    'start': prev_pos,
                    'end': new_pos,
                    'damage': damages[i],
                    'width': max(3 - i, 1)
                })

                num_forks = random.randint(2, 4)
                for _ in range(num_forks):
                    angle = random.uniform(0, math.pi * 2)
                    length = random.randint(10, 20)
                    self.fork_particles.append({
                        'start': new_pos,
                        'end': (
                            new_pos[0] + math.cos(angle) * length,
                            new_pos[1] + math.sin(angle) * length
                        ),
                        'life': random.randint(50, 150),
                        'start_time': pygame.time.get_ticks()
                    })

                prev_pos = new_pos

        def should_remove(self):
            return pygame.time.get_ticks() - self.start_time > self.duration * (2 / game_tools.game_speed_multiplier)

        def render(self, screen):
            alpha = max(0, 255 - int((pygame.time.get_ticks() - self.start_time) / self.duration * 255))

            core_color = (173, 216, 230, alpha)
            glow_color = (224, 255, 255, alpha // 2)
            fork_color = (200, 230, 255, alpha)

            for seg in self.segments:
                if not RoundFlag:
                    self.segments.remove(seg)
                else:
                    pygame.draw.line(screen, core_color, seg['start'], seg['end'], seg['width'])
                    pygame.draw.line(screen, glow_color, seg['start'], seg['end'], seg['width'] + 1)

            current_time = pygame.time.get_ticks()
            for fork in self.fork_particles[:]:
                if current_time - fork['start_time'] > fork['life']:
                    self.fork_particles.remove(fork)
                else:
                    fork_alpha = 255 - int((current_time - fork['start_time']) / fork['life'] * 255)
                    pygame.draw.line(screen, (*fork_color[:3], fork_alpha),
                                     fork['start'], fork['end'], 1)

    def update_rotation(self, enemies):

        self.target = None
        closest_distance = self.radius

        # Find closest enemy in range
        for enemy in enemies:
            dx = enemy.position[0] - self.position[0]
            dy = enemy.position[1] - self.position[1]
            distance = math.hypot(dx, dy)

            if distance <= self.radius and distance < closest_distance:
                closest_distance = distance
                self.target = enemy

        # Rotate to face target
        if self.target:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]

            # Calculate angle using same formula as MrCheese
            angle = math.degrees(math.atan2(-dy, dx) - 90)

            # Rotate image directly without smoothing
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.position)

    def update_lightning(self, enemies):
        if self.curr_bottom_upgrade >= 1:
            now = pygame.time.get_ticks()
            interval = (self.lightning_interval // self.curr_bottom_upgrade)
            scaled_interval = interval / game_tools.game_speed_multiplier

            if (now - self.last_lightning_time) > scaled_interval:
                targets = self.find_lightning_targets(enemies)
                if targets:
                    self.sfx_zap.play()
                    self.lightning_targets.append(self.LightningBolt(self.position, targets, self.lightning_damage))
                    self.last_lightning_time = now

                    for i, target in enumerate(targets[:len(self.lightning_damage)]):
                        target.take_damage(self.lightning_damage[i])

        self.lightning_targets = [bolt for bolt in self.lightning_targets if not bolt.should_remove()]

    def update(self, enemies):
        current_time = pygame.time.get_ticks()
        delta = (current_time - self.last_frame_time) * game_tools.game_speed_multiplier
        self.last_frame_time = current_time

        if self.curr_top_upgrade >= 1:
            new_count = 6 if self.curr_top_upgrade == 1 else 8
            if self.orb_count != new_count:
                self.orb_count = new_count
                self.orb_angles = [i * (360 / self.orb_count) for i in range(self.orb_count)]
                self._init_orbs()

        # Update explosive orbs based on top upgrade
        if self.curr_top_upgrade >= 3:  # Changed from 2 to 3
            self.explosive_orbs = True
            for orb in self.orbs:
                orb.explosive = True
                orb.armor_break = True
        else:
            self.explosive_orbs = False
            for orb in self.orbs:
                orb.explosive = False
                orb.armor_break = False

        if RoundFlag:
            self.currRound = False

        if not RoundFlag and not self.currRound:
            self.currRound = True
            self._init_orbs()

        self.update_orbs(enemies)
        self.update_lightning(enemies)
        self.update_rotation(enemies)

        # Update explosion particles
        for particle in self.explosion_particles[:]:
            particle.update()
            if particle.life <= 0:
                self.explosion_particles.remove(particle)

    def render(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect.topleft)

        for orb in self.orbs:
            orb.render(screen)

        for bolt in self.lightning_targets:
            bolt.render(screen)

        # Render explosion particles
        for particle in self.explosion_particles:
            particle.render(screen, color="orange")

        if UpgradeFlag and game_tools.curr_upgrade_tower == self:
            circle_surf = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (0, 0, 0, 128), (self.radius, self.radius), self.radius)
            screen.blit(circle_surf, (self.position[0] - self.radius, self.position[1] - self.radius))

    def find_lightning_targets(self, enemies):
        targets = []
        current_target = None
        max_chain = self.lightning_chain * self.curr_bottom_upgrade

        valid_enemies = [e for e in enemies
                         if math.hypot(e.position[0] - self.position[0],
                                       e.position[1] - self.position[1]) <= self.radius * 2]

        if valid_enemies:
            current_target = random.choice(valid_enemies)
            targets.append(current_target)

            for _ in range(max_chain - 1):
                next_targets = [e for e in enemies
                                if e not in targets and
                                math.hypot(e.position[0] - current_target.position[0],
                                           e.position[1] - current_target.position[1]) <= 100]
                if next_targets:
                    current_target = random.choice(next_targets)
                    targets.append(current_target)
                else:
                    break

        return targets

    def update_orbs(self, enemies):
        now = pygame.time.get_ticks()
        delta = (now - self.last_frame_time) * game_tools.game_speed_multiplier

        angles_to_remove = []
        for angle in self.orb_respawn_timers.copy():
            elapsed = (now - self.orb_respawn_timers[angle]) * game_tools.game_speed_multiplier
            if elapsed > self.recharge_time:
                # Find ALL matching orbs (in case of angle duplicates)
                matching_orbs = [o for o in self.orbs if o.angle == angle]

                if matching_orbs:
                    for orb in matching_orbs:
                        orb.alive = True
                        orb.attacking = False
                    angles_to_remove.append(angle)
                else:
                    # Clean up stale angles
                    del self.orb_respawn_timers[angle]

                # Remove processed angles
                for angle in angles_to_remove:
                    if angle in self.orb_respawn_timers:  # Check if key exists before deleting
                        del self.orb_respawn_timers[angle]

        if RoundFlag and (now - self.last_fire_time) * game_tools.game_speed_multiplier > self.fire_interval:
            targets = [e for e in enemies
                       if math.hypot(e.position[0] - self.position[0],
                                     e.position[1] - self.position[1]) <= self.radius]
            if targets:
                # Get all available orbs (not just first found)
                available_orbs = [o for o in self.orbs if o.alive and not o.attacking]
                for orb in random.sample(available_orbs, min(len(available_orbs), len(targets))):
                    orb.launch(random.choice(targets))
                self.last_fire_time = now

        for orb in self.orbs:
            if orb.attacking:
                orb.update_attack(enemies)
            else:
                orb.update_orbit()

            self.orb_speed = 0.35 if self.curr_top_upgrade == 1 else 0.5
            self.fire_interval = 1500 if self.curr_top_upgrade == 1 else 500

    def _init_orbs(self):
        self.orbs.clear()  # Clear existing orbs
        self.orb_respawn_timers.clear()  # Reset respawn timers
        self.orbs = []
        orbit_radius = self.radius / 2
        for angle in self.orb_angles:
            orb = self.OrbProjectile(self, angle, int(orbit_radius))
            orb.explosive = self.explosive_orbs
            self.orbs.append(orb)

    def shoot(self):
        pass


class MinigunTower:
    def __init__(self, position, image_path = None):
        self.position = position
        self.image_path = "assets/base_minigun.png"
        self.image = game_tools.load_image(self.image_path)
        self.original_image = game_tools.load_image(self.image_path)
        self.rect = self.image.get_rect(center=position)
        self.radius = 150  # attack range
        self.damage = 0.5
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.base_magazine = 65
        self.magazine_size = self.base_magazine
        self.reloading = False
        self.reload_time = 2.0  # seconds to reload
        self.reload_start_time = 0
        self.last_shot_time = 0  # in seconds
        self.last_update_time = pygame.time.get_ticks() / 1000.0
        self.max_spool = 15  # Maximum spool level (shots per second when fully spooled)
        self.current_spool = 0  # Current spool level (starts at 0)
        self.spool_rate = 2.0  # How quickly the minigun spools up (per second)
        self.cooldown_rate = 1.5  # How quickly the minigun spools down (per second)
        self.sell_amt = 300
        self.projectiles = []
        self.particles = []
        self.target = None
        self.beam_active = False
        self.last_beam_time = 0
        self.prev_pos = (0, 0)
        self.last_beam_damage_time = 0
        self.beam_sfx = game_tools.load_sound("assets/laser_fire.mp3")
        self.beam_channel = pygame.mixer.Channel(5)  # dedicated channel
        self.beam_playing = False  # state flag

    def find_target(self, enemies):
        target = None
        closest_distance = float('inf')
        for enemy in enemies:
            d = math.hypot(enemy.position[0] - self.position[0],
                           enemy.position[1] - self.position[1])
            if d <= self.radius and d < closest_distance:
                closest_distance = d
                target = enemy
        return target

    def update(self, enemies):
        current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
        dt = current_time - self.last_update_time  # Calculate delta time
        self.last_update_time = current_time  # Store the current time for next update

        # Reset spool and magazine after round ends
        if not RoundFlag:
            self.current_spool = 0
            self.magazine_size = self.base_magazine

        if self.curr_bottom_upgrade == 2:
            self.magazine_size = 100

        # Handle reloading
        if self.reloading:
            if current_time - self.reload_start_time >= self.reload_time:
                self.magazine_size = self.base_magazine
                self.reloading = False
            else:
                return  # Cannot fire while reloading

        self.target = self.find_target(enemies)

        if self.current_spool > 0 and (current_time - self.last_shot_time) > (1.0 / max(1, self.current_spool)):
            self.current_spool = max(0, self.current_spool - (self.cooldown_rate * dt))

        # Target selection and image rotation
        if self.target:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]
            angle = math.degrees(math.atan2(-dy, dx))
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.position)
        else:
            self.target = None  # No target: do not fire

        if self.magazine_size > 0:
            # Spool up when firing
            self.current_spool = min(self.max_spool, self.current_spool + (self.spool_rate * game_tools.game_speed_multiplier) * dt)
            # Calculate fire delay: if fully spooled, shots per second = max_spool, so delay = 1/max_spool.
            # Otherwise, fire_delay = 1 / current_spool.
            fire_delay = 1.0 / self.current_spool if self.current_spool > 0 else float('inf')
            if current_time - self.last_shot_time >= fire_delay and self.target is not None:
                self.fire_projectile(self.target)
                self.last_shot_time = current_time
                self.magazine_size -= 1
                if self.magazine_size <= 0:
                    self.start_reload()

        # Update projectiles
        for projectile in self.projectiles[:]:
            if self.curr_bottom_upgrade == 1:
                projectile.image = game_tools.load_image("assets/projectile_bullet_flame.png")
                projectile.original_image = game_tools.load_image("assets/projectile_bullet_flame.png")
            projectile.move()
            if projectile.hit:
                self.spawn_particles(projectile.position)
                self.projectiles.remove(projectile)

        # Death ray update (unchanged from your original code)
        if self.curr_bottom_upgrade == 2 and self.target:
            self.beam_active = True
            if not self.beam_playing:
                self.beam_channel.play(self.beam_sfx, loops=-1)
                self.beam_playing = True
            effective_beam_interval = 250 / game_tools.game_speed_multiplier / 1000.0  # converting ms to seconds if needed
            if current_time - self.last_beam_damage_time >= effective_beam_interval:
                self.target.take_damage(self.damage)
                self.last_beam_damage_time = current_time
        else:
            self.beam_active = False
            if self.beam_playing:
                self.beam_channel.stop()
                self.beam_playing = False

        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)

    def start_reload(self):
        self.reloading = True
        self.reload_start_time = pygame.time.get_ticks() / 1000.0
        self.current_spool = 0  # Reset spool when reloading

    def shoot(self):
        pass

    def fire_projectile(self, target):
        print(f"spawning projectile (spool level: {self.current_spool:.1f}, mag size: {self.magazine_size})")
        flame = (self.curr_bottom_upgrade == 1)
        projectile = MinigunProjectile((self.position[0], self.position[1]), target,
                                       speed=10 * game_tools.game_speed_multiplier,
                                       damage=self.damage,
                                       flame=flame)
        self.projectiles.append(projectile)
        shoot_sound = game_tools.load_sound("assets/minigun_shoot.mp3")
        if self.curr_bottom_upgrade != 2:
            shoot_sound.play()

    def spawn_particles(self, position):
        if self.curr_bottom_upgrade == 1:
            color = "orange"
        elif self.curr_bottom_upgrade == 2:
            color = 'beam'
        else:
            color = "grey"
        if self.curr_bottom_upgrade < 2:
            for _ in range(5):
                self.particles.append(MinigunParticle(position, color))
        else:
            for _ in range(2):
                self.particles.append(MinigunParticle(position, color))

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)

        current_time = pygame.time.get_ticks()
        for projectile in self.projectiles:
            if self.curr_bottom_upgrade < 2:
                projectile.render(screen)

        if self.curr_bottom_upgrade == 2:
            if self.target is not None:
                self.prev_pos = self.target.position  # Save last position
                pygame.draw.line(screen, (255, 140, 0), self.position, self.target.position, 13)

                # ⏳ Keep beam active for 1000ms after last hit
            elif 0 <= (current_time - self.last_beam_time) <= 100 and hasattr(self, 'prev_pos'):
                pygame.draw.line(screen, (255, 140, 0), self.position, self.prev_pos, 13)

        for particle in self.particles:
            particle.render(screen)
        if self.reloading:
            self.render_reload(screen)

    def render_reload(self, screen):
        current_time = pygame.time.get_ticks() / 1000.0
        progress = 1.0 if self.reload_time == 0 else (current_time - self.reload_start_time) / self.reload_time
        progress = min(progress, 1)
        bar_width = self.rect.width
        bar_height = 5
        bar_x = self.rect.left
        bar_y = self.rect.top - bar_height - 2
        # Draw the background bar (red)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Draw the progress (green)
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))


class MinigunProjectile:
    def __init__(self, position, target, speed, damage, flame=False):
        self.position = list(position)
        self.target = target
        self.speed = speed
        self.damage = damage
        self.flame = flame
        self.hit = False
        self.original_image = game_tools.load_image("assets/projectile_bullet.png")
        dx = target.position[0] - position[0]
        dy = target.position[1] - position[1]
        distance = math.hypot(dx, dy)
        if distance == 0:
            self.direction = (0, 0)
            self.angle = 0
        else:
            self.direction = (dx / distance, dy / distance)
            self.angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(self.original_image, self.angle)

    def move(self):
        self.position[0] += self.direction[0] * self.speed
        self.position[1] += self.direction[1] * self.speed
        try:
            target_x, target_y = self.target.position  # This could fail if self.target has no valid position
        except IndexError:
            return
        if math.hypot(self.position[0] - self.target.position[0], self.position[1] - self.target.position[1]) < 10:
            self.target.take_damage(self.damage)
            self.hit = True

        # Destroy projectile if it leaves screen bounds
        if not (0 <= self.position[0] <= 1280 and 0 <= self.position[1] <= 720):
            self.hit = True

    def render(self, screen):
        rect = self.image.get_rect(center=self.position)
        screen.blit(self.image, rect.topleft)


class MinigunParticle:
    def __init__(self, position, color):
        self.position = list(position)
        self.life = 250  # particle lasts 500 ms
        self.start_time = pygame.time.get_ticks()
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = [math.cos(angle) * 2, math.sin(angle) * 2]

    def update(self):
        dt = pygame.time.get_ticks() - self.start_time
        if self.color == 'beam':
            max_life = 150
        elif self.color == "orange":
            max_life = 500
        else:
            max_life = 250
        self.life = max_life - dt  # Subtract elapsed time
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

    def render(self, screen):
        if self.color == 'beam':
            max_life = 150
        elif self.color == "orange":
            max_life = 500
        elif self.color == "grey":
            max_life = 250
        alpha = max(0, int(255 * (self.life / max_life)))  # Scale alpha accordingly
        surface = pygame.Surface((4, 4), pygame.SRCALPHA)

        if self.color == ("orange" or 'beam'):
            surface.fill((255, 140, 0, alpha))
        elif self.color == "grey":
            surface.fill((200, 200, 200, alpha))

        screen.blit(surface, (self.position[0], self.position[1]))


class Ozbourne:

    def __init__(self, position, radius, weapon, damage, riff_blast_radius, image_path, riff_interval=4000):
        self.position = position
        self.radius = radius
        self.weapon = weapon
        self.damage = damage
        self.image_path = "assets/alfredo_ozbourne_base.png"
        self.image = game_tools.load_image(self.image_path)
        self.original_image = game_tools.load_image(self.image_path)
        self.rect = self.image.get_rect(center=position)
        self.riff_interval = riff_interval
        self.riff_blast_radius = riff_blast_radius
        self.last_blast_time = 0
        self.blast_active = False
        self.blast_animation_timer = 0
        self.blast_duration = 1165 * 2
        self.blast_radius = 0
        self.max_blast_radius = self.riff_blast_radius
        self.sell_amt = 250
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.riff_count = 0
        self.damage_default = self.damage
        self.riff_sfx = game_tools.load_sound("assets/riff1.mp3")
        self.riff_channel = pygame.mixer.Channel(4)
        # Flag to track if riff_longer is currently playing
        self.riff_playing = False
        self.stun_sfx = game_tools.load_sound("assets/dungbeetle_shield.mp3")
        # Solo upgrade variables:
        self.solo_icon_visible = True  # will be true at the start of each round if bottom upgrade == 2
        self.solo_active = False
        self.solo_timer = None
        self.lightning_end_time = None
        self.original_riff_interval = riff_interval
        self.original_blast_radius = riff_blast_radius
        self.original_radius = radius
        self.solo_channel = pygame.mixer.Channel(0)
        self.solo_sound = game_tools.load_sound("assets/solo.mp3")
        self.last_riff_time = 0

    def reset_solo(self):
        # Call this at the beginning of each round to re-enable the rock icon if applicable.
        if self.curr_bottom_upgrade == 2:
            self.solo_channel.stop()
            mixer.music.unpause()
            self.solo_icon_visible = True
            self.solo_active = False
            self.solo_timer = None
            self.lightning_end_time = None
            self.riff_blast_radius = self.original_blast_radius
            self.max_blast_radius = self.original_blast_radius
            self.radius = self.original_radius
            self.riff_interval = self.original_riff_interval

    def trigger_solo(self, screen):
        self.riff_channel.stop()
        if self.solo_active:
            return  # already triggered, do nothing
        # Stop any ongoing music (e.g. riff_longer effects and background music)
        pygame.mixer.music.pause()
        self.solo_channel.play(self.solo_sound, loops=0)
        # Activate the solo effect:
        self.solo_active = True
        self.solo_timer = pygame.time.get_ticks()
        self.lightning_end_time = self.solo_timer + 2000  # lightning effect lasts 2 seconds
        # Increase blast radius for 20 seconds:
        self.original_blast_radius = self.riff_blast_radius  # store current value
        self.riff_blast_radius = 500
        self.max_blast_radius = self.riff_blast_radius
        self.radius = 500
        self.original_riff_interval = self.riff_interval  # store current value
        self.riff_interval = 2000
        # Hide the rock icon so it can only be triggered once per round:
        self.solo_icon_visible = False

    def draw_lightning_effects(self, screen):
        current_time = pygame.time.get_ticks()
        if self.solo_active:
            screen_height = screen.get_height()
            # Spawn lightning every 220 pixels from x=0 to 1100:
            for x in range(0, 1101, 220):
                points = []
                y = 0
                # Create a polyline from the top to the bottom with random horizontal offsets:
                while y < screen_height:
                    offset = random.randint(-20, 20)
                    points.append((x + offset, y))
                    y += random.randint(30, 60)
                pygame.draw.lines(screen, (255, 255, 0), False, points, 2)
                # Optional: add a branch effect
                if points:
                    branch_index = random.randint(0, len(points) - 1)
                    branch_start = points[branch_index]
                    branch_points = [branch_start]
                    bx, by = branch_start
                    for i in range(3):
                        bx += random.randint(-30, 30)
                        by += random.randint(30, 60)
                        branch_points.append((bx, by))
                    pygame.draw.lines(screen, (255, 255, 0), False, branch_points, 2)

    def update(self, enemies):
        scaled_interval = self.riff_interval / game_tools.game_speed_multiplier
        scaled_duration = self.blast_duration / game_tools.game_speed_multiplier

        # Determine if any enemy is within the tower's radius
        enemy_in_range = False
        for enemy in enemies:
            distance = math.hypot(enemy.position[0] - self.position[0],
                                  enemy.position[1] - self.position[1])
            if distance <= self.radius:
                enemy_in_range = True
                break

        current_time = pygame.time.get_ticks()
        # If solo effect is active and 20 seconds have passed, revert changes.
        if self.solo_active and self.solo_timer and current_time >= self.solo_timer + (20000 / game_tools.game_speed_multiplier):
            self.riff_blast_radius = self.original_blast_radius
            self.max_blast_radius = self.original_blast_radius
            self.riff_interval = self.original_riff_interval
            self.radius = self.original_radius
            self.solo_active = False
            self.solo_channel.stop()
            # Resume background music (adjust track as appropriate)
            pygame.mixer.music.unpause()

        # If upgraded and an enemy is in range, ensure riff_longer is playing
        if self.curr_bottom_upgrade >= 1 and enemy_in_range:
            self.riff_sfx = game_tools.load_sound("assets/riff_longer.mp3")
            if not self.riff_playing and not self.solo_active:
                if not self.riff_channel.get_busy():
                    if pygame.time.get_ticks() - self.last_riff_time >= 1500:
                        mixer.music.pause()
                        self.riff_channel.set_volume(game_tools.user_volume * .75)
                        self.riff_channel.play(self.riff_sfx, loops=-1)
                        self.last_riff_time = pygame.time.get_ticks()
                self.riff_playing = True
            # Trigger blast at the specified interval
            if pygame.time.get_ticks() - self.last_blast_time >= scaled_interval:
                self.blast(enemies)
                self.last_blast_time = pygame.time.get_ticks()
        elif (pygame.time.get_ticks() - self.last_blast_time >= scaled_interval) and enemy_in_range:
            self.blast(enemies)
        else:
            # If no enemy is in range (or not upgraded), switch back to main music if needed
            if self.riff_playing and not self.solo_active:
                self.riff_channel.stop()
                mixer.music.unpause()
                self.riff_playing = False
            elif (pygame.time.get_ticks() - self.last_blast_time >= scaled_interval) and enemy_in_range:
                self.blast(enemies)
                self.last_blast_time = pygame.time.get_ticks()
            self.riff_count = 0

        # Handle blast animation timing
        if self.blast_active:
            # Calculate dt and cap it (e.g., 50 ms)
            dt = pygame.time.get_ticks() - self.last_blast_time
            dt = min(dt, 50)

            self.blast_animation_timer += dt
            self.blast_radius += (self.max_blast_radius / scaled_duration) * dt
            # Cap the blast radius to prevent runaway growth:
            self.blast_radius = min(self.blast_radius, self.max_blast_radius)
            if self.blast_animation_timer >= scaled_duration:
                self.blast_active = False
                self.blast_radius = 0
                # Optionally, reset blast_start_time here if using a separate timestamp.

        if not RoundFlag:
            self.damage = 1
            # Ensure main music plays if the round stops
            if self.curr_bottom_upgrade == 1 and self.riff_playing:
                mixer.music.load("assets/map_music.mp3")
                mixer.music.play(-1)
                self.riff_playing = False
            self.riff_count = 0

    def blast(self, enemies):
        if self.curr_bottom_upgrade < 1:
            self.riff_sfx.play()
        elif self.curr_bottom_upgrade >= 1:
            self.riff_count += 1
            self.damage = self.damage_default + (self.riff_count * 0.1)
            if self.riff_count >= 88:
                self.riff_count = 0
                self.damage = self.damage_default
        self.last_blast_time = pygame.time.get_ticks()
        self.blast_active = True
        self.blast_animation_timer = 0
        self.blast_radius = 0

        for enemy in enemies:
            distance = math.hypot(enemy.position[0] - self.position[0],
                                  enemy.position[1] - self.position[1])
            if distance <= self.riff_blast_radius:
                enemy.take_damage(self.damage)
                if self.curr_top_upgrade == 2:
                    if isinstance(enemy, enemies.DungBeetleBoss) or isinstance(enemy, enemies.BeetleEnemy) or isinstance(enemy, enemies.RoachQueenEnemy):
                        return
                    current_time = pygame.time.get_ticks()
                    game_tools.spawn_shard(enemy.position, count=3)
                    self.stun_sfx.play()
                    # Save the enemy's current speed if not already stunned
                    if not hasattr(enemy, "stun_end_time") or current_time >= enemy.stun_end_time:
                        enemy.original_speed = enemy.speed
                    enemy.speed = 0
                    enemy.stun_end_time = current_time + 1000 / game_tools.game_speed_multiplier

    def render(self, screen):
        tower_rect = self.image.get_rect(center=self.position)
        screen.blit(self.image, tower_rect)
        # Draw the rock icon if this Ozbourne has the solo upgrade.
        if self.curr_bottom_upgrade == 2 and self.solo_icon_visible:
            rock_icon = game_tools.load_image("assets/rock_icon.png")
            icon_rect = rock_icon.get_rect()
            # Position: centered horizontally over tower, 20 pixels above the top.
            icon_rect.centerx = self.position[0]
            icon_rect.bottom = self.position[1] - 30
            screen.blit(rock_icon, icon_rect)
            mouse_pos = pygame.mouse.get_pos()
            # If the icon is clicked, trigger the solo.
            if icon_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0] and RoundFlag:
                self.trigger_solo(screen)

        # If the solo effect is active, draw the lightning effects.
        if self.solo_active and self.lightning_end_time:
            self.draw_lightning_effects(screen)

        if self.blast_active:
            normalized_damage = (self.damage - 1) / (9.8 - 1)
            normalized_damage = max(0, min(1, normalized_damage))
            r = 255
            g = int(200 * (1 - normalized_damage))
            b = int(100 * (1 - normalized_damage))
            pygame.draw.circle(
                screen,
                (r, g, b),
                self.position,
                int(self.blast_radius),
                2
            )


class CheeseBeacon:
    DEBUG = True
    _all_boosts = {}  # Class-level tracking {tower: {beacon: boosts}}

    def __init__(self, position):
        self.position = position
        self.image_path = "assets/beacon_base.png"
        self.image = game_tools.load_image(self.image_path)
        self.rect = self.image.get_rect(center=position)
        self.radius = 100
        self.last_signal = 0
        self.signal_interval = 5000
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.sell_amt = 700
        self.active = True
        self.boost_timer = 0
        self._effects = []

        # Boost assets
        self.indicators = {
            'damage': game_tools.load_image("assets/damage_boost.png"),
            'radius': game_tools.load_image("assets/radius_boost.png"),
            'speed': game_tools.load_image("assets/speed_boost.png")
        }

    def update(self, towers, delta):
        if not self.active: return

        # Update timers with game speed
        self.last_signal += delta
        self.boost_timer += delta

        # Send visual signal
        if self.last_signal >= 5000:
            self.last_signal = 0
            self._create_signal_effect()

        # Refresh boosts every 500ms
        if self.boost_timer >= 500:
            self.boost_timer = 0
            self._refresh_boosts(towers)

    def _refresh_boosts(self, towers):
        current_boosts = {}
        effective_radius = self.radius

        for tower in list(CheeseBeacon._all_boosts.keys()):
            if tower not in towers:  # Tower was sold/removed
                # Restore original values before removal
                if hasattr(tower, '_base_damage'):
                    if isinstance(tower, Ozbourne):
                        if not tower.solo_active:
                            tower.damage = tower._base_damage
                            del tower._base_damage
                    else:
                        tower.damage = tower._base_damage
                        del tower._base_damage
                if hasattr(tower, '_base_radius'):
                    if isinstance(tower, Ozbourne):
                        if not tower.solo_active:
                            tower.radius = tower._base_radius
                            del tower._base_radius
                    else:
                        tower.radius = tower._base_radius
                        del tower._base_radius
                if hasattr(tower, '_base_shoot_interval'):
                    tower.shoot_interval = tower._base_shoot_interval
                    del tower._base_shoot_interval
                del CheeseBeacon._all_boosts[tower]

        # Find towers in range
        for tower in towers:
            if tower is self: continue
            dx = tower.position[0] - self.position[0]
            dy = tower.position[1] - self.position[1]
            if math.hypot(dx, dy) <= effective_radius:
                current_boosts[tower] = self._calculate_boosts(tower)

        # Update class-level boost tracking
        for tower, boosts in current_boosts.items():
            if tower not in CheeseBeacon._all_boosts:
                CheeseBeacon._all_boosts[tower] = {}
            CheeseBeacon._all_boosts[tower][self] = boosts

        # Remove old boosts
        for tower in list(CheeseBeacon._all_boosts.keys()):
            for beacon in list(CheeseBeacon._all_boosts[tower].keys()):
                if not beacon.active:
                    del CheeseBeacon._all_boosts[tower][beacon]
            if not CheeseBeacon._all_boosts[tower]:
                del CheeseBeacon._all_boosts[tower]

        # Apply actual stat modifications
        for tower, beacons in CheeseBeacon._all_boosts.items():
            self._apply_tower_boosts(tower, beacons)

        if CheeseBeacon.DEBUG:
            print(f"\n=== Beacon at {self.position} Update ===")
            print(f"Effective Radius: {effective_radius}px")
            print(f"Towers in range: {len(current_boosts)}")

    def _calculate_boosts(self, tower):
        boosts = {}
        # Damage boost
        if self.curr_top_upgrade == 0:
            dmg_boost = 1.25
            boosts['damage'] = dmg_boost
        elif self.curr_top_upgrade == 1:
            dmg_boost = 2.25
            boosts['damage'] = dmg_boost
        elif self.curr_top_upgrade == 2:
            dmg_boost = 3.33
            boosts['damage'] = dmg_boost
        elif self.curr_top_upgrade == 3:
            dmg_boost = 4.5
            boosts['damage'] = dmg_boost
        else:
            dmg_boost = 1.25

        boosts['damage'] = dmg_boost

        # Radius boost
        if self.curr_bottom_upgrade >= 1:
            boosts['radius'] = 1.25

        # Speed boost
        if self.curr_bottom_upgrade >= 2:
            boosts['speed'] = 1.25

        return boosts

    def _apply_tower_boosts(self, tower, beacons):
        if tower not in towers:  # towers should be passed from update()
            return

        if CheeseBeacon.DEBUG and not hasattr(tower, '_base_damage'):
            print(f"\nTracking new tower: {type(tower).__name__} at {tower.position}")
            print(f"Original Damage: {getattr(tower, 'damage', 'N/A')}")
            print(f"Original Radius: {getattr(tower, 'radius', 'N/A')}px")
            print(f"Original Speed: {getattr(tower, 'shoot_interval', 'N/A')}ms")

        if isinstance(tower, Ozbourne):
            if tower.solo_active:
                return

        # Damage
        base_dmg = getattr(tower, '_base_damage', None)
        if base_dmg is None:
            tower._base_damage = getattr(tower, 'damage', 1)
        total_dmg = tower._base_damage
        for boost in beacons.values():
            if total_dmg is not None:
                total_dmg *= boost.get('damage', 1)
        if hasattr(tower, 'damage'):
            tower.damage = total_dmg

        # Radius
        base_radius = getattr(tower, '_base_radius', None)
        if base_radius is None:
            tower._base_radius = getattr(tower, 'radius', 100)
        total_radius = tower._base_radius
        for boost in beacons.values():
            total_radius *= boost.get('radius', 1)
        if hasattr(tower, 'radius'):
            tower.radius = total_radius

        # Speed
        if hasattr(tower, 'shoot_interval'):
            base_speed = getattr(tower, '_base_shoot_interval', None)
            if base_speed is None:
                tower._base_shoot_interval = tower.shoot_interval
            total_speed = tower._base_shoot_interval
            for boost in beacons.values():
                if total_speed is not None:
                    total_speed /= boost.get('speed', 1)
            tower.shoot_interval = total_speed

        # Specialized attribute handling
        if isinstance(tower, Ozbourne):
            if not tower.solo_active:
                # Radius boost affects blast parameters
                if hasattr(tower, 'max_blast_radius'):
                    for boost in beacons.values():
                        total_radius *= boost.get('radius', 1)
                    tower.max_blast_radius = total_radius

                # Speed boost affects riff interval
                if hasattr(tower, 'riff_interval'):
                    base_speed = getattr(tower, '_base_riff_interval', None)
                    if base_speed is None:
                        tower._base_riff_interval = tower.riff_interval
                    total_speed = tower._base_riff_interval
                    for boost in beacons.values():
                        total_speed /= boost.get('speed', 1)
                    if not hasattr(tower, '_base_riff_interval'):
                        tower._base_riff_interval = tower.riff_interval
                    tower.riff_interval = total_speed

        elif isinstance(tower, CheddarCommando):
            # Speed boost affects reload time
            if hasattr(tower, 'reload_time'):
                base_speed = getattr(tower, '_base_reload_time', None)
                if base_speed is None:
                    tower._base_reload_time = tower.reload_time
                total_speed = tower._base_reload_time
                for boost in beacons.values():
                    total_speed /= boost.get('speed', 1)
                total_speed /= 1000
                if not hasattr(tower, '_base_reload_time'):
                    tower._base_reload_time = tower.reload_time
                tower.reload_time = tower._base_reload_time / total_speed
                print(f"total speed={total_speed}")

        elif isinstance(tower, MinigunTower):
            # Speed boost affects minigun spooling
            if hasattr(tower, 'max_spool'):
                base_speed = getattr(tower, '_base_max_spool', None)
                if base_speed is None:
                    tower._base_max_spool = tower.max_spool
                total_speed = tower._base_max_spool
                for boost in beacons.values():
                    total_speed /= boost.get('speed', 1)
                total_speed /= 3.75
                if not hasattr(tower, '_base_max_spool'):
                    tower._base_max_spool = tower.max_spool
                tower.max_spool *= total_speed
                print(f"total speed (max spool)={total_speed}")

            if hasattr(tower, 'reload_time'):
                base_speed = getattr(tower, '_base_reload_time', None)
                if base_speed is None:
                    tower._base_reload_time = tower.reload_time
                total_speed = tower._base_reload_time
                for boost in beacons.values():
                    total_speed /= boost.get('speed', 1)
                total_speed /= 1000
                if not hasattr(tower, '_base_reload_time'):
                    tower._base_reload_time = tower.reload_time
                tower.reload_time = tower.reload_time / 2

            if hasattr(tower, 'spool_rate'):
                base_speed = getattr(tower, '_base_spool_rate', None)
                if base_speed is None:
                    tower._base_spool_rate = tower.spool_rate
                total_speed = tower._base_spool_rate
                for boost in beacons.values():
                    total_speed *= boost.get('speed', 1)
                # total_speed *= 2
                if not hasattr(tower, '_base_spool_rate'):
                    tower._base_spool_rate = tower.spool_rate
                tower.spool_rate = tower._base_spool_rate * 2
                print(f"total speed (spool rate)={total_speed}")

        elif isinstance(tower, WizardTower):
            # Speed boost affects orb attack speed
            if hasattr(tower, 'attack_speed'):
                base_speed = getattr(tower, '_base_attack_speed', None)
                if base_speed is None:
                    tower._base_attack_speed = tower.attack_speed
                total_speed = tower._base_attack_speed
                for boost in beacons.values():
                    total_speed /= boost.get('speed', 1)
                if not hasattr(tower, '_base_attack_speed'):
                    tower._base_attack_speed = tower.attack_speed
                tower.attack_speed = tower._base_attack_speed * total_speed
            if hasattr(tower, 'lightning_interval'):
                base_speed = getattr(tower, '_base_lightning_interval', None)
                if base_speed is None:
                    tower._base_lightning_interval = tower.lightning_interval
                total_speed = tower._base_lightning_interval
                for boost in beacons.values():
                    total_speed /= boost.get('speed', 1)
                total_speed /= 1000
                if not hasattr(tower, '_base_attack_speed'):
                    tower._base_lightning_interval = tower.lightning_interval
                tower.lightning_interval = tower._base_lightning_interval / total_speed
                print(f"total speed (lightning)={total_speed}")

        elif isinstance(tower, RatTent):
            base_spawn = getattr(tower, '_base_spawn_interval', None)
            if base_spawn is None:
                tower._base_spawn_interval = tower.spawn_interval
            total_spawn = tower._base_spawn_interval
            for boost in beacons.values():
                total_spawn /= boost.get('speed', 1)
            tower.spawn_interval = total_spawn

        if CheeseBeacon.DEBUG:
            print(f"\nTower: {type(tower).__name__} at {tower.position}")
            print(f"Active Beacons: {len(beacons)}")
            if hasattr(tower, 'damage'):
                print(f"Damage: {tower._base_damage} -> {tower.damage}")
            if hasattr(tower, 'radius'):
                print(f"Radius: {tower._base_radius}px -> {tower.radius}px")
            if hasattr(tower, 'shoot_interval'):
                print(f"Fire Rate: {tower._base_shoot_interval}ms -> {tower.shoot_interval}ms")
            if isinstance(tower, RatTent):
                print(f"Spawn Rate: {tower._base_spawn_interval}ms -> {tower.spawn_interval}ms")
            # Ozbourne
            elif isinstance(tower, Ozbourne):
                print(f"Blast Radius: {tower.max_blast_radius}")
                print(f"Riff Interval: {tower.riff_interval}ms")

            # Commando
            elif isinstance(tower, CheddarCommando):
                print(f"Reload Time: {tower.reload_time}ms")

            # Minigun
            elif isinstance(tower, MinigunTower):
                print(f"Max Spool: {tower.max_spool}")
                print(f"Spool Rate: {tower.spool_rate}")
                print(f"Cooldown Rate: {tower.cooldown_rate}")

            # Wizard
            elif isinstance(tower, WizardTower):
                print(f"Attack Speed: {tower.attack_speed}")
                print(f"Lightning Interval: {tower.lightning_interval}")

    def _remove_tower_boosts(self, tower):
        """
        Recalculates and removes this beacon's boost effects from the given tower.
        It does so by removing this beacon’s boost from the aggregated boost dictionary
        and then reapplying all remaining boosts based on the tower’s stored base attributes.
        """
        # Get a copy of the current boost dictionary for the tower.
        remaining_boosts = {}
        if tower in CheeseBeacon._all_boosts:
            # Copy all boost entries except for this beacon.
            for beacon, boosts in CheeseBeacon._all_boosts[tower].items():
                if beacon is not self:
                    remaining_boosts[beacon] = boosts

        # Recalculate damage from base_damage
        if hasattr(tower, '_base_damage'):
            total_damage = tower._base_damage
            for boosts in remaining_boosts.values():
                total_damage *= boosts.get('damage', 1)
            tower.damage = total_damage

        # Recalculate radius from base_radius
        if hasattr(tower, '_base_radius'):
            total_radius = tower._base_radius
            for boosts in remaining_boosts.values():
                total_radius *= boosts.get('radius', 1)
            tower.radius = total_radius

        # Recalculate shooting speed from base shoot_interval (note: boosts here are applied by division)
        if hasattr(tower, '_base_shoot_interval'):
            total_shoot_interval = tower._base_shoot_interval
            for boosts in remaining_boosts.values():
                total_shoot_interval /= boosts.get('speed', 1)
            tower.shoot_interval = total_shoot_interval

        # Specialized attribute handling:
        # For Ozbourne towers: adjust max_blast_radius and riff_interval
        if isinstance(tower, Ozbourne):
            if hasattr(tower, '_base_radius'):
                total_blast_radius = tower._base_radius
                for boosts in remaining_boosts.values():
                    total_blast_radius *= boosts.get('radius', 1)
                tower.max_blast_radius = total_blast_radius
            if hasattr(tower, '_base_riff_interval'):
                total_riff_interval = tower._base_riff_interval
                for boosts in remaining_boosts.values():
                    total_riff_interval /= boosts.get('speed', 1)
                tower.riff_interval = total_riff_interval

        # For CheddarCommando towers: adjust reload time
        if isinstance(tower, CheddarCommando):
            if hasattr(tower, '_base_reload_time'):
                total_reload = tower._base_reload_time
                for boosts in remaining_boosts.values():
                    total_reload /= boosts.get('speed', 1)
                tower.reload_time = total_reload

        # For MinigunTower: adjust max_spool and spool_rate
        if isinstance(tower, MinigunTower):
            if hasattr(tower, '_base_max_spool'):
                total_max_spool = tower._base_max_spool
                for boosts in remaining_boosts.values():
                    total_max_spool /= boosts.get('speed', 1)
                tower.max_spool = total_max_spool
            if hasattr(tower, '_base_spool_rate'):
                total_spool_rate = tower._base_spool_rate
                for boosts in remaining_boosts.values():
                    total_spool_rate *= boosts.get('speed', 1)
                tower.spool_rate = total_spool_rate

        # For WizardTower: adjust attack speed
        if isinstance(tower, WizardTower):
            if hasattr(tower, '_base_attack_speed'):
                total_attack_speed = tower._base_attack_speed
                for boosts in remaining_boosts.values():
                    total_attack_speed /= boosts.get('speed', 1)
                tower.attack_speed = total_attack_speed
            if hasattr(tower, '_base_lightning_interval'):
                total_lightning_interval = tower._base_lightning_interval
                for boosts in remaining_boosts.values():
                    total_lightning_interval /= boosts.get('speed', 1)
                tower.lightning_interval = total_lightning_interval

        # For RatTent towers: adjust spawn_interval
        if isinstance(tower, RatTent):
            if hasattr(tower, '_base_spawn_interval'):
                total_spawn_interval = tower._base_spawn_interval
                for boosts in remaining_boosts.values():
                    total_spawn_interval /= boosts.get('speed', 1)
                tower.spawn_interval = total_spawn_interval

    def _create_signal_effect(self):
        # Create red radial effect at position
        effect = {
            'pos': (self.position[0], self.position[1] - 12),
            'radius': 0,
            'max_radius': 35,
            'color': (255, 0, 0, 128),
            'start_time': pygame.time.get_ticks(),
            'duration': 1000
        }
        self._effects.append(effect)

    def render_effects(self, screen):
        # Draw signal effects
        now = pygame.time.get_ticks()
        for effect in self._effects[:]:
            progress = (now - effect['start_time']) / effect['duration']
            if progress > 1:
                self._effects.remove(effect)
                continue

            alpha = int(128 * (1 - progress))
            radius = effect['radius'] + (effect['max_radius'] * progress)
            surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*effect['color'][:3], alpha),
                               (radius, radius), radius)
            screen.blit(surface, (effect['pos'][0] - radius, effect['pos'][1] - radius))

        # Draw boost indicators on towers
        for tower, beacons in CheeseBeacon._all_boosts.items():
            if isinstance(tower, CheeseBeacon):
                continue
            icons = []
            for beacon in beacons.values():
                if 'damage' in beacon:
                    icons.extend(['damage'] * (int(beacon['damage'] - .5)))
                if 'radius' in beacon:
                    icons.append('radius')
                if 'speed' in beacon:
                    icons.append('speed')

            if icons:
                x = tower.position[0] - (len(icons) * 6)
                y = tower.position[1] - 45
                for i, icon in enumerate(icons):
                    img = self.indicators[icon]
                    screen.blit(img, (x + i * 12, y))

    def sell(self):
        self.active = False
        for tower in list(CheeseBeacon._all_boosts.keys()):
            if self in CheeseBeacon._all_boosts[tower]:
                self._remove_tower_boosts(tower)
                del CheeseBeacon._all_boosts[tower][self]

    def shoot(self):
        pass

    def render(self, screen):
        """Draw the beacon tower itself"""
        if self.active:
            # Draw base tower image
            img_rect = self.image.get_rect(center=self.position)
            screen.blit(self.image, img_rect)
