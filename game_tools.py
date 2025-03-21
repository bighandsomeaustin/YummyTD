import pygame
from pygame import mixer
import math
import time

pygame.init()
pygame.display.set_mode((1280, 720))

# Asset and resource caching for performance
_asset_cache = {}
_sound_cache = {}
_font_cache = {}

def load_image(path):
    if path not in _asset_cache:
        _asset_cache[path] = pygame.image.load(path).convert_alpha()
    return _asset_cache[path]

def load_sound(path):
    if path not in _sound_cache:
        _sound_cache[path] = pygame.mixer.Sound(path)
    return _sound_cache[path]

def get_font(name, size):
    key = (name, size)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont(name, size)
    return _font_cache[key]

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
frames = [load_image(f"assets/splash/splash{i}.png") for i in range(1, 8)]
# mog frames
frames_mog = [load_image(f"assets/rat_mog/mog{i}.png") for i in range(0, 31)]
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

def play_splash_animation(scrn: pygame.Surface, pos: tuple, frame_delay: int = 5):
    for current_frame in range(len(frames)):
        # Draw the current frame
        scrn.blit(frames[current_frame], (pos[0] - 38, pos[1] - 38))
        pygame.display.flip()  # Update the display
        # Delay for frame_delay iterations of the game clock
        for _ in range(frame_delay):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); exit()
        pygame.time.delay(16)  # Adjust timing to maintain responsiveness

def play_mog_animation(scrn: pygame.Surface):
    global MogFlag
    mixer.music.pause()
    mog_song = load_sound("assets/mog_song.mp3")
    pos = (0, 0)
    mog_song.play()
    fade_into_image(scrn, "assets/rat_mog/mog12.png", 1000)
    for current_frame in range(len(frames_mog)):
        if frame_durations.get(current_frame, 250) == 0:
            continue
        scrn.blit(frames_mog[current_frame], pos)
        pygame.display.flip()  # Update the display
        duration = frame_durations.get(current_frame, 250)
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); exit()
        # Set MogFlag correctly at the last frame
        MogFlag = (current_frame == 31)

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
    image = load_image(image_path)
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
    global RoundFlag, money, UpgradeFlag, curr_upgrade_tower
    purchase = load_sound("assets/purchase_sound.mp3")
    img_tower_select = load_image("assets/tower_select.png")
    img_mrcheese_text = load_image("assets/mrcheese_text.png")
    img_ratcamp_text = load_image("assets/ratcamp_text.png")
    img_ozbourne_text = load_image("assets/ozbourne_text.png")
    img_playbutton = load_image("assets/playbutton.png")
    img_playbutton_unavail = load_image("assets/playbutton_unavail.png")
    mouse = pygame.mouse.get_pos()
    if not RoundFlag:
        scrn.blit(img_playbutton, (1110, 665))
        if 1110 <= mouse[0] <= 1110 + 81 and 665 <= mouse[1] <= 665 + 50:
            if detect_single_click():
                RoundFlag = True
                return "nextround"
    if RoundFlag:
        scrn.blit(img_playbutton_unavail, (1110, 665))
    # MRCHEESE
    if 1115 <= mouse[0] <= 1115 + 73 and 101 <= mouse[1] <= 101 + 88:
        scrn.blit(img_tower_select, (1115, 101))
        scrn.blit(img_mrcheese_text, (1113, 53))
        if detect_single_click() and money >= 150:
            purchase.play()
            return "mrcheese"
    # RAT CAMP
    elif 1195 <= mouse[0] <= 1195 + 73 and 288 <= mouse[1] <= 288 + 88:
        scrn.blit(img_ratcamp_text, (1113, 53))
        scrn.blit(img_tower_select, (1192, 288))
        if detect_single_click() and money >= 650:
            purchase.play()
            return "rattent"
    # CHEESY OZBOURNE
    elif 1118 <= mouse[0] <= 1118 + 73 and 382 <= mouse[1] <= 382 + 88:
        scrn.blit(img_ozbourne_text, (1113, 53))
        scrn.blit(img_tower_select, (1118, 382))
        if detect_single_click() and money >= 500:
            purchase.play()
            return "ozbourne"
    # check if any tower is clicked after placement
    for tower in towers:
        if (tower.position[0] - 25) <= mouse[0] <= (tower.position[0] + 25) and (tower.position[1] - 25) <= mouse[1] <= (tower.position[1] + 25):
            if detect_single_click():
                UpgradeFlag = True
                curr_upgrade_tower = tower
    if UpgradeFlag:
        handle_upgrade(scrn, curr_upgrade_tower)
    return "NULL"

def handle_upgrade(scrn, tower):
    global UpgradeFlag, money, MogFlag
    mouse = pygame.mouse.get_pos()
    purchase = load_sound("assets/purchase_sound.mp3")
    img_upgrade_window = load_image("assets/upgrade_window.png")
    img_upgrade_highlighted = load_image("assets/upgrade_window_highlighted.png")
    img_sell_button = load_image("assets/sell_button.png")
    upgrade_font = get_font("arial", 16)
    scrn.blit(img_upgrade_window, (882, 0))
    scrn.blit(img_sell_button, (997, 298))
    text_sell = upgrade_font.render(f"SELL: ${tower.sell_amt}", True, (255, 255, 255))
    scrn.blit(text_sell, (1015, 306))
    if isinstance(tower, MrCheese):
        img_booksmart_upgrade = load_image("assets/upgrade_booksmart.png")
        img_protein_upgrade = load_image("assets/upgrade_protein.png")
        img_diploma_upgrade = load_image("assets/upgrade_diploma.png")
        img_steroids_upgrade = load_image("assets/upgrade_culture_injection.png")
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
        # check bounds for sell button
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        # check bounds of upgrade, return 1 or 2 for top or bottom choice
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                if tower.curr_top_upgrade == 0 and money >= 400:
                    purchase.play()
                    money -= 400
                    tower.sell_amt += 200
                    tower.radius = 150
                    tower.shoot_interval = 750
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = load_image("assets/mrcheese_booksmart.png")
                        tower.original_image = load_image("assets/mrcheese_booksmart.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image = load_image("assets/mrcheese_booksmart+protein.png")
                        tower.original_image = load_image("assets/mrcheese_booksmart+protein.png")
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image = load_image("assets/mrcheese_steroids+booksmart.png")
                        tower.original_image = load_image("assets/mrcheese_steroids+booksmart.png")
                elif money >= 1200 and tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade != 2:
                    purchase.play()
                    money -= 1200
                    tower.sell_amt += 600
                    tower.radius = 200
                    tower.shoot_interval = 250
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = load_image("assets/mrcheese_diploma.png")
                        tower.original_image = load_image("assets/mrcheese_diploma.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image = load_image("assets/mrcheese_diploma+protein.png")
                        tower.original_image = load_image("assets/mrcheese_diploma+protein.png")
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                if money >= 450 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    tower.damage = 3
                    money -= 450
                    tower.sell_amt += 225
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image = load_image("assets/mrcheese_protein.png")
                        tower.original_image = load_image("assets/mrcheese_protein.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image = load_image("assets/mrcheese_booksmart+protein.png")
                        tower.original_image = load_image("assets/mrcheese_booksmart+protein.png")
                    elif tower.curr_top_upgrade == 2:
                        tower.image = load_image("assets/mrcheese_diploma+protein.png")
                        tower.original_image = load_image("assets/mrcheese_diploma+protein.png")
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
                    if tower.curr_top_upgrade == 0:
                        tower.image = load_image("assets/mrcheese_steroids.png")
                        tower.original_image = load_image("assets/mrcheese_steroids.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image = load_image("assets/mrcheese_steroids+booksmart.png")
                        tower.original_image = load_image("assets/mrcheese_steroids+booksmart.png")
    if isinstance(tower, RatTent):
        img_fasterrats_upgrade = load_image("assets/upgrade_fasterrats.png")
        img_strongrats_upgrade = load_image("assets/upgrade_strongerrats.png")
        upgrade_font = get_font("arial", 16)
        text_faster = upgrade_font.render("Faster Rats", True, (0, 0, 0))
        text_stronger = upgrade_font.render("Stronger Rats", True, (0, 0, 0))
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_fasterrats_upgrade, (883, 65))
            scrn.blit(text_faster, (962, 42))
        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_strongrats_upgrade, (883, 194))
            scrn.blit(text_stronger, (962, 172))
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                if tower.curr_top_upgrade == 0 and money >= 1250:
                    purchase.play()
                    money -= 1250
                    tower.sell_amt += 625
                    tower.recruit_speed = 2
                    tower.spawn_interval = 750
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = load_image("assets/camp_faster.png")
                        tower.original_image = load_image("assets/camp_faster.png")
                        tower.recruit_image = "assets/rat_recruit_faster.png"
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image = load_image("assets/camp_stronger+faster.png")
                        tower.original_image = load_image("assets/camp_stronger+faster.png")
                        tower.recruit_image = "assets/rat_recruit_stronger+faster.png"
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image = load_image("assets/mrcheese_steroids+booksmart.png")
                        tower.original_image = load_image("assets/mrcheese_steroids+booksmart.png")
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                if money >= 1000 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    tower.recruit_health = 3
                    money -= 1000
                    tower.sell_amt += 500
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image = load_image("assets/camp_stronger.png")
                        tower.original_image = load_image("assets/camp_stronger.png")
                        tower.recruit_image = "assets/rat_recruit_stronger.png"
                    elif tower.curr_top_upgrade == 1:
                        tower.image = load_image("assets/camp_stronger+faster.png")
                        tower.original_image = load_image("assets/camp_stronger+faster.png")
                        tower.recruit_image = "assets/rat_recruit_stronger+faster.png"
                    elif tower.curr_top_upgrade == 2:
                        tower.image = load_image("assets/mrcheese_diploma+protein.png")
                        tower.original_image = load_image("assets/mrcheese_diploma+protein.png")
    if isinstance(tower, Ozbourne):
        img_amplifier_upgrade = load_image("assets/upgrade_amplifier.png")
        img_longerriffs_upgrade = load_image("assets/upgrade_longerriffs.png")
        upgrade_font = get_font("arial", 16)
        text_faster = upgrade_font.render("Amplifier", True, (0, 0, 0))
        text_stronger = upgrade_font.render("Longer Riffs", True, (0, 0, 0))
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_amplifier_upgrade, (883, 65))
            scrn.blit(text_faster, (962, 42))
        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_longerriffs_upgrade, (883, 194))
            scrn.blit(text_stronger, (962, 172))
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                if tower.curr_top_upgrade == 0 and money >= 350:
                    purchase.play()
                    money -= 350
                    tower.sell_amt += 125
                    tower.riff_blast_radius = 150
                    tower.radius = 150
                    tower.max_blast_radius = 150
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = load_image("assets/alfredo_ozbourne_amplifier.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_amplifier.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                        tower.recruit_image = "assets/alfredo_ozbourne_longer_riffs+amplifier.png"
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image = load_image("assets/mrcheese_steroids+booksmart.png")
                        tower.original_image = load_image("assets/mrcheese_steroids+booksmart.png")
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                if money >= 375 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    money -= 375
                    tower.sell_amt += 187
                    tower.riff_interval = (1165 / 2)
                    tower.blast_duration = (1165 / 2)
                    tower.damage = 1
                    tower.riff_sfx = load_sound("assets/riff_longer.mp3")
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image = load_image("assets/alfredo_ozbourne_longer_riffs.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_longer_riffs.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image = load_image("assets/camp_stronger+faster.png")
                        tower.original_image = load_image("assets/camp_stronger+faster.png")
                        tower.recruit_image = "assets/rat_recruit_stronger+faster.png"
                    elif tower.curr_top_upgrade == 2:
                        tower.image = load_image("assets/mrcheese_diploma+protein.png")
                        tower.original_image = load_image("assets/mrcheese_diploma+protein.png")
    if detect_single_click() and not ((tower.position[0] - 25) <= mouse[0] <= (tower.position[0] + 25) and (tower.position[1] - 25) <= mouse[1] <= (tower.position[1] + 25)):
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
    global towers, enemies
    for tower in towers:
        tower.update(enemies)
        tower.render(scrn)
        if not isinstance(tower, RatTent) and not isinstance(tower, Ozbourne):
            tower.shoot()


def update_stats(scrn: pygame.surface, health: int, money: int, round_number: int, clock: pygame.time.Clock()):
    health_font = get_font("arial", 28)
    money_font = get_font("arial", 28)
    round_font = get_font("arial", 28)

    text1 = health_font.render(f"{health}", True, (255, 255, 255))
    text2 = money_font.render(f"{money}", True, (255, 255, 255))
    text3 = round_font.render(f"Round {round_number}", True, (255, 255, 255))

    # DEBUGGING CURSOR POS
    mouse = pygame.mouse.get_pos()
    fps = int(clock.get_fps())  # Get current FPS from the passed clock

    x_font = get_font("arial", 12)
    y_font = get_font("arial", 12)
    fps_font = get_font("arial", 12)

    text_fps = fps_font.render(f"FPS: {fps}", True, (255, 0, 0))  # Render FPS in red
    text_x = x_font.render(f"x-axis: {mouse[0]}", True, (0, 255, 0))
    text_y = y_font.render(f"y-axis: {mouse[1]}", True, (0, 255, 0))

    # Display the FPS counter just above the x/y position text
    scrn.blit(text_fps, (1000, 650))
    scrn.blit(text_x, (1000, 670))
    scrn.blit(text_y, (1000, 690))

    # BACK TO REGULAR STUFF
    scrn.blit(text1, (55, 15))
    scrn.blit(text2, (65, 62))
    scrn.blit(text3, (1150, 10))


def handle_newtower(scrn: pygame.surface, tower: str) -> bool:
    global money
    image_house_hitbox = 'assets/house_illegal_regions.png'
    house_hitbox = load_image(image_house_hitbox)
    tower_click = load_sound("assets/tower_placed.mp3")
    mouse = pygame.mouse.get_pos()
    relative_pos = (mouse[0] - hitbox_position[0], mouse[1] - hitbox_position[1])
    if tower == "NULL":
        return True
    elif tower == "mrcheese":
        img_base_rat = load_image("assets/base_rat.png")
        circle_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (100, 100), 100)
            scrn.blit(img_base_rat, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 100, mouse[1] - 100))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (100, 100), 100)
            scrn.blit(img_base_rat, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 100, mouse[1] - 100))
    elif tower == "rattent":
        img_base_tent = load_image("assets/base_camp.png")
        circle_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (50, 50), 50)
            scrn.blit(img_base_tent, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 50, mouse[1] - 50))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (50, 50), 50)
            scrn.blit(img_base_tent, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 50, mouse[1] - 50))
        if within_spawn_point((mouse[0], mouse[1]), recruit_path, radius=50):
            checkpath_font = get_font("arial", 16)
            text_checkpath = checkpath_font.render("Eligible Path", True, (0, 255, 0))
            scrn.blit(text_checkpath, (mouse[0] - 35, mouse[1] + 50))
        elif not within_spawn_point((mouse[0], mouse[1]), recruit_path, radius=50):
            checkpath_font = get_font("arial", 16)
            text_checkpath = checkpath_font.render("Ineligible Path", True, (255, 0, 0))
            scrn.blit(text_checkpath, (mouse[0] - 35, mouse[1] + 50))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower):
            tower_rattent = RatTent((mouse[0], mouse[1]), radius=50, recruit_health=1, recruit_speed=1,
                                    recruit_damage=1,
                                    image_path='assets/base_camp.png', recruit_image="assets/rat_recruit.png",
                                    spawn_interval=2000)
            towers.append(tower_rattent)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 650
            return True
    elif tower == "ozbourne":
        img_base_ozbourne = load_image("assets/alfredo_ozbourne_base.png")
        circle_surface = pygame.Surface((150, 150), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (75, 75), 75)
            scrn.blit(img_base_ozbourne, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (75, 75), 75)
            scrn.blit(img_base_ozbourne, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower):
            tower_ozbourne = Ozbourne((mouse[0], mouse[1]), radius=100, weapon="guitar", damage=1, riff_blast_radius=75,
                                      image_path="assets/alfredo_ozbourne_base.png")
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
    img_recruit_death = load_image("assets/splatter_recuit.png")

    def __init__(self, position, health, speed, path, damage, image_path):
        self.health = health
        self.speed = speed
        self.path = path
        self.damage = damage
        self.image = load_image(image_path)
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
                best_index = i + 1
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
        self.image = load_image(image_path)
        self.rect = self.image.get_rect(center=position)
        self.spawn_interval = spawn_interval
        self.last_spawn_time = 0
        self.recruits = []
        self.recruit_image = recruit_image
        self.curr_bottom_upgrade = 0
        self.curr_top_upgrade = 0
        self.sell_amt = 325

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

class MrCheese:
    sfx_squeak = load_sound("assets/mouse-squeak.mp3")
    def __init__(self, position, radius, weapon, damage, image_path, projectile_image, shoot_interval=1000):
        self.position = position
        self.radius = radius
        self.weapon = weapon
        self.damage = damage
        self.image = load_image(image_path)
        self.original_image = self.image
        self.rect = self.image.get_rect(center=position)
        self.angle = 0
        self.target = None
        self.projectiles = []
        self.projectile_image = projectile_image
        self.shoot_interval = shoot_interval
        self.last_shot_time = 0
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.penetration = False
        self.sell_amt = 75

    def update(self, enemies):
        global last_time_sfx
        self.target = None
        closest_distance = self.radius
        potential_targets = []
        current_time = pygame.time.get_ticks()
        if current_time - last_time_sfx >= 15000:
            self.sfx_squeak.play()
            last_time_sfx = current_time
        for enemy in enemies:
            distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                 (enemy.position[1] - self.position[1]) ** 2)
            if distance <= self.radius:
                potential_targets.append((distance, enemy))
        potential_targets.sort(key=lambda x: x[0])
        for _, enemy in potential_targets:
            if not any(tower.target == enemy for tower in towers if tower != self and not isinstance(tower, RatTent) and not isinstance(tower, Ozbourne)):
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
                    self.target.take_damage(self.damage)
                if not self.penetration:
                    self.projectiles.remove(projectile)
                if self.penetration:
                    projectile.penetration -= 1
                    if projectile.penetration == 0:
                        self.projectiles.remove(projectile)

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
        for projectile in self.projectiles:
            projectile.render(screen)

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if self.target and current_time - self.last_shot_time >= self.shoot_interval:
            projectile = Projectile(
                position=self.position,
                target=self.target,
                speed=10,
                damage=self.damage,
                image_path=self.projectile_image
            )
            if self.penetration:
                projectile.penetration = self.damage - round((self.damage / 2))
            self.projectiles.append(projectile)
            self.last_shot_time = current_time

class Ozbourne:
    riff_sfx = load_sound("assets/riff1.mp3")
    def __init__(self, position, radius, weapon, damage, riff_blast_radius, image_path, riff_interval=4000):
        self.position = position
        self.radius = radius
        self.weapon = weapon
        self.damage = damage
        self.image = load_image(image_path)
        self.original_image = self.image
        self.rect = self.image.get_rect(center=position)
        self.riff_interval = riff_interval
        self.riff_blast_radius = riff_blast_radius
        self.last_blast_time = 0
        self.blast_active = False
        self.blast_animation_timer = 0
        self.blast_duration = 1165
        self.blast_radius = 0
        self.max_blast_radius = self.riff_blast_radius
        self.sell_amt = 250
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.riff_count = 0
        self.damage_default = self.damage

    def update(self, enemies):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_blast_time >= self.riff_interval:
            for enemy in enemies:
                distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                     (enemy.position[1] - self.position[1]) ** 2)
                if distance <= self.radius:
                    self.blast(enemies)
                    break
                else:
                    self.riff_count = 0
                    self.riff_sfx.stop()
                    mixer.music.unpause()
                    self.damage = 1
        if self.blast_active:
            self.blast_animation_timer += pygame.time.get_ticks() - self.last_blast_time
            self.blast_radius += (self.max_blast_radius / self.blast_duration) * (pygame.time.get_ticks() - self.last_blast_time)
            if self.blast_animation_timer >= self.blast_duration:
                self.blast_active = False
                self.blast_radius = 0
        if not RoundFlag:
            self.damage = 1
            self.riff_sfx.stop()
            mixer.music.unpause()
            self.riff_count = 0

    def blast(self, enemies):
        if self.curr_bottom_upgrade < 1:
            self.riff_sfx.play()
        elif self.curr_bottom_upgrade >= 1:
            self.riff_count += 1
            if self.riff_count == 1:
                mixer.music.pause()
                self.riff_sfx.play()
            elif self.riff_count >= 88:
                self.riff_count = 0
            self.damage += (self.riff_count * .1)
        self.last_blast_time = pygame.time.get_ticks()
        self.blast_active = True
        self.blast_animation_timer = 0
        self.blast_radius = 0
        for enemy in enemies:
            distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                 (enemy.position[1] - self.position[1]) ** 2)
            if distance <= self.riff_blast_radius:
                enemy.take_damage(self.damage)

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
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

class AntEnemy:
    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")
    def __init__(self, position, health, speed, path, image_path):
        self.position = position
        self.health = health
        self.speed = speed
        self.path = path
        self.original_image = load_image(image_path)
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
            user_health -= self.health

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
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
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        if not self.is_alive:
            screen.blit(self.img_death, self.rect.topleft)

class HornetEnemy:
    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")
    def __init__(self, position, health, speed, path, image_path):
        self.position = position
        self.health = health
        self.speed = speed
        self.path = path
        self.original_image = load_image(image_path)
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
            user_health -= self.health

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
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
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        if not self.is_alive:
            screen.blit(self.img_death, self.rect.topleft)


class CentipedeEnemy:
    """
    A composite enemy consisting of:
      - Head (health=6)
      - 4 Link segments (each health=3)
      - Tail (health=3)
    Movement is fluid: each segment follows the one ahead with a smoothing delay.
    Damage is applied to the furthest (tail-first) alive segment until only the head remains.
    Speed is 1 initially, increases to 2 when 3 or fewer non-head segments remain,
    and becomes 3 when only the head is left.
    The images are flipped horizontally in rendering.
    """
    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")

    class Segment:
        def __init__(self, role, health, image, position):
            self.role = role  # "head", "link", or "tail"
            self.health = health
            self.image = image
            self.position = position  # (x, y)
            self.angle = 0  # in degrees; 0 means "facing up"
            self.alive = True
            self.death_time = None  # Stores the time of death
            self.rect = self.image.get_rect(center=position)

        def update_rect(self):
            self.rect = self.image.get_rect(center=self.position)

    def __init__(self, position, path):
        """
        :param position: Starting position (tuple)
        :param path: List of points (tuples) for the centipede head to follow.
        """
        self.path = path
        self.current_target = 0  # Index in the path for head movement
        self.base_speed = 1      # Initial speed
        self.speed = self.base_speed

        # Load images
        head_img = load_image("assets/centipede_head.png")
        link_img = load_image("assets/centipede_link.png")
        tail_img = load_image("assets/centipede_tail.png")

        # Calculate desired gap distances (so segments appear connected)
        # Gaps are computed based on half-heights of adjacent images.
        self.gap_distances = []
        gap_head_link = (head_img.get_height() / 4) + (link_img.get_height() / 4)
        self.gap_distances.append(gap_head_link)
        # For the gaps between the 4 links (using link height)
        for _ in range(5):
            gap_link_link = link_img.get_height() / 4
            self.gap_distances.append(gap_link_link)
        gap_link_tail = (link_img.get_height() / 4) + (tail_img.get_height() / 4)
        self.gap_distances.append(gap_link_tail)

        # Create segments. All segments start at the same initial position.
        self.segments = []
        # Head segment with health 6.
        self.segments.append(self.Segment("head", 6, head_img, position))
        # 6 link segments, each with health 2.
        for _ in range(6):
            self.segments.append(self.Segment("link", 2, link_img, position))
        # Tail segment with health 3.
        self.segments.append(self.Segment("tail", 3, tail_img, position))

    def update(self):
        """
        Update the centipede:
          - Move the head along its path.
          - Smoothly update each following segment so that it trails its predecessor.
          - Adjust the speed based on the number of non-head segments still alive.
          - Remove the centipede and subtract health if it reaches the end of the path.
        """
        global user_health  # Ensure this matches how health is tracked in your game

        # Determine how many non-head segments are still alive.
        non_head_alive = sum(1 for seg in self.segments[1:] if seg.alive)
        if non_head_alive >= 4:
            self.speed = 1
        elif non_head_alive > 0:
            self.speed = 2
        else:
            self.speed = 3

        # === Move the head along the path ===
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
            # Centipede reaches the end of the path
            user_health -= head.health  # Subtract health when the enemy escapes
            self.segments.clear()  # Remove all segments so it disappears
            return

        # === Smoothly update each following segment ===
        alpha = 0.2  # Smoothing factor
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
                seg.angle += alpha * ((desired_angle - seg.angle + 180) % 360 - 180)
                seg.update_rect()

    def move(self):
        """Alias move() to update() for compatibility with the game loop."""
        self.update()

    def take_damage(self, damage):
        global money
        """
        Apply damage to the centipede:
          - Damage is applied to the furthest (tail-first) alive segment among the links/tail.
          - Only if all non-head segments are destroyed is damage applied to the head.
        """
        for seg in reversed(self.segments[1:]):  # Prioritize tail & links first
            if seg.alive:
                seg.health -= damage
                if seg.health <= 0:
                    seg.alive = False
                    money += 15
                    self.sfx_splat.play()
                    seg.death_time = pygame.time.get_ticks()  # Mark the time of death
                return  # Exit after applying damage.

        # If all non-head segments are destroyed, apply damage to the head.
        head = self.segments[0]
        head.health -= damage
        if head.health <= 0:
            head.alive = False
            money += 25
            self.sfx_splat.play()
            head.death_time = pygame.time.get_ticks()

    def render(self, screen: pygame.Surface):
        """
        Render each alive segment with its current rotation.
        Show the splatter effect for a brief time after death.
        """
        current_time = pygame.time.get_ticks()
        SPLATTER_DURATION = 100  # Time in milliseconds to show the splatter (0.5 seconds)

        for seg in self.segments:
            if seg.alive:
                # Render living segments
                rotated_image = pygame.transform.rotate(seg.image, seg.angle)
                rotated_image = pygame.transform.flip(rotated_image, True, False)  # Flip horizontally
                rect = rotated_image.get_rect(center=seg.position)
                screen.blit(rotated_image, rect.topleft)
            elif seg.death_time and current_time - seg.death_time <= SPLATTER_DURATION:
                # Render splatter effect for a limited time
                rotated_splatter = pygame.transform.rotate(self.img_death, seg.angle)
                rotated_splatter = pygame.transform.flip(rotated_splatter, True, False)
                rect = rotated_splatter.get_rect(center=seg.position)
                screen.blit(rotated_splatter, rect.topleft)

    @property
    def position(self):
        """
        Expose the centipede's effective position as the position of the furthest (tail-most)
        alive segment. This helps towers target the centipede's remaining body.
        """
        for seg in reversed(self.segments):
            if seg.alive:
                return seg.position
        return self.segments[0].position

    @property
    def is_alive(self):
        """
        The centipede is considered alive as long as its head is alive.
        If all segments are cleared (e.g., reached the end), return False.
        """
        return bool(self.segments) and self.segments[0].alive


class Projectile:
    def __init__(self, position, target, speed, damage, image_path):
        self.position = list(position)
        self.target = target
        self.speed = speed
        self.damage = damage
        self.image = load_image(image_path)
        self.rect = self.image.get_rect(center=position)
        self.hit = False
        self.penetration = 0

    def move(self):
        if not self.target.is_alive:
            self.hit = True
            return
        target_x, target_y = self.target.position
        dx = target_x - self.position[0]
        dy = target_y - self.position[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance > 0:
            direction_x = dx / distance
            direction_y = dy / distance
            self.position[0] += direction_x * self.speed
            self.position[1] += direction_y * self.speed
            self.rect.center = self.position
        if distance <= self.speed:
            self.hit = True

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)


class RatRecruit:
    def __init__(self, position, health, speed, path, image_path):
        self.position = position
        self.health = health
        self.speed = speed
        self.path = path
        self.original_image = load_image(image_path)
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
            user_health -= self.health

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
