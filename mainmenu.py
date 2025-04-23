import pygame
from pygame import mixer

import game_tools
import save_manager
from game_tools import load_image, MAX_SHARDS, MAX_INDICATORS, user_volume

optionFlag = False
warningFlag = False
shard_slider_dragging = False
indicator_slider_dragging = False
music_slider_dragging = False
FullscreenFlag = False

screen = None
game_surface = None
display_info = pygame.display.Info()
full_width, full_height = display_info.current_w, display_info.current_h


def set_window():
    global full_width, full_height, FullscreenFlag

    pygame.init()
    if FullscreenFlag:
        # Create borderless fullscreen using FULLSCREEN | NOFRAME
        snart = pygame.display.set_mode((full_width, full_height), pygame.FULLSCREEN | pygame.NOFRAME | pygame.HWSURFACE | pygame.DOUBLEBUF)
        # Create a fixed-resolution off-screen surface for game rendering
        sneef = pygame.Surface((1280, 720))
    else:
        snart = pygame.display.set_mode((1280, 720),
                                        pygame.HWSURFACE | pygame.DOUBLEBUF)
        sneef = snart

    return snart, sneef


def render_mainmenu(screen: pygame.Surface):
    """
    Draws the main menu screen
    :param screen: pygame.Surface
    :return: none
    """

    font1 = pygame.font.SysFont('chalkduster.ttf', 20)
    version = font1.render('Version 1.0.0', True, (0, 255, 0))
    text_rect1 = version.get_rect()
    screen.blit(version, text_rect1)

    # Draw menu background
    img_menu = pygame.image.load("assets/menu_background.png").convert()

    # Logo
    img_logo = pygame.image.load("assets/mainmenu_logo.png").convert_alpha()

    # Play button screen
    img_play = pygame.image.load("assets/mainmenu_play.png").convert_alpha()

    # Quit button screen
    img_quit = pygame.image.load("assets/mainmenu_quit.png").convert_alpha()

    # render background
    screen.blit(img_menu, (0, 0))

    # render play button
    screen.blit(img_play, (502, 555))

    # render quit button
    screen.blit(img_quit, (502, 635))

    # render logo
    screen.blit(img_logo, (384, 40))


def mainmenu_control(screen: pygame.Surface) -> bool:
    """
    tracks cursor position on menu and controls menu elements
    :return: bool
    """
    hover_play = pygame.image.load(
        "assets/mainmenu_play_hovered.png").convert_alpha()
    hover_quit = pygame.image.load(
        "assets/mainmenu_quit_hovered.png").convert_alpha()
    img_play = pygame.image.load("assets/mainmenu_play.png").convert_alpha()
    img_quit = pygame.image.load("assets/mainmenu_quit.png").convert_alpha()
    button_press = pygame.mixer.Sound("assets/button_press.mp3")

    click = False

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit()
            exit()

    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()[0]

    if 502 <= mouse[0] <= 777 and 555 <= mouse[1] <= (555 + 75):
        screen.blit(hover_play, (502, 555))
        if click:
            button_press.play()
            return True
    else:
        screen.blit(img_play, (502, 555))

    if 502 <= mouse[0] <= 777 and 635 <= mouse[1] <= (635 + 75):
        screen.blit(hover_quit, (502, 635))
        if click:
            button_press.play()
            pygame.quit()
            # exit()
    else:
        screen.blit(img_quit, (502, 635))

    return False


def playscreen_control(screen: pygame.Surface, resume_flag: bool) -> str:
    global warningFlag
    """
    tracks cursor position on menu and controls menu elements
    :return: str
    """
    # load assets
    button_press = pygame.mixer.Sound("assets/button_press.mp3")
    img_newgame = pygame.image.load("assets/play_newgame.png").convert_alpha()
    img_resumegame = pygame.image.load("assets/play_resumegame.png").convert_alpha()
    img_options = pygame.image.load("assets/play_options.png").convert_alpha()
    img_warning = pygame.image.load("assets/newgame_warning.png").convert_alpha()
    screen.blit(img_newgame, (222, 310))
    screen.blit(img_resumegame, (565, 310))
    screen.blit(img_options, (893, 310))
    img_newgame_hovered = pygame.image.load(
        "assets/play_newgame_hovered.png").convert_alpha()
    img_resumegame_hovered = pygame.image.load(
        "assets/play_resumegame_pressed.png").convert_alpha()
    img_resumegame_unavailable = pygame.image.load(
        "assets/play_resumegame_unavailable.png").convert_alpha()
    img_option_hovered = pygame.image.load(
        "assets/play_options_pressed.png").convert_alpha()

    if not resume_flag:
        screen.blit(img_resumegame_unavailable, (565, 310))

    click = False

    for ev in pygame.event.get():
        if ev.type == pygame.MOUSEBUTTONUP:
            if ev.button == 1:
                click = True

    mouse = pygame.mouse.get_pos()
    # click = pygame.mouse.get_pressed()[0]

    if 171 <= mouse[0] <= (171 + 52) and 223 <= mouse[1] <= (223 + 60):
        if click:
            button_press.play()
            return "close"

    if 222 <= mouse[0] <= (222 + 220) and 310 <= mouse[1] <= (310 + 170) and not warningFlag:
        screen.blit(img_newgame_hovered, (222, 310))
        if click and resume_flag:
            click = False
            button_press.play()
            warningFlag = True
        elif click:
            button_press.play()
            return "New"

    if warningFlag:
        screen.blit(img_warning, (0, 0))
        if 226 <= mouse[0] <= (226 + 295) and 326 <= mouse[1] <= (326 + 179):
            if click:
                warningFlag = False
                return "New"
        elif 692 <= mouse[0] <= (692 + 220) and 310 <= mouse[1] <= (310 + 170):
            if click:
                warningFlag = False
                return "close"

    if 565 <= mouse[0] <= (565 + 220) and 310 <= mouse[1] <= (310 + 170) and resume_flag and not warningFlag:
        screen.blit(img_resumegame_hovered, (565, 310))
        if click:
            button_press.play()
            return "Resume"

    if 893 <= mouse[0] <= (893 + 220) and 310 <= mouse[1] <= (310 + 170) and not warningFlag:
        screen.blit(img_option_hovered, (893, 310))
        if click:
            button_press.play()
            return "options"


def options_control() -> str:
    global optionFlag, shard_slider_dragging, indicator_slider_dragging, music_slider_dragging, FullscreenFlag, \
        full_height, full_width, screen, game_surface, display_info
    mouse = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]

    # Load images
    options_window = load_image("assets/mainmenu_settings.png")
    option_slider = load_image("assets/mainmenu_slider.png")
    music_slider_img = load_image("assets/music_slider.png")
    checked = load_image("assets/autoplay_checked.png")
    button_press = game_tools.load_sound("assets/button_press.mp3")

    game_surface.blit(options_window, (0, 0))
    if game_tools.showFPS:
        game_surface.blit(checked, (970, 346))
    if game_tools.showCursor:
        game_surface.blit(checked, (970, 392))
    if FullscreenFlag:
        game_surface.blit(checked, (970, 438))

    speed_font = game_tools.get_font("arial", 24)
    text_speed = speed_font.render(f"{game_tools.max_speed_multiplier}", True, (0, 0, 0))
    game_surface.blit(text_speed, (976, 300))

    if 1004 <= mouse[0] <= 1004 + 21 and 301 <= mouse[1] <= 301 + 25:
        if game_tools.detect_single_click():
            button_press.play()
            game_tools.max_speed_multiplier += 1
            if game_tools.max_speed_multiplier > 10:
                game_tools.max_speed_multiplier = 10
    elif 1032 <= mouse[0] <= 1032 + 21 and 301 <= mouse[1] <= 301 + 25:
        if game_tools.detect_single_click():
            button_press.play()
            game_tools.max_speed_multiplier -= 1
            if game_tools.max_speed_multiplier < 2:
                game_tools.max_speed_multiplier = 2

    if 967 <= mouse[0] <= 967 + 34 and 345 <= mouse[1] <= 345 + 30:
        if game_tools.detect_single_click():
            if not game_tools.showFPS:
                button_press.play()
                game_tools.showFPS = True
            elif game_tools.showFPS:
                button_press.play()
                game_tools.showFPS = False

    if 967 <= mouse[0] <= 967 + 34 and 389 <= mouse[1] <= 389 + 30:
        if game_tools.detect_single_click():
            if not game_tools.showCursor:
                button_press.play()
                game_tools.showCursor = True
            elif game_tools.showCursor:
                button_press.play()
                game_tools.showCursor = False

    if 967 <= mouse[0] <= 967 + 34 and 433 <= mouse[1] <= 433 + 30:
        if game_tools.detect_single_click():
            toggle_fullscreen()
            optionFlag = False

    # ===== SHARD SLIDER =====
    shard_slider_min = 243
    shard_slider_max = 243 + 227
    shard_slider_y = 347
    shard_slider_range = shard_slider_max - shard_slider_min
    shard_slider_x = shard_slider_min + (game_tools.MAX_SHARDS / 1000) * shard_slider_range
    game_surface.blit(option_slider, (shard_slider_x - 8, shard_slider_y))  # -8 to center handle

    # ===== INDICATOR SLIDER =====
    indicator_slider_min = 243
    indicator_slider_max = 243 + 227
    indicator_slider_y = 419
    indicator_slider_x = indicator_slider_min + (game_tools.MAX_INDICATORS / 1000) * (
                indicator_slider_max - indicator_slider_min)
    game_surface.blit(option_slider, (indicator_slider_x - 8, indicator_slider_y))  # -8 to center handle

    # ===== MUSIC SLIDER =====
    music_slider_min = 439
    music_slider_max = 439 + 583
    music_slider_y = 522
    music_slider_x = music_slider_min + game_tools.user_volume * (music_slider_max - music_slider_min)
    game_surface.blit(music_slider_img, (music_slider_x - 15, music_slider_y))  # -15 to center handle

    # Close button logic
    if 1039 <= mouse[0] <= 1070 and 140 <= mouse[1] <= 178:
        if game_tools.detect_single_click():
            button_press = pygame.mixer.Sound("assets/button_press.mp3")
            button_press.play()
            optionFlag = False
            save_manager.save_settings(game_tools.MAX_SHARDS, game_tools.MAX_INDICATORS,
                                       game_tools.max_speed_multiplier, game_tools.showFPS, game_tools.showCursor,
                                       game_tools.user_volume, FullscreenFlag)
            return "options"

    # ===== DRAGGING LOGIC =====
    if mouse_pressed:
        if not any([shard_slider_dragging, indicator_slider_dragging, music_slider_dragging]):
            # Check if mouse is near slider handles (simplified collision)
            if abs(mouse[0] - shard_slider_x) < 15 and shard_slider_y <= mouse[1] <= shard_slider_y + 18:
                shard_slider_dragging = True
            elif abs(mouse[0] - indicator_slider_x) < 15 and indicator_slider_y <= mouse[1] <= indicator_slider_y + 18:
                indicator_slider_dragging = True
            elif abs(mouse[0] - music_slider_x) < 25 and music_slider_y <= mouse[1] <= music_slider_y + 31:
                music_slider_dragging = True

        if shard_slider_dragging:
            new_x = max(shard_slider_min, min(mouse[0], shard_slider_max))
            game_tools.MAX_SHARDS = int(
                ((new_x - shard_slider_min) / shard_slider_range) * 1000)  # Added inner parentheses

        if indicator_slider_dragging:
            new_x = max(indicator_slider_min, min(mouse[0], indicator_slider_max))
            game_tools.MAX_INDICATORS = int(((new_x - indicator_slider_min) / (
                    indicator_slider_max - indicator_slider_min)) * 1000)  # Added inner parentheses

        if music_slider_dragging:
            new_x = max(music_slider_min, min(mouse[0], music_slider_max))
            game_tools.user_volume = (new_x - music_slider_min) / (music_slider_max - music_slider_min)
            pygame.mixer.music.set_volume(game_tools.user_volume)

    else:
        # Reset all dragging flags when mouse released
        shard_slider_dragging = False
        indicator_slider_dragging = False
        music_slider_dragging = False

    return "options"


def toggle_fullscreen():
    global FullscreenFlag, screen, game_surface, full_width, full_height, display_info

    button_press = game_tools.load_sound("assets/button_press.mp3")
    button_press.play()

    # Toggle between fullscreen and windowed mode.
    if not FullscreenFlag:
        FullscreenFlag = True
        display_info = pygame.display.Info()
        full_width, full_height = display_info.current_w, display_info.current_h
        # Use borderless fullscreen.
        screen = pygame.display.set_mode((full_width, full_height), pygame.FULLSCREEN | pygame.NOFRAME)
        # Create an off-screen fixed-resolution rendering surface.
        game_surface = pygame.Surface((1280, 720))
    else:
        FullscreenFlag = False
        # Switch back to windowed mode by simply calling set_mode with default flags (no extra parameters)
        screen = pygame.display.set_mode((1280, 720))
        # In windowed mode, use the display surface directly.
        game_surface = screen

    save_manager.save_settings(game_tools.MAX_SHARDS, game_tools.MAX_INDICATORS,
                               game_tools.max_speed_multiplier, game_tools.showFPS, game_tools.showCursor,
                               game_tools.user_volume, FullscreenFlag)
