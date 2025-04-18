import pygame
from pygame import mixer
import mainmenu
import game_tools
import save_manager
from waves import send_wave, start_new_wave
from game_tools import music_volume, load_image
from save_manager import save_game, load_game
import game_stats
import merit_system

# Load settings
(game_tools.MAX_SHARDS, game_tools.MAX_INDICATORS,
 game_tools.max_speed_multiplier, game_tools.showFPS,
 game_tools.showCursor, game_tools.user_volume, mainmenu.FullscreenFlag) = save_manager.load_settings("settings.json")

mainmenu.screen, mainmenu.game_surface = mainmenu.set_window()

# Setup window title and icon
pygame.display.set_caption('YummyTD')
Icon = pygame.image.load('assets/icon.png')
pygame.display.set_icon(Icon)
mixer.init()
mixer.music.set_volume(music_volume)

clock = pygame.time.Clock()
running = True
state = "Menu"
resumeFlag = False
curr_wave = False
round_number = 1  # For debugging
PlayFlag = True

# Preload map image for the game background
image_map = pygame.image.load("assets/house_map_baselayer.png").convert_alpha()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if state == "Menu":
        mixer.music.load("assets/menu_music.mp3")
        mixer.music.play(loops=-1)
        loaded_round, loaded_kills, resumeFlag, game_tools.money = load_game("my_save.json")
        merit_system.load_merit_data()
        round_number = loaded_round
        game_stats.global_kill_total["count"] = loaded_kills

    # MAIN MENU loop
    while state == "Menu":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        # Draw menu background and UI on game_surface
        mainmenu.game_surface.fill("purple")
        mainmenu.render_mainmenu(mainmenu.game_surface)
        playFlag = mainmenu.mainmenu_control(mainmenu.game_surface)
        if playFlag:
            state = "Play"
        # Upscale the off-screen surface (if in fullscreen) or draw normally
        if mainmenu.FullscreenFlag:
            scaled_surface = pygame.transform.scale(mainmenu.game_surface, (mainmenu.full_width, mainmenu.full_height))
            mainmenu.screen.blit(scaled_surface, (0, 0))
        else:
            mainmenu.screen.blit(mainmenu.game_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # GAME SELECT state
    if state == "Play":
        img_play_screen = pygame.image.load("assets/play_screen.png").convert_alpha()
        mainmenu.game_surface.blit(img_play_screen, (0, 0))
        tower = "NULL"
        exit_new_tower = True
        state = "Play"  # Remains in Play state until an option is chosen

    while state == "Play":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if not mainmenu.optionFlag:
            mainmenu.render_mainmenu(mainmenu.game_surface)
            img_play_screen = pygame.image.load("assets/play_screen.png").convert_alpha()
            mainmenu.game_surface.blit(img_play_screen, (0, 0))
            option = mainmenu.playscreen_control(mainmenu.game_surface, resumeFlag)
            if option == "close":
                state = "Menu"
            elif option == "New":
                state = "New Game"
            elif option == "options":
                mainmenu.optionFlag = True
            elif option == "Resume":
                state = "Resume"
        if mainmenu.optionFlag:
            mainmenu.options_control()
        if mainmenu.FullscreenFlag:
            scaled_surface = pygame.transform.scale(mainmenu.game_surface, (mainmenu.full_width, mainmenu.full_height))
            mainmenu.screen.blit(scaled_surface, (0, 0))
        else:
            mainmenu.screen.blit(mainmenu.game_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    if state == "New Game":
        resumeFlag = False
        save_manager.wipe_save("my_save.json")
        game_stats.global_kill_total["count"] = 0
        # Fade into the background image using the final display surface when in fullscreen
        if mainmenu.FullscreenFlag:
            game_tools.fade_into_image(mainmenu.screen, "assets/house_map_baselayer.png", 500)
        else:
            game_tools.fade_into_image(mainmenu.game_surface, "assets/house_map_baselayer.png", 500)
        image_map = pygame.image.load("assets/house_map_baselayer.png").convert_alpha()
        mixer.music.fadeout(1000)
        mixer.music.load("assets/map_music.mp3")
        mixer.music.play(-1)

        # CHANGE THESE 3 FOR DEBUGGING
        game_tools.user_health = 100
        game_tools.money = 350
        round_number = 1

        game_tools.towers.clear()
        game_tools.enemies.clear()
        start_new_wave(round_number)
        state = "Game"

    if state == "Resume":
        if mainmenu.FullscreenFlag:
            game_tools.fade_into_image(mainmenu.screen, "assets/house_map_baselayer.png", 500)
        else:
            game_tools.fade_into_image(mainmenu.game_surface, "assets/house_map_baselayer.png", 500)
        image_map = pygame.image.load("assets/house_map_baselayer.png").convert_alpha()
        mixer.music.fadeout(1000)
        mixer.music.load("assets/map_music.mp3")
        mixer.music.play(-1)
        start_new_wave(round_number)
        game_tools.TowerFlag = False
        state = "Game"

    # GAME state loop
    while state == "Game":
        for events in pygame.event.get():
            # Allow tower banks to update user text
            for tower_bank in game_tools.towers:
                if isinstance(tower_bank, game_tools.RatBank):
                    tower_bank.update_user_text(events)
                    pygame.event.clear()
            if events.type == pygame.QUIT:
                pygame.quit()
                exit()
            if events.type == pygame.KEYDOWN:
                if events.key == pygame.K_ESCAPE:
                    game_tools.TowerFlag = False
                    exit_new_tower = True

        # First, draw the background map onto game_surface
        mainmenu.game_surface.blit(image_map, (0, 0))
        # Update game elements onto game_surface
        game_tools.update_towers(mainmenu.game_surface)
        game_tools.update_stats(mainmenu.game_surface, game_tools.user_health, game_tools.money, round_number, clock)
        game_tools.current_wave = round_number
        game_tools.update_shards(mainmenu.game_surface)
        cursor_select = game_tools.check_game_menu_elements(mainmenu.game_surface)

        if cursor_select == "saveandquit":
            game_tools.TowerFlag = False
            resumeFlag = True
            game_tools.RoundFlag = False
            save_game("my_save.json", round_number, game_stats.global_kill_total["count"], resumeFlag, game_tools.money)
            state = "Menu"
        if cursor_select == 'quit':
            game_tools.RoundFlag = False
            game_tools.TowerFlag = False
            state = "Menu"
        if cursor_select == "newgame":
            resumeFlag = False
            game_stats.global_kill_total["count"] = 0
            save_manager.wipe_save("my_save.json")
            state = "New Game"
        if cursor_select == 'menu':
            state = "Menu"

        if cursor_select not in ("NULL", "nextround", "saveandquit"):
            tower = cursor_select
            exit_new_tower = False

        if not exit_new_tower:
            exit_new_tower = game_tools.handle_newtower(mainmenu.game_surface, tower)

        if game_tools.RoundFlag:
            curr_wave = send_wave(mainmenu.game_surface, round_number)
            if curr_wave:
                for tower in game_tools.towers:
                    if isinstance(tower, game_tools.RatBank):
                        tower.process_loan_payment()
                        tower.process_interest()
                        tower.reset_imports()
                    if isinstance(tower, game_tools.Ozbourne):
                        tower.reset_solo()
                if game_tools.Autoplay:
                    game_tools.RoundFlag = True
                else:
                    game_tools.RoundFlag = False
                round_number += 1
                resumeFlag = True
                mainmenu.game_surface.blit(image_map, (0, 0))
                game_tools.update_towers(mainmenu.game_surface)
                game_tools.update_stats(mainmenu.game_surface, game_tools.user_health, game_tools.money, round_number,
                                        clock)
                pygame.display.flip()
                if round_number == 10:
                    merit_system.award_stars_for_round(1, mainmenu.game_surface)
                elif round_number == 20:
                    merit_system.award_stars_for_round(2, mainmenu.game_surface)
                elif round_number == 30:
                    merit_system.award_stars_for_round(3, mainmenu.game_surface)
                elif round_number == 40:
                    merit_system.award_stars_for_round(4, mainmenu.game_surface)
                elif round_number == 50:
                    merit_system.award_stars_for_round(5, mainmenu.game_surface)
                elif round_number == 65:
                    merit_system.award_stars_for_round(6, mainmenu.game_surface)
                elif round_number == 85:
                    merit_system.award_stars_for_round(7, mainmenu.game_surface)
                elif round_number == 100:
                    merit_system.award_stars_for_round(8, mainmenu.game_surface)
                if round_number > 1:
                    save_game("my_save.json", round_number, game_stats.global_kill_total["count"], resumeFlag, game_tools.money)
                start_new_wave(round_number)
                cursor_select = "NULL"

        if game_tools.MogFlag:
            if mainmenu.FullscreenFlag:
                game_tools.play_mog_animation(mainmenu.screen)
            else:
                game_tools.play_mog_animation(mainmenu.game_surface)
            game_tools.MogFlag = False
            mixer.music.unpause()

        # Upscale rendering: draw game_surface to screen
        if mainmenu.FullscreenFlag:
            scaled_surface = pygame.transform.scale(mainmenu.game_surface, (mainmenu.full_width, mainmenu.full_height))
            mainmenu.screen.blit(scaled_surface, (0, 0))
        else:
            mainmenu.screen.blit(mainmenu.game_surface, (0, 0))

        pygame.display.flip()
        clock.tick(60 * game_tools.game_speed_multiplier)

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
