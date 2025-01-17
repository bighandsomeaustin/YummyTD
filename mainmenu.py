import pygame
from pygame import mixer


def render_mainmenu(scrn: pygame.Surface):
    """
    Draws the main menu screen
    :param scrn: pygame.Surface
    :return: none
    """

    font1 = pygame.font.SysFont('chalkduster.ttf', 20)
    version = font1.render('Version 1.0.0', True, (0, 255, 0))
    text_rect1 = version.get_rect()
    scrn.blit(version, text_rect1)

    # Draw menu background
    img_menu = pygame.image.load("assets/menu_background.png").convert()

    # Logo
    img_logo = pygame.image.load("assets/mainmenu_logo.png").convert_alpha()

    # Play button screen
    img_play = pygame.image.load("assets/mainmenu_play.png").convert_alpha()

    # Quit button screen
    img_quit = pygame.image.load("assets/mainmenu_quit.png").convert_alpha()

    # render background
    scrn.blit(img_menu, (0, 0))

    # render play button
    scrn.blit(img_play, (502, 555))

    # render quit button
    scrn.blit(img_quit, (502, 635))

    # render logo
    scrn.blit(img_logo, (384, 40))


def mainmenu_control(scrn: pygame.Surface) -> bool:
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
        scrn.blit(hover_play, (502, 555))
        if click:
            button_press.play()
            return True
    else:
        scrn.blit(img_play, (502, 555))

    if 502 <= mouse[0] <= 777 and 635 <= mouse[1] <= (635 + 75):
        scrn.blit(hover_quit, (502, 635))
        if click:
            button_press.play()
            pygame.quit()
            exit()
    else:
        scrn.blit(img_quit, (502, 635))

    return False


def playscreen_control(scrn: pygame.Surface, resume_flag: bool) -> str:
    """
    tracks cursor position on menu and controls menu elements
    :return: str
    """
    # load assets
    button_press = pygame.mixer.Sound("assets/button_press.mp3")
    img_newgame = pygame.image.load("assets/play_newgame.png").convert_alpha()
    img_resumegame = pygame.image.load("assets/play_resumegame.png").convert_alpha()
    img_options = pygame.image.load("assets/play_options.png").convert_alpha()
    scrn.blit(img_newgame, (222, 310))
    scrn.blit(img_resumegame, (565, 310))
    scrn.blit(img_options, (893, 310))
    img_newgame_hovered = pygame.image.load(
        "assets/play_newgame_hovered.png").convert_alpha()
    img_resumegame_hovered = pygame.image.load(
        "assets/play_resumegame_pressed.png").convert_alpha()
    img_resumegame_unavailable = pygame.image.load(
        "assets/play_resumegame_unavailable.png").convert_alpha()
    img_option_hovered = pygame.image.load(
        "assets/play_options_pressed.png").convert_alpha()

    if not resume_flag:
        scrn.blit(img_resumegame_unavailable, (565, 310))

    click = False

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit()
            exit()

    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()[0]

    if 171 <= mouse[0] <= (171 + 52) and 223 <= mouse[1] <= (223 + 60):
        if click:
            button_press.play()
            return "close"

    if 222 <= mouse[0] <= (222 + 220) and 310 <= mouse[1] <= (310 + 170):
        scrn.blit(img_newgame_hovered, (222, 310))
        if click and resume_flag:
            button_press.play()
            # add warning
            return "New"
        elif click:
            button_press.play()
            return "New"

    if 565 <= mouse[0] <= (565 + 220) and 310 <= mouse[1] <= (310 + 170) and resume_flag:
        scrn.blit(img_resumegame_hovered, (565, 310))
        if click:
            button_press.play()
            return "close"

    if 893 <= mouse[0] <= (893 + 220) and 310 <= mouse[1] <= (310 + 170):
        scrn.blit(img_option_hovered, (893, 310))
        if click:
            button_press.play()
            return "close"



