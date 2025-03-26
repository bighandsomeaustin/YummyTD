import math
import pygame
import game_tools
from enemies import AntEnemy, HornetEnemy, CentipedeEnemy, CentipedeBoss


# initializes used variables
enemy_data = [AntEnemy, HornetEnemy]
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
wave_1 = ["ANT"] * 10  # Re-optimized using multiplication for list creation
for i in range(1, 5):
    wave_1 += ["ANT"] * (10 - i)
    wave_1 += ["HORNET"] * i
for i in range(10):
    waves.append(wave_1)
wave_11 = ["ANT"] * 10
for i in range(7, 10):
    wave_11 += ["ANT"] * (10 - i)
    wave_11 += ["HORNET"] * i
wave_11 += ["HORNET"] * 10
waves.append(wave_11)
wave_12 = []
wave_12 += ["ANT", "HORNET"]
waves.append(wave_12)
wave_13 = []
for i in range(10):
    wave_13 += ["ANT", "HORNET", "HORNET", "HORNET", "HORNET"]
waves.append(wave_13)
wave_14 = []  # Unused in the current wave sequence; kept as in original
for i in range(35):
    wave_14 += ["HORNET"]
waves.append(wave_14)
wave_15 = []
wave_15 += ["ANT"] * 15
wave_15 += ["HORNET"] * 15
for i in range(15):
    wave_15 += ["ANT", "HORNET"]
waves.append(wave_15)
wave_16 = []
wave_16 += ["CENTIPEDE"] * 3
waves.append(wave_16)
wave_17 = ["CENTIPEDEBOSS"] * 100
waves.append(wave_17)


def start_new_wave(round_number: int):
    """Initialize wave settings when a new wave starts."""
    global enemies, enemies_spawned, wave_size, spawn_interval, last_spawn_time, \
        trigger_rush, rush_num, rush_speed

    wave_data = {
        1: {"spawn_interval": 1000, "wave_size": 5, "trigger_rush": -1},
        2: {"spawn_interval": 1000, "wave_size": 10, "trigger_rush": -1},
        3: {"spawn_interval": 1000, "wave_size": 15, "trigger_rush": -1},
        4: {"spawn_interval": 750, "wave_size": 20, "trigger_rush": -1},
        5: {"spawn_interval": 750, "wave_size": 20, "trigger_rush": 15, "rush_num": 5, "rush_speed": 250},
        6: {"spawn_interval": 750, "wave_size": 30, "trigger_rush": -1},
        7: {"spawn_interval": 500, "wave_size": 30, "trigger_rush": -1},
        8: {"spawn_interval": 500, "wave_size": 45, "trigger_rush": -1},
        9: {"spawn_interval": 500, "wave_size": 45, "trigger_rush": -1},
        10: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": 25, "rush_num": 10, "rush_speed": 250},
        11: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": -1},
        12: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": -1},
        13: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": -1},
        14: {"spawn_interval": 500, "wave_size": 35, "trigger_rush": -1},
        15: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": 15, "rush_num": 20, "rush_speed": 150},
        16: {"spawn_interval": 3500, "wave_size": 3, "trigger_rush": -1},
        17: {"spawn_interval": 150, "wave_size": 100, "trigger_rush": -1}
    }

    if round_number in wave_data:
        print(f"Starting Wave {round_number}")  # Debugging
        enemies.clear()
        enemies_spawned = 0
        wave_size = wave_data[round_number]["wave_size"]
        spawn_interval = wave_data[round_number]["spawn_interval"]
        trigger_rush = wave_data[round_number]["trigger_rush"]
        if trigger_rush != -1:
            rush_num = wave_data[round_number - 1]["rush_num"]
            rush_speed = wave_data[round_number - 1]["rush_speed"]
        last_spawn_time = pygame.time.get_ticks()


def send_wave(scrn: pygame.Surface, round_number: int) -> bool:
    global enemies, last_spawn_time, enemies_spawned, wave_size, trigger_rush, \
        rush_speed, rush_num, spawn_interval, waves
    current_time = pygame.time.get_ticks()

    # Enemy Spawning Logic
    if trigger_rush != -1:
        if enemies_spawned >= trigger_rush and (enemies_spawned - trigger_rush <= rush_num):
            spawn_interval = rush_speed
    if enemies_spawned < wave_size and current_time - last_spawn_time >= spawn_interval:
        wave_used = waves[round_number - 1]
        print(f"Spawning Enemy {enemies_spawned + 1}/{wave_size}")  # Debugging
        print(len(waves))
        if wave_used[enemies_spawned] == "ANT":
            ant = AntEnemy((238, 500))
            enemies.append(ant)
        elif wave_used[enemies_spawned] == "HORNET":
            hornet = HornetEnemy((238, 500))
            enemies.append(hornet)
        elif wave_used[enemies_spawned] == "CENTIPEDE":
            centipede = CentipedeEnemy((238, 500), game_tools.house_path)
            enemies.append(centipede)
        elif wave_used[enemies_spawned] == "CENTIPEDEBOSS":
            if enemies_spawned == 0:
                centipede_boss = CentipedeBoss(enemies_spawned, (238, 500), image_path="assets/centipede_head.png")
            elif enemies_spawned < 99:
                centipede_boss = CentipedeBoss(enemies_spawned, (238, 500), image_path="assets/centipede_link.png")
            else:
                centipede_boss = CentipedeBoss(enemies_spawned, (238, 500), image_path="assets/centipede_tail.png")
                centipede_boss.speed = 0.5
                for e in enemies:
                    e.speed = 0.5
            enemies.append(centipede_boss)
        last_spawn_time = current_time
        enemies_spawned += 1

    for enemy in enemies[:]:
        enemy.render(scrn)
        enemy.move()
        if not enemy.is_alive:
            enemies.remove(enemy)

    if enemies_spawned >= wave_size and not enemies:
        print(f"Wave {round_number} Complete!")  # Debugging
        game_tools.money += (150 * math.floor(math.log(2, round_number + 1)))
        return True
    return False
