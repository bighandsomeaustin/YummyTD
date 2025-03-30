import pygame
from pygame import mixer
import math
import time
import random

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
SettingsFlag = False
curr_upgrade_tower = None
MogFlag = False
gameoverFlag = False
last_time_sfx = pygame.time.get_ticks()
money = 250  # change for debugging
user_health = 100
music_volume = 1.0
user_volume = 1.0
slider_dragging = False
game_speed_multiplier = 1  # Add at top with other globals
last_frame_time = 0  # Track frame timing

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


def get_scaled_time():
    """Returns time adjusted for game speed"""
    global last_frame_time
    current_time = pygame.time.get_ticks()
    delta = current_time - last_frame_time
    last_frame_time = current_time
    return delta * game_speed_multiplier


def get_scaled_delta():
    """Returns time delta adjusted for game speed"""
    return (1000/60) * (1/game_speed_multiplier)  # Approximate frame delta


def play_splash_animation(scrn: pygame.Surface, pos: tuple, frame_delay: int = 5):
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
                    pygame.quit();
                    exit()
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
    global RoundFlag, money, UpgradeFlag, curr_upgrade_tower, SettingsFlag, music_volume, slider_dragging, user_volume \
        , gameoverFlag, enemies, current_wave, user_health, game_speed_multiplier
    purchase = load_sound("assets/purchase_sound.mp3")
    img_tower_select = load_image("assets/tower_select.png")
    img_mrcheese_text = load_image("assets/mrcheese_text.png")
    img_ratcamp_text = load_image("assets/ratcamp_text.png")
    img_ratbank_text = load_image("assets/ratbank_text.png")
    img_ozbourne_text = load_image("assets/ozbourne_text.png")
    img_commando_text = load_image("assets/commando_text.png")
    img_playbutton = load_image("assets/playbutton.png")
    img_playbutton_1x = load_image("assets/playbutton_1x.png")
    img_playbutton_2x = load_image("assets/playbutton_2x.png")
    img_settingsbutton = load_image("assets/settingsbutton.png")
    img_settings_window = load_image("assets/ingame_settings.png")
    img_music_slider = load_image("assets/music_slider.png")
    mouse = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]

    # Slider boundaries: x from 400 (0%) to 736 (100%) and fixed y
    slider_min = 400
    slider_max = 736
    slider_y = 421
    slider_height = 18

    # Calculate slider x based on music_volume (0.0 to 1.0)
    slider_x = slider_min + user_volume * (slider_max - slider_min)

    if user_health <= 0 and not gameoverFlag:
        user_health = 0
        gameoverFlag = True
        mixer.music.load("assets/song_gameover.mp3")
        mixer.music.play(-1)
        enemies.clear()
        towers.clear()
        current_wave = 1
        RoundFlag = False
    if gameoverFlag:
        img_gameover = load_image("assets/gameover.png")
        scrn.blit(img_gameover, (0, 0))
        if 332 <= mouse[0] <= 332 + 298 and 372 <= mouse[1] <= 372 + 153:
            if detect_single_click():
                gameoverFlag = False
                return "newgame"
        if 664 <= mouse[0] <= 664 + 298 and 372 <= mouse[1] <= 372 + 153:
            if detect_single_click():
                gameoverFlag = False
                return "menu"

    if RoundFlag:
        music_volume = user_volume
    else:
        music_volume = user_volume * .5

    mixer.music.set_volume(music_volume)

    if not RoundFlag:
        scrn.blit(img_playbutton, (1110, 665))
        if 1110 <= mouse[0] <= 1110 + 81 and 665 <= mouse[1] <= 665 + 50:
            if detect_single_click():
                RoundFlag = True
                return "nextround"
    if RoundFlag:
        if game_speed_multiplier == 1:
            scrn.blit(img_playbutton_1x, (1110, 665))
        else:
            scrn.blit(img_playbutton_2x, (1110, 665))
        # 2x speed
        if 1110 <= mouse[0] <= 1110 + 81 and 665 <= mouse[1] <= 665 + 50:
            if detect_single_click():
                game_speed_multiplier = 3 if game_speed_multiplier == 1 else 1

    # settings button
    scrn.blit(img_settingsbutton, (1192, 665))
    if 1192 <= mouse[0] <= 1192 + 81 and 665 <= mouse[1] <= 665 + 50:
        if detect_single_click():
            SettingsFlag = True

    if SettingsFlag:
        scrn.blit(img_settings_window, (0, 0))
        scrn.blit(img_music_slider, (slider_x, slider_y))
        # slider range - 400 (0%) to 736 (100%)
        if 766 <= mouse[0] <= 766 + 15 and 205 <= mouse[1] <= 205 + 18:
            if detect_single_click():
                SettingsFlag = False
        if 306 <= mouse[0] <= 306 + 199 and 286 <= mouse[1] <= 286 + 114:
            if detect_single_click():
                SettingsFlag = False
                return "saveandquit"
        if 550 <= mouse[0] <= 550 + 199 and 286 <= mouse[1] <= 286 + 114:
            if detect_single_click():
                SettingsFlag = False
                return "saveandquit"  # change to quit w/o saving later
        # If left mouse button is pressed, check for dragging
        if mouse_pressed:
            # If not already dragging, check if the click is near the slider knob
            if not slider_dragging:
                if abs(mouse[0] - slider_x) < 15 and slider_y <= mouse[1] <= slider_y + slider_height:
                    slider_dragging = True
            # If dragging, update slider position and volume
            if slider_dragging:
                new_x = max(slider_min, min(mouse[0], slider_max))
                user_volume = (new_x - slider_min) / (slider_max - slider_min)
        else:
            slider_dragging = False

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
    # RAT BANK
    elif 1195 <= mouse[0] <= 1195 + 73 and 382 <= mouse[1] <= 382 + 88:
        scrn.blit(img_ratbank_text, (1113, 53))
        scrn.blit(img_tower_select, (1195, 382))
        if detect_single_click() and money >= 700:
            purchase.play()
            return "ratbank"

    # CHEDDAR COMMANDO
    elif 1195 <= mouse[0] <= 1195 + 73 and 195 <= mouse[1] <= 195 + 88:
        scrn.blit(img_commando_text, (1113, 53))
        scrn.blit(img_tower_select, (1195, 195))
        if detect_single_click() and money >= 250:
            purchase.play()
            return "soldier"
    # check if any tower is clicked after placement
    for tower in towers:
        if (tower.position[0] - 25) <= mouse[0] <= (tower.position[0] + 25) and (tower.position[1] - 25) <= mouse[
            1] <= (tower.position[1] + 25):
            if detect_single_click():
                if isinstance(tower, RatBank):
                    tower.is_selected = True
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
                    tower.riff_blast_radius = 100
                    tower.radius = 100
                    tower.max_blast_radius = 100
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = load_image("assets/alfredo_ozbourne_amplifier.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_amplifier.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
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
                    tower.riff_interval = 1165 * 2
                    tower.blast_duration = 1165 * 2
                    tower.damage = 1
                    tower.riff_sfx = load_sound("assets/riff_longer.mp3")
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image = load_image("assets/alfredo_ozbourne_longer_riffs.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_longer_riffs.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                        tower.recruit_image = "assets/alfredo_ozbourne_longer_riffs+amplifier.png"
    if isinstance(tower, RatBank):
        img_credit_upgrade = load_image("assets/upgrade_better_credit.png")
        img_cheesefargo_upgrade = load_image("assets/upgrade_cheese_fargo.png")
        upgrade_font = get_font("arial", 16)
        text_credit = upgrade_font.render("715 Credit Score", True, (0, 0, 0))
        text_fargo = upgrade_font.render("Cheese Fargo", True, (0, 0, 0))
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_credit_upgrade, (883, 65))
            scrn.blit(text_credit, (952, 42))
        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_cheesefargo_upgrade, (883, 194))
            scrn.blit(text_fargo, (962, 172))
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                if tower.curr_top_upgrade == 0 and money >= 800:
                    purchase.play()
                    money -= 800
                    tower.sell_amt += 400
                    tower.interest_rate = 1.07
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = load_image("assets/rat_bank_fargo.png")
                        tower.original_image = load_image("assets/rat_bank_fargo.png")
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                if money >= 1200 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    money -= 1200
                    tower.sell_amt += 600
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image = load_image("assets/rat_bank_fargo_skyscraper.png")
                        tower.original_image = load_image("assets/rat_bank_fargo_skyscraper.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image = load_image("assets/rat_bank_fargo_skyscraper.png")
                        tower.original_image = load_image("assets/rat_bank_fargo_skyscraper.png")
    if isinstance(tower, CheddarCommando):
        img_shotgun_upgrade = load_image("assets/upgrade_shotgun.png")
        img_rpg_upgrade = load_image("assets/upgrade_rocket.png")
        img_piercing_upgrade = load_image("assets/upgrade_piercing.png")
        img_thumper_upgrade = load_image("assets/upgrade_thumper.png")
        upgrade_font = get_font("arial", 16)
        text_shotgun = upgrade_font.render("Shotgun", True, (0, 0, 0))
        text_piercing = upgrade_font.render("Piercing Rounds", True, (0, 0, 0))
        text_rpg = upgrade_font.render("Explosive Rounds", True, (0, 0, 0))
        text_grenade = upgrade_font.render("Grenade Launcher", True, (0, 0, 0))
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_piercing_upgrade, (883, 65))
            scrn.blit(text_piercing, (952, 42))
        elif tower.curr_top_upgrade == 1:
            scrn.blit(img_shotgun_upgrade, (883, 65))
            scrn.blit(text_shotgun, (959, 42))

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_rpg_upgrade, (883, 194))
            scrn.blit(text_rpg, (942, 172))
        elif tower.curr_bottom_upgrade == 1:
            scrn.blit(img_thumper_upgrade, (883, 194))
            scrn.blit(text_grenade, (941, 172))
        # piercing upgrade
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                if tower.curr_top_upgrade == 0 and money >= 450:
                    purchase.play()
                    money -= 450
                    tower.sell_amt += 225
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image = load_image("assets/soldier_piercing.png")
                        tower.original_image = load_image("assets/soldier_piercing.png")
                # shotgun upgrade
                elif tower.curr_top_upgrade == 1 and money >= 750 and tower.curr_bottom_upgrade != 2:
                    purchase.play()
                    money -= 750
                    tower.sell_amt += 375
                    if tower.curr_bottom_upgrade < 1:
                        tower.reload_time = 5374
                        tower.shoot_interval = 1895
                        tower.reload_sound = load_sound("assets/shotgun_reload.mp3")
                        tower.radius = 75
                    tower.shoot_sound = load_sound("assets/shotgun_shoot.mp3")
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade <= 1:
                        tower.image = load_image("assets/soldier_shotgun.png")
                        tower.original_image = load_image("assets/soldier_shotgun.png")
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        # rocket launcher upgrade
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                if money >= 700 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    money -= 700
                    tower.sell_amt += 350
                    tower.curr_bottom_upgrade = 1
                    tower.radius = 150
                    tower.reload_time = 2500
                    if tower.curr_top_upgrade < 1:
                        tower.shoot_sound = load_sound("assets/launcher_shoot.mp3")
                        tower.image = load_image("assets/soldier_rocket.png")
                        tower.original_image = load_image("assets/soldier_rocket.png")
                    tower.reload_sound = load_sound("assets/commando_reload.mp3")
                    UpgradeFlag = True
                elif money >= 900 and tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade != 2:
                    purchase.play()
                    money -= 900
                    tower.sell_amt += 450
                    tower.curr_bottom_upgrade = 2
                    tower.radius = 125
                    tower.shoot_interval = 750
                    tower.reload_time = 5500
                    tower.reload_sound = load_sound("assets/shotgun_reload.mp3")
                    UpgradeFlag = True
                    tower.image = load_image("assets/soldier_thumper.png")
                    tower.original_image = load_image("assets/soldier_thumper.png")

    if detect_single_click() and not (
            (tower.position[0] - 25) <= mouse[0] <= (tower.position[0] + 25) and (tower.position[1] - 25) <= mouse[
        1] <= (tower.position[1] + 25)):
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
        if not isinstance(tower, RatBank):
            tower.update(enemies)
        tower.render(scrn)
        if not isinstance(tower, RatTent) and not isinstance(tower, Ozbourne) and not isinstance(tower, RatBank):
            tower.shoot()
    for tower in towers:
        if isinstance(tower, RatBank):
            tower.render(scrn)


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
            if event.type == pygame.KEYUP:
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
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "mrcheese":
            tower_mrcheese = MrCheese((mouse[0], mouse[1]), radius=75, weapon="Cheese", damage=1,
                                      image_path="assets/base_rat.png", projectile_image="assets/projectile_cheese.png")
            towers.append(tower_mrcheese)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 150
            return True
    elif tower == "soldier":
        img_base_soldier = load_image("assets/base_soldier.png")
        circle_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (75, 75), 75)
            scrn.blit(img_base_soldier, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (75, 75), 75)
            scrn.blit(img_base_soldier, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "soldier":
            tower_commando = CheddarCommando((mouse[0], mouse[1]))
            towers.append(tower_commando)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 250
            return True
    elif tower == "rattent":
        img_base_tent = load_image("assets/base_camp.png")
        circle_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
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
    elif tower == "ratbank":
        img_base_bank = load_image("assets/rat_bank.png")
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            scrn.blit(img_base_bank, (mouse[0] - 25, mouse[1] - 25))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            scrn.blit(img_base_bank, (mouse[0] - 25, mouse[1] - 25))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower):
            tower_ratbank = RatBank((mouse[0], mouse[1]), image_path="assets/rat_bank.png")
            towers.append(tower_ratbank)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 700
            return True
    elif tower == "ozbourne":
        img_base_ozbourne = load_image("assets/alfredo_ozbourne_base.png")
        circle_surface = pygame.Surface((150, 150), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
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
    def __init__(self, position, radius, recruit_health, recruit_speed, recruit_damage, image_path, recruit_image,
                 spawn_interval=2000):
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
        scaled_interval = self.spawn_interval / game_speed_multiplier
        if pygame.time.get_ticks() - self.last_spawn_time >= scaled_interval and RoundFlag:
            recruit_entity = RecruitEntity(self.position, 1, 1, recruit_path, 1, self.recruit_image)
            closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
            distance = ((closest_spawn_point[0] - self.position[0]) ** 2 + (
                    closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
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
                self.last_spawn_time = pygame.time.get_ticks()
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
            if not any(tower.target == enemy for tower in towers if
                       tower != self and not isinstance(tower, RatTent) and not isinstance(tower, Ozbourne)
                       and not isinstance(tower, RatBank)):
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
        scaled_interval = self.shoot_interval / game_speed_multiplier
        if self.target and self.target.is_alive:  # Add target validation
            if pygame.time.get_ticks() - self.last_shot_time >= scaled_interval:
                projectile = Projectile(
                    position=self.position,
                    target=self.target,
                    speed=10 * game_speed_multiplier,  # Scaled projectile speed
                    damage=self.damage,
                    image_path=self.projectile_image
                )
                if self.penetration:
                    projectile.penetration = self.damage - round((self.damage / 2))
                self.projectiles.append(projectile)
                self.last_shot_time = pygame.time.get_ticks()


class RatBank:
    def __init__(self, position, image_path):
        self.position = position
        self.image = load_image(image_path)
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
        # Upgrade flags
        self.curr_top_upgrade = 0  # For interest rate improvement (Cheese Fargo upgrade)
        self.curr_bottom_upgrade = 0  # For loan functionality (Cheese Fargo HQ upgrade)
        self.invested_round = current_wave  # Round tracking for investment updates
        self.curr_round = current_wave
        self.sell_amt = 350
        self.RepoFlag = False
        self.user_text = ""
        # NEW: Instance-level flag for selection (used for showing the invest button)
        self.is_selected = False

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
        global money
        investment_bg = load_image("assets/investment_window.png")
        investment_bg_no_loans = load_image("assets/investment_window_no_loans.png")
        investment_no_prov = load_image("assets/investment_window_provoloan_unavail.png")
        investment_no_brie = load_image("assets/investment_window_briefund_unavail.png")
        investment_both_unavail = load_image("assets/investment_window_both_unavail.png")
        add_investment = load_image("assets/enter_investment_window.png")
        withdraw_window = load_image("assets/withdraw_window.png")
        select_loan = load_image("assets/loan_highlight.png")
        mouse = pygame.mouse.get_pos()

        # Calculate stock price based on total towers' sell_amt
        sell_sum = 0
        for tower in towers:
            sell_sum += tower.sell_amt
        self.stock_value = int(sell_sum * 0.01)

        font = pygame.font.SysFont("arial", 20)
        text_invested = font.render(f"${self.cash_invested}", True, (255, 255, 255))
        text_generated = font.render(f"${self.cash_generated}", True, (255, 255, 255))
        text_stock = font.render(f"${self.stock_value} per share", True, (255, 255, 255))
        text_payment = font.render(f"${self.loan_payment}", True, (255, 255, 255))
        font_invest = pygame.font.SysFont("arial", 16)

        # Choose the appropriate background based on loan upgrade state
        if self.curr_bottom_upgrade < 1:
            scrn.blit(investment_bg_no_loans, (0, 0))
        elif self.briefundFlag and self.provoloanFlag:
            scrn.blit(investment_both_unavail, (0, 0))
        elif self.provoloanFlag:
            scrn.blit(investment_no_prov, (0, 0))
        elif self.briefundFlag:
            scrn.blit(investment_no_brie, (0, 0))
        else:
            scrn.blit(investment_bg, (0, 0))

        if self.curr_bottom_upgrade >= 1:
            scrn.blit(text_payment, (662, 413))

        scrn.blit(text_invested, (644, 264))
        scrn.blit(text_generated, (654, 300))
        scrn.blit(text_stock, (624, 337))

        # Close button for the investment window;
        # also reset the selection so the invest button won't reappear.
        if 799 <= mouse[0] <= 799 + 11 and 212 <= mouse[1] <= 212 + 15:
            if detect_single_click():
                self.investment_window_open = False
                self.is_selected = False

        # '+' button to open the new investment input
        if 746 <= mouse[0] <= 746 + 22 and 264 <= mouse[1] <= 264 + 23:
            if detect_single_click():
                self.open_new_investment = True

        # New investment input interface
        if self.open_new_investment:
            if not (746 <= mouse[0] <= 746 + 22 and 264 <= mouse[1] <= 264 + 23):
                if detect_single_click():
                    self.open_new_investment = False
            self.open_withdraw_window = False  # Close withdraw if open
            scrn.blit(add_investment, (771, 262))
            user_text_display = font_invest.render(self.user_text, True, (255, 255, 255))
            scrn.blit(user_text_display, (802, 285))

        # Withdraw button handling
        if 748 <= mouse[0] <= 748 + 20 and 302 <= mouse[1] <= 302 + 22:
            if detect_single_click():
                self.open_withdraw_window = True

        if self.open_withdraw_window:
            self.open_new_investment = False
            scrn.blit(withdraw_window, (769, 297))
            if not (774 <= mouse[0] <= 774 + 141 and 301 <= mouse[1] <= 320 + 17):
                if detect_single_click():
                    self.open_withdraw_window = False
            if 774 <= mouse[0] <= 774 + 141 and 301 <= mouse[1] <= 301 + 17:
                if detect_single_click():
                    money += self.cash_generated
                    self.invested_round = current_wave
                    self.cash_generated = 0
                    self.open_withdraw_window = False
            if 774 <= mouse[0] <= 744 + 141 and 320 <= mouse[1] <= 320 + 17:
                if detect_single_click():
                    money += (self.cash_generated + self.cash_invested)
                    self.invested_round = current_wave
                    self.cash_generated = 0
                    self.cash_invested = 0
                    self.open_withdraw_window = False

        # Loan handling (Cheese Fargo upgrades)
        if self.curr_bottom_upgrade >= 1:
            if 507 <= mouse[0] <= 507 + 133 and 441 <= mouse[1] <= 441 + 64 and not self.provoloanFlag:
                scrn.blit(select_loan, (507, 441))
                if detect_single_click():
                    money += self.provoloan
                    self.loan_payment += self.provoloan_payment
                    self.loan_amount += (self.provoloan * 1.14)
                    self.provoloanFlag = True
            if 639 <= mouse[0] <= 639 + 133 and 441 <= mouse[1] <= 441 + 64 and not self.briefundFlag:
                scrn.blit(select_loan, (639, 441))
                if detect_single_click():
                    money += self.briefund
                    self.loan_payment += self.briefund_payment
                    self.loan_amount += (self.briefund * 1.07)
                    self.briefundFlag = True

    def process_interest(self):
        """
        Called at the end of each round to apply interest to the invested cash,
        update cash_generated, and recalculate the stock value.
        """
        self.curr_round = current_wave
        round_diff = self.curr_round - self.invested_round
        self.cash_generated += int((self.cash_invested + self.cash_generated) *
                                   (self.interest_rate - 1))

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
        invest_btn = load_image("assets/invest_box.png")
        repossessed_window = load_image("assets/repossessed_window.png")
        scrn.blit(self.image, self.rect.topleft)

        # If this bank is selected and its investment window is not open, show its invest button.
        if self.is_selected and not self.investment_window_open:
            if self.curr_bottom_upgrade < 1:
                scrn.blit(invest_btn, (self.position[0] - 22, self.position[1] + 45))
                if (self.position[0] - 22 <= mouse[0] <= self.position[0] - 22 + 46 and
                        self.position[1] + 45 <= mouse[1] <= self.position[1] + 45 + 14):
                    if detect_single_click():
                        self.investment_window_open = True
                        UpgradeFlag = False
                        self.is_selected = False
            else:
                scrn.blit(invest_btn, (self.position[0] - 22, self.position[1] + 45 + 59))
                if (self.position[0] - 22 <= mouse[0] <= self.position[0] - 22 + 46 and
                        self.position[1] + 45 + 59 <= mouse[1] <= self.position[1] + 45 + 14 + 59):
                    if detect_single_click():
                        self.investment_window_open = True
                        self.is_selected = False
                        UpgradeFlag = False

        # If the bank is selected but a click occurs outside its area, clear the selection
        # so the invest button disappears.
        if self.is_selected and not self.investment_window_open:
            # Check if the mouse click is outside the bank's rect (you can fine-tune this as needed)
            if detect_single_click() and not self.rect.collidepoint(mouse):
                self.is_selected = False

        if self.RepoFlag:
            scrn.blit(repossessed_window, (403, 317))
            if 728 <= mouse[0] <= 728 + 12 and 323 <= mouse[1] <= 323 + 10:
                if detect_single_click():
                    self.RepoFlag = False

        if self.investment_window_open:
            self.investment_interface(scrn)

        # self.process_interest()


# New projectile class for Cheddar Commando using pygame drawing for bullets
class CommandoProjectile:
    def __init__(self, position, angle, speed, damage, piercing=False):
        self.position = list(position)  # Ensure mutability for movement
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.radius = 3  # bullet radius for drawing
        self.penetration = 5  # Add penetration counter
        self.hit = False
        self.piercing = piercing
        self.explosive = False
        self.armor_break = False

        # Calculate velocity based on angle
        rad = math.radians(angle)
        self.velocity = [speed * math.cos(rad), -speed * math.sin(rad)]

    def move(self):
        """Update projectile movement."""
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

        # Destroy projectile if it leaves screen bounds
        if not (0 <= self.position[0] <= 1280 and 0 <= self.position[1] <= 720):
            self.hit = True

    def render(self, screen):
        """Draw projectile."""
        pygame.draw.circle(screen, (255, 255, 0), (int(self.position[0]), int(self.position[1])), self.radius)


class CheddarCommando:
    def __init__(self, position, radius=75, damage=1, shoot_interval=800, reload_time=4000):
        self.position = position
        self.radius = radius
        self.damage = damage
        self.image = load_image("assets/base_soldier.png")
        self.explosion_sfx = load_sound("assets/explosion_sfx.mp3")
        self.original_image = self.image
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
        self.explosion_damage = 1
        self.explosion_pos = (0, 0)
        self.explosion_animation_timer = 0
        self.explosion_duration = 100  # Explosion lasts 50ms
        self.max_explosion_radius = 50  # Explosion damage radius (debug value; adjust as needed)
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
        self.shoot_sound = load_sound("assets/pistol_shoot.mp3")
        self.reload_sound = load_sound("assets/commando_reload.mp3")

    def update(self, enemies):
        """Update targeting, projectiles, explosion animation, and reload state."""
        # Reset ammo when round ends
        if not RoundFlag:
            self.shot_count = 0
        # Targeting logic
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
            self.angle = math.degrees(math.atan2(-dy, dx))
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(center=self.position)

        # Explosion animation update using delta time
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

        # Process projectiles
        for projectile in self.projectiles[:]:
            projectile.move()
            for enemy in enemies:
                # Use enemy center plus half its width to allow partial overlap to count
                enemy_center = enemy.rect.center
                dist = math.hypot(projectile.position[0] - enemy_center[0],
                                  projectile.position[1] - enemy_center[1])
                if dist < enemy.rect.width / 2:
                    enemy.take_damage(projectile.damage, projectile=projectile)
                    if projectile.explosive:
                        self.explosion_pos = enemy.rect.center
                        self.explosion(enemies)
                        self.explosion_sfx.play()
                    projectile.hit = True
                    if not projectile.piercing:
                        break
            # Remove the redundant damage application here
            if projectile.hit:
                if not projectile.piercing:
                    self.projectiles.remove(projectile)
                else:
                    projectile.penetration -= 1
                    if projectile.penetration <= 0:
                        self.projectiles.remove(projectile)

        # Reload handling
        if self.is_reloading:
            scaled_reload = self.reload_time / game_speed_multiplier
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
                if isinstance(enemy, BeetleEnemy):
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
            scaled_reload = self.reload_time / game_speed_multiplier
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
        scaled_interval = self.shoot_interval / game_speed_multiplier
        if self.target and not self.is_reloading and pygame.time.get_ticks() - self.last_shot_time >= scaled_interval:
            self.shoot_sound.play()
            self.has_fired = True
            # If top upgrade is active, fire a spread shot
            if self.curr_top_upgrade > 1:
                spread_angles = [-20, -10, 0, 10, 20]
                for offset in spread_angles:
                    proj = CommandoProjectile(self.position, self.angle + offset, speed=20, damage=self.damage)
                    if self.curr_bottom_upgrade >= 1:
                        proj.explosive = True
                        proj.armor_break = True
                    if self.curr_top_upgrade >= 1:
                        proj.piercing = True
                    self.projectiles.append(proj)
            else:
                proj = CommandoProjectile(self.position, self.angle, speed=20, damage=self.damage)
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
                self.reload_sound.play()
                self.shot_count = 0  # Reset shot count IMMEDIATELY to prevent standard reload logic

            # **Standard Reload Logic**
            elif self.curr_top_upgrade > 1 and self.shot_count >= 7:
                self.is_reloading = True
                self.reload_start_time = pygame.time.get_ticks()
                self.reload_sound.play()
            elif self.curr_bottom_upgrade > 1 and self.shot_count >= 6:
                self.is_reloading = True
                self.reload_start_time = pygame.time.get_ticks()
                self.reload_sound.play()
            elif self.shot_count >= 12:
                self.is_reloading = True
                self.reload_start_time = pygame.time.get_ticks()
                self.reload_sound.play()


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
        self.blast_duration = 1165 * 2
        self.blast_radius = 0
        self.max_blast_radius = self.riff_blast_radius
        self.sell_amt = 250
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.riff_count = 0
        self.damage_default = self.damage

    def update(self, enemies):
        scaled_interval = self.riff_interval / game_speed_multiplier
        scaled_duration = self.blast_duration / game_speed_multiplier
        if pygame.time.get_ticks() - self.last_blast_time >= scaled_interval:
            for enemy in enemies:
                distance = math.sqrt((enemy.position[0] - self.position[0]) ** 2 +
                                     (enemy.position[1] - self.position[1]) ** 2)
                if distance <= self.radius:
                    self.blast(enemies)
                    self.last_blast_time = pygame.time.get_ticks()
                    break
                else:
                    self.riff_count = 0
                    self.riff_sfx.stop()
                    mixer.music.unpause()
                    self.damage = 1
        if self.blast_active:
            self.blast_animation_timer += pygame.time.get_ticks() - self.last_blast_time
            self.blast_radius += (self.max_blast_radius / scaled_duration) * (
                    pygame.time.get_ticks() - self.last_blast_time)
            if self.blast_animation_timer >= scaled_duration:
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
                self.damage = 1
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
        self.shards = []  # New: Particle storage

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

    def spawn_shards(self, count=8):
        for _ in range(count):
            shard = {
                'pos': [self.position[0], self.position[1]],
                'vel': [random.uniform(-3, 3), random.uniform(-3, 3)],
                'lifetime': random.randint(100, 600),
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3)
            }
            self.shards.append(shard)

    def update_shards(self, screen):
        current_time = pygame.time.get_ticks()
        for shard in self.shards[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                self.shards.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (255, 255, 255, alpha)
                shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, damage, projectile=None):
        global money
        self.health -= damage
        self.spawn_shards()
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            money += 5

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)
            self.update_shards(screen)  # NEW: Render particles


class BeetleEnemy:
    def __init__(self, position, path):
        """
        Initialize a BeetleEnemy.
        :param position: Starting (x, y) tuple.
        :param path: List of waypoints (tuples) to follow.
        """
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
        self.base_image = load_image("assets/beetle_base.png")
        self.image = self.base_image
        self.original_image = self.image

        # Set up rect for positioning/collision
        self.rect = self.image.get_rect(center=self.position)

        self.is_alive = True

        # Load sound effects
        self.armor_hit_sound = load_sound("assets/armor_hit.mp3")
        self.armor_break_sound = load_sound("assets/armor_break.mp3")

        # Shard effect properties for armor break
        self.shards = []  # List to store shard particles

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
            self.is_alive = False

    def update_orientation(self, direction_x, direction_y):
        """
        Rotate the image so that the beetle faces its moving direction.
        """
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def spawn_shards(self, count=10):
        """
        Spawn a burst of shards to simulate armor breaking.
        Each shard is represented as a dictionary with position, velocity, lifetime, and start_time.
        """
        for _ in range(count):
            shard = {
                'pos': [self.position[0], self.position[1]],
                'vel': [random.uniform(-3, 8), random.uniform(-3, 3)],
                'lifetime': random.randint(100, 600),  # lifetime in milliseconds
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3)
            }
            self.shards.append(shard)

    def update_shards(self, screen):
        """
        Update and render shard particles.
        """
        current_time = pygame.time.get_ticks()
        for shard in self.shards[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                self.shards.remove(shard)
            else:
                # Update position
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                # Fade out effect: alpha decreases over time
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (255, 255, 255, alpha)
                # Create a surface for the shard
                shard_surface = pygame.Surface((shard['radius']*2, shard['radius']*2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

    def render(self, screen: pygame.Surface):
        """
        Render the beetle on the given screen along with shard particles if any.
        """
        screen.blit(self.image, self.rect.topleft)
        # Render shard particles
        self.update_shards(screen)

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
            self.spawn_shards(count=15)

            # Instantly remove all armor layers
            self.current_armor_layer = 0
            self.current_layer_health = 0

            # Update the image to final damage state
            self.original_image = load_image("assets/beetle_damage3.png")
            self.image = self.original_image

            # Apply full damage to base health
            self.health -= damage
            if self.health <= 0:
                self.is_alive = False
            return  # Exit immediately to prevent normal armor processing

        # For every hit, play the armor hit sound if armor is present
        if self.current_armor_layer > 0:
            self.armor_hit_sound.play()

        # Normal damage processing (when not armor_break)
        if self.current_armor_layer > 0:
            self.current_layer_health -= damage
            if self.current_layer_health <= 0:
                overflow = -self.current_layer_health
                self.current_armor_layer -= 1

                # Spawn shards effect on armor layer break
                self.spawn_shards(count=10)

                # If breaking the last armor layer, play the armor break sound
                if self.current_armor_layer == 0:
                    self.armor_break_sound.play()

                # Update the image based on armor remaining
                if self.current_armor_layer == 2:
                    self.original_image = load_image("assets/beetle_damage1.png")
                elif self.current_armor_layer == 1:
                    self.original_image = load_image("assets/beetle_damage2.png")
                elif self.current_armor_layer == 0:
                    self.original_image = load_image("assets/beetle_damage3.png")
                self.image = self.original_image

                # Reset armor health unless all armor is broken
                if self.current_armor_layer > 0:
                    self.current_layer_health = 5

                # If there is overflow damage after breaking armor, apply it to health
                if self.current_armor_layer == 0 and overflow > 0:
                    self.health -= overflow
        else:
            # No armor remains; apply damage directly to base health.
            self.health -= damage

        if self.health <= 0:
            self.is_alive = False


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
        self.shards = []  # NEW: Particle storage

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

    # NEW: Shard particle methods (same as AntEnemy)
    def spawn_shards(self, count=10):
        for _ in range(count):
            shard = {
                'pos': [self.position[0], self.position[1]],
                'vel': [random.uniform(-5, 5), random.uniform(-5, 5)],
                'lifetime': random.randint(100, 600),
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3)
            }
            self.shards.append(shard)

    def update_shards(self, screen):
        current_time = pygame.time.get_ticks()
        for shard in self.shards[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                self.shards.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (255, 255, 255, alpha)
                shard_surface = pygame.Surface((shard['radius']*2, shard['radius']*2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, damage, projectile=None):
        global money
        self.health -= damage
        self.spawn_shards()  # NEW: Create particles on hit
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            money += 10

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)
        self.update_shards(screen)  # NEW: Render particles


class CentipedeEnemy:
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
            self.death_time = None  # time when the segment died
            self.rect = self.image.get_rect(center=position)

        def update_rect(self):
            self.rect = self.image.get_rect(center=self.position)

    def __init__(self, position, path, links=6):
        """
        :param position: Starting position (tuple)
        :param path: List of points (tuples) for the centipede head to follow.
        :param links: Number of link segments between the head and tail.
        """
        self.path = path
        self.current_target = 0  # Index in the path for head movement
        self.base_speed = 1
        self.speed = self.base_speed
        self.links = links

        # Load images
        head_img = load_image("assets/centipede_head.png")
        link_img = load_image("assets/centipede_link.png")
        tail_img = load_image("assets/centipede_tail.png")

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
        self.shards = []

    def spawn_shards(self, count=10):
        """
        Spawn a burst of shard particles to simulate a link breaking.
        """
        for _ in range(count):
            shard = {
                'pos': [self.position[0], self.position[1]],
                'vel': [random.uniform(-3, 8), random.uniform(-3, 3)],
                'lifetime': random.randint(100, 600),
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3)
            }
            self.shards.append(shard)

    def update_shards(self, screen):
        """
        Update and render shard particles.
        """
        current_time = pygame.time.get_ticks()
        for shard in self.shards[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                self.shards.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (255, 255, 255, alpha)
                shard_surface = pygame.Surface((shard['radius']*2, shard['radius']*2), pygame.SRCALPHA)
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
        global user_health

        # Adjust speed based on number of alive non-head segments.
        non_head_alive = sum(1 for seg in self.segments[1:] if seg.alive)
        if non_head_alive >= 4:
            self.speed = 1
        elif non_head_alive > 0:
            self.speed = 2
        else:
            self.speed = 3

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
            user_health -= head.health + tot_health * 2
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
                area_radius = getattr(projectile, "explosion_radius", 50)

        # Radial (area) damage branch.
        if area_center is not None and area_radius > 0:
            any_hit = False
            for seg in self.segments[1:][:]:
                if seg.alive:
                    seg_center = seg.rect.center
                    tolerance = seg.rect.width * 0.5
                    if math.hypot(seg_center[0] - area_center[0], seg_center[1] - area_center[1]) <= area_radius + tolerance:
                        seg.health -= damage
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
            if head.health <= 0:
                head.alive = False
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
                if seg.health <= 0:
                    seg.alive = False
                    seg.death_time = pygame.time.get_ticks()
                    self.spawn_shards(count=10)
                    self.remove_segment(seg)
                return  # Exit after damaging one segment

        # If no non-head segments are alive, apply damage to the head.
        head = self.segments[0]
        head.health -= damage
        if head.health <= 0:
            head.alive = False
            head.death_time = pygame.time.get_ticks()

    def remove_segment(self, seg):
        """
        Remove a destroyed segment and recalculate gap distances so that the remaining segments remain connected.
        """
        if seg in self.segments:
            self.segments.remove(seg)
            head_img = load_image("assets/centipede_head.png")
            link_img = load_image("assets/centipede_link.png")
            tail_img = load_image("assets/centipede_tail.png")
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
        self.update_shards(screen)




class Projectile:
    def __init__(self, position, target, speed, damage, image_path):
        self.position = list(position)
        self.target = target
        self.speed = speed * game_speed_multiplier  # Scaled at creation
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
