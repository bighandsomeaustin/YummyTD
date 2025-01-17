import pygame
from pygame import mixer
import math
import time

pygame.init()
pygame.display.set_mode((1280, 720))

towers = []
enemies = []
hitbox_position = (0, 0)  # Top-left corner

# Load frames once globally
frames = [pygame.image.load(f"assets/splash/splash{i}.png").convert_alpha() for i in range(1, 8)]


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
    purchase = pygame.mixer.Sound("assets/purchase_sound.mp3")
    img_tower_select = pygame.image.load("assets/tower_select.png").convert_alpha()
    img_mrcheese_text = pygame.image.load("assets/mrcheese_text.png").convert_alpha()

    mouse = pygame.mouse.get_pos()

    if 1115 <= mouse[0] <= (1115 + 73) and 101 <= mouse[1] <= (101 + 88):
        scrn.blit(img_tower_select, (1115, 101))
        scrn.blit(img_mrcheese_text, (1113, 53))
        if detect_single_click():  # Detect the transition from not pressed to pressed
            purchase.play()
            return "mrcheese"

    return "NULL"


def update_towers(scrn: pygame.surface):
    """if not hasattr(update_towers, "last_angle"):
        update_towers.last_angle = 0

    img_base_rat = pygame.image.load("assets/base_rat.png").convert_alpha()
    image_rect = img_base_rat.get_rect(center=(512, 512))
    base_rat_radius = 100

    mouse = pygame.mouse.get_pos()

    distance = math.sqrt((mouse[0] - image_rect.centerx) ** 2 + (mouse[1] - image_rect.centery) ** 2)

    dx = mouse[0] - image_rect.centerx
    dy = mouse[1] - image_rect.centery
    angle = math.degrees(math.atan2(dy, dx))

    if distance <= base_rat_radius:
        update_towers.last_angle = angle
        rotated_image = pygame.transform.rotate(img_base_rat, -angle)
        rotated_rect = rotated_image.get_rect(center=image_rect.center)
        scrn.blit(rotated_image, rotated_rect.topleft)
    else:
        rotated_image = pygame.transform.rotate(img_base_rat, -update_towers.last_angle)
        rotated_rect = rotated_image.get_rect(center=image_rect.center)
        scrn.blit(rotated_image, rotated_rect.topleft)"""
    for tower in towers:
        tower.render(scrn)


def handle_newtower(scrn: pygame.surface, tower: str) -> bool:
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
                                  image_path="assets/base_rat.png")
        towers.append(tower_mrcheese)
        tower_click.play()
        play_splash_animation(scrn, (mouse[0], mouse[1]))
        return True

    if tower == "NULL":
        return False

    return False


class MrCheese:
    def __init__(self, position, radius, weapon, damage, image_path):
        self.position = position  # (x, y) tuple
        self.radius = radius
        self.weapon = weapon
        self.damage = damage
        self.image = pygame.image.load(image_path).convert_alpha()
        self.original_image = self.image
        self.rect = self.image.get_rect(center=position)
        self.angle = 0  # Default orientation
        self.target = None  # Current target (e.g., enemy)

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

    def render(self, screen):
        # Draw the tower
        screen.blit(self.image, self.rect.topleft)
        # Optionally draw the radius for debugging
        # pygame.draw.circle(screen, (0, 255, 0), self.position, self.radius, 1)

    def shoot(self):
        # Define what happens when the tower shoots
        if self.target:
            print(f"Tower at {self.position} shooting {self.target} with {self.weapon} causing {self.damage} damage.")


class AntEnemy:
    def __init__(self, position, health, speed, path, image_path):
        self.position = position  # (x, y) tuple
        self.health = health
        self.speed = speed
        self.path = path  # List of (x, y) points the enemy follows
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size  # Width and height of the enemy
        self.current_target = 0  # Current target index in the path
        self.is_alive = True

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

            # Check if the enemy reached the target
            if distance <= self.speed:
                self.current_target += 1

        # If the enemy has reached the end of the path
        if self.current_target >= len(self.path):
            self.is_alive = False  # Mark as no longer active (escaped)

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False

    def render(self, screen):
        # Draw the enemy on the screen
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
            # Optionally, draw the health bar
            pygame.draw.rect(screen, (255, 0, 0), (*self.rect.topleft, self.size[0], 5))
            pygame.draw.rect(
                screen,
                (0, 255, 0),
                (*self.rect.topleft, self.size[0] * (self.health / 100), 5)
            )
