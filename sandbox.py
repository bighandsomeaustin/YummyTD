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


def sandbox_cursor(scrn) -> str:
    mouse = pygame.mouse.get_pos()
    if 959 <= mouse[0] <= 959 + 129 and 646 <= mouse[1] <= 646 + 18:
        if game_tools.detect_single_click():
            return "skip"

    if 907 <= mouse[0] <= 907 + 179 and 676 <= mouse[1] <= 676 + 18:
        if game_tools.detect_single_click():
            return "clear"
