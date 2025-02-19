import math
import pygame
from game_tools import (AntEnemy, HornetEnemy, house_path, enemies, money)
# initializes used variables
enemy_data = [AntEnemy, HornetEnemy]
wave_size = 0
spawn_interval = 0
last_spawn_time = 0
current_wave = 1
enemies_spawned = 0

# initializes enemies used in the waves
waves = []
wave_1 = ["ANT" for _ in range(10)]
for i in range(4):
    wave_1 += ["ANT" for _ in range(8)]
    wave_1 += ["HORNET" for _ in range(2)]
for i in range(10):
    waves.append(wave_1)
wave_11 = ["ANT" for _ in range(10)]
for i in range(3):
    wave_11 += ["ANT" for _ in range(8)]
    wave_11 += ["HORNET" for _ in range(2)]
wave_11 += ["HORNET" for _ in range(10)]
for i in range(10):
    waves.append(wave_1)
for i in range(10):
    waves.append(wave_11)

def start_new_wave(round_number: int):
    """Initialize wave settings when a new wave starts."""
    global enemies, enemies_spawned, wave_size, spawn_interval, last_spawn_time, trigger_rush, rush_num, rush_speed, wave_1_10, wave_11_20

    wave_data = {
        1: {"spawn_interval": 1000, "wave_size": 5, "trigger_rush": None},
        2: {"spawn_interval": 1000, "wave_size": 10, "trigger_rush": None},
        3: {"spawn_interval": 1000, "wave_size": 15, "trigger_rush": None},
        4: {"spawn_interval": 750, "wave_size": 20, "trigger_rush": None},
        5: {"spawn_interval": 750, "wave_size": 20, "trigger_rush": 15, "rush_num": 5, "rush_speed": 50},
        6: {"spawn_interval": 750, "wave_size": 30, "trigger_rush": None},
        7: {"spawn_interval": 500, "wave_size": 30, "trigger_rush": None},
        8: {"spawn_interval": 500, "wave_size": 45, "trigger_rush": None},
        9: {"spawn_interval": 500, "wave_size": 45, "trigger_rush": None},
        10: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": 25, "rush_num": 10, "rush_speed": 100},
        11: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        12: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        13: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        14: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        15: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": 15, "rush_num": 20, "rush_speed": 150},
        16: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        17: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        18: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        19: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None},
        20: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": None}
    }

    if round_number in wave_data:
        print(f"Starting Wave {round_number}")  # Debugging
        enemies.clear()
        enemies_spawned = 0
        wave_size = wave_data[round_number]["wave_size"]
        spawn_interval = wave_data[round_number]["spawn_interval"]
        trigger_rush = wave_data[round_number]["trigger_rush"]
        # initializing rush if it exists within the current wave
        if trigger_rush:
            rush_num = wave_data[round_number]["rush_num"]
            rush_speed = wave_data[round_number]["rush_speed"]
        last_spawn_time = pygame.time.get_ticks()


def send_wave(scrn: pygame.Surface, round_number: int) -> bool:
    global enemies, last_spawn_time, enemies_spawned, wave_size, trigger_rush, rush_speed, rush_num, spawn_interval, money, waves
    current_time = pygame.time.get_ticks()

   # Enemy Spawning Logic
    # Check if current enemy is part of a rush
    if not (trigger_rush is None):
        if enemies_spawned >= trigger_rush and ((enemies_spawned - trigger_rush <= rush_num)):
            spawn_interval = rush_speed
    if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
        wave_used = waves[round_number]
        print(f"Spawning Enemy {enemies_spawned + 1}/{wave_size}")  # Debugging
        # Check and spawn the correct enemy next in the wave
        if wave_used[enemies_spawned] == "ANT":
            ant = AntEnemy((238, 500), 1, 1, house_path, "assets/ant_base.png")
            enemies.append(ant)
        elif wave_used[enemies_spawned] == "HORNET":
            hornet = HornetEnemy((238, 500), 3, 2, house_path, "assets/hornet_base.png")
            enemies.append(hornet)
        last_spawn_time = current_time
        enemies_spawned += 1

    # Update and Render Enemies
    for enemy in enemies[:]:
        enemy.render(scrn)
        enemy.move()
        if not enemy.is_alive:
            for i in range(len(enemy_data)):
                if enemy is enemy_data[i]:
                    money += 20*i
            enemies.remove(enemy)

    # Check if the wave is complete (all enemies spawned & defeated)
    if enemies_spawned >= wave_size and not enemies:
        print(f"Wave {round_number} Complete!")  # Debugging
        money += round(300 * (math.log(round_number + 1) / math.log(51)))
        return True  # Signal wave completion
    return False
