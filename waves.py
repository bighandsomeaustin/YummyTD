import math
import pygame
import game_tools
import random
import save_progress

# initializes used variables
enemy_data = [game_tools.AntEnemy, game_tools.HornetEnemy, game_tools.BeetleEnemy]
wave_size = 0
spawn_interval = 0
last_spawn_time = 0
current_wave = 1
enemies_spawned = 0
enemies = game_tools.enemies
trigger_rush = -1
rush_num = -1
rush_speed = -1
rush_active = False
rush_spawned = 0
original_spawn_interval = 0

waves = []

waves.append(["ANT"] * 10)
waves.append(["ANT"] * 10)
waves.append(["ANT"] * 15)
waves.append(["ANT"] * 15 + ["HORNET"] * 2)
waves.append(["ANT"] * 10 + ["HORNET"] * 5)

waves.append(["HORNET"] * 5 + ["ANT"] * 12)  # Wave 6 (Index 5)
waves.append(["ANT"] * 15 + ["HORNET"] * 5)  # Wave 7 (Index 6)
waves.append(["CENTIPEDE"])       # Wave 8 (Index 7)
waves.append(["ANT"] * 20 + ["HORNET"] * 10)  # Wave 9 (Index 8)
waves.append(["ANT"] * 15 + ["HORNET"] * 5 + ["HORNET"] * 10)  # Wave 10 (Index 9)


waves.append(["BEETLE"] * 2)         # Wave 11 (Index 10)
waves.append(["BEETLE"] * 2 + ["ANT"] * 10 + ["HORNET"] * 10)  # Wave 12 (Index 11)
waves.append(["CENTIPEDE"] * 3)       # Wave 13 (Index 12)
waves.append(["ANT"] * 40)  # Wave 14 (Index 13)
waves.append(["CENTIPEDE"] * 1 + ["ANT"] * 15 + ["BEETLE"] * 3 + ["HORNET"] * 5)  # Wave 15 (Index 14)


waves.append(["CENTIPEDE_BOSS"] * 1)  # Wave 16 (Index 15)
waves.append(["BEETLE"] * 3 + ["HORNET"] * 7 + ["CENTIPEDE"] * 4)       # Wave 17 (Index 16)
waves.append(["ANT"] * 30 + ["HORNET"] * 10 + ["BEETLE"] * 5 + ["CENTIPEDE"] * 5)  # Wave 18 (Index 17)


def start_new_wave(round_number: int):
    """Initialize wave settings when a new wave starts."""
    global enemies, enemies_spawned, wave_size, spawn_interval, last_spawn_time, \
        trigger_rush, rush_num, rush_speed, rush_active, rush_spawned

    wave_data = {
        # Early Game (Waves 1-5)
        1: {"spawn_interval": 2500, "wave_size": 10, "trigger_rush": -1},
        2: {"spawn_interval": 1500, "wave_size": 10, "trigger_rush": -1},
        3: {"spawn_interval": 2000, "wave_size": 15, "trigger_rush": 10, "rush_num": 5, "rush_speed": 1000},
        4: {"spawn_interval": 1800, "wave_size": 17, "trigger_rush": -1},
        5: {"spawn_interval": 600, "wave_size": 15, "trigger_rush": 10, "rush_num": 5, "rush_speed": 4500},

        # Mid Game (Waves 6-10)
        6: {"spawn_interval": 2500, "wave_size": 17, "trigger_rush": -1},
        7: {"spawn_interval": 1000, "wave_size": 20, "trigger_rush": 15, "rush_num": 5, "rush_speed": 2500},
        8: {"spawn_interval": 4000, "wave_size": 1, "trigger_rush": -1},  # Centipede wave
        9: {"spawn_interval": 500, "wave_size": 30, "trigger_rush": 20, "rush_num": 10, "rush_speed": 2500},
        10: {"spawn_interval": 1000, "wave_size": 30, "trigger_rush": 20, "rush_num": 15, "rush_speed": 2500},

        # Late Game (Waves 11-15)
        11: {"spawn_interval": 1500, "wave_size": 2, "trigger_rush": -1},
        12: {"spawn_interval": 2500, "wave_size": 22, "trigger_rush": 2, "rush_num": 10, "rush_speed": 500},
        13: {"spawn_interval": 2500, "wave_size": 3, "trigger_rush": -1},  # Centipede squad
        14: {"spawn_interval": 800, "wave_size": 40, "trigger_rush": -1},
        15: {"spawn_interval": 1500, "wave_size": 23, "trigger_rush": 18, "rush_num": 5, "rush_speed": 2500},

        # Endgame (Waves 16-18)
        16: {"spawn_interval": 4000, "wave_size": 1, "trigger_rush": -1},  # Boss wave
        17: {"spawn_interval": 2500, "wave_size": 15, "trigger_rush": 11, "rush_num": 4, "rush_speed": 1000},
        18: {"spawn_interval": 500, "wave_size": 50, "trigger_rush": 30, "rush_num": 20, "rush_speed": 2500}
    }

    if round_number in wave_data:
        config = wave_data[round_number]
        enemies.clear()
        enemies_spawned = 0
        wave_size = config["wave_size"]
        spawn_interval = config["spawn_interval"]
        trigger_rush = config["trigger_rush"]
        rush_active = False
        rush_spawned = 0
        if trigger_rush != -1:
            rush_num = config["rush_num"]
            rush_speed = config["rush_speed"]
        last_spawn_time = pygame.time.get_ticks()


def send_wave(scrn: pygame.Surface, round_number: int) -> bool:
    global enemies, last_spawn_time, enemies_spawned, wave_size, trigger_rush, \
        rush_speed, rush_num, spawn_interval, waves, rush_active, rush_spawned

    global original_spawn_interval  # Add this to track normal speed

    # Get adjusted time based on game speed
    current_time = pygame.time.get_ticks()
    adjusted_spawn_interval = spawn_interval / game_tools.game_speed_multiplier
    adjusted_rush_speed = rush_speed / game_tools.game_speed_multiplier if rush_speed != -1 else -1

    # Enemy Spawning Logic
    if trigger_rush != -1:
        if not rush_active and enemies_spawned >= trigger_rush:
            # Start rush period
            rush_active = True
            original_spawn_interval = adjusted_spawn_interval  # Store normal speed
            adjusted_spawn_interval = adjusted_rush_speed
            rush_spawned = 0

        if rush_active:
            rush_spawned += 1
            if rush_spawned >= rush_num:
                # End rush period
                rush_active = False
                adjusted_spawn_interval = original_spawn_interval  # Restore normal speed

    if enemies_spawned < wave_size and current_time - last_spawn_time >= adjusted_spawn_interval:
        offset = random.randint(-16, 16)
        spawn_pos = (238 + offset, 500)
        offset_path = [(x + offset, y) for (x, y) in game_tools.house_path]

        wave_used = waves[round_number - 1]

        enemy_type = wave_used[enemies_spawned % len(wave_used)]

        if enemy_type == "ANT":
            enemies.append(game_tools.AntEnemy(spawn_pos, 1, 1, offset_path, "assets/ant_base.png"))
        elif enemy_type == "HORNET":
            enemies.append(game_tools.HornetEnemy(spawn_pos, 2, 2, offset_path, "assets/hornet_base.png"))
        elif enemy_type == "CENTIPEDE":
            enemies.append(game_tools.CentipedeEnemy(spawn_pos, offset_path))
        elif enemy_type == "CENTIPEDE_BOSS":
            enemies.append(game_tools.CentipedeEnemy(spawn_pos, offset_path, links=18))
        elif enemy_type == "BEETLE":
            enemies.append(game_tools.BeetleEnemy(spawn_pos, offset_path))

        last_spawn_time = current_time
        enemies_spawned += 1

    # Update enemies
    for enemy in enemies[:]:
        enemy.render(scrn)
        enemy.move()
        if not enemy.is_alive:
            enemies.remove(enemy)

    if enemies_spawned >= wave_size and not enemies:
        base_reward = 150
        wave_bonus = math.floor(math.log(round_number + 1, 2))  # Proper logarithmic scaling
        game_tools.money += base_reward + (25 * wave_bonus)
        return True
    return False
