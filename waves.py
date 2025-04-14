import math
import pygame
import game_tools
import random
import game_stats
import merit_system

# -----------------------------
# Global Variables and Initialization
# -----------------------------
enemies = game_tools.enemies
money = game_tools.money  # This is updated in game_tools
last_spawn_time = 0
segment_completion_time = None
FINAL_CLEANUP_DELAY = 1000 / game_tools.game_speed_multiplier  # in milliseconds
new_enemy = None

# Round configuration: each round is a list of segments.
# Each segment is a dict with keys:
#   "enemies": list of enemy type strings ("ANT", "HORNET", "BEETLE", "SPIDER", "CENTIPEDE", "CENTIPEDE_BOSS")
#   "spawn_interval": milliseconds between spawns in this segment.
#   "delay": milliseconds to wait after the segment is finished before starting the next segment.
#   "rush": (optional) dict with keys "trigger" (enemy count to start rush), "num" (number of enemies at rush speed),
#           and "speed" (spawn interval during rush).
round_configs = {}

# --- Manually defined rounds (1-18) ---
round_configs[1] = [  # Introductory ant wave
    {"enemies": ["ANT"] * 10, "spawn_interval": 1500, "delay": 0}
]
round_configs[2] = [  # Faster ant wave
    {"enemies": ["ANT"] * 10, "spawn_interval": 1000, "delay": 0}
]
round_configs[3] = [  # Mild rush: ants with a rush after 10 spawns
    {"enemies": ["ANT"] * 15,
     "spawn_interval": 1000,
     "delay": 0,
     "rush": {"trigger": 10, "num": 5, "speed": 750}}
]
round_configs[4] = [  # Mix in a few hornets
    {"enemies": ["ANT"] * 15 + ["HORNET"] * 2,
     "spawn_interval": 1200,
     "delay": 0}
]
round_configs[5] = [  # More hornets and faster spawns
    {"enemies": ["ANT"] * 10 + ["HORNET"] * 5,
     "spawn_interval": 600,
     "delay": 0,
     "rush": {"trigger": 8, "num": 3, "speed": 500}}
]
round_configs[6] = [  # Hornet-focused wave with a brief delay\n
    {"enemies": ["HORNET"] * 5 + ["ANT"] * 12,
     "spawn_interval": 1000,
     "delay": 500}
]
round_configs[7] = [  # Larger ant-hornet mix with a mid-round rush
    {"enemies": ["ANT"] * 15 + ["HORNET"] * 5,
     "spawn_interval": 1200,
     "delay": 0,
     "rush": {"trigger": 12, "num": 4, "speed": 600}}
]
round_configs[8] = [  # A single centipede (big enemy)\n
    {"enemies": ["CENTIPEDE"], "spawn_interval": 4000, "delay": 0}
]
round_configs[9] = [  # Larger ant swarm with hornets\n
    {"enemies": ["ANT"] * 20 + ["HORNET"] * 10,
     "spawn_interval": 500,
     "delay": 0}
]
round_configs[10] = [  # Extended hornet barrage in two segments\n
    {"enemies": ["HORNET"] * 10, "spawn_interval": 700, "delay": 2000},
    {"enemies": ["HORNET"] * 10 + ["ANT"] * 5,
     "spawn_interval": 600,
     "delay": 0,
     "rush": {"trigger": 10, "num": 5, "speed": 400}}
]
round_configs[11] = [  # Beetle and spider combo\n
    {"enemies": ["BEETLE"] * 2 + ["SPIDER"],
     "spawn_interval": 1800,
     "delay": 0}
]
round_configs[12] = [  # Mixed forces with beetles, ants, and hornets\n
    {"enemies": ["BEETLE"] * 2 + ["ANT"] * 10 + ["HORNET"] * 10,
     "spawn_interval": 1500,
     "delay": 500}
]
round_configs[13] = [  # Small centipede squad\n
    {"enemies": ["CENTIPEDE"] * 3,
     "spawn_interval": 2200,
     "delay": 0}
]
round_configs[14] = [  # Massive ant swarm in two phases\n
    {"enemies": ["ANT"] * 100, "spawn_interval": 20, "delay": 2000},
    {"enemies": ["ANT"] * 100, "spawn_interval": 20, "delay": 0}
]
round_configs[15] = [  # Spider-themed round with a rush\n
    {"enemies": ["SPIDER"] * 20,
     "spawn_interval": 800,
     "delay": 0,
     "rush": {"trigger": 10, "num": 5, "speed": 400}},
    {"enemies": ["SPIDER"] * 10,
     "spawn_interval": 600,
     "delay": 0}
]
round_configs[16] = [  # Boss round – Centipede Boss\n
    {"enemies": ["CENTIPEDE_BOSS"], "spawn_interval": 4000, "delay": 0}
]
round_configs[17] = [  # Mixed beetles and hornets with double rush\n
    {"enemies": ["BEETLE"] * 3 + ["HORNET"] * 7,
     "spawn_interval": 1200,
     "delay": 1000,
     "rush": {"trigger": 5, "num": 3, "speed": 500}},
    {"enemies": ["HORNET"] * 5,
     "spawn_interval": 800,
     "delay": 0,
     "rush": {"trigger": 3, "num": 2, "speed": 400}}
]
round_configs[18] = [  # Heavy mix – ants, hornets, beetles, and centipedes\n
    {"enemies": ["ANT"] * 30 + ["HORNET"] * 10,
     "spawn_interval": 800,
     "delay": 500},
    {"enemies": ["BEETLE"] * 5 + ["CENTIPEDE"] * 5,
     "spawn_interval": 1000,
     "delay": 0,
     "rush": {"trigger": 5, "num": 3, "speed": 500}}
]

for r in range(1, 101):
    segments = []

    if r == 1:
        segments.append({"enemies": ["ANT"] * 10,
                         "spawn_interval": 1000,
                         "delay": 0})

    elif r == 2:
        segments.append({"enemies": ["ANT"] * 15,
                         "spawn_interval": 1000,
                         "delay": 0})

    elif r == 3:
        segments.append({"enemies": ["ANT"] * 10,
                         "spawn_interval": 1250,
                         "delay": 1500})
        segments.append({"enemies": (["ANT"] + ["HORNET"]) * 2,
                         "spawn_interval": 1250,
                         "delay": 0})

    elif r == 4:
        segments.append({"enemies": ["ANT"] * 10,
                         "spawn_interval": 1250,
                         "delay": 2500})
        segments.append({"enemies": ["ANT"] * 5 + ["HORNET"] * 5,
                         "spawn_interval": 1250,
                         "delay": 0})
    elif r == 5:
        segments.append({"enemies": ["HORNET"] * 10,
                         "spawn_interval": 1750,
                         "delay": 1000})
        segments.append({"enemies": ["ANT"] * 10,
                         "spawn_interval": 500,
                         "delay": 0})

    elif r == 6:
        segments.append({"enemies": ["ANT"] * 20,
                         "spawn_interval": 500,
                         "delay": 1500})
        segments.append({"enemies": ["HORNET"] * 10,
                         "spawn_interval": 1250,
                         "delay": 0})

    elif r == 7:
        segments.append({"enemies": (["ANT"] + ["HORNET"]) * 12,
                         "spawn_interval": 1000,
                         "delay": 0})

    elif r == 8:
        segments.append({"enemies": ["HORNET"] * 20,
                         "spawn_interval": 1500,
                         "delay": 0})

    elif r == 9:
        segments.append({"enemies": ["ANT"] * 10,
                         "spawn_interval": 250,
                         "delay": 3500})
        segments.append({"enemies": ["SPIDER"] * 2,
                         "spawn_interval": 1750,
                         "delay": 0})

    elif r == 10:
        segments.append({"enemies": (["HORNET"] * 2 + ["ANT"]) * 10,
                         "spawn_interval": 1000,
                         "delay": 5500})
        segments.append({"enemies": ["HORNET"] * 10,
                         "spawn_interval": 250,
                         "delay": 0})

    elif r == 11:
        segments.append({"enemies": ((["ANT"] * 2 + ["HORNET"] * 2) * 4 + ["SPIDER"]) * 3,
                         "spawn_interval": 1250,
                         "delay": 0})

    elif r == 12:
        segments.append({"enemies": ["HORNET"] * 10,
                         "spawn_interval": 5,
                         "delay": 5500})
        segments.append({"enemies": ["ANT"] * 20,
                         "spawn_interval": 5,
                         "delay": 5500})
        segments.append({"enemies": ["SPIDER"] * 3,
                         "spawn_interval": 5,
                         "delay": 0})

    elif r == 13:
        segments.append({"enemies": ["ANT"] * 25,
                         "spawn_interval": 5,
                         "delay": 3500})
        segments.append({"enemies": ["ANT"] * 25,
                         "spawn_interval": 5,
                         "delay": 8500})
        segments.append({"enemies": ["DRAGONFLY"],
                         "spawn_interval": 5,
                         "delay": 0})

    elif r == 14:
        segments.append({"enemies": ["SPIDER"] * 25,
                         "spawn_interval": 1500,
                         "delay": 0})

    elif r == 15:
        segments.append({"enemies": (["ANT"] * 10 + ["HORNET"] * 5 + ["DRAGONFLY"]) * 8,
                         "spawn_interval": 750,
                         "delay": 0})

    elif r == 16:
        segments.append({"enemies": (["SPIDER"] * 4 + ["DRAGONFLY"]) * 5,
                         "spawn_interval": 500,
                         "delay": 0})

    elif r == 17:
        for i in range(4):
            segments.append({"enemies": ["FIREFLY"] + ["ANT"] * 20,
                             "spawn_interval": 10,
                             "delay": 1500})
            segments.append({"enemies": ["HORNET"] * 10,
                             "spawn_interval": 10,
                             "delay": 1500})
        segments.append({"enemies": ["DRAGONFLY"] * 2,
                         "spawn_interval": 10,
                         "delay": 0})

    elif r == 18:
        for i in range(5):
            segments.append({"enemies": ["ANT"] * 30,
                             "spawn_interval": 50,
                             "delay": 2500})
            segments.append({"enemies": ["SPIDER"] * 10,
                             "spawn_interval": 500,
                             "delay": 4500})

    elif r == 19:
        segments.append({"enemies": ["DRAGONFLY"] * 8,
                         "spawn_interval": 10,
                         "delay": 4000})
        segments.append({"enemies": ["FIREFLY"],
                         "spawn_interval": 10,
                         "delay": 0})
        segments.append({"enemies": ["BEETLE"],
                         "spawn_interval": 10,
                         "delay": 0})

    elif r == 20:
        segments.append({"enemies": ["BEETLE"] * 8,
                         "spawn_interval": 3500,
                         "delay": 0})

    elif r == 21:
        for i in range(5):
            segments.append({"enemies": ["FIREFLY"] * 2 + ["ANT"] * 20,
                             "spawn_interval": 10,
                             "delay": 3500})
            segments.append({"enemies": ["SPIDER"] * 4 + ["DRAGONFLY"] * 4,
                             "spawn_interval": 10,
                             "delay": 2500})

    elif r == 22:
        for i in range(4):
            segments.append({"enemies": ["HORNET"] * 5,
                             "spawn_interval": 200,
                             "delay": 0})
            segments.append({"enemies": ["CENTIPEDE"] * 2,
                             "spawn_interval": 1000,
                             "delay": 2000})

    elif r == 23:
        segments.append({"enemies": ["CENTIPEDE"] * 8,
                         "spawn_interval": 500,
                         "delay": 2000})
        segments.append({"enemies": ["CENTIPEDE_BOSS"] * 4,
                         "spawn_interval": 3000,
                         "delay": 0})

    elif r == 24:
        for i in range(5):
            segments.append({"enemies": ["FIREFLY"],
                             "spawn_interval": 1000,
                             "delay": 0})
            segments.append({"enemies": ["CENTIPEDE"] * 2,
                             "spawn_interval": 500,
                             "delay": 2000})
            segments.append({"enemies": ["FIREFLY"],
                             "spawn_interval": 1000,
                             "delay": 0})
            segments.append({"enemies": ["BEETLE"] * 2,
                             "spawn_interval": 1000,
                             "delay": 4000})
            segments.append({"enemies": ["ROACH"] * 10,
                             "spawn_interval": 50,
                             "delay": 0})

    elif r == 25:
        segments.append({"enemies": ["FIREFLY"] * 4,
                         "spawn_interval": 500,
                         "delay": 0})
        segments.append({"enemies": ["DRAGONFLY"] * 8,
                         "spawn_interval": 100,
                         "delay": 4500})
        segments.append({"enemies": ["FIREFLY"] * 4,
                         "spawn_interval": 500,
                         "delay": 0})
        segments.append({"enemies": ["BEETLE"] * 8,
                         "spawn_interval": 5,
                         "delay": 0})
        segments.append({"enemies": ["FIREFLY"] * 8,
                         "spawn_interval": 25,
                         "delay": 0})
        segments.append({"enemies": ["ROACH_QUEEN"] * 2,
                         "spawn_interval": 2000,
                         "delay": 0})
    elif r == 26:
        for i in range(5):
            segments.append({"enemies": ["FIREFLY"] * 4,
                             "spawn_interval": 500,
                             "delay": 0})
            segments.append({"enemies": ["ROACH"] * 5,
                             "spawn_interval": 10,
                             "delay": 0})
            segments.append({"enemies": ["ROACH_QUEEN"],
                             "spawn_interval": 500,
                             "delay": 3000})
            segments.append({"enemies": ["HORNET"] * 20,
                             "spawn_interval": 5,
                             "delay": 0})
    elif r == 27:
        for i in range(5):
            segments.append({"enemies": ["ROACH"] * 5,
                             "spawn_interval": 5,
                             "delay": 3000})
            segments.append({"enemies": ["ROACH_QUEEN"] * 2,
                             "spawn_interval": 500,
                             "delay": 4000})

    elif r == 28:
        for i in range(5):
            segments.append({"enemies": ["FIREFLY"] * 4,
                             "spawn_interval": 5,
                             "delay": 0})
            segments.append({"enemies": ["ANT"] * 50,
                             "spawn_interval": 5,
                             "delay": 4000})

    elif r == 29:
        segments.append({"enemies": (["FIREFLY"] + ["BEETLE"] * 4) * 4,
                         "spawn_interval": 500,
                         "delay": 8000})
        segments.append({"enemies": ["FIREFLY"] * 10 + ["DUNG_BEETLE"],
                         "spawn_interval": 500,
                         "delay": 0})

    elif r == 30:
        segments.append({"enemies": (["FIREFLY"] + ["ANT"] * 20),
                         "spawn_interval": 5,
                         "delay": 0})
        segments.append({"enemies": (["FIREFLY_ALT1"] + ["ROACH_ALT1"] * 5 + ["ROACH_QUEEN_ALT1"]),
                         "spawn_interval": 5,
                         "delay": 0})

    elif r == 31:
        for i in range(10):
            segments.append({"enemies": ["HORNET"] * 5,
                             "spawn_interval": 150,
                             "delay": 1000})
            segments.append({"enemies": ["SPIDER"],
                             "spawn_interval": 150,
                             "delay": 1000})

    else:
        segments.append({"enemies": ["MILLIPEDE"],
                         "spawn_interval": 150,
                         "delay": 4000})
        for i in range(int(r / 10) + 2):
            segments.append({"enemies": ["FIREFLY"] * 2,
                             "spawn_interval": 25,
                             "delay": 0})
            segments.append({"enemies": ["ANT"] * r,
                             "spawn_interval": 5,
                             "delay": 2000})
            segments.append({"enemies": ["HORNET"] * (int(r / 10) + 5),
                             "spawn_interval": 150,
                             "delay": 2000})
            segments.append({"enemies": ["CENTIPEDE"] * int(r / 10),
                             "spawn_interval": 150,
                             "delay": 4000})
            segments.append({"enemies": ["FIREFLY"] * 2,
                             "spawn_interval": 25,
                             "delay": 0})
            segments.append({"enemies": ["ROACH_QUEEN"],
                             "spawn_interval": 5,
                             "delay": 3000})
            segments.append({"enemies": ["DRAGONFLY"] * 2,
                             "spawn_interval": 25,
                             "delay": 0})
            segments.append({"enemies": ["SPIDER"] * 2,
                             "spawn_interval": 25,
                             "delay": 2000})
        segments.append({"enemies": ["DUNG_BEETLE"],
                         "spawn_interval": 25,
                         "delay": 0})


    round_configs[r] = segments

# -----------------------------
# Wave State Variables
# -----------------------------
current_round_config = []  # List of segments for the current round
current_segment_index = 0  # Which segment in the current round we are processing
segment_enemy_spawned = 0  # Count of enemies spawned in current segment
segment_start_time = 0  # Time when current segment started

# For handling rush phases per segment
rush_active = False
rush_info = None
rush_spawned = 0
original_spawn_interval = None


# -----------------------------
# Wave Functions
# -----------------------------
def start_new_wave(round_number: int):
    """Initialize wave settings when a new wave starts."""
    global current_round_config, current_segment_index, segment_enemy_spawned, segment_start_time
    global rush_active, rush_info, rush_spawned, original_spawn_interval, enemies

    if round_number <= 100:
        current_round_config = round_configs[round_number]
    else:
        # Endless mode: scale difficulty dynamically
        endless_segment = {
            "enemies": ["ANT"] * int(round_number * 2.5) + ["HORNET"] * int(round_number * 0.8) + ["BEETLE"] * int(
                round_number * 0.5),
            "spawn_interval": max(20, 2000 - int((round_number - 100) ** 1.2 * 30)),
            "delay": 0,
            "rush": {"trigger": int(round_number * 0.6), "num": 7, "speed": max(150, 1000 - (round_number - 100) * 20)}
        }
        current_round_config = [endless_segment]
    current_segment_index = 0
    segment_enemy_spawned = 0
    segment_start_time = pygame.time.get_ticks()
    rush_active = False
    rush_info = None
    rush_spawned = 0
    original_spawn_interval = None
    enemies[:] = [enemy for enemy in enemies if enemy.is_alive]


def get_rand_round():
    det = random.randint(1, 5)
    if det == 1:
        rand_enemy = "ANT"
        rand_amt = 20
        rand_spawn = 250
    elif det == 2:
        rand_enemy = "HORNET"
        rand_amt = 10
        rand_spawn = 500
    elif det == 3:
        rand_enemy = "BEETLE"
        rand_amt = 2
        rand_spawn = 750
    elif det == 4:
        rand_enemy = "SPIDER"
        rand_amt = 4
        rand_spawn = 1000
    elif det == 5:
        rand_enemy = "CENTIPEDE"
        rand_amt = 2
        rand_spawn = 750
    else:
        rand_enemy = "ANT"
        rand_amt = 20
        rand_spawn = 250

    return rand_enemy, rand_spawn, rand_amt


FINAL_CLEANUP_DELAY = 1000  # in milliseconds


def send_wave(scrn: pygame.Surface, round_number: int) -> bool:
    global current_round_config, current_segment_index, segment_enemy_spawned, segment_start_time, segment_completion_time
    global rush_active, rush_info, rush_spawned, original_spawn_interval, enemies, new_enemy

    if 30 <= round_number < 40:
        health_mult = 2
    elif 50 <= round_number < 70:
        health_mult = 3
    elif 70 <= round_number < 80:
        health_mult = 4
    elif 80 <= round_number < 90:
        health_mult = 5
    elif 90 <= round_number < 100:
        health_mult = 6
    elif round_number > 100:
        health_mult = int(round_number / 10) - 3
    else:
        health_mult = 1

    # Remove dead enemies.
    enemies[:] = [enemy for enemy in enemies if enemy.is_alive]
    # pygame.time.get_ticks() = pygame.time.get_ticks()

    # Final phase: if all segments are done, wait until all enemies are cleared.
    if current_segment_index >= len(current_round_config):
        if not enemies:
            print(f"Wave {round_number} completed.")
            base_reward = 25
            bonus = math.floor(math.log(round_number + 1, 2))
            game_tools.money += base_reward + (25 * bonus)
            return True
        return False

    segment = current_round_config[current_segment_index]
    effective_interval = segment["spawn_interval"] / game_tools.game_speed_multiplier

    # Handle rush logic.
    if "rush" in segment:
        if not rush_active and segment_enemy_spawned >= segment["rush"]["trigger"]:
            rush_active = True
            rush_info = segment["rush"]
            original_spawn_interval = effective_interval
            effective_interval = rush_info["speed"] / game_tools.game_speed_multiplier
            rush_spawned = 0
            print("[→] Rush triggered.")
        elif rush_active:
            effective_interval = rush_info["speed"] / game_tools.game_speed_multiplier
            if rush_spawned >= rush_info["num"]:
                rush_active = False
                effective_interval = original_spawn_interval / game_tools.game_speed_multiplier
                print("[✓] Rush complete.")

    # Spawn an enemy if there are still enemies to spawn in this segment.
    if segment_enemy_spawned < len(segment["enemies"]):
        if pygame.time.get_ticks() - segment_start_time >= effective_interval:
            enemy_type = segment["enemies"][segment_enemy_spawned]

            spawn_pos = (238 + random.randint(-16, 16), 500)
            # Create a slightly varied path.
            offset_path = [(x + random.randint(-8, 8), y) for (x, y) in game_tools.house_path]

            spawn_pos_alt1 = (155 + random.randint(-16, 16), 168)
            # Create a slightly varied path.
            offset_path_alt1 = [(x + random.randint(-8, 8), y) for (x, y) in game_tools.house_path_alternate]

            # REGULAR PATH
            if enemy_type == "ANT":
                new_enemy = (game_tools.AntEnemy(spawn_pos, 1, 1, offset_path, "assets/ant_base.png"))
            elif enemy_type == "HORNET":
                new_enemy = (game_tools.HornetEnemy(spawn_pos, 2, 2, offset_path, "assets/hornet_base.png"))
            elif enemy_type == "BEETLE":
                new_enemy = (game_tools.BeetleEnemy(spawn_pos, offset_path))
            elif enemy_type == "SPIDER":
                new_enemy = (game_tools.SpiderEnemy(spawn_pos, offset_path))
            elif enemy_type == "CENTIPEDE":
                new_enemy = (game_tools.CentipedeEnemy(spawn_pos, offset_path))
            elif enemy_type == "CENTIPEDE_BOSS":
                new_enemy = (game_tools.CentipedeEnemy(spawn_pos, offset_path, links=24))
            elif enemy_type == "DRAGONFLY":
                new_enemy = (game_tools.DragonflyEnemy(spawn_pos, offset_path))
            elif enemy_type == "ROACH_QUEEN":
                new_enemy = (game_tools.RoachQueenEnemy(spawn_pos, offset_path))
            elif enemy_type == "ROACH":
                new_enemy = (game_tools.RoachMinionEnemy(position=spawn_pos, path=offset_path,
                                                           speed=random.randint(1, 4), health=3))
            elif enemy_type == "FIREFLY":
                new_enemy = (game_tools.FireflyEnemy(spawn_pos, offset_path))
            elif enemy_type == "DUNG_BEETLE":
                new_enemy = (game_tools.DungBeetleBoss(spawn_pos, offset_path))
            elif enemy_type == "MILLIPEDE":
                new_enemy = (game_tools.MillipedeBoss(spawn_pos, offset_path, links=16))
            # ALTERNATE PATH 1
            elif enemy_type == "ANT_ALT1":
                new_enemy = (game_tools.AntEnemy(spawn_pos_alt1, 1, 1, offset_path_alt1, "assets/ant_base.png"))
            elif enemy_type == "HORNET_ALT1":
                new_enemy = (game_tools.HornetEnemy(spawn_pos_alt1, 2, 2, offset_path_alt1, "assets/hornet_base.png"))
            elif enemy_type == "BEETLE_ALT1":
                new_enemy = (game_tools.BeetleEnemy(spawn_pos_alt1, offset_path_alt1))
            elif enemy_type == "SPIDER_ALT1":
                new_enemy = (game_tools.SpiderEnemy(spawn_pos_alt1, offset_path_alt1))
            elif enemy_type == "CENTIPEDE_ALT1":
                new_enemy = (game_tools.CentipedeEnemy(spawn_pos_alt1, offset_path_alt1))
            elif enemy_type == "CENTIPEDE_BOSS_ALT1":
                new_enemy = (game_tools.CentipedeEnemy(spawn_pos_alt1, offset_path_alt1, links=24))
            elif enemy_type == "DRAGONFLY_ALT1":
                new_enemy = (game_tools.DragonflyEnemy(spawn_pos_alt1, offset_path_alt1))
            elif enemy_type == "ROACH_QUEEN_ALT1":
                new_enemy = (game_tools.RoachQueenEnemy(spawn_pos_alt1, offset_path_alt1))
            elif enemy_type == "ROACH_ALT1":
                new_enemy = (game_tools.RoachMinionEnemy(position=spawn_pos_alt1, path=offset_path_alt1,
                                                           speed=random.randint(1, 4), health=3))
            elif enemy_type == "FIREFLY_ALT1":
                new_enemy = (game_tools.FireflyEnemy(spawn_pos_alt1, offset_path_alt1))
            elif enemy_type == "DUNG_BEETLE_ALT1":
                new_enemy = (game_tools.DungBeetleBoss(spawn_pos_alt1, offset_path_alt1))
            elif enemy_type == "MILLIPEDE_ALT1":
                new_enemy = (game_tools.MillipedeBoss(spawn_pos_alt1, offset_path_alt1, links=16))

            # apply damage multiplier
            if new_enemy is not None:
                if hasattr(new_enemy, "health"):
                    new_enemy.health *= health_mult
                if isinstance(new_enemy, game_tools.CentipedeEnemy):
                    for seg in new_enemy.segments:
                        seg.health *= health_mult
                enemies.append(new_enemy)

            segment_enemy_spawned += 1
            if rush_active:
                rush_spawned += 1
            segment_start_time = pygame.time.get_ticks()
            if segment_enemy_spawned == len(segment["enemies"]):
                segment_completion_time = pygame.time.get_ticks()
                print(f"Finished spawning segment {current_segment_index}.")

    for enemy in enemies:
        if isinstance(enemy, game_tools.FireflyEnemy):
            enemy.update_heal_effect(enemies)

    # Then process enemy movement and damage
    for enemy in enemies.copy():  # Use copy to avoid modification during iteration
        enemy.move()
        if not enemy.is_alive:
            enemies.remove(enemy)
            game_stats.global_kill_total["count"] += 1

        # Then render (order matters less here)
    for enemy in enemies:
        enemy.render(scrn)

    game_tools.update_stunned_enemies(enemies)

    for tower in game_tools.towers:
        if isinstance(tower, game_tools.RatBank):
            if tower.investment_window_open:
                tower.investment_interface(scrn)

    # Determine if the segment is done.
    seg_delay = segment.get("delay", 0) / game_tools.game_speed_multiplier
    segment_done = False
    # For non-final segments, mark as done after spawn count reached and delay elapsed.
    if current_segment_index < len(current_round_config) - 1:
        if segment_enemy_spawned >= len(segment["enemies"]):
            if seg_delay != 0:
                if segment_completion_time and pygame.time.get_ticks() - segment_completion_time >= seg_delay:
                    segment_done = True
            else:
                segment_done = True
    else:
        # Final segment: only mark complete if spawn count is reached AND no enemies remain.
        if segment_enemy_spawned >= len(segment["enemies"]) and not enemies:
            segment_done = True

    if segment_done:
        print(f"Segment {current_segment_index} complete.")
        current_segment_index += 1
        segment_enemy_spawned = 0
        segment_start_time = pygame.time.get_ticks()
        segment_completion_time = None
        rush_active = False
        rush_info = None
        rush_spawned = 0

    return False

# -----------------------------
# End of waves.py
# -----------------------------
