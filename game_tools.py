import pygame
from pygame import mixer
import math
import time

pygame.init()
pygame.display.set_mode((1280, 720))

towers = []
enemies = []
enemies_spawned = 0
wave_size = 0
spawn_interval = 0
last_spawn_time = 0
current_wave = 1
hitbox_position = (0, 0)  # Top-left corner
RoundFlag = False
UpgradeFlag = False
curr_upgrade_tower = None
money = 200       # change for debugging
user_health = 100

# Load frames once globally
frames = [pygame.image.load(f"assets/splash/splash{i}.png").convert_alpha() for i in range(1, 8)]
house_path = [(237, 502), (221, 447), (186, 417), (136, 408), (113, 385), (113, 352),
              (137, 335), (297, 329), (322, 306), (339, 257), (297, 228), (460, 164),
              (680, 174), (687, 294), (703, 340), (884, 344), (897, 476), (826, 515),
              (727, 504), (580, 524)]


def play_splash_animation(scrn: pygame.Surface, pos: tuple[int, int], frame_delay: int = 5):
    for current_frame in range(len(frames)):
        # Draw the current frame
        scrn.blit(frames[current_frame], (pos[0] - 38, pos[1] - 38))
        pygame.display.flip()  # Update the display

        # Delay for frame_delay iterations of the game clock
        for _ in range(frame_delay):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

        pygame.time.delay(16)  # Adjust timing to maintain responsiveness


def detect_single_click(delay=.3):
    # Static variables for tracking mouse state and time of last click
    if not hasattr(detect_single_click, "was_pressed"):
        detect_single_click.was_pressed = False
        detect_single_click.last_click_time = 0

    # Current time
    current_time = time.time()

    # Check if the left mouse button is pressed
    click = pygame.mouse.get_pressed()[0]

    # Detect the transition from "not pressed" to "pressed" with delay
    if click and not detect_single_click.was_pressed:
        if current_time - detect_single_click.last_click_time >= delay:
            detect_single_click.was_pressed = True
            detect_single_click.last_click_time = current_time
            return True
    elif not click:
        detect_single_click.was_pressed = False

    return False


def check_hitbox(image, position, placed_towers):
    x, y = position

    # Check if the position is within the transparent area of the main hitbox image
    if 0 <= x < image.get_width() and 0 <= y < image.get_height():
        pixel = image.get_at((x, y))
        if pixel.a != 0:  # Not transparent
            return False

    # Check if the position is on top of any existing tower
    for tower in placed_towers:
        if hasattr(tower, 'rect') and hasattr(tower, 'image'):
            tower_x, tower_y = tower.rect.topleft
            tower_width, tower_height = tower.image.get_width(), tower.image.get_height()

            if tower_x <= x < tower_x + tower_width and tower_y <= y < tower_y + tower_height:
                relative_x = x - tower_x
                relative_y = y - tower_y

                pixel = tower.image.get_at((int(relative_x), int(relative_y)))
                if pixel.a != 0:  # Not transparent
                    return False

    return True  # Valid placement


def fade_into_image(scrn: pygame.Surface, image_path: str, duration: int = 200):
    """
    Fades into an image over a specified duration.
    :param scrn: Pygame display surface
    :param image_path: Path to the image file
    :param duration: Duration of the fade in milliseconds
    """
    clock = pygame.time.Clock()
    image = pygame.image.load(image_path).convert_alpha()
    image_rect = image.get_rect(center=scrn.get_rect().center)

    fade_surface = pygame.Surface(scrn.get_size()).convert_alpha()
    fade_surface.fill((0, 0, 0))

    alpha = 255  # Start fully opaque
    fade_steps = duration // 10  # Number of steps based on duration

    for step in range(fade_steps + 1):
        scrn.blit(image, image_rect)
        fade_surface.set_alpha(alpha)
        scrn.blit(fade_surface, (0, 0))
        pygame.display.flip()

        alpha -= 255 // fade_steps
        clock.tick(60)  # Limit frame rate to 60 FPS

    scrn.blit(image, image_rect)  # Final draw without fade


def check_game_menu_elements(scrn: pygame.surface) -> str:
    global RoundFlag
    global money
    global UpgradeFlag
    global curr_upgrade_tower
    purchase = pygame.mixer.Sound("assets/purchase_sound.mp3")
    img_tower_select = pygame.image.load("assets/tower_select.png").convert_alpha()
    img_mrcheese_text = pygame.image.load("assets/mrcheese_text.png").convert_alpha()
    img_playbutton = pygame.image.load("assets/playbutton.png").convert_alpha()
    img_playbutton_unavail = pygame.image.load("assets/playbutton_unavail.png").convert_alpha()

    mouse = pygame.mouse.get_pos()

    if not RoundFlag:
        scrn.blit(img_playbutton, (1110, 665))
        if 1110 <= mouse[0] <= (1110 + 81) and 665 <= mouse[1] <= (665 + 50):
            if detect_single_click():
                RoundFlag = True
                return "nextround"

    if RoundFlag:
        scrn.blit(img_playbutton_unavail, (1110, 665))

    if 1115 <= mouse[0] <= (1115 + 73) and 101 <= mouse[1] <= (101 + 88):
        scrn.blit(img_tower_select, (1115, 101))
        scrn.blit(img_mrcheese_text, (1113, 53))
        if detect_single_click() and money >= 150:  # Detect the transition from not pressed to pressed
            purchase.play()
            return "mrcheese"

    # check if any tower is clicked after placement
    for tower in towers:
        if (tower.position[0] - 25) <= mouse[0] <= (tower.position[0] + 25) and (tower.position[1] - 25) <= mouse[1] \
                <= (tower.position[1] + 25):
            if detect_single_click():
                UpgradeFlag = True
                curr_upgrade_tower = tower

    if UpgradeFlag:
        handle_upgrade(scrn, curr_upgrade_tower)

    return "NULL"


def handle_upgrade(scrn, tower):
    global UpgradeFlag
    mouse = pygame.mouse.get_pos()
    if not ((tower.position[0] - 25) <= mouse[0] <= (tower.position[0] + 25) and (tower.position[1] - 25) <= mouse[1]
            <= (tower.position[1] + 25)):
        if detect_single_click():
            UpgradeFlag = False
            return
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                UpgradeFlag = False
                return

    circle_surface = pygame.Surface((2 * tower.radius, 2 * tower.radius), pygame.SRCALPHA)
    pygame.draw.circle(circle_surface, (0, 0, 0, 128), (100, 100), tower.radius)  # Black with 50% opacity
    scrn.blit(circle_surface, (tower.position[0] - 100, tower.position[1] - 100))


def update_towers(scrn: pygame.surface):
    global towers
    global enemies
    for tower in towers:
        tower.update(enemies)
        tower.shoot()
        tower.render(scrn)


def update_stats(scrn: pygame.surface, health: int, money: int, round_number: int):
    health_font = pygame.font.SysFont("arial", 28)
    money_font = pygame.font.SysFont("arial", 28)
    round_font = pygame.font.SysFont("arial", 28)
    text1 = health_font.render(f"{health}", True, (255, 255, 255))
    text2 = money_font.render(f"{money}", True, (255, 255, 255))
    text3 = round_font.render(f"Round {round_number}", True, (255, 255, 255))
    scrn.blit(text1, (55, 15))
    scrn.blit(text2, (65, 62))
    scrn.blit(text3, (1150, 10))


def handle_newtower(scrn: pygame.surface, tower: str) -> bool:
    global money
    image_house_hitbox = 'assets/house_illegal_regions.png'
    house_hitbox = pygame.image.load(image_house_hitbox).convert_alpha()
    tower_click = pygame.mixer.Sound("assets/tower_placed.mp3")

    mouse = pygame.mouse.get_pos()
    # Convert mouse position to the hitbox's local coordinates
    relative_pos = (mouse[0] - hitbox_position[0], mouse[1] - hitbox_position[1])

    if tower == "mrcheese":
        img_base_rat = pygame.image.load("assets/base_rat.png").convert_alpha()
        # Create a surface for the circle
        circle_surface = pygame.Surface((200, 200), pygame.SRCALPHA)  # 200x200 for radius 100
        # quit selection if escape pressed
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (100, 100), 100)  # Black with 50% opacity
            scrn.blit(img_base_rat, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 100, mouse[1] - 100))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (100, 100), 100)  # Red with 50% opacity
            scrn.blit(img_base_rat, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 100, mouse[1] - 100))

    if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower):
        tower_mrcheese = MrCheese((mouse[0], mouse[1]), radius=100, weapon="Cheese", damage=1,
                                  image_path="assets/base_rat.png", projectile_image="assets/projectile_cheese.png")
        towers.append(tower_mrcheese)
        tower_click.play()
        play_splash_animation(scrn, (mouse[0], mouse[1]))
        money -= 150
        return True

    if tower == "NULL":
        return False

    return False


class MrCheese:
    def __init__(self, position, radius, weapon, damage, image_path, projectile_image, shoot_interval=1000):
        self.position = position  # (x, y) tuple
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

    def update(self, enemies):
        # Find the closest enemy within the radius
        self.target = None
        closest_distance = self.radius

        for enemy in enemies:
            distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                 (enemy.position[1] - self.position[1]) ** 2)
            if distance <= closest_distance:
                closest_distance = distance
                self.target = enemy

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
                if self.target is not None:
                    if self.target.is_alive:  # Apply damage if the target is still alive
                        self.target.take_damage(self.damage)
                self.projectiles.remove(projectile)

    def render(self, screen):
        # Draw the tower
        screen.blit(self.image, self.rect.topleft)
        # Optionally draw the radius for debugging
        # pygame.draw.circle(screen, (0, 255, 0), self.position, self.radius, 1)

        # Render all projectiles
        for projectile in self.projectiles:
            projectile.render(screen)

    def shoot(self):
        # Shoot a projectile if enough time has passed since the last shot
        current_time = pygame.time.get_ticks()
        if self.target and current_time - self.last_shot_time >= self.shoot_interval:
            projectile = Projectile(
                position=self.position,
                target=self.target,
                speed=10,  # Speed of the projectile
                damage=self.damage,
                image_path=self.projectile_image
            )
            self.projectiles.append(projectile)
            self.last_shot_time = current_time


class AntEnemy:
    global user_health

    def __init__(self, position, health, speed, path, image_path):
        self.position = position  # (x, y) tuple
        self.health = health
        self.speed = speed
        self.path = path  # List of (x, y) points the enemy follows
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size  # Width and height of the enemy
        self.current_target = 0  # Current target index in the path
        self.is_alive = True

    def move(self):
        # Move towards the next point in the path
        global user_health
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
            user_health -= self.health

    def update_orientation(self, direction_x, direction_y):
        """Rotate the image to face the movement direction."""
        # Calculate angle in radians and convert to degrees
        angle = math.degrees(math.atan2(-direction_y, direction_x))  # Flip y-axis for Pygame
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, damage):
        global money
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False
            money += 5

    def render(self, screen):
        # Draw the enemy on the screen
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
            # Optionally, draw the health bar
            # pygame.draw.rect(screen, (255, 0, 0), (*self.rect.topleft, self.size[0], 5))
            # pygame.draw.rect(
            #     screen,
            #     (0, 255, 0),
            #     (*self.rect.topleft, self.size[0] * (self.health / 100), 5)
            # )


class HornetEnemy:
    global user_health

    def __init__(self, position, health, speed, path, image_path):
        self.position = position  # (x, y) tuple
        self.health = health
        self.speed = speed
        self.path = path  # List of (x, y) points the enemy follows
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size  # Width and height of the enemy
        self.current_target = 0  # Current target index in the path
        self.is_alive = True

    def move(self):
        # Move towards the next point in the path
        global user_health
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
            user_health -= self.health

    def update_orientation(self, direction_x, direction_y):
        """Rotate the image to face the movement direction."""
        # Calculate angle in radians and convert to degrees
        angle = math.degrees(math.atan2(-direction_y, direction_x))  # Flip y-axis for Pygame
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, damage):
        global money
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False
            money += 10

    def render(self, screen):
        # Draw the enemy on the screen
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
            # Optionally, draw the health bar
            # pygame.draw.rect(screen, (255, 0, 0), (*self.rect.topleft, self.size[0], 5))
            # pygame.draw.rect(
            #     screen,
            #     (0, 255, 0),
            #     (*self.rect.topleft, self.size[0] * (self.health / 100), 5)
            # )


class Projectile:
    def __init__(self, position, target, speed, damage, image_path):
        self.position = list(position)  # Current position as [x, y]
        self.target = target  # Target enemy (an instance of AntEnemy)
        self.speed = speed  # Speed of the projectile
        self.damage = damage  # Damage caused by the projectile
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(center=position)
        self.hit = False  # Whether the projectile has hit the target

    def move(self):
        # Calculate direction towards the target
        if not self.target.is_alive:  # If the target is dead, stop moving
            self.hit = True
            return

        target_x, target_y = self.target.position
        dx = target_x - self.position[0]
        dy = target_y - self.position[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Move the projectile towards the target
        if distance > 0:
            direction_x = dx / distance
            direction_y = dy / distance
            self.position[0] += direction_x * self.speed
            self.position[1] += direction_y * self.speed
            self.rect.center = self.position

        # Check if the projectile reaches the target
        if distance <= self.speed:
            self.hit = True  # Mark as hit

    def render(self, screen):
        # Draw the projectile
        screen.blit(self.image, self.rect.topleft)


def start_new_wave(round_number: int):
    """Initialize wave settings when a new wave starts."""
    global enemies, enemies_spawned, wave_size, spawn_interval, last_spawn_time

    wave_data = {
        1: {"spawn_interval": 1000, "wave_size": 5},
        2: {"spawn_interval": 750, "wave_size": 10},
        3: {"spawn_interval": 500, "wave_size": 15},
        4: {"spawn_interval": 1000, "wave_size": 20},
        5: {"spawn_interval": 750, "wave_size": 20},
        6: {"spawn_interval": 500, "wave_size": 30},
        7: {"spawn_interval": 500, "wave_size": 30},
        8: {"spawn_interval": 500, "wave_size": 45}
    }

    if round_number in wave_data:
        print(f"Starting Wave {round_number}")  # Debugging
        enemies.clear()
        enemies_spawned = 0
        wave_size = wave_data[round_number]["wave_size"]
        spawn_interval = wave_data[round_number]["spawn_interval"]
        last_spawn_time = pygame.time.get_ticks()


def send_wave(scrn: pygame.Surface, round_number: int) -> bool:
    global enemies, last_spawn_time, enemies_spawned, wave_size, spawn_interval, money

    current_time = pygame.time.get_ticks()

    # Enemy Spawning Logic
    if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval and round_number < 4:
        print(f"Spawning Enemy {enemies_spawned + 1}/{wave_size}")  # Debugging
        ant = AntEnemy((238, 500), 1, 1, house_path, "assets/ant_base.png")
        enemies.append(ant)
        last_spawn_time = current_time
        enemies_spawned += 1

    if round_number == 4:
        if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
            ant = AntEnemy((238, 500), 1, 1, house_path, "assets/ant_base.png")
            enemies.append(ant)
            if enemies_spawned < 10:
                spawn_interval = 100
            elif 10 <= enemies_spawned <= 20:
                spawn_interval = 750
            last_spawn_time = current_time
            enemies_spawned += 1

    if round_number == 5:
        if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
            ant = AntEnemy((238, 500), 1, 1, house_path, "assets/ant_base.png")
            hornet = HornetEnemy((238, 500), 3, 2, house_path, "assets/hornet_base.png")
            if enemies_spawned <= 4:
                enemies.append(ant)
            elif enemies_spawned == 4:
                enemies.append(ant)
                spawn_interval = 3000
            elif 5 < enemies_spawned <= 9:
                spawn_interval = 750
                enemies.append(hornet)
            elif enemies_spawned == 9:
                enemies.append(hornet)
                spawn_interval = 6000
            elif 10 <= enemies_spawned <= 20:
                enemies.append(ant)
                spawn_interval = 500
            last_spawn_time = current_time
            enemies_spawned += 1

    if round_number == 6:
        if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
            ant = AntEnemy((238, 500), 1, 1, house_path, "assets/ant_base.png")
            hornet = HornetEnemy((238, 500), 3, 2, house_path, "assets/hornet_base.png")
            if enemies_spawned <= 9:
                spawn_interval = 50
                enemies.append(ant)
            elif enemies_spawned == 9:
                enemies.append(ant)
                spawn_interval = 5000
            elif 10 < enemies_spawned <= 19:
                spawn_interval = 50
                enemies.append(ant)
            elif enemies_spawned == 20:
                enemies.append(ant)
                spawn_interval = 6000
            elif 20 <= enemies_spawned <= 30:
                enemies.append(ant)
                enemies.append(hornet)
                spawn_interval = 500
            last_spawn_time = current_time
            enemies_spawned += 1
    if round_number == 7:
        if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
            ant = AntEnemy((238, 500), 1, 1, house_path, "assets/ant_base.png")
            hornet = HornetEnemy((238, 500), 3, 2, house_path, "assets/hornet_base.png")
            if enemies_spawned <= 4:
                spawn_interval = 50
                enemies.append(hornet)
            elif enemies_spawned == 5:
                enemies.append(hornet)
                spawn_interval = 5000
            elif 5 <= enemies_spawned <= 24:
                spawn_interval = 50
                enemies.append(ant)
            elif enemies_spawned == 25:
                enemies.append(ant)
                spawn_interval = 6000
            elif 25 <= enemies_spawned <= 30:
                enemies.append(hornet)
                spawn_interval = 50
            last_spawn_time = current_time
            enemies_spawned += 1

    if round_number == 8:
        if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
            ant = AntEnemy((238, 500), 1, 1, house_path, "assets/ant_base.png")
            hornet = HornetEnemy((238, 500), 3, 2, house_path, "assets/hornet_base.png")
            if enemies_spawned <= 9:
                spawn_interval = 50
                enemies.append(ant)
            elif enemies_spawned == 9:
                enemies.append(ant)
                spawn_interval = 5000
            elif 10 < enemies_spawned <= 14:
                spawn_interval = 200
                enemies.append(hornet)
            elif enemies_spawned == 20:
                enemies.append(hornet)
                spawn_interval = 5000
            elif 20 <= enemies_spawned <= 29:
                enemies.append(ant)
                spawn_interval = 50
            elif enemies_spawned == 29:
                enemies.append(ant)
                spawn_interval = 5000
            elif 30 <= enemies_spawned <= 34:
                enemies.append(hornet)
                spawn_interval = 200
            elif enemies_spawned == 34:
                enemies.append(hornet)
                spawn_interval = 5000
            elif 35 <= enemies_spawned <= 45:
                enemies.append(ant)
                spawn_interval = 50
            last_spawn_time = current_time
            enemies_spawned += 1

    # Update and Render Enemies
    for enemy in enemies[:]:
        enemy.render(scrn)
        enemy.move()
        if not enemy.is_alive:
            enemies.remove(enemy)

    # Check if the wave is complete (all enemies spawned & defeated)
    if enemies_spawned >= wave_size and not enemies:
        print(f"Wave {round_number} Complete!")  # Debugging
        money += round(300 * (math.log(round_number + 1) / math.log(51)))
        return True  # Signal wave completion

    return False
