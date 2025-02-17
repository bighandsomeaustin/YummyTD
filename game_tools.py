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
MogFlag = False
last_time_sfx = pygame.time.get_ticks()
money = 25000  # change for debugging
user_health = 100

# Load frames once globally
frames = [pygame.image.load(f"assets/splash/splash{i}.png").convert_alpha() for i in range(1, 8)]
# mog frames
frames_mog = [pygame.image.load(f"assets/rat_mog/mog{i}.png").convert_alpha() for i in range(0, 31)]
# Define custom frame durations
frame_durations = {0: 0,
                   1: 0,
                   2: 0,
                   3: 0,
                   4: 0,
                   5: 0,
                   6: 0,
                   7: 0,
                   8: 0,
                   9: 0,
                   10: 0,
                   11: 0,
                   12: 750,
                   13: 75,
                   14: 75,
                   15: 75,
                   16: 500,
                   17: 75,
                   18: 75,
                   19: 75,
                   22: 1000,
                   31: 500
                   }  # Frame timings
# for 250ms

for i in range(27, 31):
    frame_durations[i] = 250

house_path = [(237, 502), (221, 447), (186, 417), (136, 408), (113, 385), (113, 352),
              (137, 335), (297, 329), (322, 306), (339, 257), (297, 228), (460, 164),
              (680, 174), (687, 294), (703, 340), (884, 344), (897, 476), (826, 515),
              (727, 504), (580, 524)]
recruit_path = [(580, 524), (727, 504), (826, 515), (897, 476), (884, 344), (703, 340),
                (687, 294), (680, 174), (460, 164), (297, 228), (339, 257), (322, 306),
                (297, 329), (137, 335), (113, 352), (113, 385), (136, 408), (186, 417),
                (221, 447), (237, 502)]


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


def play_mog_animation(scrn: pygame.Surface):
    global MogFlag
    mixer.music.pause()
    mog_song = pygame.mixer.Sound("assets/mog_song.mp3")
    pos = (0, 0)

    mog_song.play()
    fade_into_image(scrn, "assets/rat_mog/mog12.png", 1000)

    for current_frame in range(len(frames_mog)):
        if frame_durations.get(current_frame, 250) == 0:
            continue
        scrn.blit(frames_mog[current_frame], pos)
        pygame.display.flip()  # Update the display

        # Set frame duration dynamically
        duration = frame_durations.get(current_frame, 250)  # Default is 250ms unless specified

        # Keep event handling active while waiting
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

        # Set MogFlag correctly at the last frame
        MogFlag = current_frame == 31


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


def within_spawn_point(cursor_position, path, radius=50):
    def closest_point_on_segment(p, p1, p2):
        x, y = p
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return p1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return (x1 + t * dx, y1 + t * dy)

    closest_point = None
    min_distance = float('inf')

    for i in range(len(path) - 1):
        p1, p2 = path[i], path[i + 1]
        px, py = closest_point_on_segment(cursor_position, p1, p2)
        distance = ((px - cursor_position[0]) ** 2 + (py - cursor_position[1]) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            closest_point = (px, py)

    return min_distance <= radius


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
    img_ratcamp_text = pygame.image.load("assets/ratcamp_text.png").convert_alpha()
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

    # MRCHEESE
    if 1115 <= mouse[0] <= (1115 + 73) and 101 <= mouse[1] <= (101 + 88):
        scrn.blit(img_tower_select, (1115, 101))
        scrn.blit(img_mrcheese_text, (1113, 53))
        if detect_single_click() and money >= 150:  # Detect the transition from not pressed to pressed
            purchase.play()
            return "mrcheese"

    # RAT CAMP
    elif 1195 <= mouse[0] <= (1195 + 73) and 288 <= mouse[1] <= (288 + 88):
        scrn.blit(img_ratcamp_text, (1113, 53))
        scrn.blit(img_tower_select, (1192, 288))
        # add camp tower text
        if detect_single_click() and money >= 500:  # Detect the transition from not pressed to pressed
            purchase.play()
            return "rattent"

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
    global UpgradeFlag, money, MogFlag
    mouse = pygame.mouse.get_pos()
    purchase = pygame.mixer.Sound("assets/purchase_sound.mp3")
    img_upgrade_window = pygame.image.load("assets/upgrade_window.png").convert_alpha()
    img_upgrade_highlighted = pygame.image.load("assets/upgrade_window_highlighted.png")

    scrn.blit(img_upgrade_window, (882, 0))
    if isinstance(tower, MrCheese):
        img_booksmart_upgrade = pygame.image.load("assets/upgrade_booksmart.png")
        img_protein_upgrade = pygame.image.load("assets/upgrade_protein.png")
        img_diploma_upgrade = pygame.image.load("assets/upgrade_diploma.png")
        img_steroids_upgrade = pygame.image.load("assets/upgrade_culture_injection.png")
        upgrade_font = pygame.font.SysFont("arial", 16)
        text_booksmart = upgrade_font.render("Book Smart", True, (0, 0, 0))
        text_protein = upgrade_font.render("Protein 9000", True, (0, 0, 0))
        text_diploma = upgrade_font.render("College Diploma", True, (0, 0, 0))
        text_steroids = upgrade_font.render("Culture Injection", True, (0, 0, 0))
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_booksmart_upgrade, (883, 65))
            scrn.blit(text_booksmart, (962, 42))
        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_protein_upgrade, (883, 194))
            scrn.blit(text_protein, (962, 172))
        if tower.curr_top_upgrade == 1:
            scrn.blit(img_diploma_upgrade, (883, 65))
            scrn.blit(text_diploma, (952, 42))
        if tower.curr_bottom_upgrade == 1:
            scrn.blit(img_steroids_upgrade, (883, 194))
            scrn.blit(text_steroids, (954, 172))
        # check bounds of upgrade, return 1 or 2 for top or bottom choice
        if 883 <= mouse[0] <= (883 + 218) and 65 <= mouse[1] <= (65 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # booksmart upgrade
                if tower.curr_top_upgrade == 0 and money >= 400:
                    purchase.play()
                    money -= 400
                    tower.radius = 150
                    tower.shoot_interval = 750
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = pygame.image.load("assets/mrcheese_booksmart.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/mrcheese_booksmart.png").convert_alpha()
                    # condition if both upgrades
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image = pygame.image.load("assets/mrcheese_booksmart+protein.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/mrcheese_booksmart+protein.png").convert_alpha()
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image = pygame.image.load("assets/mrcheese_steroids+booksmart.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/mrcheese_steroids+booksmart.png").convert_alpha()
                # diploma upgrade
                elif money >= 1200 and tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade != 2:
                    purchase.play()
                    money -= 1200
                    tower.radius = 200
                    # see holobugs
                    tower.shoot_interval = 250
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    # if no protein
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = pygame.image.load("assets/mrcheese_diploma.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/mrcheese_diploma.png").convert_alpha()
                    # if protein
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image = pygame.image.load("assets/mrcheese_diploma+protein.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/mrcheese_diploma+protein.png").convert_alpha()

        if 883 <= mouse[0] <= (883 + 218) and 194 <= mouse[1] <= (194 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # protein upgrade
                if money >= 450 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    tower.damage = 3
                    money -= 450
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    if tower.curr_top_upgrade == 0:
                        tower.image = pygame.image.load("assets/mrcheese_protein.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/mrcheese_protein.png").convert_alpha()
                    # condition if both upgrades
                    elif tower.curr_top_upgrade == 1:
                        tower.image = pygame.image.load("assets/mrcheese_booksmart+protein.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/mrcheese_booksmart+protein.png").convert_alpha()
                    elif tower.curr_top_upgrade == 2:
                        tower.image = pygame.image.load("assets/mrcheese_diploma+protein.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/mrcheese_diploma+protein.png").convert_alpha()
                # culture injection
                elif money >= 900 and tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade != 2:
                    purchase.play()
                    tower.damage = 5
                    tower.penetration = True
                    money -= 900
                    tower.shoot_interval -= 150
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    MogFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image = pygame.image.load("assets/mrcheese_steroids.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/mrcheese_steroids.png").convert_alpha()
                    # condition if both upgrades
                    elif tower.curr_top_upgrade == 1:
                        tower.image = pygame.image.load("assets/mrcheese_steroids+booksmart.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/mrcheese_steroids+booksmart.png").convert_alpha()
    if isinstance(tower, RatTent):
        img_fasterrats_upgrade = pygame.image.load("assets/upgrade_fasterrats.png")
        img_strongrats_upgrade = pygame.image.load("assets/upgrade_strongerrats.png")
        upgrade_font = pygame.font.SysFont("arial", 16)
        text_faster = upgrade_font.render("Faster Rats", True, (0, 0, 0))
        text_stronger = upgrade_font.render("Stronger Rats", True, (0, 0, 0))
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_fasterrats_upgrade, (883, 65))
            scrn.blit(text_faster, (962, 42))
        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_strongrats_upgrade, (883, 194))
            scrn.blit(text_stronger, (962, 172))
        if 883 <= mouse[0] <= (883 + 218) and 65 <= mouse[1] <= (65 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # faster rats upgrade
                if tower.curr_top_upgrade == 0 and money >= 1250:
                    purchase.play()
                    money -= 1250
                    tower.recruit_speed = 2
                    tower.spawn_interval = 750
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = pygame.image.load("assets/camp_faster.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/camp_faster.png").convert_alpha()
                        tower.recruit_image = "assets/rat_recruit_faster.png"
                    # condition if both upgrades
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image = pygame.image.load("assets/camp_stronger+faster.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/camp_stronger+faster.png").convert_alpha()
                        tower.recruit_image = "assets/rat_recruit_stronger+faster.png"
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image = pygame.image.load("assets/mrcheese_steroids+booksmart.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/mrcheese_steroids+booksmart.png").convert_alpha()
        if 883 <= mouse[0] <= (883 + 218) and 194 <= mouse[1] <= (194 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # stronger upgrade
                if money >= 1000 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    tower.recruit_health = 3
                    money -= 1000
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    if tower.curr_top_upgrade == 0:
                        tower.image = pygame.image.load("assets/camp_stronger.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/camp_stronger.png").convert_alpha()
                        tower.recruit_image = "assets/rat_recruit_stronger.png"
                    # condition if both upgrades
                    elif tower.curr_top_upgrade == 1:
                        tower.image = pygame.image.load("assets/camp_stronger+faster.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/camp_stronger+faster.png").convert_alpha()
                        tower.recruit_image = "assets/rat_recruit_stronger+faster.png"
                    elif tower.curr_top_upgrade == 2:
                        tower.image = pygame.image.load("assets/mrcheese_diploma+protein.png").convert_alpha()
                        tower.original_image = pygame.image.load("assets/mrcheese_diploma+protein.png").convert_alpha()

    # check if user quits upgrade handler
    if not ((tower.position[0] - 25) <= mouse[0] <= (tower.position[0] + 25) and (tower.position[1] - 25) <= mouse[
        1]
            <= (tower.position[1] + 25)):
        if detect_single_click():
            UpgradeFlag = False
            return
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                UpgradeFlag = False
                return
        if event.type == pygame.QUIT:
            pygame.quit()

    circle_surface = pygame.Surface((2 * tower.radius, 2 * tower.radius), pygame.SRCALPHA)
    pygame.draw.circle(circle_surface, (0, 0, 0, 128), (tower.radius, tower.radius), tower.radius)
    scrn.blit(circle_surface, (tower.position[0] - tower.radius, tower.position[1] - tower.radius))


def update_towers(scrn: pygame.surface):
    global towers
    global enemies
    for tower in towers:
        tower.update(enemies)
        tower.render(scrn)
        if not isinstance(tower, RatTent):
            tower.shoot()


def update_stats(scrn: pygame.surface, health: int, money: int, round_number: int):
    health_font = pygame.font.SysFont("arial", 28)
    money_font = pygame.font.SysFont("arial", 28)
    round_font = pygame.font.SysFont("arial", 28)
    text1 = health_font.render(f"{health}", True, (255, 255, 255))
    text2 = money_font.render(f"{money}", True, (255, 255, 255))
    text3 = round_font.render(f"Round {round_number}", True, (255, 255, 255))
    # DEBUGGING CURSOR POS
    mouse = pygame.mouse.get_pos()
    x_font = pygame.font.SysFont("arial", 12)
    y_font = pygame.font.SysFont("arial", 12)
    text_x = x_font.render(f"x-axis: {mouse[0]}", True, (0, 255, 0))
    text_y = y_font.render(f"y-axis: {mouse[1]}", True, (0, 255, 0))
    scrn.blit(text_x, (1000, 670))
    scrn.blit(text_y, (1000, 690))
    # BACK TO REGULAR STUFF
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

    if tower == "NULL":
        return True

    elif tower == "mrcheese":
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

    elif tower == "rattent":
        img_base_tent = pygame.image.load("assets/base_camp.png").convert_alpha()
        # Create a surface for the circle
        circle_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        # quit selection if escape pressed
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (50, 50), 50)  # Black with 50% opacity
            scrn.blit(img_base_tent, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 50, mouse[1] - 50))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (50, 50), 50)  # Red with 50% opacity
            scrn.blit(img_base_tent, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 50, mouse[1] - 50))
        if within_spawn_point((mouse[0], mouse[1]), recruit_path, radius=50):
            checkpath_font = pygame.font.SysFont("arial", 16)
            text_checkpath = checkpath_font.render("Eligible Path", True, (0, 255, 0))
            scrn.blit(text_checkpath, (mouse[0] - 35, mouse[1] + 50))
        elif not within_spawn_point((mouse[0], mouse[1]), recruit_path, radius=50):
            checkpath_font = pygame.font.SysFont("arial", 16)
            text_checkpath = checkpath_font.render("Ineligible Path", True, (255, 0, 0))
            scrn.blit(text_checkpath, (mouse[0] - 35, mouse[1] + 50))

        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower):
            tower_rattent = RatTent((mouse[0], mouse[1]), radius=50, recruit_health=1, recruit_speed=1, recruit_damage=1,
                                    image_path='assets/base_camp.png', recruit_image="assets/rat_recruit.png",
                                    spawn_interval=2000)
            towers.append(tower_rattent)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 500
            return True

    if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "mrcheese":
        tower_mrcheese = MrCheese((mouse[0], mouse[1]), radius=100, weapon="Cheese", damage=1,
                                  image_path="assets/base_rat.png", projectile_image="assets/projectile_cheese.png")
        towers.append(tower_mrcheese)
        tower_click.play()
        play_splash_animation(scrn, (mouse[0], mouse[1]))
        money -= 150
        return True

    return False


class MrCheese:
    sfx_squeak = pygame.mixer.Sound("assets/mouse-squeak.mp3")

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
        self.curr_top_upgrade = 0  # Tracks top upgrade status
        self.curr_bottom_upgrade = 0  # tracks bottom upgrade status
        self.penetration = False

    def update(self, enemies):
        global last_time_sfx
        self.target = None
        closest_distance = self.radius
        potential_targets = []
        current_time = pygame.time.get_ticks()
        if current_time - last_time_sfx >= 15000:
            self.sfx_squeak.play()
            last_time_sfx = current_time
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
            if not any(tower.target == enemy for tower in towers if tower != self and not isinstance(tower, RatTent)):
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
            if self.penetration:
                projectile.penetration = self.damage - round((self.damage / 2))
            self.projectiles.append(projectile)
            self.last_shot_time = current_time


class RecruitEntity:
    img_recruit_death = pygame.image.load("assets/splatter_recuit.png").convert_alpha()

    def __init__(self, position, health, speed, path, damage, image_path):
        self.health = health
        self.speed = speed
        self.path = path
        self.damage = damage
        self.image = pygame.image.load(image_path).convert_alpha()
        self.original_image = self.image
        self.rect = self.image.get_rect(center=position)
        self.position, self.current_target = self.get_closest_point_on_path(position)
        self.is_alive = True
        self.was_alive = False

    def get_closest_point_on_path(self, position):
        closest_point = None
        min_distance = float('inf')
        best_index = 0

        for i in range(len(self.path) - 1):
            p1, p2 = self.path[i], self.path[i + 1]
            px, py = self.closest_point_on_segment(position, p1, p2)
            distance = ((px - position[0]) ** 2 + (py - position[1]) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_point = (px, py)
                best_index = i + 1  # Move to the next segment to prevent backtracking

        return closest_point, best_index

    def closest_point_on_segment(self, p, p1, p2):
        x, y = p
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return p1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return (x1 + t * dx, y1 + t * dy)

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

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def check_collision(self, enemies):
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect) and enemy.is_alive:
                enemy.take_damage(self.damage)
                self.health -= 1
                if self.health <= 0:
                    self.is_alive = False
                    self.was_alive = True
                break

    def update(self, enemies):
        self.move()
        self.check_collision(enemies)

    def render(self, screen):
        if self.was_alive:
            screen.blit(self.img_recruit_death, self.rect.topleft)
            self.was_alive = False
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)


class RatTent:

    def __init__(self, position, radius, recruit_health, recruit_speed, recruit_damage, image_path, recruit_image, spawn_interval=2000):
        self.position = position
        self.radius = radius
        self.recruit_health = recruit_health
        self.recruit_speed = recruit_speed
        self.recruit_damage = recruit_damage
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(center=position)
        self.spawn_interval = spawn_interval
        self.last_spawn_time = 0
        self.recruits = []
        self.recruit_image = recruit_image
        self.curr_bottom_upgrade = 0
        self.curr_top_upgrade = 0

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
        for recruit in self.recruits:
            recruit.render(screen)

    def update(self, enemies):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time >= self.spawn_interval and RoundFlag:
            recruit_entity = RecruitEntity(self.position, 1, 1, recruit_path, 1, self.recruit_image)
            closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
            distance = ((closest_spawn_point[0] - self.position[0]) ** 2 + (closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
            if distance <= self.radius:
                recruit = RecruitEntity(
                    position=closest_spawn_point,
                    health=self.recruit_health,
                    speed=self.recruit_speed,
                    path=recruit_path,
                    damage=self.recruit_damage,
                    image_path=self.recruit_image
                )
                self.recruits.append(recruit)
                self.last_spawn_time = current_time

        for recruit in self.recruits[:]:
            recruit.update(enemies)
            if not recruit.is_alive:
                self.recruits.remove(recruit)
            if not RoundFlag:
                self.recruits.remove(recruit)


class AntEnemy:
    global user_health
    sfx_splat = pygame.mixer.Sound("assets/splat_sfx.mp3")
    img_death = pygame.image.load("assets/splatter.png").convert_alpha()

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
            self.sfx_splat.play()
            money += 5

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


class HornetEnemy:
    global user_health
    sfx_splat = pygame.mixer.Sound("assets/splat_sfx.mp3")
    img_death = pygame.image.load("assets/splatter.png").convert_alpha()

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
            self.sfx_splat.play()
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
        if not self.is_alive:
            screen.blit(self.img_death, self.rect.topleft)


class Projectile:
    def __init__(self, position, target, speed, damage, image_path):
        self.position = list(position)  # Current position as [x, y]
        self.target = target  # Target enemy (an instance of AntEnemy)
        self.speed = speed  # Speed of the projectile
        self.damage = damage  # Damage caused by the projectile
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(center=position)
        self.hit = False  # Whether the projectile has hit the target
        self.penetration = 0

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


class RatRecruit:
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


def start_new_wave(round_number: int):
    """Initialize wave settings when a new wave starts."""
    global enemies, enemies_spawned, wave_size, spawn_interval, last_spawn_time, trigger_rush, rush_num, rush_speed, wave_1_10, wave_11_20

    wave_data = {
        1: {"spawn_interval": 1000, "wave_size": 5, "trigger_rush": None},
        2: {"spawn_interval": 750, "wave_size": 10, "trigger_rush": None},
        3: {"spawn_interval": 500, "wave_size": 15, "trigger_rush": None},
        4: {"spawn_interval": 1000, "wave_size": 20, "trigger_rush": None},
        5: {"spawn_interval": 750, "wave_size": 20, "trigger_rush": 15, "rush_num": 5, "rush_speed": 40},
        6: {"spawn_interval": 500, "wave_size": 30, "trigger_rush": None},
        7: {"spawn_interval": 500, "wave_size": 30, "trigger_rush": None},
        8: {"spawn_interval": 500, "wave_size": 45, "trigger_rush": None},
        9: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        10: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        11: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        12: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        13: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        14: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        15: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        16: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        17: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        18: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        19: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        20: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None}
    }

    # Create the wave list
    wave_1_10 = []
    for i in range(5):
        wave_1_10 += ["ANT" for _ in range(9)]
        wave_1_10 += ["HORNET"]
    wave_11_20 = []
    for i in range(6):
       wave_11_20 += ["ANT" for _ in range(5)]
       wave_11_20 += ["HORNET" for _ in range(5)]

    if round_number in wave_data:
        print(f"Starting Wave {round_number}")  # Debugging
        enemies.clear()
        enemies_spawned = 0
        wave_size = wave_data[round_number]["wave_size"]
        spawn_interval = wave_data[round_number]["spawn_interval"]
        trigger_rush = wave_data[round_number]["trigger_rush"]
        # initializing rush if it exists within the current wave
        if trigger_rush:
            rush_num = wave_data[round_number]["rush_num"]
            rush_speed = wave_data[round_number]["rush_speed"]
        last_spawn_time = pygame.time.get_ticks()

def send_wave(scrn: pygame.Surface, round_number: int) -> bool:
    global enemies, last_spawn_time, enemies_spawned, wave_size, trigger_rush, rush_speed, rush_num, spawn_interval, money, wave_11_20, wave_1_10
    current_time = pygame.time.get_ticks()

   # Enemy Spawning Logic
    # Check if current enemy is part of a rush
    if not (trigger_rush is None):
        if enemies_spawned >= trigger_rush and ((enemies_spawned - trigger_rush <= rush_num)):
            spawn_interval = rush_speed
    if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
        if 1 <= round_number < 11:
            wave_used = wave_1_10
        elif 11 <= round_number < 21:
            wave_used = wave_11_20
        print(f"Spawning Enemy {enemies_spawned + 1}/{wave_size}")  # Debugging
        # Check and spawn the correct enemy next in the wave
        if wave_used[enemies_spawned] == "ANT":
            ant = AntEnemy((238, 500), 1, 1, house_path, "assets/ant_base.png")
            enemies.append(ant)
        elif wave_used[enemies_spawned] == "HORNET":
            hornet = HornetEnemy((238, 500), 3, 2, house_path, "assets/hornet_base.png")
            enemies.append(hornet)
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
