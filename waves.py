import math
import pygame
import game_tools
from enemies import AntEnemy, HornetEnemy
# import save_progress
# initializes used variables
wave_size = 0
spawn_interval = 0
last_spawn_time = 0
current_wave = 1
enemies_spawned = 0
enemies = game_tools.enemies
trigger_rush = -1
rush_num = -1
rush_speed = -1

# initializes enemies used in the waves
waves = []
wave_1 = ["ANT" for _ in range(19)]
wave_1 += ["HORNET"]
for i in range(4):
    waves.append(wave_1)
wave_5 = ["ANT" for _ in range(14)]
wave_5 += ["HORNET", "HORNET", "ANT", "ANT", "ANT", "ANT", "HORNET"]
for i in range(19):
    wave_5 += ["ANT"]
wave_5 += ["HORNET", "HORNET", "HORNET", "HORNET", "HORNET"]
wave_5 += ["ANT", "ANT", "ANT", "ANT", "ANT"]
for i in range(6):
    waves.append(wave_5)

wave_11 = ["ANT" for _ in range(10)]
for i in range(7, 10):
    wave_11 += ["ANT" for _ in range(10 - i)]
    wave_11 += ["HORNET" for _ in range(i)]
wave_11 += ["HORNET" for _ in range(10)]
waves.append(wave_1)
for i in range(10):
    waves.append(wave_11)
wave_12 = []
for i in range(25):
    wave_12 += ["ANT", "HORNET"]
waves.append(wave_12)
wave_13 = []
for i in range(10):
    wave_13 += ["ANT", "HORNET", "HORNET", "HORNET", "HORNET"]
waves.append(wave_13)
wave_14 = []
for i in range(35):
    wave_14 += ["HORNET"]
wave_15 = []
wave_15 += ["HORNET" for _ in range(19)]
wave_15 += ["ANT"]
wave_15 += ["HORNET" for _ in range(19)]
wave_15 += ["ANT"]
for i in range(10):
    wave_15 += ["HORNET", "ANT", "HORNET"]


def start_new_wave(round_number: int):
    """Initialize wave settings when a new wave starts."""
    global enemies, enemies_spawned, wave_size, spawn_interval, last_spawn_time, \
        trigger_rush, rush_num, rush_speed, wave_1, wave_11, wave_12

    wave_data = {
        1: {"spawn_interval": 1000, "wave_size": 5, "trigger_rush": -1},
        2: {"spawn_interval": 1000, "wave_size": 10, "trigger_rush": -1},
        3: {"spawn_interval": 1000, "wave_size": 15, "trigger_rush": -1},
        4: {"spawn_interval": 750, "wave_size": 20, "trigger_rush": -1},
        5: {"spawn_interval": 750, "wave_size": 20, "trigger_rush": -1},
        6: {"spawn_interval": 750, "wave_size": 30, "trigger_rush": -1},
        7: {"spawn_interval": 500, "wave_size": 30, "trigger_rush": -1},
        8: {"spawn_interval": 500, "wave_size": 45, "trigger_rush": -1},
        9: {"spawn_interval": 500, "wave_size": 45, "trigger_rush": -1},
        10: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": 25, "rush_num": 10, "rush_speed": 250},
        11: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": -1},
        12: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": -1},
        13: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": -1},
        14: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": -1},
        15: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": 15, "rush_num": 20, "rush_speed": 150},
    }

    if round_number in wave_data:
        print(f"Starting Wave {round_number}")  # Debugging
        enemies.clear()
        enemies_spawned = 0
        wave_size = wave_data[round_number]["wave_size"]
        spawn_interval = wave_data[round_number]["spawn_interval"]
        trigger_rush = wave_data[round_number]["trigger_rush"]
        # initializing rush if it exists within the current wave
        if trigger_rush != -1:
            rush_num = wave_data[round_number]["rush_num"]
            rush_speed = wave_data[round_number]["rush_speed"]
        last_spawn_time = pygame.time.get_ticks()


def send_wave(scrn: pygame.Surface, round_number: int) -> bool:
    global enemies, last_spawn_time, enemies_spawned, wave_size, trigger_rush, \
        rush_speed, rush_num, spawn_interval, waves
    current_time = pygame.time.get_ticks()

    # Enemy Spawning Logic
    # Check if current enemy is part of a rush
    if trigger_rush != -1:
        if enemies_spawned >= trigger_rush and (enemies_spawned - trigger_rush <= rush_num):
            spawn_interval = rush_speed
    if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
        if round_number <= 10:
            wave_used = waves[0]
        else:
            wave_used = waves[round_number]
        print(f"Spawning Enemy {enemies_spawned + 1}/{wave_size}")  # Debugging
        # Check what enemy is next to be spawned, spawn that enemy
        if wave_used[enemies_spawned] == "ANT":
            ant = AntEnemy((238, 500))
            enemies.append(ant)
        elif wave_used[enemies_spawned] == "HORNET":
            hornet = HornetEnemy((238, 500))
            enemies.append(hornet)
        # Update spawn time and how many enemies have been spawned
        last_spawn_time = current_time
        enemies_spawned += 1

    # Update and Render Enemies
    for enemy in enemies:
        enemy.render(scrn)
        enemy.move()
        if not enemy.is_alive:
            enemies.remove(enemy)

    # Check if the wave is complete (all enemies spawned & defeated)
    if enemies_spawned >= wave_size and not enemies:
        print(f"Wave {round_number} Complete!")  # Debugging
        game_tools.money += 150 * math.floor((math.log2(round_number + 1)))
        return True  # Signal wave completion
    return False
