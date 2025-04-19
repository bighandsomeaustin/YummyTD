import pygame
from pygame import mixer
import math
import time
import random
import game_stats
import mainmenu
import merit_system
import save_manager

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
TowerFlag = False
BankruptFlag = False
curr_upgrade_tower = None
MogFlag = False
Autoplay = False
showFPS = False
showCursor = False
gameoverFlag = False
contFlag = False
winFlag = False
last_time_sfx = pygame.time.get_ticks()
# defaults
money = 350
user_health = 100
music_volume = 1.0
user_volume = 1.0
slider_dragging = False
game_speed_multiplier = 1  # Add at top with other globals
max_speed_multiplier = 2
last_frame_time = 0  # Track frame timing
global_damage_indicators = []
global_impact_particles = []

MAX_SHARDS = 500
MAX_INDICATORS = 500


class Shard:
    def __init__(self, pos, velocity, color=(255, 255, 255), radius=3, lifetime=30):
        self.pos = list(pos)
        self.velocity = velocity
        self.color = color
        self.radius = radius
        self.lifetime = lifetime

    def update(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)


def spawn_shard(pos, color=(255, 255, 255), count=5, speed=3, radius_range=(1, 3), lifetime_range=(100, 600)):
    global global_impact_particles
    if MAX_SHARDS <= 0:
        return

    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        velocity = [math.cos(angle) * random.randint(-1 * speed, speed), math.sin(angle) * random.randint(-1 * speed, speed)]
        shard = {
            'pos': [pos[0], pos[1]],
            'vel': velocity,
            'lifetime': random.randint(*lifetime_range),
            'start_time': pygame.time.get_ticks(),
            'radius': random.randint(*radius_range),
            'color': color
        }
        if len(global_impact_particles) < MAX_SHARDS:
            global_impact_particles.append(shard)


def update_shards(screen):
    current_time = pygame.time.get_ticks()
    for shard in global_impact_particles[:]:
        elapsed = current_time - shard['start_time']
        if elapsed > shard['lifetime']:
            global_impact_particles.remove(shard)
        else:
            shard['pos'][0] += shard['vel'][0]
            shard['pos'][1] += shard['vel'][1]
            alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
            base_color = shard.get('color', (255, 255, 255))
            color = (*base_color, alpha)
            surf = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (shard['radius'], shard['radius']), shard['radius'])
            screen.blit(surf, shard['pos'])


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


house_path_alternate = [(155, 168), (460, 172), (680, 174), (687, 294), (703, 340), (884, 344), (897, 476), (826, 515),
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
    return (1000 / 60) * (1 / game_speed_multiplier)  # Approximate frame delta


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
                    pygame.quit()
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
                else:
                    return True
    return True  # Valid placement


def apply_mantis_debuff(tower):
    current_time = pygame.time.get_ticks()
    # If not already stored, record the original shoot_interval.
    if "original_shoot_interval" not in tower.__dict__:
        tower.__dict__["original_shoot_interval"] = getattr(tower, "shoot_interval", 1000)
        print("Original shoot_interval set to", tower.__dict__["original_shoot_interval"])
    # Only apply the debuff if it isn’t already active.
    if not tower.__dict__.get("mantis_debuff_active", False):
        new_interval = tower.__dict__["original_shoot_interval"] * 2  # 50% slower.
        tower.__dict__["shoot_interval"] = new_interval
        print("Debuff applied: shoot_interval changed to", new_interval)
        # Update the tower's base shooting interval if it exists.
        if "_base_shoot_interval" in tower.__dict__:
            tower.__dict__["_base_shoot_interval"] = new_interval
        # Reset the firing timer.
        tower.__dict__["last_shot_time"] = current_time
        tower.__dict__["mantis_debuff_active"] = True
        tower.__dict__["mantis_debuff_end_time"] = current_time + 15000
        tower.__dict__["mantis_debuff_applied_time"] = current_time
        tower.__dict__["mantis_debuff_active"] = True


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
        , gameoverFlag, enemies, current_wave, user_health, game_speed_multiplier, Autoplay, max_speed_multiplier, TowerFlag, \
        BankruptFlag, winFlag, contFlag

    purchase = load_sound("assets/purchase_sound.mp3")
    invalid = load_sound("assets/invalid.mp3")
    img_tower_select = load_image("assets/tower_select.png")
    img_mrcheese_text = load_image("assets/mrcheese_text.png")
    img_ratcamp_text = load_image("assets/ratcamp_text.png")
    img_ratbank_text = load_image("assets/ratbank_text.png")
    img_ozbourne_text = load_image("assets/ozbourne_text.png")
    img_commando_text = load_image("assets/commando_text.png")
    img_minigun_text = load_image("assets/minigun_text.png")
    img_wizard_text = load_image("assets/wizard_text.png")
    img_beacon_text = load_image("assets/beacon_text.png")
    img_sniper_text = load_image("assets/sniper_text.png")
    img_frost_text = load_image("assets/frost_text.png")
    img_ratman_text = load_image("assets/ratman_text.png")
    img_mortar_text = load_image("assets/mortar_text.png")
    img_playbutton = load_image("assets/playbutton.png")
    img_playbutton_1x = load_image("assets/playbutton_1x.png")
    img_playbutton_2x = load_image("assets/playbutton_2x.png")
    img_settingsbutton = load_image("assets/settingsbutton.png")
    img_settings_window = load_image("assets/ingame_settings.png")
    img_music_slider = load_image("assets/music_slider.png")
    autoplay_check = load_image("assets/autoplay_checked.png")
    img_bankrupt = load_image("assets/bankrupt_window.png")
    img_win = load_image("assets/win_window.png")

    mouse = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]

    # Slider boundaries: x from 400 (0%) to 736 (100%) and fixed y
    slider_min = 400
    slider_max = 736
    slider_y = 421
    slider_height = 18

    # Calculate slider x based on music_volume (0.0 to 1.0)
    slider_x = slider_min + user_volume * (slider_max - slider_min)

    TowerFlag = False

    # bankruptcy window
    if BankruptFlag:
        scrn.blit(img_bankrupt, (0, 0))
        if 964 <= mouse[0] <= 964 + 34 and 100 <= mouse[1] <= 100 + 57:
            if detect_single_click():
                BankruptFlag = False

    if user_health <= 0 and not gameoverFlag:
        pygame.mixer.stop()
        SettingsFlag = False
        contFlag = False
        save_manager.wipe_save()
        game_stats.global_kill_total["count"] = 0
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

    if current_wave == 100 and not winFlag and not contFlag:
        winFlag = True

    if winFlag:
        scrn.blit(img_win, (0, 0))
        if 392 <= mouse[0] <= 392 + 194 and 367 <= mouse[1] <= 367 + 113:
            if detect_single_click():
                winFlag = False
                contFlag = True
        if 693 <= mouse[0] <= 693 + 194 and 367 <= mouse[1] <= 367 + 113:
            if detect_single_click():
                winFlag = False
                contFlag = False
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
                TowerFlag = False
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
                game_speed_multiplier = max_speed_multiplier if game_speed_multiplier == 1 else 1

    # settings button
    scrn.blit(img_settingsbutton, (1192, 665))
    if 1192 <= mouse[0] <= 1192 + 81 and 665 <= mouse[1] <= 665 + 50:
        if detect_single_click():
            SettingsFlag = True

    if SettingsFlag:
        scrn.blit(img_settings_window, (0, 0))
        scrn.blit(img_music_slider, (slider_x, slider_y))
        if Autoplay:
            scrn.blit(autoplay_check, (386, 245))
        # slider range - 400 (0%) to 736 (100%)
        if 766 <= mouse[0] <= 766 + 15 and 205 <= mouse[1] <= 205 + 18:
            if detect_single_click():
                SettingsFlag = False
                save_manager.save_settings(MAX_SHARDS, MAX_INDICATORS,
                                           max_speed_multiplier, showFPS, showCursor,
                                           user_volume, mainmenu.FullscreenFlag)
        if 306 <= mouse[0] <= 306 + 199 and 286 <= mouse[1] <= 286 + 114:
            if detect_single_click():
                SettingsFlag = False
                save_manager.save_settings(MAX_SHARDS, MAX_INDICATORS,
                                           max_speed_multiplier, showFPS, showCursor,
                                           user_volume, mainmenu.FullscreenFlag)
                return "saveandquit"
        if 387 <= mouse[0] <= 387 + 30 and 247 <= mouse[1] <= 247 + 30:
            if detect_single_click():
                if not Autoplay:
                    Autoplay = True
                elif Autoplay:
                    Autoplay = False
        if 550 <= mouse[0] <= 550 + 199 and 286 <= mouse[1] <= 286 + 114:
            if detect_single_click():
                SettingsFlag = False
                save_manager.save_settings(MAX_SHARDS, MAX_INDICATORS,
                                           max_speed_multiplier, showFPS, showCursor,
                                           user_volume, mainmenu.FullscreenFlag)
                return "quit"
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
        if detect_single_click():
            if money >= 150:
                purchase.play()
                return "mrcheese"
            else:
                invalid.play()

    # COLBY FROST
    elif 1195 <= mouse[0] <= 1195 + 73 and 101 <= mouse[1] <= 101 + 88:
        scrn.blit(img_frost_text, (1113, 53))
        scrn.blit(img_tower_select, (1195, 101))
        if detect_single_click():
            if money >= 200:
                purchase.play()
                return "frost"
            else:
                invalid.play()

    # RAT CAMP
    elif 1195 <= mouse[0] <= 1195 + 73 and 288 <= mouse[1] <= 288 + 88:
        scrn.blit(img_ratcamp_text, (1113, 53))
        scrn.blit(img_tower_select, (1192, 288))
        if detect_single_click():
            if money >= 650:
                purchase.play()
                return "rattent"
            else:
                invalid.play()

    # CHEESY OZBOURNE
    elif 1118 <= mouse[0] <= 1118 + 73 and 382 <= mouse[1] <= 382 + 88:
        scrn.blit(img_ozbourne_text, (1113, 53))
        scrn.blit(img_tower_select, (1118, 382))
        if detect_single_click():
            if money >= 500:
                purchase.play()
                return "ozbourne"
            else:
                invalid.play()

    # RAT BANK
    elif 1195 <= mouse[0] <= 1195 + 73 and 382 <= mouse[1] <= 382 + 88:
        scrn.blit(img_ratbank_text, (1113, 53))
        scrn.blit(img_tower_select, (1195, 382))
        if detect_single_click():
            if money >= 700:
                purchase.play()
                return "ratbank"
            else:
                invalid.play()

    # CHEDDAR COMMANDO
    elif 1195 <= mouse[0] <= 1195 + 73 and 195 <= mouse[1] <= 195 + 88:
        scrn.blit(img_commando_text, (1113, 53))
        scrn.blit(img_tower_select, (1195, 195))
        if detect_single_click():
            if money >= 250:
                purchase.play()
                return "soldier"
            else:
                invalid.play()

    # MINIGUN
    elif 1118 <= mouse[0] <= 1118 + 73 and 475 <= mouse[1] <= 475 + 88:
        scrn.blit(img_minigun_text, (1113, 53))
        scrn.blit(img_tower_select, (1118, 475))
        if detect_single_click():
            if money >= 600:
                purchase.play()
                return "minigun"
            else:
                invalid.play()

    # WIZARD
    elif 1118 <= mouse[0] <= 1118 + 73 and 288 <= mouse[1] <= 288 + 88:
        scrn.blit(img_wizard_text, (1113, 53))
        scrn.blit(img_tower_select, (1118, 288))
        if detect_single_click():
            if money >= 400:
                purchase.play()
                return "wizard"
            else:
                invalid.play()

    # CHEESE BEACON
    elif 1195 <= mouse[0] <= 1195 + 73 and 475 <= mouse[1] <= 475 + 88:
        scrn.blit(img_beacon_text, (1113, 53))
        scrn.blit(img_tower_select, (1195, 475))
        if detect_single_click():
            if money >= 1400:
                purchase.play()
                return "beacon"
            else:
                invalid.play()

    # RAT SNIPER
    elif 1118 <= mouse[0] <= 1118 + 73 and 195 <= mouse[1] <= 195 + 88:
        scrn.blit(img_sniper_text, (1113, 53))
        scrn.blit(img_tower_select, (1118, 195))
        if detect_single_click():
            if money >= 350:
                purchase.play()
                return "sniper"
            else:
                invalid.play()

    # RATMAN
    elif 1118 <= mouse[0] <= 1118 + 73 and 567 <= mouse[1] <= 567 + 88:
        scrn.blit(img_ratman_text, (1113, 53))
        scrn.blit(img_tower_select, (1118, 567))
        if detect_single_click():
            if money >= 2600:
                purchase.play()
                return "ratman"
            else:
                invalid.play()

    # MORTAR
    elif 1195 <= mouse[0] <= 1195 + 73 and 567 <= mouse[1] <= 567 + 88:
        scrn.blit(img_mortar_text, (1113, 53))
        scrn.blit(img_tower_select, (1195, 567))
        if detect_single_click():
            if money >= 1500:
                purchase.play()
                return "mortar"
            else:
                invalid.play()

    for tower in towers:
        tower_rect = tower.image.get_rect(center=tower.position)

        # Only do any tower‐click selection/deselection when NOT placing a new one:
        if not TowerFlag:
            # select a tower (or mortar) for upgrades/target‐dragging
            if tower_rect.collidepoint(mouse) and detect_single_click():
                if isinstance(tower, (RatBank, MortarStrike)):
                    tower.is_selected = True
                UpgradeFlag = True
                curr_upgrade_tower = tower

            # deselect the mortar if you click outside both its base and its marker
            if isinstance(tower, MortarStrike) and tower.is_selected and detect_single_click():
                marker_rect = tower.target_image.get_rect(center=tower.target_pos)
                if not (marker_rect.collidepoint(mouse) or tower_rect.collidepoint(mouse)):
                    tower.is_selected = False
                    UpgradeFlag = True


    if UpgradeFlag and not TowerFlag:
        handle_upgrade(scrn, curr_upgrade_tower)
    return "NULL"


def blit_text(scrn, text, choice):
    font = get_font("arial", 16)
    if choice == "top":
        rect = pygame.Rect(897, 39, 193, 24)
    elif choice == "bottom":
        rect = pygame.Rect(897, 170, 193, 24)
    else:
        rect = pygame.Rect(897, 170, 193, 24)
    text_surface = font.render(text, True, (0, 0, 0))
    text_rect = text_surface.get_rect(center=rect.center)
    scrn.blit(text_surface, text_rect)


def handle_upgrade(scrn, tower):
    global UpgradeFlag, money, MogFlag, TowerFlag, BankruptFlag
    TowerFlag = False
    mouse = pygame.mouse.get_pos()
    purchase = load_sound("assets/purchase_sound.mp3")
    img_upgrade_window = load_image("assets/upgrade_window.png")
    img_upgrade_highlighted = load_image("assets/upgrade_window_highlighted.png")
    img_max_upgrades = load_image("assets/upgrade_max.png")
    img_sell_button = load_image("assets/sell_button.png")
    img_bankrupt_button = load_image("assets/bunkrupt_button.png")
    upgrade_font = get_font("arial", 16)
    # cleaner bounds
    top = (883, 65)
    bottom = (883, 194)
    scrn.blit(img_upgrade_window, (882, 0))
    if isinstance(tower, RatBank):
        if tower.briefundFlag or tower.provoloanFlag:
            scrn.blit(img_bankrupt_button, (947, 298))
        else:
            scrn.blit(img_sell_button, (997, 298))
            text_sell = upgrade_font.render(f"SELL: ${tower.sell_amt}", True, (255, 255, 255))
            scrn.blit(text_sell, (1015, 306))
    else:
        scrn.blit(img_sell_button, (997, 298))
        text_sell = upgrade_font.render(f"SELL: ${tower.sell_amt}", True, (255, 255, 255))
        scrn.blit(text_sell, (1015, 306))
    if isinstance(tower, MrCheese):
        img_booksmart_upgrade = load_image("assets/upgrade_booksmart.png")
        img_protein_upgrade = load_image("assets/upgrade_protein.png")
        img_diploma_upgrade = load_image("assets/upgrade_diploma.png")
        img_steroids_upgrade = load_image("assets/upgrade_culture_injection.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_booksmart_upgrade, (883, 65))
            blit_text(scrn, "Book Smart", "top")
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_diploma_upgrade, (883, 65))
            blit_text(scrn, "College Diploma", "top")
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_protein_upgrade, (883, 194))
            blit_text(scrn, "Protein 9000", "bottom")
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
            scrn.blit(img_steroids_upgrade, (883, 194))
            blit_text(scrn, "Culture Injection", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)

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
                    tower.radius += 50
                    tower.shoot_interval -= 250
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/mrcheese_booksmart.png"
                        tower.image = load_image("assets/mrcheese_booksmart.png")
                        tower.original_image = load_image("assets/mrcheese_booksmart.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/mrcheese_booksmart+protein.png"
                        tower.image = load_image("assets/mrcheese_booksmart+protein.png")
                        tower.original_image = load_image("assets/mrcheese_booksmart+protein.png")
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image_path = "assets/mrcheese_steroids+booksmart.png"
                        tower.image = load_image("assets/mrcheese_steroids+booksmart.png")
                        tower.original_image = load_image("assets/mrcheese_steroids+booksmart.png")
                elif money >= 1200 and tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade != 2:
                    purchase.play()
                    money -= 1200
                    tower.sell_amt += 600
                    tower.radius += 50
                    tower.shoot_interval -= 500
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/mrcheese_diploma.png"
                        tower.image = load_image("assets/mrcheese_diploma.png")
                        tower.original_image = load_image("assets/mrcheese_diploma.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/mrcheese_diploma+protein.png"
                        tower.image = load_image("assets/mrcheese_diploma+protein.png")
                        tower.original_image = load_image("assets/mrcheese_diploma+protein.png")
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                if money >= 450 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    tower.damage += 1
                    money -= 450
                    tower.sell_amt += 225
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/mrcheese_protein.png"
                        tower.image = load_image("assets/mrcheese_protein.png")
                        tower.original_image = load_image("assets/mrcheese_protein.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/mrcheese_booksmart+protein.png"
                        tower.image = load_image("assets/mrcheese_booksmart+protein.png")
                        tower.original_image = load_image("assets/mrcheese_booksmart+protein.png")
                    elif tower.curr_top_upgrade == 2:
                        tower.image_path = "assets/mrcheese_diploma+protein.png"
                        tower.image = load_image("assets/mrcheese_diploma+protein.png")
                        tower.original_image = load_image("assets/mrcheese_diploma+protein.png")
                elif money >= 900 and tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade != 2:
                    purchase.play()
                    tower.damage += 1
                    tower.penetration = True
                    money -= 900
                    tower.sell_amt += 450
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    MogFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/mrcheese_steroids.png"
                        tower.image = load_image("assets/mrcheese_steroids.png")
                        tower.original_image = load_image("assets/mrcheese_steroids.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/mrcheese_steroids+booksmart.png"
                        tower.image = load_image("assets/mrcheese_steroids+booksmart.png")
                        tower.original_image = load_image("assets/mrcheese_steroids+booksmart.png")
    if isinstance(tower, RatTent):
        img_fasterrats_upgrade = load_image("assets/upgrade_fasterrats.png")
        img_strongrats_upgrade = load_image("assets/upgrade_strongerrats.png")
        img_freak_upgrade = load_image("assets/upgrade_freak.png")
        img_army_upgrade = load_image("assets/upgrade_army.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_fasterrats_upgrade, (883, 65))
            blit_text(scrn, "Faster Rats", "top")
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            blit_text(scrn, "Task Force Cheese", "top")
            scrn.blit(img_army_upgrade, (883, 65))
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_strongrats_upgrade, (883, 194))
            blit_text(scrn, "Stronger Rats", "bottom")
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
            scrn.blit(img_freak_upgrade, (883, 194))
            blit_text(scrn, "Freak Release", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                if tower.curr_top_upgrade == 0 and money >= 1250:
                    purchase.play()
                    money -= 1250
                    tower.sell_amt += 625
                    tower.recruit_speed += 1
                    tower.spawn_interval -= 750
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/camp_faster.png"
                        tower.image = load_image("assets/camp_faster.png")
                        tower.original_image = load_image("assets/camp_faster.png")
                        tower.recruit_image = "assets/rat_recruit_faster.png"
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/camp_stronger+faster.png"
                        tower.image = load_image("assets/camp_stronger+faster.png")
                        tower.original_image = load_image("assets/camp_stronger+faster.png")
                        tower.recruit_image = "assets/rat_recruit_stronger+faster.png"
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image_path = "assets/camp_stronger+faster.png"
                        tower.image = load_image("assets/camp_stronger+faster.png")
                        tower.original_image = load_image("assets/camp_stronger+faster.png")

                elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2 and money >= 1500:
                    purchase.play()
                    money -= 1500
                    tower.sell_amt += 750
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True

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
                    tower.recruit_health += 1
                    money -= 1000
                    tower.sell_amt += 500
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/camp_stronger.png"
                        tower.image = load_image("assets/camp_stronger.png")
                        tower.original_image = load_image("assets/camp_stronger.png")
                        tower.recruit_image = "assets/rat_recruit_stronger.png"
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/camp_stronger+faster.png"
                        tower.image = load_image("assets/camp_stronger+faster.png")
                        tower.original_image = load_image("assets/camp_stronger+faster.png")

                elif money >= 2200 and tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
                    purchase.play()
                    money -= 2200
                    tower.sell_amt += 1100
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True

    if isinstance(tower, Ozbourne):
        img_amplifier_upgrade = load_image("assets/upgrade_amplifier.png")
        img_longerriffs_upgrade = load_image("assets/upgrade_longerriffs.png")
        img_watts_upgrade = load_image("assets/upgrade_watts.png")
        img_solo_upgrade = load_image("assets/upgrade_solo.png")
        upgrade_font = get_font("arial", 16)
        text_faster = upgrade_font.render("Amplifier", True, (0, 0, 0))
        text_stronger = upgrade_font.render("Longer Riffs", True, (0, 0, 0))
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_amplifier_upgrade, (883, 65))
            scrn.blit(text_faster, (962, 42))
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_watts_upgrade, (883, 65))
            blit_text(scrn, "One Million Wats", "top")
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_longerriffs_upgrade, (883, 194))
            scrn.blit(text_stronger, (962, 172))
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
            scrn.blit(img_solo_upgrade, (883, 194))
            blit_text(scrn, "Guitar Solo", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)

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
                        tower.image_path = "assets/alfredo_ozbourne_amplifier.png"
                        tower.image = load_image("assets/alfredo_ozbourne_amplifier.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_amplifier.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/alfredo_ozbourne_longer_riffs+amplifier.png"
                        tower.image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                elif tower.curr_top_upgrade == 1 and money >= 850 and tower.curr_bottom_upgrade < 2:
                    purchase.play()
                    money -= 850
                    tower.sell_amt += 425
                    tower.riff_blast_radius = 150
                    tower.radius = 150
                    tower.max_blast_radius = 150
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                mixer.music.load("assets/map_music.mp3")
                mixer.music.play(-1)
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
                        tower.image_path = "assets/alfredo_ozbourne_longer_riffs.png"
                        tower.image = load_image("assets/alfredo_ozbourne_longer_riffs.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_longer_riffs.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/alfredo_ozbourne_longer_riffs+amplifier.png"
                        tower.image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                        tower.original_image = load_image("assets/alfredo_ozbourne_longer_riffs+amplifier.png")
                        tower.recruit_image = "assets/alfredo_ozbourne_longer_riffs+amplifier.png"
                elif money >= 1850 and tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
                    purchase.play()
                    money -= 1850
                    tower.sell_amt += 925
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
    if isinstance(tower, RatBank):
        img_credit_upgrade = load_image("assets/upgrade_better_credit.png")
        img_cheesefargo_upgrade = load_image("assets/upgrade_cheese_fargo.png")
        img_import_upgrade = load_image("assets/upgrade_imports.png")
        img_gouda_upgrade = load_image("assets/upgrade_gouda.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_credit_upgrade, (883, 65))
            blit_text(scrn, "715 Credit Score", "top")
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_import_upgrade, top)
            blit_text(scrn, "Cheddar Imports", "top")
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_gouda_upgrade, bottom)
            blit_text(scrn, "Gouda Investments", "bottom")
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
            scrn.blit(img_cheesefargo_upgrade, bottom)
            blit_text(scrn, "Cheese Fargo", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)

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
                    if tower.curr_bottom_upgrade < 2:
                        tower.image_path = "assets/rat_bank_fargo.png"
                        tower.image = load_image("assets/rat_bank_fargo.png")
                        tower.original_image = load_image("assets/rat_bank_fargo.png")
                elif tower.curr_top_upgrade == 1 and money >= 400 and tower.curr_bottom_upgrade < 2:
                    purchase.play()
                    money -= 400
                    tower.sell_amt += 200
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    tower.image_path = "assets/rat_bank_imports.png"
                    tower.image = load_image("assets/rat_bank_imports.png")
                    tower.original_image = load_image("assets/rat_bank_imports.png")

        # bankruptcy handling
        if 947 <= mouse[0] <= 947 + 150 and 298 <= mouse[1] <= 298 + 35:
            if tower.briefundFlag or tower.provoloanFlag:
                if detect_single_click():
                    # pull all money out of bank
                    money += tower.sell_amt
                    money += tower.cash_generated
                    money += tower.cash_invested
                    money -= int(tower.loan_amount)
                    # make bankrupt window appear
                    towers.remove(tower)
                    UpgradeFlag = False
                    BankruptFlag = True
                    return

        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if not tower.briefundFlag and not tower.provoloanFlag:
                if detect_single_click():
                    money += tower.sell_amt
                    money += tower.cash_generated
                    money += tower.cash_invested
                    towers.remove(tower)
                    UpgradeFlag = False
                    return

        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                if money >= 1600 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    money -= 1600
                    tower.sell_amt += 800
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True

                elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2 and money >= 1200:
                    purchase.play()
                    money -= 1200
                    tower.sell_amt += 600
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    tower.image_path = "assets/rat_bank_fargo_skyscraper.png"
                    tower.image = load_image("assets/rat_bank_fargo_skyscraper.png")
                    tower.original_image = load_image("assets/rat_bank_fargo_skyscraper.png")
    if isinstance(tower, MinigunTower):
        img_fasterspool_upgrade = load_image("assets/upgrade_faster_spool.png")
        img_biggermags_upgrade = load_image("assets/upgrade_bigger_mags.png")
        img_twinguns_upgrade = load_image("assets/upgrade_twinguns.png")
        img_flamebullets_upgrade = load_image("assets/upgrade_flame.png")
        img_deathray_upgrade = load_image("assets/upgrade_deathray.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_fasterspool_upgrade, (883, 65))
            blit_text(scrn, "Faster Spool", "top")
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_biggermags_upgrade, (883, 65))
            blit_text(scrn, "Bigger Mags", "top")
        elif tower.curr_top_upgrade == 2 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_twinguns_upgrade, (883, 65))
            blit_text(scrn, "Twin Guns", "top")
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_flamebullets_upgrade, (883, 194))
            blit_text(scrn, "Flaming Fromage", "bottom")
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
            scrn.blit(img_deathray_upgrade, (883, 194))
            blit_text(scrn, "Death Ray", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)
        # TOP UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # faster spool
                if tower.curr_top_upgrade == 0 and money >= 400:
                    purchase.play()
                    money -= 400
                    tower.sell_amt += 200
                    tower.max_spool += 10
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/minigun_faster_spool.png"
                        tower.image = load_image("assets/minigun_faster_spool.png")
                        tower.original_image = load_image("assets/minigun_faster_spool.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/minigun_faster_spool+flame.png"
                        tower.image = load_image("assets/minigun_faster_spool+flame.png")
                        tower.original_image = load_image("assets/minigun_faster_spool+flame.png")
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image_path = "assets/minigun_deathray+faster_spool.png"
                        tower.image = load_image("assets/minigun_deathray+faster_spool.png")
                        tower.original_image = load_image("assets/minigun_deathray+faster_spool.png")
                # bigger mags
                elif tower.curr_top_upgrade == 1 and money >= 350:
                    purchase.play()
                    money -= 350
                    tower.sell_amt += 175
                    tower.base_magazine = 120
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/minigun_bigger_mags.png"
                        tower.image = load_image("assets/minigun_bigger_mags.png")
                        tower.original_image = load_image("assets/minigun_bigger_mags.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/minigun_bigger_mags+flame.png"
                        tower.image = load_image("assets/minigun_bigger_mags+flame.png")
                        tower.original_image = load_image("assets/minigun_bigger_mags+flame.png")
                # twin guns
                elif tower.curr_top_upgrade == 2 and money >= 1250:
                    purchase.play()
                    money -= 1250
                    tower.sell_amt += 625
                    tower.magazine_size = 240
                    tower.max_spool *= 2
                    tower.damage += 1
                    tower.reload_time *= 2
                    tower.curr_top_upgrade = 3
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/minigun_twin_guns.png"
                        tower.image = load_image("assets/minigun_twin_guns.png")
                        tower.original_image = load_image("assets/minigun_twin_guns.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/minigun_twin_guns+flame.png"
                        tower.image = load_image("assets/minigun_twin_guns+flame.png")
                        tower.original_image = load_image("assets/minigun_twin_guns+flame.png")
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        # BOTTOM UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # flaming fromage
                if tower.curr_bottom_upgrade == 0 and money >= 550:
                    purchase.play()
                    money -= 550
                    tower.sell_amt += 275
                    tower.damage = 1.5
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/minigun_flamebullets.png"
                        tower.image = load_image("assets/minigun_flamebullets.png")
                        tower.original_image = load_image("assets/minigun_flamebullets.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/minigun_faster_spool+flame.png"
                        tower.image = load_image("assets/minigun_faster_spool+flame.png")
                        tower.original_image = load_image("assets/minigun_faster_spool+flame.png")
                    elif tower.curr_top_upgrade == 2:
                        tower.image_path = "assets/minigun_bigger_mags+flame.png"
                        tower.image = load_image("assets/minigun_bigger_mags+flame.png")
                        tower.original_image = load_image("assets/minigun_bigger_mags+flame.png")
                    elif tower.curr_top_upgrade == 3:
                        tower.image_path = "assets/minigun_twin_guns+flame.png"
                        tower.image = load_image("assets/minigun_twin_guns+flame.png")
                        tower.original_image = load_image("assets/minigun_twin_guns+flame.png")
                # death ray
                elif tower.curr_bottom_upgrade == 1 and money >= 2500 and tower.curr_top_upgrade < 2:
                    purchase.play()
                    money -= 2500
                    tower.sell_amt += 1250
                    tower.spool_rate = 70.0
                    tower.max_spool = 70
                    tower.damage = 0.2
                    tower.radius = 175
                    tower.reload_time = 0.1
                    tower.cooldown_rate = 0.0
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/minigun_deathray.png"
                        tower.image = load_image("assets/minigun_deathray.png")
                        tower.original_image = load_image("assets/minigun_deathray.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/minigun_deathray+faster_spool.png"
                        tower.image = load_image("assets/minigun_deathray+faster_spool.png")
                        tower.original_image = load_image("assets/minigun_deathray+faster_spool.png")
    if isinstance(tower, RatSniper):
        img_collateral_upgrade = load_image("assets/upgrade_collateral.png")
        img_50cal_upgrade = load_image("assets/upgrade_powerful.png")
        img_chain_upgrade = load_image("assets/upgrade_collateral_chain.png")
        img_rechamber_upgrade = load_image("assets/upgrade_rechambering.png")
        img_semiauto_upgrade = load_image("assets/upgrade_semiauto.png")
        img_fmj_upgrade = load_image("assets/upgrade_fmj.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_collateral_upgrade, (883, 65))
            blit_text(scrn, "Collateral Hits", "top")
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_50cal_upgrade, (883, 65))
            blit_text(scrn, "50cal Rounds", "top")
        elif tower.curr_top_upgrade == 2 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_chain_upgrade, (883, 65))
            blit_text(scrn, "Collateral Chain", "top")
        else:
            scrn.blit(img_max_upgrades, top)
        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_rechamber_upgrade, (883, 194))
            blit_text(scrn, "Fast Rechambering", "bottom")
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
            scrn.blit(img_semiauto_upgrade, (883, 194))
            blit_text(scrn, "FMJ Rounds", "bottom")
        elif tower.curr_bottom_upgrade == 2 and tower.curr_top_upgrade < 2:
            scrn.blit(img_fmj_upgrade, (883, 194))
            blit_text(scrn, "Semi-Automatic", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)
        # TOP UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # collateral
                if tower.curr_top_upgrade == 0 and money >= 600:
                    purchase.play()
                    money -= 600
                    tower.sell_amt += 300
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/sniper+collateral.png"
                        tower.image_path_shoot = "assets/sniper+collateral_shoot.png"
                        tower.image = load_image("assets/sniper+collateral.png")
                        tower.base_image = load_image("assets/sniper+collateral.png")
                        tower.shoot_image = load_image("assets/sniper+collateral_shoot.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/sniper+collateral+rechamber.png"
                        tower.image_path_shoot = "assets/sniper+collateral+rechamber_shoot.png"
                        tower.image = load_image("assets/sniper+collateral+rechamber.png")
                        tower.base_image = load_image("assets/sniper+collateral+rechamber.png")
                        tower.shoot_image = load_image("assets/sniper+collateral+rechamber_shoot.png")
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image_path = "assets/sniper+collateral+semiauto.png"
                        tower.image_path_shoot = "assets/sniper+collateral+semiauto_shoot.png"
                        tower.image = load_image("assets/sniper+collateral+semiauto.png")
                        tower.base_image = load_image("assets/sniper+collateral+semiauto.png")
                        tower.shoot_image = load_image("assets/sniper+collateral+semiauto_shoot.png")
                    elif tower.curr_bottom_upgrade == 3:
                        tower.image_path = "assets/sniper+collateral+fmj.png"
                        tower.image_path_shoot = "assets/sniper+collateral+fmj_shoot.png"
                        tower.image = load_image("assets/sniper+collateral+fmj.png")
                        tower.base_image = load_image("assets/sniper+collateral+fmj.png")
                        tower.shoot_image = load_image("assets/sniper+collateral+fmj_shoot.png")
                # 50cal
                elif tower.curr_top_upgrade == 1 and money >= 1200 and tower.curr_bottom_upgrade < 2:
                    purchase.play()
                    money -= 1200
                    tower.sell_amt += 600
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/sniper+50cal.png"
                        tower.image_path_shoot = "assets/sniper+50cal_shoot.png"
                        tower.image = load_image("assets/sniper+50cal.png")
                        tower.base_image = load_image("assets/sniper+50cal.png")
                        tower.shoot_image = load_image("assets/sniper+50cal_shoot.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/sniper+50cal+rechamber.png"
                        tower.image_path_shoot = "assets/sniper+50cal+rechamber_shoot.png"
                        tower.image = load_image("assets/sniper+50cal+rechamber.png")
                        tower.base_image = load_image("assets/sniper+50cal+rechamber.png")
                        tower.shoot_image = load_image("assets/sniper+50cal+rechamber_shoot.png")
                # chain collateral
                elif tower.curr_top_upgrade == 2 and money >= 1500 and tower.curr_bottom_upgrade < 2:
                    purchase.play()
                    money -= 1500
                    tower.sell_amt += 750
                    tower.curr_top_upgrade = 3
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/sniper+hollowpoint.png"
                        tower.image_path_shoot = "assets/sniper+hollowpoint_shoot.png"
                        tower.image = load_image("assets/sniper+hollowpoint.png")
                        tower.base_image = load_image("assets/sniper+hollowpoint.png")
                        tower.shoot_image = load_image("assets/sniper+hollowpoint_shoot.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/sniper+hollowpoint+rechamber.png"
                        tower.image_path_shoot = "assets/sniper+hollowpoint+rechamber_shoot.png"
                        tower.image = load_image("assets/sniper+hollowpoint+rechamber.png")
                        tower.base_image = load_image("assets/sniper+hollowpoint+rechamber.png")
                        tower.shoot_image = load_image("assets/sniper+hollowpoint+rechamber_shoot.png")
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        # BOTTOM UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # rechamber
                if tower.curr_bottom_upgrade == 0 and money >= 1500:
                    purchase.play()
                    money -= 1500
                    tower.sell_amt += 750
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/sniper+rechamber.png"
                        tower.image_path_shoot = "assets/sniper+rechamber_shoot.png"
                        tower.image = load_image("assets/sniper+rechamber.png")
                        tower.base_image = load_image("assets/sniper+rechamber.png")
                        tower.shoot_image = load_image("assets/sniper+rechamber_shoot.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/sniper+collateral+rechamber.png"
                        tower.image_path_shoot = "assets/sniper+collateral+rechamber_shoot.png"
                        tower.image = load_image("assets/sniper+collateral+rechamber.png")
                        tower.base_image = load_image("assets/sniper+collateral+rechamber.png")
                        tower.shoot_image = load_image("assets/sniper+collateral+rechamber_shoot.png")
                    elif tower.curr_top_upgrade == 2:
                        tower.image_path = "assets/sniper+50cal+rechamber.png"
                        tower.image_path_shoot = "assets/sniper+50cal+rechamber_shoot.png"
                        tower.image = load_image("assets/sniper+50cal+rechamber.png")
                        tower.base_image = load_image("assets/sniper+50cal+rechamber.png")
                        tower.shoot_image = load_image("assets/sniper+50cal+rechamber_shoot.png")
                    elif tower.curr_top_upgrade == 3:
                        tower.image_path = "assets/sniper+hollowpoint+rechamber.png"
                        tower.image_path_shoot = "assets/sniper+hollowpoint+rechamber_shoot.png"
                        tower.image = load_image("assets/sniper+hollowpoint+rechamber.png")
                        tower.base_image = load_image("assets/sniper+hollowpoint+rechamber.png")
                        tower.shoot_image = load_image("assets/sniper+hollowpoint+rechamber_shoot.png")
                # semiauto
                elif tower.curr_bottom_upgrade == 1 and money >= 2000 and tower.curr_top_upgrade < 2:
                    purchase.play()
                    money -= 2000
                    tower.sell_amt += 1000
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/sniper+semiauto.png"
                        tower.image_path_shoot = "assets/sniper+semiauto_shoot.png"
                        tower.image = load_image("assets/sniper+semiauto.png")
                        tower.base_image = load_image("assets/sniper+semiauto.png")
                        tower.shoot_image = load_image("assets/sniper+semiauto_shoot.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/sniper+collateral+semiauto.png"
                        tower.image_path_shoot = "assets/sniper+collateral+semiauto_shoot.png"
                        tower.image = load_image("assets/sniper+collateral+semiauto.png")
                        tower.base_image = load_image("assets/sniper+collateral+semiauto.png")
                        tower.shoot_image = load_image("assets/sniper+collateral+semiauto_shoot.png")
                # semiauto
                elif tower.curr_bottom_upgrade == 2 and money >= 1500 and tower.curr_top_upgrade < 2:
                    purchase.play()
                    money -= 1500
                    tower.sell_amt += 750
                    tower.curr_bottom_upgrade = 3
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/sniper+fmj.png"
                        tower.image_path_shoot = "assets/sniper+fmj_shoot.png"
                        tower.image = load_image("assets/sniper+fmj.png")
                        tower.base_image = load_image("assets/sniper+fmj.png")
                        tower.shoot_image = load_image("assets/sniper+fmj_shoot.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/sniper+collateral+fmj.png"
                        tower.image_path_shoot = "assets/sniper+collateral+fmj_shoot.png"
                        tower.image = load_image("assets/sniper+collateral+fmj.png")
                        tower.base_image = load_image("assets/sniper+collateral+fmj.png")
                        tower.shoot_image = load_image("assets/sniper+collateral+fmj_shoot.png")
    if isinstance(tower, RatFrost):
        # top upgrades
        img_snowball_upgrade = load_image("assets/upgrade_snowball.png")
        img_deadly_snowballs_upgrade = load_image("assets/upgrade_deadly_snowballs.png")
        img_snowball_barrage_upgrade = load_image("assets/upgrade_snowball_barrage.png")
        # bottom upgrades
        img_freeze_radius_upgrade = load_image("assets/upgrade_freeze_radius.png")
        img_snow_flurry_upgrade = load_image("assets/upgrade_snow_flurry.png")
        img_freezing_temps_upgrade = load_image("assets/upgrade_freezing_temps.png")

        # show upgrade images
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_snowball_upgrade, (883, 65))
            blit_text(scrn, "Snowballs", "top")
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_deadly_snowballs_upgrade, (883, 65))
            blit_text(scrn, "Deadly Snowballs", "top")
        elif tower.curr_top_upgrade == 2 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_snowball_barrage_upgrade, (883, 65))
            blit_text(scrn, "Snowball Barrage", "top")
        else:
            scrn.blit(img_max_upgrades, top)
        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_freeze_radius_upgrade, (883, 194))
            blit_text(scrn, "Bigger Storm", "bottom")
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
            scrn.blit(img_snow_flurry_upgrade, (883, 194))
            blit_text(scrn, "Snow Flurries", "bottom")
        elif tower.curr_bottom_upgrade == 2 and tower.curr_top_upgrade < 2:
            scrn.blit(img_freezing_temps_upgrade, (883, 194))
            blit_text(scrn, "Sub-Zero Temps", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)

        # TOP UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # snowballs
                if tower.curr_top_upgrade == 0 and money >= 250:
                    purchase.play()
                    money -= 250
                    tower.sell_amt += 125
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True

                # deadly snowballs
                elif tower.curr_top_upgrade == 1 and money >= 300 and tower.curr_bottom_upgrade < 2:
                    purchase.play()
                    money -= 300
                    tower.sell_amt += 150
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True

                # snowball barrage
                elif tower.curr_top_upgrade == 2 and money >= 450 and tower.curr_bottom_upgrade < 2:
                    purchase.play()
                    money -= 450
                    tower.sell_amt += 225
                    tower.curr_top_upgrade = 3
                    UpgradeFlag = True

        # sell button
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return

        # BOTTOM UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # radius
                if tower.curr_bottom_upgrade == 0 and money >= 350:
                    purchase.play()
                    money -= 350
                    tower.sell_amt += 175
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True

                # snow flurry
                elif tower.curr_bottom_upgrade == 1 and money >= 450 and tower.curr_top_upgrade < 2:
                    purchase.play()
                    money -= 450
                    tower.sell_amt += 225
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True

                # subzero
                elif tower.curr_bottom_upgrade == 2 and money >= 350 and tower.curr_top_upgrade < 2:
                    purchase.play()
                    money -= 350
                    tower.sell_amt += 175
                    tower.curr_bottom_upgrade = 3
                    UpgradeFlag = True

    if isinstance(tower, WizardTower):
        img_apprentice_upgrade = load_image("assets/upgrade_apprentice.png")
        img_master_upgrade = load_image("assets/upgrade_master.png")
        img_explosive_orbs_upgrade = load_image("assets/upgrade_explosiveorbs.png")
        img_lightning_upgrade = load_image("assets/upgrade_lightning.png")
        img_storm_upgrade = load_image("assets/upgrade_storm.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_apprentice_upgrade, (883, 65))
            blit_text(scrn, "Rat Apprentice", "top")
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_master_upgrade, (883, 65))
            blit_text(scrn, "Master Wizard", "top")
        elif tower.curr_top_upgrade == 2 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_explosive_orbs_upgrade, (883, 65))
            blit_text(scrn, "Explosive Orbs", "top")
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_lightning_upgrade, (883, 194))
            blit_text(scrn, "Lightning Spell", "bottom")
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 3:
            scrn.blit(img_storm_upgrade, (883, 194))
            blit_text(scrn, "Lightning Storm", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)
        # TOP UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # apprentice
                if tower.curr_top_upgrade == 0 and money >= 400:
                    purchase.play()
                    money -= 400
                    tower.sell_amt += 200
                    tower.radius += 25
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/wizard+apprentice.png"
                        tower.image = load_image("assets/wizard+apprentice.png")
                        tower.original_image = load_image("assets/wizard+apprentice.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/wizard+lightning+apprentice.png"
                        tower.image = load_image("assets/wizard+lightning+apprentice.png")
                        tower.original_image = load_image("assets/wizard+lightning+apprentice.png")
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image_path = "assets/wizard+storm+apprentice.png"
                        tower.image = load_image("assets/wizard+storm+apprentice.png")
                        tower.original_image = load_image("assets/wizard+storm+apprentice.png")
                # master
                elif tower.curr_top_upgrade == 1 and money >= 1200:
                    purchase.play()
                    money -= 1200
                    tower.sell_amt += 600
                    tower.radius += 25
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/wizard+master.png"
                        tower.image = load_image("assets/wizard+master.png")
                        tower.original_image = load_image("assets/wizard+master.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/wizard+lightning+master.png"
                        tower.image = load_image("assets/wizard+lightning+master.png")
                        tower.original_image = load_image("assets/wizard+lightning+master.png")
                # explosive orbs
                elif tower.curr_top_upgrade == 2 and money >= 1000:
                    purchase.play()
                    money -= 1000
                    tower.sell_amt += 500
                    tower.curr_top_upgrade = 3
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/wizard+explosiveorbs.png"
                        tower.image = load_image("assets/wizard+explosiveorbs.png")
                        tower.original_image = load_image("assets/wizard+explosiveorbs.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/wizard+explosiveorbs+lightning.png"
                        tower.image = load_image("assets/wizard+explosiveorbs+lightning.png")
                        tower.original_image = load_image("assets/wizard+explosiveorbs+lightning.png")
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return
        # BOTTOM UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # lightning
                if tower.curr_bottom_upgrade == 0 and money >= 1850:
                    purchase.play()
                    money -= 1850
                    tower.sell_amt += 925
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/wizard+lightning.png"
                        tower.image = load_image("assets/wizard+lightning.png")
                        tower.original_image = load_image("assets/wizard+lightning.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/wizard+lightning+apprentice.png"
                        tower.image = load_image("assets/wizard+lightning+apprentice.png")
                        tower.original_image = load_image("assets/wizard+lightning+apprentice.png")
                    elif tower.curr_top_upgrade == 2:
                        tower.image_path = "assets/wizard+lightning+master.png"
                        tower.image = load_image("assets/wizard+lightning+master.png")
                        tower.original_image = load_image("assets/wizard+lightning+master.png")
                    elif tower.curr_top_upgrade == 3:
                        tower.image_path = "assets/wizard+explosiveorbs+lightning.png"
                        tower.image = load_image("assets/wizard+explosiveorbs+lightning.png")
                        tower.original_image = load_image("assets/wizard+explosiveorbs+lightning.png")
                # storm
                elif tower.curr_bottom_upgrade == 1 and money >= 2600 and tower.curr_top_upgrade < 2:
                    purchase.play()
                    money -= 2600
                    tower.sell_amt += 1300
                    tower.radius += 50
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/wizard+storm.png"
                        tower.image = load_image("assets/wizard+storm.png")
                        tower.original_image = load_image("assets/wizard+storm.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/wizard+storm+apprentice.png"
                        tower.image = load_image("assets/wizard+storm+apprentice.png")
                        tower.original_image = load_image("assets/wizard+storm+apprentice.png")
    if isinstance(tower, CheddarCommando):
        img_shotgun_upgrade = load_image("assets/upgrade_shotgun.png")
        img_rpg_upgrade = load_image("assets/upgrade_rocket.png")
        img_piercing_upgrade = load_image("assets/upgrade_piercing.png")
        img_thumper_upgrade = load_image("assets/upgrade_thumper.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_piercing_upgrade, (883, 65))
            blit_text(scrn, "Piercing Rounds", "top")
        elif tower.curr_top_upgrade == 1 and tower.curr_bottom_upgrade < 2:
            scrn.blit(img_shotgun_upgrade, (883, 65))
            blit_text(scrn, "Shotgun", "top")
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_rpg_upgrade, (883, 194))
            blit_text(scrn, "Explosive Rounds", "bottom")
        elif tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade < 2:
            scrn.blit(img_thumper_upgrade, (883, 194))
            blit_text(scrn, "Grenade Launcher", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)
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
                        tower.image_path = "assets/soldier_piercing.png"
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
                        tower.reload_path = "assets/shotgun_reload.mp3"
                    tower.sound_path = "assets/shotgun_shoot.mp3"
                    tower.shoot_sound = load_sound("assets/shotgun_shoot.mp3")
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade < 1:
                        tower.image_path = "assets/soldier_shotgun.png"
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
                    tower.reload_time = 3500
                    if tower.curr_top_upgrade < 1:
                        tower.image_path = "assets/soldier_rocket.png"
                        tower.sound_path = "assets/launcher_shoot.mp3"
                        tower.shoot_sound = load_sound("assets/launcher_shoot.mp3")
                        tower.image = load_image("assets/soldier_rocket.png")
                        tower.original_image = load_image("assets/soldier_rocket.png")
                    tower.reload_path = "assets/commando_reload.mp3"
                    tower.reload_sound = load_sound("assets/commando_reload.mp3")
                    UpgradeFlag = True
                # grenade launcher
                elif money >= 900 and tower.curr_bottom_upgrade == 1 and tower.curr_top_upgrade != 2:
                    purchase.play()
                    money -= 900
                    tower.sell_amt += 450
                    tower.curr_bottom_upgrade = 2
                    tower.radius = 125
                    tower.shoot_interval = 1500
                    tower.reload_time = 7500
                    tower.reload_path = "assets/shotgun_reload.mp3"
                    tower.reload_sound = load_sound("assets/shotgun_reload.mp3")
                    UpgradeFlag = True
                    tower.image_path = "assets/soldier_thumper.png"
                    tower.image = load_image("assets/soldier_thumper.png")
                    tower.original_image = load_image("assets/soldier_thumper.png")

    if isinstance(tower, Ratman):
        img_supervision_upgrade = load_image("assets/upgrade_supervision.png")
        img_superspeed_upgrade = load_image("assets/upgrade_superspeed.png")
        img_roborat_upgrade = load_image("assets/upgrade_ratman_roborat.png")
        img_fondue_upgrade = load_image("assets/upgrade_fondue.png")
        img_plasma_upgrade = load_image("assets/upgrade_plasma.png")
        img_cheesegod_upgrade = load_image("assets/upgrade_cheesegod.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_supervision_upgrade, (883, 65))
            blit_text(scrn, "Supervision", "top")
        elif tower.curr_top_upgrade == 1:
            scrn.blit(img_superspeed_upgrade, (883, 65))
            blit_text(scrn, "Superspeed", "top")
        elif tower.curr_top_upgrade == 2 and tower.curr_bottom_upgrade < 3:
            scrn.blit(img_roborat_upgrade, (883, 65))
            blit_text(scrn, "Robo-Rat", "top")
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_fondue_upgrade, (883, 194))
            blit_text(scrn, "Fondue Blast", "bottom")
        elif tower.curr_bottom_upgrade == 1:
            scrn.blit(img_plasma_upgrade, (883, 194))
            blit_text(scrn, "Plasmatic Provolone", "bottom")
        elif tower.curr_bottom_upgrade == 2 and tower.curr_top_upgrade < 3:
            scrn.blit(img_cheesegod_upgrade, (883, 194))
            blit_text(scrn, "Cheese God", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)
        # TOP UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # Supervision
                if tower.curr_top_upgrade == 0 and money >= 850:
                    purchase.play()
                    money -= 850
                    tower.sell_amt += 425
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    tower.get_upgrades()
                # Superspeed
                elif tower.curr_top_upgrade == 1 and money >= 1500:
                    purchase.play()
                    money -= 1500
                    tower.sell_amt += 750
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    tower.get_upgrades()
                # Robo-Rat
                elif tower.curr_top_upgrade == 2 and money >= 7300 and tower.curr_bottom_upgrade < 3:
                    purchase.play()
                    money -= 7300
                    tower.sell_amt += 3650
                    tower.curr_top_upgrade = 3
                    UpgradeFlag = True
                    tower.get_upgrades()

        # SELL BUTTON
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return

        # BOTTOM UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # FONDUE BLAST
                if tower.curr_bottom_upgrade == 0 and money >= 2200:
                    purchase.play()
                    money -= 2200
                    tower.sell_amt += 1100
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    tower.get_upgrades()
                # PLASMATIC PROVOLONE
                elif tower.curr_bottom_upgrade == 1 and money >= 3000:
                    purchase.play()
                    money -= 3000
                    tower.sell_amt += 1500
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    tower.get_upgrades()
                # CHEESE GOD
                elif tower.curr_bottom_upgrade == 2 and money >= 12000 and tower.curr_top_upgrade < 3:
                    purchase.play()
                    money -= 12000
                    tower.sell_amt += 6000
                    tower.curr_bottom_upgrade = 3
                    UpgradeFlag = True
                    tower.get_upgrades()

    if isinstance(tower, MortarStrike):
        img_bigger_upgrade = load_image("assets/upgrade_biggerbombs.png")
        img_napalm_upgrade = load_image("assets/upgrade_napalm.png")
        img_tzar_upgrade = load_image("assets/upgrade_tzar.png")
        img_rapid_upgrade = load_image("assets/upgrade_rapid.png")
        img_cluster_upgrade = load_image("assets/upgrade_cluster.png")
        img_triple_upgrade = load_image("assets/upgrade_triple.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_bigger_upgrade, (883, 65))
            blit_text(scrn, "Bigger Bombs", "top")
        elif tower.curr_top_upgrade == 1:
            scrn.blit(img_napalm_upgrade, (883, 65))
            blit_text(scrn, "Napalm", "top")
        elif tower.curr_top_upgrade == 2 and tower.curr_bottom_upgrade < 3:
            scrn.blit(img_tzar_upgrade, (883, 65))
            blit_text(scrn, "Tzar Bomba", "top")
        else:
            scrn.blit(img_max_upgrades, top)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_rapid_upgrade, (883, 194))
            blit_text(scrn, "Rapid Reload", "bottom")
        elif tower.curr_bottom_upgrade == 1:
            scrn.blit(img_cluster_upgrade, (883, 194))
            blit_text(scrn, "Cluster Bombs", "bottom")
        elif tower.curr_bottom_upgrade == 2 and tower.curr_top_upgrade < 3:
            scrn.blit(img_triple_upgrade, (883, 194))
            blit_text(scrn, "Triple Barrel", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)
        # TOP UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                # Bigger Bombs
                if tower.curr_top_upgrade == 0 and money >= 400:
                    purchase.play()
                    money -= 400
                    tower.sell_amt += 200
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    tower.get_upgrades()
                # Napalm
                elif tower.curr_top_upgrade == 1 and money >= 900:
                    purchase.play()
                    money -= 900
                    tower.sell_amt += 450
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    tower.get_upgrades()
                # Tzar Bomba
                elif tower.curr_top_upgrade == 2 and money >= 5400 and tower.curr_bottom_upgrade < 3:
                    purchase.play()
                    money -= 5400
                    tower.sell_amt += 2700
                    tower.curr_top_upgrade = 3
                    UpgradeFlag = True
                    tower.get_upgrades()

        # SELL BUTTON
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                towers.remove(tower)
                UpgradeFlag = False
                return

        # BOTTOM UPGRADE PATH
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # Rapid Reload
                if tower.curr_bottom_upgrade == 0 and money >= 1100:
                    purchase.play()
                    money -= 1100
                    tower.sell_amt += 550
                    tower.curr_bottom_upgrade = 1
                    UpgradeFlag = True
                    tower.get_upgrades()
                # Cluster Bombs
                elif tower.curr_bottom_upgrade == 1 and money >= 900:
                    purchase.play()
                    money -= 900
                    tower.sell_amt += 450
                    tower.curr_bottom_upgrade = 2
                    UpgradeFlag = True
                    tower.get_upgrades()
                # Triple Barrel
                elif tower.curr_bottom_upgrade == 2 and money >= 2600 and tower.curr_top_upgrade < 3:
                    purchase.play()
                    money -= 2600
                    tower.sell_amt += 1300
                    tower.curr_bottom_upgrade = 3
                    UpgradeFlag = True
                    tower.get_upgrades()

    if isinstance(tower, CheeseBeacon):
        img_damage3_upgrade = load_image("assets/upgrade_damage3.png")
        img_damage4_upgrade = load_image("assets/upgrade_damage4.png")
        img_damage5_upgrade = load_image("assets/upgrade_damage5.png")
        img_radius_upgrade = load_image("assets/upgrade_radius.png")
        img_speed_upgrade = load_image("assets/upgrade_speed.png")
        if tower.curr_top_upgrade == 0:
            scrn.blit(img_damage3_upgrade, (883, 65))
            blit_text(scrn, "Organic Cheese", "top")
        elif tower.curr_top_upgrade == 1:
            scrn.blit(img_damage4_upgrade, (883, 65))
            blit_text(scrn, "Pasteurized Cheese", "top")
        elif tower.curr_top_upgrade == 2:
            scrn.blit(img_damage5_upgrade, (883, 65))
            blit_text(scrn, "Antibiotic-Free", "top")
        else:
            scrn.blit(img_max_upgrades, bottom)

        if tower.curr_bottom_upgrade == 0:
            scrn.blit(img_radius_upgrade, (883, 194))
            blit_text(scrn, "Vitamin Enhanced Cheese", "bottom")
        elif tower.curr_bottom_upgrade == 1:
            scrn.blit(img_speed_upgrade, (883, 194))
            blit_text(scrn, "Caffienated Cheese", "bottom")
        else:
            scrn.blit(img_max_upgrades, bottom)
        # damage 3x
        if 883 <= mouse[0] <= 883 + 218 and 65 <= mouse[1] <= 65 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 65))
            if detect_single_click():
                if tower.curr_top_upgrade == 0 and money >= 2500:
                    purchase.play()
                    money -= 2500
                    tower.sell_amt += 1250
                    tower.curr_top_upgrade = 1
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/beacon+damageboost.png"
                        tower.image = load_image("assets/beacon+damageboost.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/beacon+radius+damage.png"
                        tower.image = load_image("assets/beacon+radius+damage.png")
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image_path = "assets/beacon+speed+damage.png"
                        tower.image = load_image("assets/beacon+speed+damage.png")
                # damage 4x
                elif tower.curr_top_upgrade == 1 and money >= 4000:
                    purchase.play()
                    money -= 4000
                    tower.sell_amt += 200
                    tower.curr_top_upgrade = 2
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/beacon_damage2.png"
                        tower.image = load_image("assets/beacon_damage2.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/beacon+radius+damage2.png"
                        tower.image = load_image("assets/beacon+radius+damage2.png")
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image_path = "assets/beacon+speed+damage2.png"
                        tower.image = load_image("assets/beacon+speed+damage2.png")
                # damage 5x
                elif tower.curr_top_upgrade == 2 and money >= 5200:
                    purchase.play()
                    money -= 5200
                    tower.sell_amt += 2600
                    tower.curr_top_upgrade = 3
                    UpgradeFlag = True
                    if tower.curr_bottom_upgrade == 0:
                        tower.image_path = "assets/beacon_damage3.png"
                        tower.image = load_image("assets/beacon_damage3.png")
                    elif tower.curr_bottom_upgrade == 1:
                        tower.image_path = "assets/beacon+radius+damage3.png"
                        tower.image = load_image("assets/beacon+radius+damage3.png")
                    elif tower.curr_bottom_upgrade == 2:
                        tower.image_path = "assets/beacon+speed+damage3.png"
                        tower.image = load_image("assets/beacon+speed+damage3.png")
        if 997 <= mouse[0] <= 997 + 105 and 298 <= mouse[1] <= 298 + 35:
            if detect_single_click():
                money += tower.sell_amt
                tower.sell()  # call to remove boosts
                towers.remove(tower)
                UpgradeFlag = False
                return
        if 883 <= mouse[0] <= 883 + 218 and 194 <= mouse[1] <= 194 + 100:
            scrn.blit(img_upgrade_highlighted, (883, 194))
            if detect_single_click():
                # radius
                if money >= 600 and tower.curr_bottom_upgrade == 0:
                    purchase.play()
                    money -= 600
                    tower.sell_amt += 300
                    tower.curr_bottom_upgrade = 1
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/beacon+radius.png"
                        tower.image = load_image("assets/beacon+radius.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/beacon+radius+damage.png"
                        tower.image = load_image("assets/beacon+radius+damage.png")
                    elif tower.curr_top_upgrade == 2:
                        tower.image_path = "assets/beacon+radius+damage2.png"
                        tower.image = load_image("assets/beacon+radius+damage2.png")
                    elif tower.curr_top_upgrade == 3:
                        tower.image_path = "assets/beacon+radius+damage3.png"
                        tower.image = load_image("assets/beacon+radius+damage3.png")
                    UpgradeFlag = True
                # speed
                elif money >= 2200 and tower.curr_bottom_upgrade == 1:
                    purchase.play()
                    money -= 2200
                    tower.sell_amt += 1100
                    tower.curr_bottom_upgrade = 2
                    if tower.curr_top_upgrade == 0:
                        tower.image_path = "assets/beacon+speed.png"
                        tower.image = load_image("assets/beacon+speed.png")
                    elif tower.curr_top_upgrade == 1:
                        tower.image_path = "assets/beacon+speed+damage.png"
                        tower.image = load_image("assets/beacon+speed+damage.png")
                    elif tower.curr_top_upgrade == 2:
                        tower.image_path = "assets/beacon+speed+damage2.png"
                        tower.image = load_image("assets/beacon+speed+damage2.png")
                    elif tower.curr_top_upgrade == 3:
                        tower.image_path = "assets/beacon+speed+damage3.png"
                        tower.image = load_image("assets/beacon+speed+damage3.png")

    # CLICK OUT OF UPGRADE WINDOW
    if detect_single_click() and not (
            (tower.position[0] - 25) <= mouse[0] <= (tower.position[0] + 25) and (tower.position[1] - 25) <= mouse[
        1] <= (tower.position[1] + 25)):
        UpgradeFlag = False
        return
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                TowerFlag = False
                UpgradeFlag = False
                return
        if event.type == pygame.QUIT:
            pygame.quit()

    circle_surface = pygame.Surface((2 * tower.radius, 2 * tower.radius), pygame.SRCALPHA)
    pygame.draw.circle(circle_surface, (0, 0, 0, 128), (tower.radius, tower.radius), tower.radius)
    scrn.blit(circle_surface, (tower.position[0] - tower.radius, tower.position[1] - tower.radius))


def update_towers(scrn: pygame.surface):
    global towers, enemies, last_frame_time, game_speed_multiplier
    # Calculate delta time
    current_time = pygame.time.get_ticks()
    delta = (current_time - last_frame_time) * game_speed_multiplier
    last_frame_time = current_time

    for tower in towers:
        if not isinstance(tower, RatBank) and not isinstance(tower, CheeseBeacon):
            tower.update(enemies)
        tower.render(scrn)
        if not isinstance(tower, RatTent) and not isinstance(tower, Ozbourne) and not isinstance(tower, RatBank) \
                and not isinstance(tower, RatSniper):
            tower.shoot()
        if isinstance(tower, CheeseBeacon):
            tower.update(towers, delta)

    for tower in towers:
        if isinstance(tower, RatBank):
            if tower.investment_window_open:
                tower.investment_interface(scrn)
        if isinstance(tower, CheeseBeacon):
            tower.render_effects(scrn)

    # Mantis debuff cleanup
    for tower in towers:
        if hasattr(tower, "mantis_debuff_active") and tower.mantis_debuff_active:
            if pygame.time.get_ticks() < tower.mantis_debuff_end_time:
                spawn_shard(tower.position, color=(105, 160, 25), count=random.randint(0, 1))
            elapsed_virtual_time = (pygame.time.get_ticks() - tower.mantis_debuff_applied_time) * game_speed_multiplier
            if elapsed_virtual_time >= 15000:
                tower.shoot_interval = tower.original_shoot_interval
                tower.mantis_debuff_active = False
                print("reset debuff!", tower.shoot_interval)


def update_and_render_damage_indicators(screen):
    current_time = pygame.time.get_ticks()
    for indicator in global_damage_indicators[:]:
        elapsed = current_time - indicator['start_time']
        if elapsed > indicator['lifetime']:
            global_damage_indicators.remove(indicator)
        else:
            # Update position
            indicator['pos'][0] += indicator['vel'][0]
            indicator['pos'][1] += indicator['vel'][1]

            # Fade out: calculate alpha from remaining time
            fade_ratio = 1 - (elapsed / indicator['lifetime'])
            alpha = max(0, min(255, int(255 * fade_ratio)))

            # Apply alpha to a copy of the surface
            faded_surface = indicator['surface'].copy()
            faded_surface.set_alpha(alpha)

            # Draw to screen
            screen.blit(faded_surface, indicator['pos'])


def update_stars(scrn, round_number):
    img_stars = load_image("assets/stars_UI/stars0.png")
    img_trophy = None
    pos = (988, 135)
    if 10 <= round_number < 20:
        img_stars = load_image("assets/stars_UI/stars1.png")
    elif 20 <= round_number < 30:
        img_stars = load_image("assets/stars_UI/stars2.png")
    elif 30 <= round_number < 40:
        img_stars = load_image("assets/stars_UI/stars3.png")
        img_trophy = load_image("assets/stars_UI/bronze_trophy.png")
    elif 40 <= round_number < 50:
        img_stars = load_image("assets/stars_UI/stars4.png")
        img_trophy = load_image("assets/stars_UI/bronze_trophy.png")
    elif 50 <= round_number < 65:
        img_stars = load_image("assets/stars_UI/stars5.png")
        img_trophy = load_image("assets/stars_UI/silver_trophy.png")
    elif 65 <= round_number < 85:
        img_stars = load_image("assets/stars_UI/stars6.png")
        img_trophy = load_image("assets/stars_UI/gold_trophy.png")
    elif 85 <= round_number < 100:
        img_stars = load_image("assets/stars_UI/stars7.png")
        img_trophy = load_image("assets/stars_UI/gold_trophy.png")
    elif 100 <= round_number:
        img_stars = load_image("assets/stars_UI/stars8.png")
        img_trophy = load_image("assets/stars_UI/diamond_trophy.png")

    scrn.blit(img_stars, (970, 5))
    if img_trophy is not None:
        scrn.blit(img_trophy, pos)


def update_stunned_enemies(enemies):
    current_time = pygame.time.get_ticks()
    for enemy in enemies:
        if hasattr(enemy, "stun_end_time") and current_time >= enemy.stun_end_time:
            # Restore enemy speed using the saved original speed
            enemy.speed = getattr(enemy, "original_speed", enemy.speed)
            # Remove the temporary stun attributes
            del enemy.stun_end_time
            if hasattr(enemy, "original_speed"):
                del enemy.original_speed


def update_stats(scrn: pygame.surface, health: int, money: int, round_number: int, clock: pygame.time.Clock()):
    health_font = get_font("arial", 28)
    money_font = get_font("arial", 28)
    round_font = get_font("arial", 28)

    text1 = health_font.render(f"{int(health)}", True, (255, 255, 255))
    text2 = money_font.render(f"{money}", True, (255, 255, 255))
    text3 = round_font.render(f"Round {round_number}", True, (255, 255, 255))

    img_kills = load_image("assets/kills_icon.png")

    # DEBUGGING CURSOR POS
    mouse = pygame.mouse.get_pos()
    fps = int(clock.get_fps())  # Get current FPS from the passed clock

    x_font = get_font("arial", 12)
    y_font = get_font("arial", 12)
    fps_font = get_font("arial", 12)

    text_fps = fps_font.render(f"FPS: {fps}", True, (255, 0, 0))  # Render FPS in red
    text_x = x_font.render(f"x-axis: {mouse[0]}", True, (0, 255, 0))
    text_y = y_font.render(f"y-axis: {mouse[1]}", True, (0, 255, 0))

    # update all damage indicators!
    update_and_render_damage_indicators(scrn)
    # display star count
    update_stars(scrn, round_number)

    # total kills icon
    kill_font = get_font("arial", 16)
    text_kills = kill_font.render(f"{game_stats.global_kill_total['count']}", True, (255, 255, 255))

    scrn.blit(img_kills, (22, 673))
    scrn.blit(text_kills, (58, 678))

    # Display the FPS counter just above the x/y position text
    if showFPS:
        scrn.blit(text_fps, (1000, 690))

    if showCursor:
        scrn.blit(text_x, (932, 670))
        scrn.blit(text_y, (932, 690))

    # BACK TO REGULAR STUFF
    scrn.blit(text1, (55, 15))
    scrn.blit(text2, (65, 62))
    scrn.blit(text3, (1150, 10))


def handle_newtower(scrn: pygame.surface, tower: str) -> bool:
    global money, TowerFlag
    TowerFlag = True
    image_house_hitbox = 'assets/house_illegal_regions.png'
    house_hitbox = load_image(image_house_hitbox)
    tower_click = load_sound("assets/tower_placed.mp3")
    mouse = pygame.mouse.get_pos()
    relative_pos = (mouse[0] - hitbox_position[0], mouse[1] - hitbox_position[1])
    if tower == "NULL":
        TowerFlag = False
        return True
    elif tower == "mrcheese":
        img_base_rat = load_image("assets/base_rat.png")
        circle_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
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
            tower_mrcheese = MrCheese((mouse[0], mouse[1]), radius=100, weapon="Cheese", damage=1,
                                      image_path="assets/base_rat.png", projectile_image="assets/projectile_cheese.png")
            towers.append(tower_mrcheese)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 150
            TowerFlag = False
            return True
    elif tower == "ratman":
        img_base_rat = load_image("assets/base_ratman.png")
        circle_surface = pygame.Surface((350, 350), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (175, 175), 175)
            scrn.blit(img_base_rat, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 175, mouse[1] - 175))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (175, 175), 175)
            scrn.blit(img_base_rat, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 175, mouse[1] - 175))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "ratman":
            tower_ratman = Ratman((mouse[0], mouse[1]), radius=175, weapon="cheese", damage=2, shoot_interval=500,
                                      image_path="assets/base_ratman.png", projectile_image="assets/projectile_cheese.png")
            towers.append(tower_ratman)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 2600
            TowerFlag = False
            return True

    elif tower == "mortar":
        img_base = load_image("assets/mortar_base.png")
        circle = pygame.Surface((100, 100), pygame.SRCALPHA)
        # placement preview
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle, (0, 0, 0, 128), (50, 50), 50)
        else:
            pygame.draw.circle(circle, (255, 0, 0, 128), (50, 50), 50)
        scrn.blit(img_base, (mouse[0] - 23, mouse[1] - 23))
        scrn.blit(circle, (mouse[0] - 50, mouse[1] - 50))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower):
            mortar = MortarStrike((mouse[0], mouse[1]), "assets/mortar_base.png")
            towers.append(mortar)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 750  # adjust cost
            TowerFlag = False
            return True
    elif tower == "soldier":
        img_base_soldier = load_image("assets/base_soldier.png")
        circle_surface = pygame.Surface((150, 150), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
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
            TowerFlag = False
            return True
    elif tower == "frost":
        img_base_frost = load_image("assets/base_frost.png")
        circle_surface = pygame.Surface((150, 150), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (75, 75), 75)
            scrn.blit(img_base_frost, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (75, 75), 75)
            scrn.blit(img_base_frost, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "frost":
            tower_frost = RatFrost((mouse[0], mouse[1]))
            towers.append(tower_frost)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 200
            TowerFlag = False
            return True
    elif tower == "sniper":
        img_base_sniper = load_image("assets/sniper_base.png")
        circle_surface = pygame.Surface((50, 50), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (25, 25), 25)
            scrn.blit(img_base_sniper, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 25, mouse[1] - 25))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (25, 25), 25)
            scrn.blit(img_base_sniper, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 25, mouse[1] - 25))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "sniper":
            tower_sniper = RatSniper((mouse[0], mouse[1]))
            towers.append(tower_sniper)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 350
            TowerFlag = False
            return True
    elif tower == "wizard":
        img_base_wizard = load_image("assets/wizard_base.png")
        circle_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (100, 100), 100)
            scrn.blit(img_base_wizard, (mouse[0] - 15, mouse[1] - 19))
            scrn.blit(circle_surface, (mouse[0] - 100, mouse[1] - 100))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (100, 100), 100)
            scrn.blit(img_base_wizard, (mouse[0] - 15, mouse[1] - 19))
            scrn.blit(circle_surface, (mouse[0] - 100, mouse[1] - 100))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "wizard":
            tower_wizard = WizardTower((mouse[0], mouse[1]))
            towers.append(tower_wizard)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 400
            TowerFlag = False
            return True
    elif tower == "beacon":
        img_base_beacon = load_image("assets/beacon_base.png")
        circle_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (100, 100), 100)
            scrn.blit(img_base_beacon, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 100, mouse[1] - 100))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (100, 100), 100)
            scrn.blit(img_base_beacon, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 100, mouse[1] - 100))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower) and tower == "beacon":
            tower_beacon = CheeseBeacon((mouse[0], mouse[1]))
            towers.append(tower_beacon)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 1400
            TowerFlag = False
            return True
    elif tower == "rattent":
        img_base_tent = load_image("assets/base_camp.png")
        circle_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
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
            TowerFlag = False
            return True
    elif tower == "ratbank":
        img_base_bank = load_image("assets/rat_bank.png")
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
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
            TowerFlag = False
            return True
    elif tower == "ozbourne":
        img_base_ozbourne = load_image("assets/alfredo_ozbourne_base.png")
        circle_surface = pygame.Surface((150, 150), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
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
            TowerFlag = False
            return True
    elif tower == "minigun":
        img_base_minigun = load_image("assets/base_minigun.png")
        circle_surface = pygame.Surface((150, 150), pygame.SRCALPHA)
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    TowerFlag = False
                    return True
        if check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (0, 0, 0, 128), (75, 75), 75)
            scrn.blit(img_base_minigun, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        elif not check_hitbox(house_hitbox, relative_pos, towers):
            pygame.draw.circle(circle_surface, (255, 0, 0, 128), (75, 75), 75)
            scrn.blit(img_base_minigun, (mouse[0] - 25, mouse[1] - 25))
            scrn.blit(circle_surface, (mouse[0] - 75, mouse[1] - 75))
        if detect_single_click() and check_hitbox(house_hitbox, relative_pos, tower):
            tower_minigun = MinigunTower((mouse[0], mouse[1]))
            towers.append(tower_minigun)
            tower_click.play()
            play_splash_animation(scrn, (mouse[0], mouse[1]))
            money -= 600
            TowerFlag = False
            return True

    return False


class RecruitEntity:
    img_recruit_death = load_image("assets/splatter_recuit.png")

    def __init__(self, position, health, speed, path, damage, image_path):
        self.health = health
        self.speed = speed
        self.path = path
        self.damage = damage
        self.frames = ["assets/freak_recruit_frames/freak0.png", "assets/freak_recruit_frames/freak1.png",
                       "assets/freak_recruit_frames/freak2.png", "assets/freak_recruit_frames/freak3.png",
                       "assets/freak_recruit_frames/freak4.png", "assets/freak_recruit_frames/freak5.png",
                       "assets/freak_recruit_frames/freak6.png", "assets/freak_recruit_frames/freak7.png"]
        self.current_frame = 0
        self.frame_duration = 150  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        self.image = load_image(image_path)
        self.original_image = self.image
        self.rect = self.image.get_rect(center=position)
        self.position, self.current_target = self.get_closest_point_on_path(position)
        self.is_alive = True
        self.was_alive = False
        self.buff = False
        self.current_angle = 0

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
            if distance < 0.0001:
                # Snap to this waypoint and move on
                self.position = (target_x, target_y)
                self.rect.center = self.position
                self.current_target += 1
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
        angle = math.degrees(math.atan2(-direction_y, direction_x)) - 90
        self.current_angle = angle  # Save it
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            new_frame_img = load_image(self.frames[self.current_frame])
            self.original_image = new_frame_img
            self.image = pygame.transform.rotate(self.original_image, self.current_angle)
            self.last_frame_update = current_time

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
        if self.buff:
            self.update_animation()

    def render(self, screen):
        if self.was_alive:
            screen.blit(self.img_recruit_death, self.rect.topleft)
            self.was_alive = False
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)


class RatTent:
    def __init__(self, position, radius, recruit_health, recruit_speed, recruit_damage, image_path, recruit_image,
                 spawn_interval=3000):
        self.image_path = "assets/base_camp.png"
        self.image = load_image(self.image_path)
        self.position = position
        self.radius = radius
        self.recruit_health = recruit_health
        self.recruit_speed = recruit_speed
        self.recruit_damage = recruit_damage
        self.damage = self.recruit_damage
        self.rect = self.image.get_rect(center=position)
        self.spawn_interval = spawn_interval
        self.last_spawn_time = 0
        self.freak_last_spawn_time = 0
        self.recruits = []
        self.recruit_image = recruit_image
        self.curr_bottom_upgrade = 0
        self.curr_top_upgrade = 0
        self.sell_amt = 325
        self.horn_sfx = load_sound("assets/battle_horn.mp3")
        self.freak_sfx = load_sound("assets/freak-squeak.mp3")
        self.freak_death = load_sound("assets/freak_death.mp3")

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
        for recruit in self.recruits:
            recruit.render(screen)

    def update(self, enemies):
        scaled_interval = self.spawn_interval / game_speed_multiplier
        if self.curr_top_upgrade > 0:
            self.spawn_interval = 1500
        # use default spawning
        if self.curr_top_upgrade < 2:
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
                        image_path=self.recruit_image,
                    )
                    if self.curr_top_upgrade > 0:
                        recruit.speed = 2
                    if self.curr_bottom_upgrade > 1:
                        recruit.health = 2
                    self.recruits.append(recruit)
                    self.last_spawn_time = pygame.time.get_ticks()

        # ARMY RELEASE!
        if self.curr_top_upgrade == 2 and self.curr_bottom_upgrade < 2:
            if pygame.time.get_ticks() - self.last_spawn_time >= (scaled_interval * 10) and RoundFlag:
                self.horn_sfx.play()
                recruit_entity = RecruitEntity(self.position, 1, 1, recruit_path, 1, self.recruit_image)
                closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
                distance = ((closest_spawn_point[0] - self.position[0]) ** 2 + (
                        closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
                if distance <= self.radius:
                    for _ in range(60):
                        offset_path = [(x + random.randint(-16, 16), y + random.randint(-8, 8)) for (x, y) in recruit_path]
                        recruit = RecruitEntity(
                            position=(closest_spawn_point[0] + random.randint(-16, 16), closest_spawn_point[1] + random.randint(-16, 16)),
                            health=self.recruit_health / 2,
                            speed=self.recruit_speed,
                            path=offset_path,
                            damage=self.recruit_damage / 2,
                            image_path="assets/recruit_army.png"
                        )
                        self.recruits.append(recruit)
                        self.last_spawn_time = pygame.time.get_ticks()

        # RELEASE A FREAK!!
        if self.curr_bottom_upgrade > 1 and self.curr_top_upgrade < 2:
            if pygame.time.get_ticks() - self.freak_last_spawn_time >= (scaled_interval * 5) and RoundFlag:
                self.freak_sfx.play()
                recruit_entity = RecruitEntity(self.position, 1, 1, recruit_path, 1, self.recruit_image)
                closest_spawn_point, _ = recruit_entity.get_closest_point_on_path(self.position)
                distance = ((closest_spawn_point[0] - self.position[0]) ** 2 + (
                        closest_spawn_point[1] - self.position[1]) ** 2) ** 0.5
                if distance <= self.radius:
                    recruit = RecruitEntity(
                        position=closest_spawn_point,
                        health=10,
                        speed=.5,
                        path=recruit_path,
                        damage=3,
                        image_path="assets/freak_recruit_frames/freak0.png"
                    )
                    recruit.buff = True
                    self.recruits.append(recruit)
                    self.freak_last_spawn_time = pygame.time.get_ticks()

        for recruit in self.recruits[:]:
            recruit.update(enemies)
            if not recruit.is_alive and recruit is not None:
                if recruit.buff:
                    self.freak_death.play()
                self.recruits.remove(recruit)
            if not RoundFlag and recruit is not None:
                self.recruits.remove(recruit)


class MrCheese:
    sfx_squeak = load_sound("assets/mouse-squeak.mp3")

    def __init__(self, position, radius, weapon, damage, image_path, projectile_image, shoot_interval=1500):
        self.image_path = image_path
        self.image = load_image(self.image_path)
        self.position = position
        self.radius = radius
        self.weapon = weapon
        self.damage = damage
        self.original_image = load_image(self.image_path)
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
        self.impact_shards = []  # Changed from particles to shards

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
                    self._create_impact_shards(projectile.position)
                    self.target.take_damage(self.damage)
                if not self.penetration:
                    self.projectiles.remove(projectile)
                if self.penetration:
                    projectile.penetration -= 1
                    if projectile.penetration == 0:
                        self.projectiles.remove(projectile)
        self._update_impact_shards()

    def _create_impact_shards(self, position):
        """Create cheese-themed impact shards"""
        for _ in range(8):
            self.impact_shards.append({
                'pos': list(position),
                'vel': [random.uniform(-5, 5), random.uniform(-5, 5)],
                'lifetime': random.randint(50, 300),  # Shorter lifetime than firefly
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3),  # Smaller than firefly shards
                'color': (255, 245, 200)  # Pale cheese color
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
                    projectile.penetration = 4
                self.projectiles.append(projectile)
                self.last_shot_time = pygame.time.get_ticks()


class Ratman:
    sfx_squeak = load_sound("assets/mouse-squeak.mp3")

    def __init__(self, position, radius=150, weapon='cheese', damage=1, image_path=None, projectile_image=None,
                 shoot_interval=500):
        self.image_path = image_path
        self.image = load_image(self.image_path)
        self.position = position
        self.radius = radius
        self.weapon = weapon
        self.damage = damage
        self.original_image = load_image(self.image_path)
        self.rect = self.image.get_rect(center=position)
        self.angle = 0
        self.target = None
        self.projectiles = []
        self.projectile_image = projectile_image
        self.shoot_interval = shoot_interval
        self.last_shot_time = 0
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.curr_bottom_upgrade = 0
        self.sell_amt = 1300
        self.impact_shards = []  # Changed from particles to shards
        self.robo = False

        self.get_upgrades()

    def get_upgrades(self):
        # Super Radius
        if self.curr_top_upgrade == 1:
            self.radius = 225
            if self.curr_bottom_upgrade == 0:
                self.image_path = "assets/ratman+supervision.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 1:
                self.image_path = "assets/ratman+fondue.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 2:
                self.image_path = "assets/ratman+plasma.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
        # Super Speed
        elif self.curr_top_upgrade == 2:
            self.shoot_interval = 250
            self.radius = 225
            if self.curr_bottom_upgrade == 0:
                self.image_path = "assets/ratman_superspeed.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 1:
                self.image_path = "assets/ratman+fondue+superspeed.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 2:
                self.image_path = "assets/ratman+plasma+speed.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
        # RoboRat
        elif self.curr_top_upgrade == 3 and self.curr_bottom_upgrade < 3:
            self.robo = True
            self.shoot_interval = 250
            self.radius = 250
            self.image_path = "assets/ratman+roborat.png"
            self.image = load_image(self.image_path)
            self.original_image = load_image(self.image_path)
        # Fondue
        if self.curr_bottom_upgrade == 1:
            self.weapon = 'fondue'
            self.damage = 4
            self.projectile_image = "assets/fondue.png"
            if self.curr_top_upgrade == 0:
                self.image_path = "assets/ratman+fondue.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 1:
                self.image_path = "assets/ratman+fondue.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 2:
                self.image_path = "assets/ratman+fondue+superspeed.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
        # Plasmatic Provolone
        elif self.curr_bottom_upgrade == 2:
            self.weapon = 'plasma'
            self.damage = 6
            self.projectile_image = "assets/plasma_proj.png"
            if self.curr_top_upgrade == 0:
                self.image_path = "assets/ratman+plasma.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 1:
                self.image_path = "assets/ratman+plasma.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 2:
                self.image_path = "assets/ratman+plasma+speed.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
        # Cheese God
        elif self.curr_bottom_upgrade == 3 and self.curr_top_upgrade < 3:
            self.weapon = 'god'
            self.damage = 8
            self.shoot_interval = 125
            self.projectile_image = "assets/cheesegod_proj.png"
            self.image_path = "assets/ratman+cheesegod.png"
            self.image = load_image(self.image_path)
            self.original_image = load_image(self.image_path)

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

    def _create_impact_shards(self, position):
        """Create cheese-themed impact shards"""
        for _ in range(8):
            self.impact_shards.append({
                'pos': list(position),
                'vel': [random.uniform(-5, 5), random.uniform(-5, 5)],
                'lifetime': random.randint(50, 300),
                'start_time': pygame.time.get_ticks(),
                'radius': random.randint(1, 3),
                'color': (255, 245, 200)
            })

    def _update_impact_shards(self):
        """Update shard positions and lifetimes"""
        current_time = pygame.time.get_ticks()
        for shard in self.impact_shards[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                self.impact_shards.remove(shard)
            else:
                shard['vel'][1] += 0.3  # gravity effect
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
            angle = elapsed * 0.3
            shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
            pygame.draw.rect(
                pygame.transform.rotate(shard_surface, angle),
                (*shard['color'], alpha),
                (0, 0, shard['radius'], shard['radius'] * 2)
            )
            screen.blit(shard_surface, shard['pos'])

    def shoot(self):
        # how fast we’re allowed to fire
        interval = self.shoot_interval / game_speed_multiplier
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
                proj = Projectile(
                    position=self.position,
                    target=self.target,
                    speed=10,
                    damage=self.damage,
                    image_path=self.projectile_image
                )
                proj.vx = math.cos(ang_rad) * proj.speed
                proj.vy = math.sin(ang_rad) * proj.speed

            elif self.weapon == 'fondue':
                proj = Projectile(
                    position=self.position,
                    target=self.target,
                    speed=5,
                    damage=self.damage,
                    image_path=self.projectile_image,
                )
                proj.penetration = 2,
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
                    proj = Projectile(
                        position=(ox, oy),
                        target=self.target,
                        speed=10,
                        damage=self.damage,
                        image_path=self.projectile_image
                    )
                    proj.vx = math.cos(arm_rad) * proj.speed
                    proj.vy = math.sin(arm_rad) * proj.speed

                elif self.weapon == 'fondue':
                    proj = Projectile(
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
        self.original_image = load_image(image_path or "assets/mortar_base.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        # Rotation angle
        self.angle = 0
        self.radius = 0
        self.explosion_radius = 75
        # Target marker image and position
        self.target_image = load_image("assets/strike.png")
        self.explosion_sfx = load_sound("assets/explosion_sfx.mp3")
        self.target_pos = list(position)
        self.dragging = False
        self.is_selected = False
        # Firing
        self.shoot_interval = 6500  # ms
        self.last_shot_time = 0
        # Damage
        self.damage = 3
        # Upgrade
        self.curr_top_upgrade = 0
        self.curr_bottom_upgrade = 0
        # Explosion schedule
        self.explosions = []
        # Sell value
        self.sell_amt = 375

        self.get_upgrades()

    def get_upgrades(self):
        # Bigger Bombs
        if self.curr_top_upgrade == 1:
            self.explosion_radius = 100
            if self.curr_bottom_upgrade == 0:
                self.image_path = "assets/mortar+biggerbombs.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 1:
                self.image_path = "assets/mortar_biggerbombs+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 2:
                self.image_path = "assets/mortar_biggerbombs+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 3:
                self.image_path = "assets/mortar+triple+bigger.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
        # Napalm
        elif self.curr_top_upgrade == 2:
            self.damage = 5
            self.explosion_radius = 100
            self.EXPLOSION_DURATION = 500
            if self.curr_bottom_upgrade == 0:
                self.image_path = "assets/mortar+napalm.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 1:
                self.image_path = "assets/mortar+napalm+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 2:
                self.image_path = "assets/mortar+napalm+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_bottom_upgrade == 3:
                self.image_path = "assets/mortar+triple+napalm.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
        # Tzar Bomba
        elif self.curr_top_upgrade == 3 and self.curr_bottom_upgrade < 3:
            self.explosion_radius = 250
            self.damage = 8
            self.EXPLOSION_DURATION = 500
            self.explosion_sfx = load_sound("assets/tzar_sfx.mp3")
            self.image_path = "assets/mortar+tzar.png"
            self.image = load_image(self.image_path)
            self.original_image = load_image(self.image_path)
        # Rapid Reload
        if self.curr_bottom_upgrade == 1:
            self.shoot_interval = 3500
            if self.curr_top_upgrade == 0:
                self.image_path = "assets/mortar+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 1:
                self.image_path = "assets/mortar_biggerbombs+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 2:
                self.image_path = "assets/mortar+napalm+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
        # Cluster Bombs
        elif self.curr_bottom_upgrade == 2:
            self.shoot_interval = 3500
            if self.curr_top_upgrade == 0:
                self.image_path = "assets/mortar+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 1:
                self.image_path = "assets/mortar_biggerbombs+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 2:
                self.image_path = "assets/mortar+napalm+rapid.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
        # Triple Barrel
        elif self.curr_bottom_upgrade == 3 and self.curr_top_upgrade < 3:
            self.shoot_interval = 3500
            if self.curr_top_upgrade == 0:
                self.image_path = "assets/mortar+triple.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 1:
                self.image_path = "assets/mortar+triple+bigger.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)
            elif self.curr_top_upgrade == 2:
                self.image_path = "assets/mortar+triple+napalm.png"
                self.image = load_image(self.image_path)
                self.original_image = load_image(self.image_path)

    def update(self, enemies):
        now = pygame.time.get_ticks()
        # Shooting
        if now - self.last_shot_time >= self.shoot_interval / game_speed_multiplier:
            self.last_shot_time = now
            # spawn main explosion
            self._spawn_explosion(self.target_pos, self.explosion_radius, self.damage, enemies)
            # cluster bombs
            if self.curr_bottom_upgrade >= 2:
                for i in range(5):
                    angle = i * (2 * math.pi / 5)
                    ox = self.target_pos[0] + math.cos(angle) * self.explosion_radius
                    oy = self.target_pos[1] + math.sin(angle) * self.explosion_radius
                    self._spawn_explosion((ox, oy), self.explosion_radius * 0.33, self.damage * 0.33, enemies)
            # triple barrel
            if self.curr_bottom_upgrade == 3:
                for i in (-1, 1):
                    pos = self.target_pos[0], self.target_pos[1] + i * self.explosion_radius
                    self._spawn_explosion(pos, self.explosion_radius, self.damage, enemies)
                    for j in range(5):
                        angle = j * (2 * math.pi / 5)
                        ox = pos[0] + math.cos(angle) * self.explosion_radius
                        oy = pos[1] + math.sin(angle) * self.explosion_radius
                        self._spawn_explosion((ox, oy), self.explosion_radius * 0.33, self.damage * 0.33, enemies)
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
        self.explosion_sfx.play()
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

        explosion = {
            'pos': pos,
            'radius': radius,
            'start': pygame.time.get_ticks(),
            'particles': parts
        }

        # napalm fire effect
        if self.curr_top_upgrade >= 2:
            fire = []
            for _ in range(30):
                angle = random.uniform(-math.pi / 3, math.pi + math.pi / 3)
                speed = random.uniform(radius * 0.2, radius * 0.5)
                fire.append({
                    'pos': [pos[0], pos[1]],
                    'vel': [math.cos(angle) * speed, -abs(math.sin(angle) * speed) * 0.5],
                    'life': self.EXPLOSION_DURATION * 1.5,
                    'color': (255, random.randint(80, 160), 0)
                })
            explosion['fire_particles'] = fire

        self.explosions.append(explosion)

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

        # Draw explosions (with napalm fire when upgraded)
        now = pygame.time.get_ticks()
        for exp in self.explosions[:]:
            elapsed = now - exp['start']
            if elapsed > self.EXPLOSION_DURATION:
                self.explosions.remove(exp)
                continue

            p = elapsed / self.EXPLOSION_DURATION
            alpha = int(255 * (1 - p))

            # flash + ring
            fr = exp['radius'] * (0.5 + 0.5 * p)
            surf = pygame.Surface((fr * 2, fr * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 200, 50, alpha // 2), (fr, fr), int(fr))
            pygame.draw.circle(surf, (255, 100, 0, alpha), (fr, fr), int(exp['radius']), 3)
            screen.blit(surf, (exp['pos'][0] - fr, exp['pos'][1] - fr))

            # debris particles
            for part in exp['particles'][:]:
                t = elapsed / part['life']
                if t >= 1:
                    exp['particles'].remove(part)
                    continue
                part['pos'][0] += part['vel'][0] * (1 / 60)
                part['pos'][1] += part['vel'][1] * (1 / 60)
                pa = int(alpha * (1 - t))
                pygame.draw.circle(
                    screen,
                    (255, 220, 100, pa),
                    (int(part['pos'][0]), int(part['pos'][1])),
                    max(1, int(exp['radius'] * 0.05 * (1 - t)))
                )

            # napalm fire particles (only if upgraded and present)
            if self.curr_top_upgrade >= 2 and 'fire_particles' in exp:
                for fire in exp['fire_particles'][:]:
                    tf = (now - exp['start']) / fire['life']
                    if tf >= 1:
                        exp['fire_particles'].remove(fire)
                        continue
                    # rising, flickering flames
                    fire['pos'][0] += fire['vel'][0] * (1 / 60)
                    fire['pos'][1] += fire['vel'][1] * (1 / 60)
                    size = random.uniform(2, 6) * (1 - tf)
                    fa = int(255 * (1 - tf))
                    pygame.draw.circle(
                        screen,
                        (*fire['color'], fa),
                        (int(fire['pos'][0]), int(fire['pos'][1])),
                        int(size)
                    )

    def shoot(self):
        pass


class ImportTruck:
    def __init__(self, position, path, health):
        self.position = position
        self.speed = 0.75
        self.health = health
        self.path = path
        self.original_image = load_image("assets/import_truck.png")
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
        self.image = load_image(self.image_path)
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
        self.sfx_horn = load_sound("assets/truck_honk.mp3")
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
        investment_bg = load_image("assets/investment_window.png")
        investment_bg_no_loans = load_image("assets/investment_window_no_loans.png")
        investment_no_prov = load_image("assets/investment_window_provoloan_unavail.png")
        investment_no_brie = load_image("assets/investment_window_briefund_unavail.png")
        investment_both_unavail = load_image("assets/investment_window_both_unavail.png")
        investment_imports = load_image("assets/investment_window_imports.png")
        french = load_image("assets/french_avail.png")
        french_unavail = load_image("assets/french_unavail.png")
        polish = load_image("assets/polish_avail.png")
        polish_unavail = load_image("assets/polish_unavail.png")
        dutch = load_image("assets/dutch_avail.png")
        dutch_unavail = load_image("assets/dutch_unavail.png")
        import_select = load_image("assets/import_select.png")
        add_investment = load_image("assets/enter_investment_window.png")
        withdraw_window = load_image("assets/withdraw_window.png")
        select_loan = load_image("assets/loan_highlight.png")
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

        # Import handling
        if self.curr_top_upgrade > 1:
            # France
            if 484 <= mouse[0] <= 484 + 90 and 407 <= mouse[1] <= 407 + 62 and self.french:
                scrn.blit(import_select, (484, 407))
                if detect_single_click():
                    if money >= 200:
                        self.french = False
                        money -= 200
                        self.send_import(10)
            # Poland
            if 595 <= mouse[0] <= 595 + 90 and 407 <= mouse[1] <= 407 + 62 and self.polish:
                scrn.blit(import_select, (593, 407))
                if detect_single_click():
                    if money >= 1000:
                        self.polish = False
                        money -= 1000
                        self.send_import(60)
            # Netherlands
            if 707 <= mouse[0] <= 707 + 90 and 407 <= mouse[1] <= 407 + 62 and self.dutch:
                scrn.blit(import_select, (705, 407))
                if detect_single_click():
                    if money >= 2000:
                        self.dutch = False
                        money -= 2000
                        self.send_import(150)

        # Loan handling (Cheese Fargo upgrades)
        if self.curr_bottom_upgrade > 1:
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

    def send_import(self, health_amt):
        spawn_pos = (238 + random.randint(-16, 16), 500)
        offset_path = [(x + random.randint(-8, 8), y) for (x, y) in house_path]
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
        self.curr_round = current_wave
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
        invest_btn = load_image("assets/invest_box.png")
        repossessed_window = load_image("assets/repossessed_window.png")
        scrn.blit(self.image, self.rect.topleft)

        # If this bank is selected and its investment window is not open, show its invest button.
        if self.is_selected and not self.investment_window_open:
            if self.curr_bottom_upgrade < 2:
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
        self.image = load_image(image_path) if image_path else None
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
        self.image = load_image(self.image_path)
        self.position = position
        self.radius = radius
        self.damage = damage
        self.explosion_sfx = load_sound("assets/explosion_sfx.mp3")
        self.original_image = load_image(self.image_path)
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
        self.shoot_sound = load_sound(self.sound_path)
        self.reload_path = "assets/commando_reload.mp3"
        self.reload_sound = load_sound(self.reload_path)

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
                self.explosion_damage = 0.25
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


class RatFrost:
    sfx_frost = load_sound("assets/frost_sfx.mp3")
    sfx_freeze = load_sound("assets/slow_sfx.mp3")

    def __init__(self, position):
        self.position = position
        self.base_image = load_image("assets/base_frost.png")
        self.image = self.base_image
        self.rect = self.image.get_rect(center=position)
        self.sell_amt = 100
        self.angle = 0

        # Base stats
        self.radius = 75
        self.slow_multiplier = 0.75
        self.radius_image = load_image("assets/frost_freeze_radius_75.png")
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
            return 750 / game_speed_multiplier
        if self.curr_top_upgrade >= 1:
            return 1500 / game_speed_multiplier
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
            screen.blit(load_image(radius_img), (self.position[0] - 75, self.position[1] - 75))
        else:
            screen.blit(load_image(radius_img), (self.position[0] - 100, self.position[1] - 100))
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
        self.base_image = load_image(self.image_path)
        self.shoot_image = load_image(self.image_path_shoot)
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
        self.shoot_sound = load_sound("assets/sniper_shoot.mp3")
        self.sell_amt = 175

    def select_target(self, enemies):
        """
        Select a target from the list of enemies.
        Prioritize CentipedeEnemy regardless of health.
        If none are found, select an enemy that has a health attribute and is still alive (health > 0).
        """
        centipedes = [enemy for enemy in enemies if isinstance(enemy, CentipedeEnemy)]
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

        # Scale the effective interval by game_speed_multiplier.
        scaled_interval = effective_interval / game_speed_multiplier

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
            global_impact_particles.append(particle)

    def render(self, screen):
        screen.blit(self.image, self.rect.topleft)
        for projectile in self.projectiles:
            projectile.render(screen)


class WizardTower:
    sfx_zap = load_sound("assets/zap_sfx.mp3")
    sfx_explosion = load_sound("assets/explosion_sfx.mp3")

    def __init__(self, position):
        self.image_path = "assets/wizard_base.png"
        self.position = position
        self.base_image = load_image(self.image_path)
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
            self.image = load_image("assets/orb_projectile.png")
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
                delta = (current_time - self.last_update) * game_speed_multiplier
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
                delta = (current_time - self.last_update) * game_speed_multiplier
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
            return pygame.time.get_ticks() - self.start_time > self.duration * (2 / game_speed_multiplier)

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
            scaled_interval = interval / game_speed_multiplier

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
        delta = (current_time - self.last_frame_time) * game_speed_multiplier
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

        if UpgradeFlag and curr_upgrade_tower == self:
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
        delta = (now - self.last_frame_time) * game_speed_multiplier

        angles_to_remove = []
        for angle in self.orb_respawn_timers.copy():
            elapsed = (now - self.orb_respawn_timers[angle]) * game_speed_multiplier
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

        if RoundFlag and (now - self.last_fire_time) * game_speed_multiplier > self.fire_interval:
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
    def __init__(self, position, image_path=None):
        self.position = position
        self.image_path = "assets/base_minigun.png"
        self.image = load_image(self.image_path)
        self.original_image = self.image
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
        self.beam_sfx = load_sound("assets/laser_fire.mp3")
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
            self.current_spool = min(self.max_spool, self.current_spool + (self.spool_rate * game_speed_multiplier) * dt)
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
                projectile.image = load_image("assets/projectile_bullet_flame.png")
                projectile.original_image = load_image("assets/projectile_bullet_flame.png")
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
            effective_beam_interval = 250 / game_speed_multiplier / 1000.0  # converting ms to seconds if needed
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
                                       speed=10 * game_speed_multiplier,
                                       damage=self.damage,
                                       flame=flame)
        self.projectiles.append(projectile)
        shoot_sound = load_sound("assets/minigun_shoot.mp3")
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
        self.original_image = load_image("assets/projectile_bullet.png")
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
        self.image = load_image(self.image_path)
        self.original_image = load_image(self.image_path)
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
        self.riff_sfx = load_sound("assets/riff1.mp3")
        self.riff_channel = pygame.mixer.Channel(4)
        # Flag to track if riff_longer is currently playing
        self.riff_playing = False
        self.stun_sfx = load_sound("assets/dungbeetle_shield.mp3")
        # Solo upgrade variables:
        self.solo_icon_visible = True  # will be true at the start of each round if bottom upgrade == 2
        self.solo_active = False
        self.solo_timer = None
        self.lightning_end_time = None
        self.original_riff_interval = riff_interval
        self.original_blast_radius = riff_blast_radius
        self.original_radius = radius
        self.solo_channel = pygame.mixer.Channel(0)
        self.solo_sound = load_sound("assets/solo.mp3")
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
        scaled_interval = self.riff_interval / game_speed_multiplier
        scaled_duration = self.blast_duration / game_speed_multiplier

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
        if self.solo_active and self.solo_timer and current_time >= self.solo_timer + (20000 / game_speed_multiplier):
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
            self.riff_sfx = load_sound("assets/riff_longer.mp3")
            if not self.riff_playing and not self.solo_active:
                try:
                    if not self.riff_channel.get_busy():
                        if pygame.time.get_ticks() - self.last_riff_time >= 1500:
                            mixer.music.pause()
                            self.riff_channel.set_volume(user_volume * .75)
                            self.riff_channel.play(self.riff_sfx, loops=-1)
                            self.last_riff_time = pygame.time.get_ticks()
                except Exception:
                    print("Warning: Failed to load Ozbourne riff")
                    return
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
                    if isinstance(enemy, DungBeetleBoss) or isinstance(enemy, BeetleEnemy) or isinstance(enemy, RoachQueenEnemy):
                        return
                    current_time = pygame.time.get_ticks()
                    spawn_shard(enemy.position, count=3)
                    self.stun_sfx.play()
                    # Save the enemy's current speed if not already stunned
                    if not hasattr(enemy, "stun_end_time") or current_time >= enemy.stun_end_time:
                        enemy.original_speed = enemy.speed
                    enemy.speed = 0
                    enemy.stun_end_time = current_time + 1000 / game_speed_multiplier

    def render(self, screen):
        tower_rect = self.image.get_rect(center=self.position)
        screen.blit(self.image, tower_rect)
        # Draw the rock icon if this Ozbourne has the solo upgrade.
        if self.curr_bottom_upgrade == 2 and self.solo_icon_visible:
            rock_icon = load_image("assets/rock_icon.png")
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
        self.image = load_image(self.image_path)
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
            'damage': load_image("assets/damage_boost.png"),
            'radius': load_image("assets/radius_boost.png"),
            'speed': load_image("assets/speed_boost.png")
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


class AntEnemy:

    def __init__(self, position, health, speed, path, image_path):
        self.position = position
        self.health = health
        self.speed = speed
        self.path = path
        self.original_image = load_image(image_path)
        self.sfx_splat = load_sound("assets/splat_sfx.mp3")
        self.img_death = load_image("assets/splatter.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        # global_impact_particles = []  # New: Particle storage

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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money
        self.health -= damage
        self.show_damage_indicator(damage)
        spawn_shard(
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
            money += 2

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)


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
        # global_impact_particles = []  # List to store shard particles

    def move(self):
        """
        Move the beetle along its predefined path.
        """
        global user_health
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
            user_health -= self.base_health + self.total_armor_layers * self.current_layer_health
            self.is_alive = False

    def update_orientation(self, direction_x, direction_y):
        """
        Rotate the image so that the beetle faces its moving direction.
        """
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def spawn_shards(self, count=5):
        global global_impact_particles
        """
        Spawn a burst of shards to simulate armor breaking.
        Each shard is represented as a dictionary with position, velocity, lifetime, and start_time.
        """
        for _ in range(count):
            spawn_shard(self.position, count=5)

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
                # Update position
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                # Fade out effect: alpha decreases over time
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (255, 255, 255, alpha)
                # Create a surface for the shard
                shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

    def render(self, screen: pygame.Surface):
        """
        Render the beetle on the given screen along with shard particles if any.
        """
        screen.blit(self.image, self.rect.topleft)

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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money
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
            self.original_image = load_image("assets/beetle_damage3.png")
            self.image = self.original_image

            # Apply full damage to base health
            self.health -= damage
            self.show_damage_indicator(damage)
            if self.health <= 0:
                self.is_alive = False
                game_stats.global_kill_total["count"] += 1
                money += 10
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
                    self.show_damage_indicator(damage)
        else:
            # No armor remains; apply damage directly to base health.
            self.health -= damage
            self.show_damage_indicator(damage)

        if self.health <= 0:
            self.is_alive = False
            game_stats.global_kill_total["count"] += 1
            money += 10


class HornetEnemy:

    def __init__(self, position, health, speed, path, image_path):
        self.position = position
        self.health = health
        self.speed = speed
        self.path = path
        self.original_image = load_image(image_path)
        self.image = self.original_image
        self.sfx_splat = load_sound("assets/splat_sfx.mp3")
        self.img_death = load_image("assets/splatter.png")
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        # global_impact_particles = []  # NEW: Particle storage

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
    def spawn_shards(self, count=5):
        global global_impact_particles
        for _ in range(count):
            spawn_shard(self.position, count=5)

    def update_shards(self, screen):
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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()  # NEW: Create particles on hit
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            game_stats.global_kill_total["count"] += 1
            money += 4

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)


class SpiderEnemy:
    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")

    def __init__(self, position, path):
        self.position = position
        self.health = 5
        self.speed = 1.5
        self.path = path
        self.frames = ["assets/spider_frames/spider0.png", "assets/spider_frames/spider1.png",
                       "assets/spider_frames/spider2.png", "assets/spider_frames/spider3.png",
                       "assets/spider_frames/spider4.png"]
        self.current_frame = 0
        self.frame_duration = 175  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        self.original_image = load_image("assets/spider_frames/spider0.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        # global_impact_particles = []  # NEW: Particle storage

    def move(self):
        global user_health
        self.update_animation()
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
    def spawn_shards(self, count=5):
        global global_impact_particles
        for _ in range(count):
            spawn_shard(self.position, count=5)

    def update_shards(self, screen):
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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()  # NEW: Create particles on hit
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            money += 6
            game_stats.global_kill_total["count"] += 1

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = load_image(self.frames[self.current_frame])
            self.original_image = load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)



class FireflyEnemy:
    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")
    MAX_RADIUS = 75
    MIN_RADIUS = 0
    BASE_COLOR = (247, 217, 59)

    def __init__(self, position, path):
        self.position = position
        self.health = 20
        self.speed = 1
        self.path = path
        self.frames = ["assets/firefly_frames/firefly0.png", "assets/firefly_frames/firefly1.png",
                       "assets/firefly_frames/firefly2.png", "assets/firefly_frames/firefly3.png",
                       "assets/firefly_frames/firefly4.png", "assets/firefly_frames/firefly5.png",
                       "assets/firefly_frames/firefly6.png"]
        self.current_frame = 0
        self.frame_duration = 75  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        self.original_image = load_image("assets/firefly_frames/firefly0.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        # global_impact_particles = []  # NEW: Particle storage
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
            global_impact_particles.append(particle)

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

    def move(self):
        global user_health
        self.update_animation()
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
        self.update_glow_animation()

    # NEW: Shard particle methods (same as AntEnemy)
    def spawn_shards(self, count=5):
        global global_impact_particles
        for _ in range(count):
            spawn_shard(self.position, count=5)

    def update_shards(self, screen):
        current_time = pygame.time.get_ticks()
        for shard in global_impact_particles[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                global_impact_particles.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                color = (247, 217, 59, alpha)
                shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money
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
            money += 10
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
            global_impact_particles.append(particle)

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = load_image(self.frames[self.current_frame])
            self.original_image = load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

    def render(self, screen):
        if self.is_alive:
            self.render_glow(screen)  # Draw glow first
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)


class DragonflyEnemy:
    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")

    def __init__(self, position, path):
        self.position = position
        self.health = 3
        self.speed = 3
        self.path = path
        self.frames = ["assets/dragonfly_frames/dragonfly0.png", "assets/dragonfly_frames/dragonfly1.png",
                       "assets/dragonfly_frames/dragonfly2.png", "assets/dragonfly_frames/dragonfly3.png"]
        self.current_frame = 0
        self.frame_duration = 75  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        self.original_image = load_image("assets/dragonfly_frames/dragonfly0.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        # global_impact_particles = []  # NEW: Particle storage

    def move(self):
        global user_health
        self.update_animation()
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
    def spawn_shards(self, count=5):
        spawn_shard(self.position, count=5)

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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()  # NEW: Create particles on hit
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            money += 10
            game_stats.global_kill_total["count"] += 1

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = load_image(self.frames[self.current_frame])
            self.original_image = load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)


class MantisBoss:
    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")

    def __init__(self, position, path):
        self.position = position
        self.health = 250
        self.speed = .15
        self.path = path
        self.radius = 250
        self.frames = []
        for i in range(0, 15):
            self.frames.append(f"assets/mantis_frames/mantis{i}.png")
        self.current_frame = 0
        self.frame_duration = 125  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        self.original_image = load_image("assets/mantis_frames/mantis0.png")
        self.image = self.original_image
        self.target = None
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        self.shoot_interval = 15000
        self.shoot_sound = load_sound("assets/mantis_shoot.mp3")
        self.last_shot_time = 0
        self.projectiles = []

    def move(self):
        global user_health
        self.update_animation()

        # === Targeting ===
        self.target = None
        potential_targets = []
        for enemy in towers:
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
            for enemy in towers:
                enemy_center = enemy.rect.center
                dist = math.hypot(projectile.position[0] - enemy_center[0],
                                  projectile.position[1] - enemy_center[1])
                if dist < enemy.rect.width / 2:
                    projectile.hit = True
                    spawn_shard(projectile.position, color=(105, 160, 25), count=25)
                    if hasattr(enemy, "shoot_interval"):
                        apply_mantis_debuff(enemy)
            if projectile.hit:
                self.projectiles.remove(projectile)

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
    def spawn_shards(self, count=5):
        spawn_shard(self.position, count=5)

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def shoot(self):
        scaled_interval = self.shoot_interval / game_speed_multiplier
        if self.target and pygame.time.get_ticks() - self.last_shot_time >= scaled_interval:
            self.shoot_sound.play()
            proj = Projectile(self.position, self.target, speed=5, damage=0, image_path="assets/mantis_ball.png")
            self.projectiles.append(proj)
            self.last_shot_time = pygame.time.get_ticks()

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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money
        self.health -= damage
        self.show_damage_indicator(damage)
        self.spawn_shards()  # NEW: Create particles on hit
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            money += 10
            game_stats.global_kill_total["count"] += 1

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = load_image(self.frames[self.current_frame])
            self.original_image = load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)

        for projectile in self.projectiles:
            projectile.render(screen)


class TermiteEnemy:

    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")

    def __init__(self, path, position=None):
        """
        Initializes the TermiteEnemy.
        :param path: A list of (x, y) tuples representing the enemy's path.
        :param position: Optional starting position; if None, uses the first point in the path.
        """
        self.path = path
        if position is None:
            self.position = path[0]
            self.current_target = 1
        else:
            self.position = position
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

        self.health = 1
        self.speed = 1  # Movement speed per update.
        self.image = load_image("assets/termite.png")
        self.original_image = self.image
        self.rect = self.image.get_rect(center=self.position)
        self.rotated_image = self.image  # Will be updated with rotation.
        self.is_alive = True

        global game_speed_multiplier
        # Use virtual time (real ticks * game_speed_multiplier) for burrow timing.
        self.next_burrow_time = 0
        self.is_burrowed = False
        self.burrow_start_time = 0
        self.burrow_duration = 1000  # Duration in virtual ms

    def move(self):
        """Moves normally along the path."""
        global user_health

        if self.is_burrowed:
            if pygame.time.get_ticks() - self.burrow_start_time >= self.burrow_duration:
                self.finish_burrow()
                self.is_burrowed = False
        else:
            if pygame.time.get_ticks() >= self.next_burrow_time:
                self.start_burrow()

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

        if self.is_burrowed:
            spawn_shard(self.position, color=(139, 69, 19), count=1)

    def update_orientation(self, direction_x, direction_y):
        angle = math.degrees(math.atan2(-direction_y, direction_x))
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def start_burrow(self):
        """
        Initiates the burrow:
          - Plays the pop sound.
          - Spawns brown particles at the current location.
          - Sets the termite as burrowed and chooses a random virtual burrow duration (1000–3000 ms).
        """
        global game_speed_multiplier
        dig_sfx = load_sound("assets/dig.mp3")
        dig_sfx.play()
        spawn_shard(self.position, color=(139, 69, 19), count=10)
        self.is_burrowed = True
        self.burrow_start_time = pygame.time.get_ticks()
        self.burrow_duration = random.randint(1500, 5500) / game_speed_multiplier
        self.speed = random.uniform(.1, 1.0)

    def finish_burrow(self):
        """
        Finishes burrowing:
          - Advances the termite five waypoints ahead. If that index equals the path end,
            reappear at the last point before the final.
          - Spawns particles at the new location.
          - Resets burrow state and sets the next burrow virtual time.
        """
        global game_speed_multiplier
        pop_sound = load_sound("assets/pop.mp3")
        pop_sound.play()
        spawn_shard(self.position, color=(139, 69, 19), count=10)
        self.is_burrowed = False
        self.next_burrow_time = pygame.time.get_ticks() + random.randint(4000, 8000) / game_speed_multiplier
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
            spawn_shard(self.position)
            import game_stats  # Ensure game_stats is imported
            game_stats.global_kill_total["count"] += 1
            global money
            money += 4

    def show_damage_indicator(self, damage):
        """
        Displays damage by spawning red particles at the termite's location.
        """
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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def render(self, screen):
        """
        Draws the termite on the screen only if it is not burrowed.
        """
        if not self.is_burrowed:
            if self.is_alive:
                screen.blit(self.image, self.rect.topleft)
            else:
                screen.blit(self.img_death, self.rect.topleft)


class DungBeetleBoss:
    sfx_splat = load_sound("assets/splat_sfx.mp3")
    img_death = load_image("assets/splatter.png")
    sfx_squeak = load_sound("assets/dungbeetle_squeak.mp3")
    sfx_shield = load_sound("assets/dungbeetle_shield.mp3")
    sfx_death = load_sound("assets/dungbeetle_death.mp3")

    def __init__(self, position, path):
        self.position = position
        self.health = 175
        self.speed = 0.15
        self.path = path
        self.frames = ["assets/dungbeetle_frames/dung0.png", "assets/dungbeetle_frames/dung1.png",
                       "assets/dungbeetle_frames/dung2.png", "assets/dungbeetle_frames/dung3.png",
                       "assets/dungbeetle_frames/dung4.png", "assets/dungbeetle_frames/dung5.png",
                       "assets/dungbeetle_frames/dung6.png", "assets/dungbeetle_frames/dung7.png",
                       "assets/dungbeetle_frames/dung8.png", "assets/dungbeetle_frames/dung9.png",
                       "assets/dungbeetle_frames/dung10.png"]
        self.current_frame = 0
        self.frame_duration = 250  # milliseconds per frame
        self.last_frame_update = pygame.time.get_ticks()
        self.original_image = load_image("assets/dungbeetle_frames/dung0.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        # global_impact_particles = []  # for hit/blue particle effects

        # Squeak timer: play squeak sound every random interval (3000-10000ms)
        self.next_squeak_time = pygame.time.get_ticks() + random.randint(2000, 5000)

        # Health threshold for triggering shield effects every 10 points lost.
        self.next_threshold = self.health - 60

        # For trailing particles when health is below 10
        self.trail_particles = []

    def move(self):
        global user_health
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
        if self.current_target < len(self.path):
            target_x, target_y = self.path[self.current_target]
            dx = target_x - self.position[0]
            dy = target_y - self.position[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance != 0:
                direction_x = dx / distance
                direction_y = dy / distance
            else:
                direction_x = direction_y = 0
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
        global global_impact_particles
        # Standard shards spawned when taking damage.
        for _ in range(count):
            spawn_shard(self.position, count=5)

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
            global_impact_particles.append(particle)

    def update_shards(self, screen):
        current_time = pygame.time.get_ticks()
        for shard in global_impact_particles[:]:
            elapsed = current_time - shard['start_time']
            if elapsed > shard['lifetime']:
                global_impact_particles.remove(shard)
            else:
                shard['pos'][0] += shard['vel'][0]
                shard['pos'][1] += shard['vel'][1]
                alpha = max(0, 255 - int((elapsed / shard['lifetime']) * 255))
                # Use particle's color with fading alpha.
                color = (*shard['color'][:3], alpha) if 'color' in shard else (255, 255, 255, alpha)
                shard_surface = pygame.Surface((shard['radius'] * 2, shard['radius'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(shard_surface, color, (shard['radius'], shard['radius']), shard['radius'])
                screen.blit(shard_surface, (shard['pos'][0], shard['pos'][1]))

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

        speed = random.uniform(0.5, 2)
        vel_x = math.sin(angle_rad) * speed
        vel_y = -math.cos(angle_rad) * speed  # Negative because up is -y in Pygame

        indicator = {
            'surface': text_surface,
            'pos': list(self.rect.center) + [0, -20],
            'vel': [vel_x, vel_y],
            'lifetime': random.randint(100, 250),
            'start_time': pygame.time.get_ticks()
        }
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money, enemies
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
                enemies.append(new_beetle)
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
                enemies.append(new_beetle)
            self.sfx_death.play()
            money += 100
            game_stats.global_kill_total["count"] += 1

    def update_animation(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_frame_update >= self.frame_duration / game_speed_multiplier:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = load_image(self.frames[self.current_frame])
            self.original_image = load_image(self.frames[self.current_frame])
            self.last_frame_update = current_time

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(self.img_death, self.rect.topleft)
        # Render trail particles (with refined blue effect)
        for particle in self.trail_particles:
            elapsed = pygame.time.get_ticks() - particle['start_time']
            alpha = max(0, 255 - int((elapsed / particle['lifetime']) * 255))
            trail_surface = pygame.Surface((particle['radius'] * 2, particle['radius'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (0, 0, 255, alpha), (particle['radius'], particle['radius']),
                               particle['radius'])
            screen.blit(trail_surface, (particle['pos'][0], particle['pos'][1]))


class RoachQueenEnemy:
    def __init__(self, position, path, health=30, speed=0.5):
        self.position = position
        self.health = health
        self.speed = speed
        self.path = path
        self.original_image = load_image("assets/roach_queen.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = 0
        self.is_alive = True
        # Multiplication timing
        self.spawn_time = pygame.time.get_ticks()
        self.last_multiply_time = self.spawn_time + 500  # First multiply after 500ms
        self.multiply_interval = 12000  # Starts at 4000ms, decreases by 500ms down to 500ms
        self.has_multiplied_initially = False
        self.total_spawned = 2
        # For spawn animation particles
        self.spawn_particles = []

    def move(self):
        global user_health
        # Move along the path (like AntEnemy)
        if self.current_target < len(self.path):
            target_x, target_y = self.path[self.current_target]
            dx = target_x - self.position[0]
            dy = target_y - self.position[1]
            distance = math.hypot(dx, dy)
            if distance != 0:
                direction_x = dx / distance
                direction_y = dy / distance
            else:
                direction_x, direction_y = 0, 0
            self.position = (self.position[0] + direction_x * self.speed,
                             self.position[1] + direction_y * self.speed)
            self.rect.center = self.position
            self.update_orientation(direction_x, direction_y)
            if distance <= self.speed:
                self.current_target += 1
        if self.current_target >= len(self.path):
            self.is_alive = False
            user_health -= self.health

        # Multiplication logic
        current_time = pygame.time.get_ticks()
        if not self.has_multiplied_initially and current_time - self.spawn_time >= 500 / game_speed_multiplier:
            self.multiply()
            self.has_multiplied_initially = True
            self.last_multiply_time = current_time
        elif current_time - self.last_multiply_time >= self.multiply_interval / game_speed_multiplier:
            self.multiply()
            self.last_multiply_time = current_time
            self.multiply_interval = max(2000, self.multiply_interval - 500)

        self.update_spawn_particles()

    def multiply(self):
        # Play multiplication sound and create animation particles.
        load_sound("assets/roach_multiply.mp3").play()
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
            enemies.append(roach)
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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        self.health -= damage
        self.show_damage_indicator(damage)
        if self.health <= 0:
            self.is_alive = False
            load_sound("assets/splat_sfx.mp3").play()
            global money
            money += 15
            game_stats.global_kill_total["count"] += 1

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(load_image("assets/splatter.png"), self.rect.topleft)
        self.render_spawn_particles(screen)


# ------------------------------------------------------------
# RoachMinionEnemy class (adjusted to use queen's current_target)
# ------------------------------------------------------------
class RoachMinionEnemy:
    def __init__(self, position, health, path, speed, current_target=0):
        self.position = position
        self.health = health
        self.speed = speed
        self.path = path
        self.original_image = load_image("assets/roach.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.size = self.rect.size
        self.current_target = current_target  # Start from the queen's target
        self.is_alive = True
        # global_impact_particles = []  # For particle effects if needed

    def move(self):
        global user_health
        if self.current_target < len(self.path):
            target_x, target_y = self.path[self.current_target]
            dx = target_x - self.position[0]
            dy = target_y - self.position[1]
            distance = math.hypot(dx, dy)
            if distance != 0:
                direction_x = dx / distance
                direction_y = dy / distance
            else:
                direction_x, direction_y = 0, 0
            self.position = (self.position[0] + direction_x * self.speed,
                             self.position[1] + direction_y * self.speed)
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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

    def take_damage(self, damage, projectile=None):
        global money
        self.health -= damage
        self.show_damage_indicator(damage)
        if self.health <= 0:
            self.is_alive = False
            money += 3
            game_stats.global_kill_total["count"] += 1
            load_sound("assets/splat_sfx.mp3").play()

    def render(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        else:
            screen.blit(load_image("assets/splatter.png"), self.rect.topleft)


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
        self.health = 6

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
        # global_impact_particles = []

    def spawn_shards(self, count=10):
        global global_impact_particles
        """
        Spawn a burst of shard particles to simulate a link breaking.
        """
        for _ in range(count):
            spawn_shard(self.position, count=5)

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
        global user_health

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
            user_health -= int(head.health + tot_health * 2)
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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

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
                money += 10
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
            money += 10
            game_stats.global_kill_total["count"] += 1
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


class MillipedeBoss:
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
            if current_time - self.last_frame_update >= self.frame_duration / game_speed_multiplier:
                self.current_frame = (self.current_frame + 1) % len(segment)
                self.image = load_image(segment[self.current_frame])
                self.last_frame_update = current_time

    def __init__(self, position, path, links=6):
        """
        :param position: Starting position (tuple)
        :param path: List of points (tuples) for the centipede head to follow.
        :param links: Number of link segments between the head and tail.
        """
        self.path = path
        self.current_target = 0  # Index in the path for head movement
        self.base_speed = 0.35
        self.speed = self.base_speed
        self.links = links
        self.health = 30
        self.sfx_channel = pygame.mixer.Channel(3)
        self.millipede_sfx = load_sound("assets/centipede_crawl.mp3")
        self.sfx_playing = False

        # Load images
        head_img = load_image("assets/centipede_boss/head0.png")
        link_img = load_image("assets/centipede_boss/link0.png")
        tail_img = load_image("assets/centipede_boss/tail0.png")

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
        # global_impact_particles = []

    def spawn_shards(self, count=10):
        global global_impact_particles
        """
        Spawn a burst of shard particles to simulate a link breaking.
        """
        for _ in range(count):
            spawn_shard(self.position, count=5)

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
        global user_health
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
            user_health -= 99
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
        if len(global_damage_indicators) < MAX_INDICATORS:
            global_damage_indicators.append(indicator)

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
                money += 200
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
            money += 10
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
            head_img = load_image("assets/centipede_boss/head0.png")
            link_img = load_image("assets/centipede_boss/link0.png")
            tail_img = load_image("assets/centipede_boss/tail0.png")
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
        if self.damage > 0:
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
        # Rotate turret toward target
        original_image = self.image
        dx = self.target.position[0] - self.position[0]
        dy = self.target.position[1] - self.position[1]
        angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(original_image, angle)
        self.rect = self.image.get_rect(center=self.position)
        # Draw tower
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
