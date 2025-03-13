# Example file showing a basic pygame "game loop"
import pygame
from pygame import mixer
import mainmenu
import game_tools
from save_progress import (save_data, load_data)
from waves import (send_wave, start_new_wave)

# pygame setup

# change the window screen title
pygame.display.set_caption('YummyTD')
Icon = pygame.image.load('assets/icon.png')
pygame.display.set_icon(Icon)
pygame.init()
mixer.init()
mixer.music.load("assets/menu_music.mp3")
mixer.music.set_volume(0.15)
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
state = "Menu"
resumeFlag = False
mixer.music.play(loops=-1)
curr_wave = False
round_number = 1    # change for debugging
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
        start_new_wave(round_number)
        mixer.music.fadeout(1000)
        mixer.music.load("assets/map_music.mp3")
        mixer.music.play(-1)
        # save current new game data
        # this will overwrite any previous saves
        # save_data(game_tools.towers, "towers.pkl")
        # save_data(game_tools.user_health, "health.pkl")
        # save_data(round_number, "round_number.pkl")
        # save_data(game_tools.money, "money.pkl")
        # load new game values (default)
        # game_tools.towers = load_data("towers.pkl")
        # game_tools.user_health = load_data("health.pkl")
        # game_tools.money = load_data("money.pkl")
        # round_number = load_data("round_number.pkl")

    while state == "New Game":

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        game_tools.update_towers(screen)
        game_tools.update_stats(screen, game_tools.user_health, game_tools.money, round_number)

        cursor_select = game_tools.check_game_menu_elements(screen)
        if cursor_select is not ("NULL" or "nextround"):
            tower = cursor_select
            exit_new_tower = False

        if not exit_new_tower:
            exit_new_tower = game_tools.handle_newtower(screen, tower)

        if game_tools.RoundFlag:
            mixer.music.set_volume(0.35)
            curr_wave = send_wave(screen, round_number)

            if curr_wave:
                mixer.music.set_volume(0.10)
                game_tools.RoundFlag = False
                round_number += 1
                # save new state after starting new round
                # save_data(game_tools.towers, "towers.pkl")
                # Towers can't be pickled!! will need to use .json eventually
                # save_data(game_tools.user_health, "health.pkl")
                # save_data(round_number, "round_number.pkl")
                # save_data(game_tools.money, "money.pkl")

                start_new_wave(round_number)
                cursor_select = "NULL"

        if game_tools.MogFlag:
            game_tools.play_mog_animation(screen)
            game_tools.MogFlag = False
            mixer.music.unpause()

        pygame.display.flip()
        screen.blit(image_map, (0, 0))
        clock.tick(60)  # limits FPS to 60

pygame.quit()
