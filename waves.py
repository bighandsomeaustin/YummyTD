import math
import pygame
import game_tools
import random
import game_stats

# -----------------------------
# Global Variables and Initialization
# -----------------------------
enemies = game_tools.enemies
money = game_tools.money  # This is updated in game_tools
last_spawn_time = 0
segment_completion_time = None
FINAL_CLEANUP_DELAY = 1000 / game_tools.game_speed_multiplier  # in milliseconds

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

for r in range(19, 101):
    segments = []

    if r == 19:

        segments.append({"enemies": ["ANT"] * (r * 2) + ["HORNET"] * (r // 2),
                         "spawn_interval": max(300, 500 - r * 10),
                         "delay": 1000})
        segments.append({"enemies": ["ANT"] * (r * 3),
                         "spawn_interval": 50,
                         "delay": 1000})
        segments.append({"enemies": ["CENTIPEDE"] * 5,
                         "spawn_interval": 50,
                         "delay": 0})
    elif r == 20:
        # Spider round: all spiders with a mid-round rush\n
        segments.append({"enemies": ["ROACH_QUEEN"] * 2,
                         "spawn_interval": 3500,
                         "delay": 5000})
        segments.append({"enemies": ["DRAGONFLY"] * 6,
                         "spawn_interval": 750,
                         "delay": 0})
    elif r == 21:
        # Beetle round: tougher enemies in moderate numbers\n
        segments.append({"enemies": ["BEETLE"] * 3 + ["FIREFLY"] * 4 + ["BEETLE"] * 3,
                         "spawn_interval": 100,
                         "delay": 4500,
                         "rush": {"trigger": 7, "num": 3, "speed": 50}})
        segments.append({"enemies": ["BEETLE"] * (r // 2) + ["ANT"] * (2 * r),
                         "spawn_interval": 1000,
                         "delay": 500,
                         "rush": {"trigger": int((r // 2 + r) * 0.4), "num": 3, "speed": 200}})
    elif r == 22:
        # Centipede rush: mix of centipedes and ants\n
        segments.append({"enemies": ["DRAGONFLY"] * 4 + ["CENTIPEDE"] * (r // 3) + ["HORNET"] * (10),
                         "spawn_interval": 900,
                         "delay": 3500,
                         "rush": {"trigger": int((r // 3 + r) * 0.6), "num": 5, "speed": 350}})
        segments.append({"enemies": ["ROACH_QUEEN"] * 2,
                         "spawn_interval": 3500,
                         "delay": 0})
    elif r == 23:
        # Mixed forces with a delayed second phase\n
        segments.append({"enemies": ["ANT"] * (r * 4),
                         "spawn_interval": 50,
                         "delay": 1500})
        segments.append({"enemies": ["HORNET"] * (r * 2),
                         "spawn_interval": 200,
                         "delay": 0,
                         "rush": {"trigger": int(r * 0.5), "num": 3, "speed": 400}})
    elif r == 24:
        # Mixed forces with a delayed second phase\n
        segments.append({"enemies": ["ANT"] * 10 + ["FIREFLY"] * 3,
                         "spawn_interval": 0,
                         "delay": 3500})
        segments.append({"enemies": ["HORNET"] * 5 + ["FIREFLY"] * 3,
                         "spawn_interval": 50,
                         "delay": 3500})
        segments.append({"enemies": ["DRAGONFLY"] * 4 + ["FIREFLY"] * 3,
                         "spawn_interval": 50,
                         "delay": 3500})
    elif r == 25:
        # DUNG BEETLE BOSS!!!
        segments.append({"enemies": ["DUNG_BEETLE"],
                         "spawn_interval": 3000,
                         "delay": 0})

    # another dung beetle, with some more enemies
    elif r == 26:
        segments.append({"enemies": ["DUNG_BEETLE"],
                         "spawn_interval": 2000,
                         "delay": 7000})
        segments.append({"enemies": (["FIREFLY"] + ["BEETLE"] * 2 + ["FIREFLY"] + ["BEETLE"] * 2) * 8,
                         "spawn_interval": 500,
                         "delay": 2000})
        # dragonfly rush
        segments.append({"enemies": ["DRAGONFLY"] * 25,
                         "spawn_interval": 50,
                         "delay": 7000})
        # dung beetle
        segments.append({"enemies": ["DUNG_BEETLE"],
                         "spawn_interval": 2000,
                         "delay": 0})

    # huge centipede + fireflies + roach queen finale
    elif r == 27:
        segments.append({"enemies": ["CENTIPEDE_BOSS"] * 4,
                         "spawn_interval": 1000,
                         "delay": 3000})
        segments.append({"enemies": (["CENTIPEDE"] * 2 + ["FIREFLY"] + ["CENTIPEDE"] * 2) * 9,
                         "spawn_interval": 750,
                         "delay": 3000})
        segments.append({"enemies": (["FIREFLY"] * 2 + ["ROACH_QUEEN"] * 4 + ["FIREFLY"] * 2) * 4,
                         "spawn_interval": 50,
                         "delay": 0})

    # insane barrage of dragonflies, beetles, spiders
    elif r == 28:
        segments.append({"enemies": (["BEETLE"] + ["SPIDER"] + ["DRAGONFLY"] * 5) * 15,
                         "spawn_interval": 150,
                         "delay": 3000})
        segments.append({"enemies": (["FIREFLY"] + ["ROACH_QUEEN"] + ["ROACH"] * 3) * 5,
                         "spawn_interval": 250,
                         "delay": 3000})

    # 3 dung beetle bosses stacked, followed by 10 roach queens
    elif r == 29:
        segments.append({"enemies": (["HORNET"] + ["DRAGONFLY"]) * 60,
                         "spawn_interval": 150,
                         "delay": 1000})
        segments.append({"enemies": ["DUNG_BEETLE"] * 3,
                         "spawn_interval": 500,
                         "delay": 6000})
        segments.append({"enemies": (["ROACH_QUEEN"] + ["ROACH"] * 4) * 10,
                         "spawn_interval": 150,
                         "delay": 0})

    # free money, before health multiplier increase
    elif r == 30:
        segments.append({"enemies": ["SPIDER"] * 60,
                         "spawn_interval": 250,
                         "delay": 3000})
        segments.append({"enemies": ["CENTIPEDE"] * 30,
                         "spawn_interval": 350,
                         "delay": 5000})
        segments.append({"enemies": ["ANT"] * 100,
                         "spawn_interval": 5,
                         "delay": 0})

    # start off with some basic enemies
    elif r == 31:
        segments.append({"enemies": ["ANT"] * 30,
                         "spawn_interval": 200,
                         "delay": 3000})
        segments.append({"enemies": ["HORNET"] * 20,
                         "spawn_interval": 400,
                         "delay": 3000})
        segments.append({"enemies": ["BEETLE"] * 5,
                         "spawn_interval": 500,
                         "delay": 3000})
        # THEN BOOM!!!
        segments.append({"enemies": ["DUNG_BEETLE"] * 2,
                         "spawn_interval": 1000,
                         "delay": 0})

    # dragonflies, fireflies, dung beetle, repeat
    elif r == 32:

        for i in range(2):
            for _ in range(6):
                segments.append({"enemies": (["BEETLE"] * 4 + ["FIREFLY"] * 2),
                                 "spawn_interval": 100,
                                 "delay": 500})

            segments.append({"enemies": ["DRAGON"] * 2,
                             "spawn_interval": 100,
                             "delay": 0})
            segments.append({"enemies": ["DUNG_BEETLE"],
                             "spawn_interval": 200,
                             "delay": 2500})

    # huge ant masses, broken up by roach queens, centipede bosses
    elif r == 33:

        for i in range(5):
            for _ in range(2):
                segments.append({"enemies": ["ANT"] * 40,
                                 "spawn_interval": 5,
                                 "delay": 1000})

                segments.append({"enemies": ["ANT"] * 40,
                                 "spawn_interval": 5,
                                 "delay": 1000})

            segments.append({"enemies": (["ROACH_QUEEN"] * 5 + ["CENTIPEDE_BOSS"] * 3),
                             "spawn_interval": 200,
                             "delay": 500})

    # get shit on
    elif r == 34:

        segments.append({"enemies": ["DUNG_BEETLE"] * 3,
                         "spawn_interval": 1000,
                         "delay": 0})

    # just spamming roach queens
    elif r == 35:

        segments.append({"enemies": ["ROACH"] * 30,
                         "spawn_interval": 50,
                         "delay": 6000})

        segments.append({"enemies": (["FIREFLY"] + ["ROACH_QUEEN"] * 3 + ["CENTIPEDE"] * 2) * 10,
                         "spawn_interval": 10,
                         "delay": 0})

    # what happens if I send 50 dragonflies
    elif r == 36:

        # lets be silly for a second
        for i in range(5):
            segments.append({"enemies": ["ANT"] * 10,
                             "spawn_interval": 5,
                             "delay": 1500})

        segments.append({"enemies": ["DRAGONFLY"] * 50,
                         "spawn_interval": 50,
                         "delay": 0})

    # stupid amount of beetles, will probably break game
    elif r == 37:

        segments.append({"enemies": ["BEETLE"] * 30,
                         "spawn_interval": 5,
                         "delay": 0})

    else:

        segments.append({
            "enemies": ["SPIDER", "HORNET"] * (r // 5),
            "spawn_interval": 150,
            "delay": 500
        })
        segments.append({"enemies": ["CENTIPEDE_BOSS"] * 2 * (r % 10),
                         "spawn_interval": 1500,
                         "delay": 1000})
        ant_swarm = 100 + r * 2
        segments.append({"enemies": ["ANT"] * ant_swarm,
                         "spawn_interval": max(20, 100 - r),
                         "delay": 1000})

    if r > 18:
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
    global rush_active, rush_info, rush_spawned, original_spawn_interval, enemies

    if round_number > 30:
        health_mult = 1.5
    elif round_number > 50:
        health_mult = 2
    elif round_number > 70:
        health_mult = 2.5
    elif round_number > 80:
        health_mult = 2.75
    elif round_number > 90:
        health_mult = 3
    elif round_number > 100:
        health_mult = ((round_number % 10) / 2) - 1
    else:
        health_mult = 1

    # Remove dead enemies.
    enemies[:] = [enemy for enemy in enemies if enemy.is_alive]
    # pygame.time.get_ticks() = pygame.time.get_ticks()

    # Final phase: if all segments are done, wait until all enemies are cleared.
    if current_segment_index >= len(current_round_config):
        if not enemies:
            print(f"Wave {round_number} completed.")
            base_reward = 150
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
            if enemy_type == "ANT":
                enemies.append(game_tools.AntEnemy(spawn_pos, 1, 1, offset_path, "assets/ant_base.png"))
            elif enemy_type == "HORNET":
                enemies.append(game_tools.HornetEnemy(spawn_pos, 2, 2, offset_path, "assets/hornet_base.png"))
            elif enemy_type == "BEETLE":
                enemies.append(game_tools.BeetleEnemy(spawn_pos, offset_path))
            elif enemy_type == "SPIDER":
                enemies.append(game_tools.SpiderEnemy(spawn_pos, offset_path))
            elif enemy_type == "CENTIPEDE":
                enemies.append(game_tools.CentipedeEnemy(spawn_pos, offset_path))
            elif enemy_type == "CENTIPEDE_BOSS":
                enemies.append(game_tools.CentipedeEnemy(spawn_pos, offset_path, links=24))
            elif enemy_type == "DRAGONFLY":
                enemies.append(game_tools.DragonflyEnemy(spawn_pos, offset_path))
            elif enemy_type == "ROACH_QUEEN":
                enemies.append(game_tools.RoachQueenEnemy(spawn_pos, offset_path))
            elif enemy_type == "ROACH":
                enemies.append(game_tools.RoachMinionEnemy(position=spawn_pos, path=offset_path,
                                                           speed=random.randint(1, 4), health=3))
            elif enemy_type == "FIREFLY":
                enemies.append(game_tools.FireflyEnemy(spawn_pos, offset_path))
            elif enemy_type == "DUNG_BEETLE":
                enemies.append(game_tools.DungBeetleBoss(spawn_pos, offset_path))

            # apply health multiplier for later rounds
            for enemy in enemies:
                if hasattr(enemy, "health"):
                    enemy.health *= health_mult
                # handle weird enemy classes
                if isinstance(enemy, game_tools.CentipedeEnemy):
                    for seg in enemy.segments:
                        seg.health *= health_mult

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
