import json
import pygame
import game_tools
import game_stats

###############################################################################
# TOWER_CONSTRUCTOR_ATTRIBUTES:
# Must match the tower class __init__ exactly. No extras.
###############################################################################
TOWER_CONSTRUCTOR_ATTRIBUTES = {
    "MrCheese": [
        "image_path",
        "position",
        "radius",
        "weapon",
        "damage",
        "projectile_image",
        "shoot_interval",
    ],
    "RatTent": [
        "position",
        "radius",
        "recruit_health",
        "recruit_speed",
        "recruit_damage",
        "image_path",
        "recruit_image",
        "spawn_interval",
    ],
    "Ozbourne": [
        "position",
        "radius",
        "weapon",
        "damage",
        "image_path",
        "riff_blast_radius",
        "riff_interval",
    ],
    "RatBank": [
        "position",
        "image_path",
    ],
    "MinigunTower": [
        "position",
        #"image_path",
    ],
    "RatSniper": [
        "position",
        "shoot_interval",
        "damage",
        #"image_path",
    ],
    "RatFrost": [
        "position",
        #"image_path",
    ],
    "WizardTower": [
        "position",
        #"image_path",
    ],
    "CheeseBeacon": [
        "position",
        #"image_path",
    ],
    "CheddarCommando": [
        "position",
        "radius",
        "damage",
        "shoot_interval",
        "reload_time",
        #"image_path",
    ],
}

###############################################################################
# TOWER_SAVE_ATTRIBUTES:
# Extra fields to load/save after constructing the tower.
###############################################################################
TOWER_SAVE_ATTRIBUTES = {
    "MrCheese": [
        "image_path",
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "penetration",
        "sell_amt",
        "radius",
        "shoot_interval",
        "weapon",
        "damage",
        "image_path",
        "projectile_image",
    ],
    "RatTent": [
        "image_path",
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "spawn_interval",
        "recruit_speed",
        "recruit_health",
        "recruit_damage",
        "image_path",
        "recruit_image",
    ],
    "Ozbourne": [
        "image_path",
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "riff_interval",
        "blast_duration",
        "riff_blast_radius",
        "max_blast_radius",
        "damage",
        "radius",
        "weapon",
        "image_path",
        "projectile_image",
    ],
    "RatBank": [
        "image_path",
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "interest_rate",
        "cash_invested",
        "cash_generated",
        "loan_amount",
        "loan_payment",
        "provoloanFlag",
        "briefundFlag",
        "is_selected",
    ],
    "MinigunTower": [
        "image_path",
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "damage",
        "radius",
        "magazine_size",
        "base_magazine",
        "reload_time",
    ],
    "RatSniper": [
        "image_path",
        "image_path_shoot"
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "shoot_interval",
        "damage",
    ],
    "RatFrost": [
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "damage",
        "radius",
        "shoot_interval",
        "slow_effect",
    ],
    "WizardTower": [
        "image_path",
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "damage",
        "radius",
    ],
    "CheeseBeacon": [
        "image_path",
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "buff_radius",
    ],
    "CheddarCommando": [
        "image_path",
        "sound_path",
        "reload_path"
        "curr_top_upgrade",
        "curr_bottom_upgrade",
        "sell_amt",
        "radius",
        "damage",
        "shoot_interval",
        "reload_time",
    ],
}


###############################################################################
# Because “TypeError: Object of type Sound is not JSON serializable” can happen,
# we skip raw Sound objects, storing only their path if possible.
###############################################################################
def sanitize_for_json(value):
    # If it's a pygame Sound, store a default string path
    if isinstance(value, pygame.mixer.Sound):
        return "assets/riff.mp3"
    return value  # Otherwise leave it be


###############################################################################
# 1) Save
###############################################################################
def save_game(filename, wave_number, kill_count, resume_flag, money):
    data = {
        "wave_number": wave_number,
        "kill_count": kill_count,
        "resume_flag": resume_flag,
        "towers": [],
        "money": money
    }

    for tower in game_tools.towers:
        tower_type = tower.__class__.__name__
        if tower_type not in TOWER_CONSTRUCTOR_ATTRIBUTES:
            print(f"[WARN] Tower type '{tower_type}' not recognized. Skipping.")
            continue

        tower_dict = {"tower_type": tower_type}

        # 1) Save constructor attrs
        for attr in TOWER_CONSTRUCTOR_ATTRIBUTES[tower_type]:
            val = getattr(tower, attr, None)
            tower_dict[attr] = sanitize_for_json(val)

        # 2) Save extra fields
        for attr in TOWER_SAVE_ATTRIBUTES.get(tower_type, []):
            val = getattr(tower, attr, None)
            tower_dict[attr] = sanitize_for_json(val)

        data["towers"].append(tower_dict)

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Game saved to {filename}!")


def save_settings(filename, max_shards, max_indicators, game_speed, showfps, showcursor, music_level, fullscreen):
    data = {
        "max_shards": max_shards,
        "max_indicators": max_indicators,
        "game_speed": game_speed,
        "showfps": showfps,
        "showcursor": showcursor,
        "music_level": music_level,
        "fullscreen": fullscreen
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Settings saved to {filename}!")


###############################################################################
# 2) Load
###############################################################################
def load_game(filename):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"No save file found at {filename}.")
        return 1, 0, False, 250

    wave_number = data.get("wave_number", 1)
    kill_count = data.get("kill_count", 0)
    resume_flag = data.get("resume_flag", False)
    money = data.get("money", 250)

    game_tools.towers.clear()

    towers_list = data.get("towers", [])
    for tower_data in towers_list:
        tower_type = tower_data.get("tower_type")
        if tower_type not in TOWER_CONSTRUCTOR_ATTRIBUTES:
            print(f"[WARN] Unrecognized tower_type '{tower_type}' in save. Skipping.")
            continue

        cls_ = getattr(game_tools, tower_type, None)
        if cls_ is None:
            print(f"[WARN] No class found for tower_type={tower_type}. Skipping.")
            continue

        # Build constructor kwargs:
        init_args = {}
        for attr in TOWER_CONSTRUCTOR_ATTRIBUTES[tower_type]:
            init_args[attr] = tower_data.get(attr)

        # Attempt instantiation:
        try:
            new_tower = cls_(**init_args)
        except TypeError as e:
            print(f"[ERROR] Failed to instantiate tower '{tower_type}': {e}")
            continue

        # Restore extra attributes
        for attr in TOWER_SAVE_ATTRIBUTES.get(tower_type, []):
            if attr in tower_data:
                setattr(new_tower, attr, tower_data[attr])

        # If needed, load images post-init:
        # (But only if the tower constructor doesn't already do it.)
        if hasattr(new_tower, "image_path"):
            ip = getattr(new_tower, "image_path", "")
            if isinstance(ip, str) and ip:
                try:
                    new_tower.image = game_tools.load_image(ip)
                except Exception as ex:
                    print(f"[WARN] Could not load image '{ip}': {ex}")
                    new_tower.image = game_tools.load_image("assets/fallback.png")

        if hasattr(new_tower, "projectile_image"):
            pi = getattr(new_tower, "projectile_image", "")
            if isinstance(pi, str) and pi:
                try:
                    new_tower.projectile_img_obj = game_tools.load_image(pi)
                except:
                    print("[WARN] Could not load projectile image. Using fallback.")
                    new_tower.projectile_img_obj = game_tools.load_image("assets/fallback_projectile.png")

        # For MrCheese, ensure defaults if missing
        if tower_type == "MrCheese":
            if getattr(new_tower, "curr_top_upgrade", None) is None:
                new_tower.curr_top_upgrade = 0
            if getattr(new_tower, "curr_bottom_upgrade", None) is None:
                new_tower.curr_bottom_upgrade = 0
            if getattr(new_tower, "penetration", None) is None:
                new_tower.penetration = False
            if getattr(new_tower, "sell_amt", None) is None:
                new_tower.sell_amt = 75

        game_tools.towers.append(new_tower)
        game_tools.TowerFlag = False

    print(f"Game loaded from {filename} (wave={wave_number}, kills={kill_count}, resume={resume_flag}).")
    return wave_number, kill_count, resume_flag, money


def load_settings(filename):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"No save file found at {filename}.")
        return 500, 500, 2, False, False, 1.0, False

    max_shards = data.get("max_shards", 500)
    max_indicators = data.get("max_indicators", 500)
    game_speed = data.get("game_speed", 2)
    showfps = data.get("showfps", False)
    showcursor = data.get("showcursor", False)
    music_level = data.get("music_level", 1.0)
    fullscreen = data.get("fullscreen", False)

    return max_shards, max_indicators, game_speed, showfps, showcursor, music_level, fullscreen


def wipe_save(filename):
    """
    Overwrites the save file with a minimal/empty JSON structure,
    effectively resetting progress.
    """
    data = {
        "wave_number": 1,
        "kill_count": 0,
        "towers": [],
        "resume_flag": False
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"{filename} has been reset to an empty state.")
