import pygame
from pygame import mixer
import math
import time
from towers import MrCheese, RatTent, Ozbourne

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
money = 400000  # change for debugging
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
        return x1 + t * dx, y1 + t * dy

    min_distance = float('inf')

    for i in range(len(path) - 1):
        p1, p2 = path[i], path[i + 1]
        px, py = closest_point_on_segment(cursor_position, p1, p2)
        distance = ((px - cursor_position[0]) ** 2 + (py - cursor_position[1]) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance

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
    img_ozbourne_text = pygame.image.load("assets/ozbourne_text.png").convert_alpha()
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
        if detect_single_click() and money >= 650:  # Detect the transition from not pressed to pressed
            purchase.play()
            return "rattent"

    # CHEESY OZBOURNE
    elif 1118 <= mouse[0] <= (1118 + 73) and 382 <= mouse[1] <= (382 + 88):
        scrn.blit(img_ozbourne_text, (1113, 53))
        scrn.blit(img_tower_select, (1118, 382))
        # add ozbourne tower text
        if detect_single_click() and money >= 500:  # Detect the transition from not pressed to pressed
            purchase.play()
            return "ozbourne"

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
    img_sell_button = pygame.image.load("assets/sell_button.png").convert_alpha()
    upgrade_font = pygame.font.SysFont("arial", 16)

    scrn.blit(img_upgrade_window, (882, 0))
    scrn.blit(img_sell_button, (997, 298))
    text_sell = upgrade_font.render(f"SELL: ${tower.sell_amt}", True, (255, 255, 255))
    scrn.blit(text_sell, (1015, 306))
    if isinstance(tower, MrCheese):
        top_upgrades = [pygame.image.load("assets/upgrade_booksmart.png"),
                        pygame.image.load("assets/upgrade_diploma.png")]
        bottom_upgrades = [pygame.image.load("assets/upgrade_protein.png"),
                           pygame.image.load("assets/upgrade_culture_injection.png")]
        text_top = [upgrade_font.render("Book Smart", True, (0, 0, 0)),
                    upgrade_font.render("College Diploma", True, (0, 0, 0))]
        text_bottom = [upgrade_font.render("Protein 9000", True, (0, 0, 0)),
                       upgrade_font.render("Culture Injection", True, (0, 0, 0))]
        if tower.curr_top_upgrade < 2:
            scrn.blit(top_upgrades[tower.curr_top_upgrade], (883, 65))
            scrn.blit(text_top[tower.curr_top_upgrade], (962, 42))
        if tower.curr_bottom_upgrade < 2:
            scrn.blit(bottom_upgrades[tower.curr_bottom_upgrade], (883, 194))
            scrn.blit(text_bottom[tower.curr_bottom_upgrade], (962, 172))
        # check bounds for sell button
        if 997 <= mouse[0] <= (997 + 105) and 298 <= mouse[1] <= (298 + 35):
            if detect_single_click():
                # refund tower sell amount and remove tower
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        # check bounds of upgrade, return 1 or 2 for top or bottom choice
        if 883 <= mouse[0] <= (883 + 218) and 65 <= mouse[1] <= (65 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # booksmart upgrade
                if tower.curr_top_upgrade == 0 and money >= 400:
                    purchase.play()
                    money -= 400
                    tower.sell_amt += 200
                    tower.radius = 150
                    tower.shoot_interval = 750
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    tower_images = [pygame.image.load("assets/mrcheese_booksmart.png"),
                                    pygame.image.load("assets/mrcheese_booksmart+protein.png"),
                                    pygame.image.load("assets/mrcheese_steroids+booksmart.png")]
                    tower.image = tower_images[tower.curr_bottom_upgrade]
                    tower.original_image = tower_images[tower.curr_bottom_upgrade]
                # diploma upgrade
                elif money >= 1200 and tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade != 2:
                    purchase.play()
                    money -= 1200
                    tower.sell_amt += 600
                    tower.radius = 200
                    # see holobugs
                    tower.shoot_interval = 250
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    # if no protein
                    tower_images = [pygame.image.load("assets/mrcheese_diploma.png").convert_alpha(),
                                    pygame.image.load("assets/mrcheese_diploma+protein.png").convert_alpha()]
                    tower.image = tower_images[tower.curr_bottom_upgrade]
                    tower.original_image = tower_images[tower.curr_bottom_upgrade]

        if 883 <= mouse[0] <= (883 + 218) and 194 <= mouse[1] <= (194 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # protein upgrade
                if money >= 450 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    tower.damage = 3
                    money -= 450
                    tower.sell_amt += 225
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    tower_images = [pygame.image.load("assets/mrcheese_protein.png").convert_alpha(),
                                    pygame.image.load("assets/mrcheese_booksmart+protein.png").convert_alpha(),
                                    pygame.image.load("assets/mrcheese_diploma+protein.png").convert_alpha()]
                    tower.image = tower_images[tower.curr_top_upgrade]
                    tower.original_image = tower_images[tower.curr_top_upgrade]
                # culture injection
                elif money >= 900 and tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade != 2:
                    purchase.play()
                    tower.damage = 5
                    tower.penetration = True
                    money -= 900
                    tower.sell_amt += 450
                    tower.shoot_interval -= 150
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    MogFlag = True
                    tower_images = [pygame.image.load("assets/mrcheese_steroids.png").convert_alpha(),
                                    pygame.image.load("assets/mrcheese_steroids+booksmart.png")]
                    tower.image = tower_images[tower.curr_top_upgrade]
                    tower.original_image = tower_images[tower.curr_top_upgrade]
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
                    tower.sell_amt += 625
                    tower.speed = 2
                    tower.shoot_interval = 750
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    tower_images = [pygame.image.load("assets/camp_faster.png").convert_alpha(),
                                    pygame.image.load("assets/camp_stronger+faster.png").convert_alpha()]
                    tower.image = tower_images[tower.curr_bottom_upgrade]
                    tower.original_image = tower_images[tower.curr_bottom_upgrade]
        # check bounds for sell button
        if 997 <= mouse[0] <= (997 + 105) and 298 <= mouse[1] <= (298 + 35):
            if detect_single_click():
                # refund tower sell amount and remove tower
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        if 883 <= mouse[0] <= (883 + 218) and 194 <= mouse[1] <= (194 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # stronger upgrade
                if money >= 1000 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    tower.health = 3
                    money -= 1000
                    tower.sell_amt += 500
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    tower_images = [pygame.image.load("assets/camp_stronger.png").convert_alpha(),
                                    pygame.image.load("assets/camp_stronger+faster.png").convert_alpha()]
                    tower.image = tower_images[tower.curr_top_upgrade]
                    tower.image = tower_images[tower.curr_top_upgrade]
    if isinstance(tower, Ozbourne):
        img_amplifier_upgrade = pygame.image.load("assets/upgrade_amplifier.png")
        img_longerriffs_upgrade = pygame.image.load("assets/upgrade_longerriffs.png")
        upgrade_font = pygame.font.SysFont("arial", 16)
        text_faster = upgrade_font.render("Amplifier", True, (0, 0, 0))
        text_stronger = upgrade_font.render("Longer Riffs", True, (0, 0, 0))
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_amplifier_upgrade, (883, 65))
            scrn.blit(text_faster, (962, 42))
        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_longerriffs_upgrade, (883, 194))
            scrn.blit(text_stronger, (962, 172))
        if 883 <= mouse[0] <= (883 + 218) and 65 <= mouse[1] <= (65 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # amplifier upgrade
                if tower.curr_top_upgrade == 0 and money >= 350:
                    purchase.play()
                    money -= 350
                    tower.sell_amt += 125
                    tower.riff_blast_radius = 150
                    tower.radius = 150
                    tower.max_blast_radius = 150
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = pygame.image.load("assets/alfredo_ozbourne_amplifier.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/alfredo_ozbourne_amplifier.png").convert_alpha()
        # check bounds for sell button
        if 997 <= mouse[0] <= (997 + 105) and 298 <= mouse[1] <= (298 + 35):
            if detect_single_click():
                # refund tower sell amount and remove tower
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        if 883 <= mouse[0] <= (883 + 218) and 194 <= mouse[1] <= (194 + 100):
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # longer riffs upgrade
                if money >= 375 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    money -= 375
                    tower.sell_amt += 187
                    tower.riff_interval = (1165 / 2)
                    tower.blast_duration = (1165 / 2)
                    tower.damage = 1
                    tower.riff_sfx = pygame.mixer.Sound("assets/riff_longer.mp3")
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    # condition if first upgrade
                    if tower.curr_top_upgrade == 0:
                        tower.image = pygame.image.load("assets/alfredo_ozbourne_longer_riffs.png").convert_alpha()
                        tower.original_image = pygame.image.load(
                            "assets/alfredo_ozbourne_longer_riffs.png").convert_alpha()
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
        if not isinstance(tower, Ozbourne):
            tower.shoot(enemies)


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
            tower_rattent = RatTent((mouse[0], mouse[1]))
            towers.append(tower_rattent)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 650
            return True

    elif tower == "ozbourne":
        img_base_ozbourne = pygame.image.load("assets/alfredo_ozbourne_base.png").convert_alpha()
        # Create a surface for the circle
        circle_surface = pygame.Surface((150, 150), pygame.SRCALPHA)  # radius of 75
        # quit selection if escape pressed
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (75, 75), 75)  # Black with 50% opacity
            scrn.blit(img_base_ozbourne, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (75, 75), 75)  # Red with 50% opacity
            scrn.blit(img_base_ozbourne, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))

        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower):
            tower_ozbourne = Ozbourne((mouse[0], mouse[1]))
            towers.append(tower_ozbourne)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 500
            return True

    if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "mrcheese":
        tower_mrcheese = MrCheese((mouse[0], mouse[1]), radius=75, weapon="Cheese", damage=1,
                                  image_path="assets/base_rat.png", projectile_image="assets/projectile_cheese.png")
        towers.append(tower_mrcheese)
        tower_click.play()
        play_splash_animation(scrn, (mouse[0], mouse[1]))
        money -= 150
        return True

    return False


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
        return x1 + t * dx, y1 + t * dy

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
