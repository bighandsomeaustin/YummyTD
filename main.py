# Example file showing a basic pygame "game loop"
import pygame
from pygame import mixer
import mainmenu
import game_tools
import save_manager
from waves import (send_wave, start_new_wave)
from game_tools import music_volume, load_image
from save_manager import save_game, load_game
import game_stats

# pygame setup

# change the window screen title
pygame.display.set_caption('YummyTD')
Icon = pygame.image.load('assets/icon.png')
pygame.display.set_icon(Icon)
pygame.init()
mixer.init()
mixer.music.set_volume(music_volume)
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
state = "Menu"
resumeFlag = False
curr_wave = False
round_number = 1  # change for debugging
PlayFlag = True

game_tools.MAX_SHARDS, game_tools.MAX_INDICATORS, game_tools.max_speed_multiplier, game_tools.showFPS, \
    game_tools.showCursor, game_tools.user_volume = save_manager.load_settings("settings.json")

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    if state == "Menu":
        mixer.music.load("assets/menu_music.mp3")
        mixer.music.play(loops=-1)
        loaded_round, loaded_kills, resumeFlag, game_tools.money = load_game("my_save.json")
        round_number = loaded_round
        game_stats.global_kill_total["count"] = loaded_kills

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

        if not mainmenu.optionFlag:
            mainmenu.render_mainmenu(screen)
            img_play_screen = pygame.image.load("assets/play_screen.png").convert_alpha()
            screen.blit(img_play_screen, (0, 0))
            option = mainmenu.playscreen_control(screen, resumeFlag)
            if option == "close":
                state = "Menu"
            elif option == "New":
                state = "New Game"
            elif option == "options":
                mainmenu.optionFlag = True
            elif option == "Resume":
                state = "Resume"

        if mainmenu.optionFlag:
            mainmenu.options_control(screen)

        pygame.display.flip()
        clock.tick(60)  # limits FPS to 60

    if state == "New Game":
        resumeFlag = False
        save_manager.wipe_save("my_save.json")
        game_tools.fade_into_image(screen, "assets/house_map_baselayer.png", 500)
        image_map = pygame.image.load("assets/house_map_baselayer.png").convert_alpha()
        mixer.music.fadeout(1000)
        mixer.music.load("assets/map_music.mp3")
        mixer.music.play(-1)
        game_tools.user_health = 100
        game_tools.money = 25000
        round_number = 1
        game_tools.towers.clear()
        game_tools.enemies.clear()
        start_new_wave(round_number)
        state = "Game"

    if state == "Resume":
        game_tools.fade_into_image(screen, "assets/house_map_baselayer.png", 500)
        image_map = pygame.image.load("assets/house_map_baselayer.png").convert_alpha()
        mixer.music.fadeout(1000)
        mixer.music.load("assets/map_music.mp3")
        mixer.music.play(-1)
        start_new_wave(round_number)
        game_tools.TowerFlag = False
        state = "Game"

    while state == "Game":
        for events in pygame.event.get():
            for tower_bank in game_tools.towers:
                if isinstance(tower_bank, game_tools.RatBank):
                    tower_bank.update_user_text(events)
                    pygame.event.clear()
            if events.type == pygame.QUIT:
                pygame.quit()
            if events.type == pygame.KEYDOWN:
                if events.key == pygame.K_ESCAPE:
                    game_tools.TowerFlag = False
                    exit_new_tower = True

        game_tools.update_towers(screen)
        game_tools.update_stats(screen, game_tools.user_health, game_tools.money, round_number, clock)
        game_tools.current_wave = round_number
        game_tools.update_shards(screen)
        cursor_select = game_tools.check_game_menu_elements(screen)

        if cursor_select == "saveandquit":
            game_tools.TowerFlag = False
            resumeFlag = True
            save_game("my_save.json", round_number, game_stats.global_kill_total["count"], resumeFlag, game_tools.money)
            state = "Menu"
        if cursor_select == 'quit':
            game_tools.TowerFlag = False
            state = "Menu"
        if cursor_select == "newgame":
            resumeFlag = False
            game_stats.global_kill_total["count"] = 0
            save_manager.wipe_save("my_save.json")
            state = "New Game"
        if cursor_select == 'menu':
            state = 'Menu'

        if cursor_select is not ("NULL" or "nextround" or "saveandquit"):
            tower = cursor_select
            exit_new_tower = False

        if not exit_new_tower:
            exit_new_tower = game_tools.handle_newtower(screen, tower)

        if game_tools.RoundFlag:
            curr_wave = send_wave(screen, round_number)
            if curr_wave:
                for tower in game_tools.towers:
                    if isinstance(tower, game_tools.RatBank):
                        tower.process_loan_payment()
                        tower.process_interest()
                        tower.reset_imports()
                if game_tools.Autoplay:
                    game_tools.RoundFlag = True
                else:
                    game_tools.RoundFlag = False
                round_number += 1
                resumeFlag = True
                if round_number > 1:
                    save_game("my_save.json", round_number, game_stats.global_kill_total["count"], resumeFlag, game_tools.money)
                start_new_wave(round_number)
                cursor_select = "NULL"

        if game_tools.MogFlag:
            game_tools.play_mog_animation(screen)
            game_tools.MogFlag = False
            mixer.music.unpause()

        pygame.display.flip()
        screen.blit(image_map, (0, 0))
        clock.tick(60 * game_tools.game_speed_multiplier)  # limits FPS to 60

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
