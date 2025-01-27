# Example file showing a basic pygame "game loop"
import pygame
from pygame import mixer
import mainmenu
import game_tools

# pygame setup

# change the window screen title
pygame.display.set_caption('YummyTD')
Icon = pygame.image.load('assets/icon.png')
pygame.display.set_icon(Icon)
pygame.init()
mixer.init()
mixer.music.load("assets/menu_music.mp3")
mixer.music.set_volume(0.25)
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
state = "Menu"
resumeFlag = False
mixer.music.play(loops=-1)
curr_wave = False
round_number = 1
PlayFlag = True

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    # MAIN MENU
    while state == "Menu":

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("purple")
        mainmenu.render_mainmenu(screen)
        playFlag = mainmenu.mainmenu_control(screen)
        if playFlag:
            state = "Play"
        # flip() the display to put your work on screen
        pygame.display.flip()
        clock.tick(60)  # limits FPS to 60

    # GAME SELECT
    if state == "Play":
        img_play_screen = pygame.image.load("assets/play_screen.png").convert_alpha()
        screen.blit(img_play_screen, (0, 0))
        tower = "NULL"
        exit_new_tower = True

    while state == "Play":

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        option = mainmenu.playscreen_control(screen, resumeFlag)

        if option == "close":
            state = "Menu"

        if option == "New":
            state = "New Game"

        pygame.display.flip()
        clock.tick(60)  # limits FPS to 60

    if state == "New Game":
        game_tools.fade_into_image(screen, "assets/house_map_baselayer.png", 500)
        image_map = pygame.image.load(
            "assets/house_map_baselayer.png").convert_alpha()

    while state == "New Game":

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        game_tools.update_towers(screen)

        cursor_select = game_tools.check_game_menu_elements(screen)
        if cursor_select is not "NULL":
            tower = cursor_select
            exit_new_tower = False

        if not exit_new_tower:
            exit_new_tower = game_tools.handle_newtower(screen, tower)

        if PlayFlag:

            curr_wave = game_tools.send_wave(screen, round_number)

            if curr_wave:
                # PlayFlag = False
                round_number += 1

        pygame.display.flip()
        screen.blit(image_map, (0, 0))
        clock.tick(60)  # limits FPS to 60

pygame.quit()
