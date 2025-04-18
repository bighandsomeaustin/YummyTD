# merit_system.py

import json
import os
import pygame
import game_tools

# Global variables for star merit system.
TOTAL_STARS = 0
CHECKPOINT_DATA = None  # Will store checkpoint information (only one checkpoint per round)

# Define some example achievements.
ACHIEVEMENTS = {
    "kill_10000_bugs": {
        "description": "Kill 10,000 bugs",
        "target": 10000,
        "progress": 0,
        "star_reward": 1,
        "completed": False,
    },
    "earn_100000_cash": {
        "description": "Earn 100,000 cash",
        "target": 100000,
        "progress": 0,
        "star_reward": 2,
        "completed": False,
    },
    "round30_mrcheese_only": {
        "description": "Reach round 30 using only MrCheese",
        "target": 30,
        "progress": 0,
        "star_reward": 5,
        "completed": False,
    },
    # Additional achievements can be defined here.
}

MERIT_SAVE_FILE = "merit_save.json"


def load_merit_data():
    global TOTAL_STARS, ACHIEVEMENTS, CHECKPOINT_DATA
    if not os.path.exists(MERIT_SAVE_FILE):
        save_merit_data()
    else:
        with open(MERIT_SAVE_FILE, "r") as f:
            data = json.load(f)
            TOTAL_STARS = data.get("total_stars", 0)
            ACHIEVEMENTS = data.get("achievements", ACHIEVEMENTS)
            CHECKPOINT_DATA = data.get("checkpoint", None)


def save_merit_data():
    data = {
        "total_stars": TOTAL_STARS,
        "achievements": ACHIEVEMENTS,
        "checkpoint": CHECKPOINT_DATA
    }
    with open(MERIT_SAVE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def award_stars_for_round(awarded, screen):
    """
    Award stars when round thresholds are met:
      - 1 star for reaching round 30,
      - 1 additional star for reaching round 60,
      - 1 additional star for reaching round 100.

    This function adds the awarded stars to TOTAL_STARS and triggers an animation.
    """
    global TOTAL_STARS
    TOTAL_STARS += awarded
    play_star_animation(awarded)
    save_merit_data()


import pygame


def fade_image(screen, image, pos, duration=1000, fade_type="in"):
    """
    Fades an image either in or out over a specified duration.

    Parameters:
      screen   - pygame.Surface where the image will be blitted. The background should already be drawn.
      image    - pygame.Surface of the image (e.g., loaded via game_tools.load_image).
      pos      - tuple (x, y) specifying where to blit the image.
      duration - fade duration in milliseconds (default 1000).
      fade_type- "in" for fade in (alpha 0 -> 255) or "out" for fade out (alpha 255 -> 0).

    This function captures the current screen background so that only the image fades.
    """
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    # Capture the current background
    background = screen.copy()

    # Create a copy of the image so the original remains unchanged.
    fading_image = image.copy()

    # Initialize alpha based on fade type.
    if fade_type == "in":
        fading_image.set_alpha(0)
    elif fade_type == "out":
        fading_image.set_alpha(255)
    else:
        raise ValueError("fade_type must be either 'in' or 'out'.")

    finished = False
    while not finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                finished = True

        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time

        if elapsed >= duration:
            elapsed = duration
            finished = True

        if fade_type == "in":
            # Increase alpha from 0 to 255.
            alpha = int((elapsed / duration) * 255)
        else:  # fade_type == "out":
            # Decrease alpha from 255 down to 0.
            alpha = 255 - int((elapsed / duration) * 255)

        fading_image.set_alpha(alpha)

        # Restore the background and then draw the fading image on top.
        screen.blit(background, (0, 0))
        screen.blit(fading_image, pos)
        pygame.display.flip()
        clock.tick(60)

    # Ensure final state.
    if fade_type == "in":
        fading_image.set_alpha(255)
    else:
        fading_image.set_alpha(0)
    screen.blit(background, (0, 0))
    screen.blit(fading_image, pos)
    pygame.display.flip()


def play_star_animation(star_count):
    """
    Plays the complete star reward animation.

    For star_count == 1 or 2, it performs the regular animation:
      1. Plays the reward sound.
      2. Fades in a previous star image over 500 ms.
      3. Immediately spawns a particle explosion behind the star and displays the current star image
         fully opaque for 1000 ms while updating particles.
      4. Fades out the current star image over 500 ms.

    For star_count == 3 (i.e. round 30), after the regular animation a trophy bonus is played:
      5. Fades in the trophy image over 750 ms.
      6. Displays the trophy fully for 2250 ms (with a cheering sound).
      7. Fades out the trophy image over 750 ms.

    Parameters:
      star_count - the number of stars to reward (1, 2, or 3)
      screen     - the pygame.Surface on which to perform the animation
    """
    screen = pygame.display.get_surface()
    pygame.mixer.music.pause()

    clock = pygame.time.Clock()
    # Capture the current background once.
    background = screen.copy()

    # Set up assets and positions based on star_count.
    trophy_animation = False
    sfx_channel = pygame.mixer.Channel(7)
    boom_sound = game_tools.load_sound("assets/vine_boom.mp3")
    trophy_sound = game_tools.load_sound("assets/kids_cheering.mp3")
    if star_count == 1:
        img_prev = game_tools.load_image("assets/stars0.png")
        img_current = game_tools.load_image("assets/stars1.png")
        shard_pos = (538, 130)
        reward_sound = game_tools.load_sound("assets/songs/lvl10.mp3")
    elif star_count == 2:
        img_prev = game_tools.load_image("assets/stars1.png")
        img_current = game_tools.load_image("assets/stars2.png")
        shard_pos = (405, 200)
        reward_sound = game_tools.load_sound("assets/songs/lvl20.mp3")
    elif star_count == 3:
        img_prev = game_tools.load_image("assets/stars2.png")
        img_current = game_tools.load_image("assets/stars3.png")
        shard_pos = (355, 303)
        reward_sound = game_tools.load_sound("assets/songs/lvl30.mp3")
        trophy_animation = True
        trophy_img = game_tools.load_image("assets/bronze_trophy.png")
    elif star_count == 4:
        img_prev = game_tools.load_image("assets/stars3.png")
        img_current = game_tools.load_image("assets/stars4.png")
        shard_pos = (405, 373)
        reward_sound = game_tools.load_sound("assets/songs/lvl40.mp3")
    elif star_count == 5:
        img_prev = game_tools.load_image("assets/stars4.png")
        img_current = game_tools.load_image("assets/stars5.png")
        shard_pos = (498, 440)
        reward_sound = game_tools.load_sound("assets/songs/lvl50.mp3")
        trophy_animation = True
        trophy_img = game_tools.load_image("assets/silver_trophy.png")
    elif star_count == 6:
        img_prev = game_tools.load_image("assets/stars5.png")
        img_current = game_tools.load_image("assets/stars6.png")
        shard_pos = (598, 407)
        reward_sound = game_tools.load_sound("assets/songs/lvl65.mp3")
        trophy_animation = True
        trophy_img = game_tools.load_image("assets/gold_trophy.png")
    elif star_count == 7:
        img_prev = game_tools.load_image("assets/stars6.png")
        img_current = game_tools.load_image("assets/stars7.png")
        shard_pos = (654, 325)
        reward_sound = game_tools.load_sound("assets/songs/lvl85.mp3")
    elif star_count == 8:
        img_prev = game_tools.load_image("assets/stars7.png")
        img_current = game_tools.load_image("assets/stars8.png")
        shard_pos = (614, 205)
        reward_sound = game_tools.load_sound("assets/songs/lvl100.mp3")
        trophy_animation = True
        trophy_img = game_tools.load_image("assets/diamond_trophy.png")
    else:
        # Fallback assets.
        img_prev = game_tools.load_image("assets/stars0.png")
        img_current = game_tools.load_image("assets/stars1.png")
        shard_pos = (578, 130)
        reward_sound = game_tools.load_sound("assets/songs/lvl10.mp3")

    # Set the display position for the star animation.
    pos = (265, 49)

    # --- Regular Star Animation ---

    # 1. Play the reward sound.
    sfx_channel.set_volume(0.25)
    sfx_channel.play(reward_sound, fade_ms=250)

    # 2. Fade in previous star image over 500 ms.
    fade_in_duration = 500  # ms
    start_time = pygame.time.get_ticks()
    while True:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        if elapsed > fade_in_duration:
            elapsed = fade_in_duration
        alpha = int((elapsed / fade_in_duration) * 255)
        screen.blit(background, (0, 0))
        temp_img = img_prev.copy()
        temp_img.set_alpha(alpha)
        screen.blit(temp_img, pos)
        pygame.display.flip()
        clock.tick(60)
        if elapsed >= fade_in_duration:
            break

    # 3. Spawn particle explosion and display current star image fully for 1000 ms.
    boom_sound.play()
    game_tools.spawn_shard(shard_pos, (255, 255, 255), 50, 5, (3, 6), (500, 1000))
    wait_duration = 2250  # ms
    start_wait = pygame.time.get_ticks()
    while True:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_wait
        screen.blit(background, (0, 0))
        temp_img = img_current.copy()
        temp_img.set_alpha(255)
        screen.blit(temp_img, pos)
        game_tools.update_shards(screen)
        pygame.display.flip()
        clock.tick(60)
        if elapsed >= wait_duration:
            break

    # 4. Fade out current star image over 500 ms.
    fade_out_duration = 500  # ms
    start_time = pygame.time.get_ticks()
    while True:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        if elapsed > fade_out_duration:
            elapsed = fade_out_duration
        alpha = 255 - int((elapsed / fade_out_duration) * 255)
        screen.blit(background, (0, 0))
        temp_img = img_current.copy()
        temp_img.set_alpha(alpha)
        screen.blit(temp_img, pos)
        game_tools.update_shards(screen)
        pygame.display.flip()
        clock.tick(60)
        if elapsed >= fade_out_duration:
            break

    # --- Trophy Animation for Round 30 ---
    if trophy_animation:
        pos = (265, 149)
        trophy_fade_duration = 750  # ms for fade in/out
        # 5. Fade in trophy image.
        start_time = pygame.time.get_ticks()
        while True:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - start_time
            if elapsed > trophy_fade_duration:
                elapsed = trophy_fade_duration
            alpha = int((elapsed / trophy_fade_duration) * 255)
            screen.blit(background, (0, 0))
            temp_img = trophy_img.copy()
            temp_img.set_alpha(alpha)
            screen.blit(temp_img, pos)
            game_tools.update_shards(screen)
            pygame.display.flip()
            clock.tick(60)
            if elapsed >= trophy_fade_duration:
                break

        # 6. Display trophy fully for 2250 ms.
        if star_count == 8:
            game_tools.spawn_shard((375, 375), (255, 247, 122), 75, 12, (1, 3), (1500, 2500))
            game_tools.spawn_shard((675, 244), (144, 255, 238), 75, 12, (1, 3), (1500, 2500))
            game_tools.spawn_shard((525, 144), (121, 255, 85), 75, 12, (1, 3), (1500, 2500))
            display_duration = 2000  # ms
        else:
            game_tools.spawn_shard((375, 375), (255, 255, 255), 35, 10, (1, 4), (500, 1000))
            game_tools.spawn_shard((675, 244), (255, 255, 255), 35, 10, (1, 4), (500, 1000))
            game_tools.spawn_shard((525, 144), (255, 255, 255), 35, 10, (1, 4), (500, 1000))
            display_duration = 2250  # ms
        start_wait = pygame.time.get_ticks()
        trophy_sound.play()  # play trophy sound
        while True:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - start_wait
            screen.blit(background, (0, 0))
            temp_img = trophy_img.copy()
            temp_img.set_alpha(255)
            screen.blit(temp_img, pos)
            game_tools.update_shards(screen)
            pygame.display.flip()
            clock.tick(60)
            if elapsed >= display_duration:
                break

        # 7. Fade out trophy image over 750 ms.
        start_time = pygame.time.get_ticks()
        if star_count == 8:
            trophy_fade_duration = 2000
        while True:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - start_time
            if elapsed > trophy_fade_duration:
                elapsed = trophy_fade_duration
            alpha = 255 - int((elapsed / trophy_fade_duration) * 255)
            screen.blit(background, (0, 0))
            temp_img = trophy_img.copy()
            temp_img.set_alpha(alpha)
            screen.blit(temp_img, pos)
            game_tools.update_shards(screen)
            pygame.display.flip()
            clock.tick(60)
            if elapsed >= trophy_fade_duration:
                break

    # Finalize: re-blit the background so the animation is cleared.
    screen.blit(background, (0, 0))
    pygame.display.flip()
    pygame.mixer.music.unpause()


# Functions for spending stars on upgrades.

def purchase_health_upgrade():
    """
    Spend 1 star to grant an additional +5 starting health.
    (Implement the effect on game configuration as needed.)
    """
    global TOTAL_STARS
    if TOTAL_STARS >= 1:
        TOTAL_STARS -= 1
        print("Purchased +5 starting health!")
        # Here, integrate with your game config to add +5 to starting health.
        save_merit_data()
    else:
        print("Not enough stars to purchase health upgrade.")


def purchase_cash_upgrade():
    """
    Spend 1 star to grant an additional +5 starting cash.
    (Implement the effect on game configuration as needed.)
    """
    global TOTAL_STARS
    if TOTAL_STARS >= 1:
        TOTAL_STARS -= 1
        print("Purchased +5 starting cash!")
        # Here, integrate with your game config to add +5 to starting money.
        save_merit_data()
    else:
        print("Not enough stars to purchase cash upgrade.")


# Checkpoint functions

def create_checkpoint(current_game_state):
    """
    Spend 1 star to create a checkpoint.
    current_game_state should be a dictionary with details like round, health, money, towers, etc.
    Checkpoints are only allowed if none exists for the current round.
    """
    global TOTAL_STARS, CHECKPOINT_DATA
    if TOTAL_STARS >= 1 and CHECKPOINT_DATA is None:
        TOTAL_STARS -= 1
        CHECKPOINT_DATA = {
            "game_state": current_game_state,
            "used": False,
        }
        print("Checkpoint created.")
        save_merit_data()
    else:
        print("Not enough stars or a checkpoint already exists.")


def use_checkpoint():
    """
    If a checkpoint is available and not yet used, mark it as used and return the saved game state.
    Otherwise, return None.
    """
    global CHECKPOINT_DATA
    if CHECKPOINT_DATA and not CHECKPOINT_DATA["used"]:
        CHECKPOINT_DATA["used"] = True
        print("Checkpoint used. Restoring game state.")
        save_merit_data()
        return CHECKPOINT_DATA["game_state"]
    else:
        print("No available checkpoint.")
        return None


def checkpoint_expired():
    """
    Called if the player dies again after using a checkpoint.
    This should trigger game over/reset logic (e.g., resetting the round to 1).
    """
    print("Checkpoint expired. Resetting game to round 1.")
    global CHECKPOINT_DATA
    CHECKPOINT_DATA = None
    save_merit_data()
    return True  # Indicates that the game should reset to round 1.


# Achievement system functions

def update_achievement(ach_name, progress_increment):
    """
    Updates progress on the specified achievement. If progress reaches or exceeds the target,
    the achievement is marked as completed and the corresponding star reward is added.
    """
    if ach_name in ACHIEVEMENTS:
        achievement = ACHIEVEMENTS[ach_name]
        if not achievement["completed"]:
            achievement["progress"] += progress_increment
            print(f"Achievement '{ach_name}' progress: {achievement['progress']}/{achievement['target']}")
            if achievement["progress"] >= achievement["target"]:
                achievement["completed"] = True
                award = achievement["star_reward"]
                global TOTAL_STARS
                TOTAL_STARS += award
                print(f"Achievement '{ach_name}' completed! Awarded {award} star(s). Total stars: {TOTAL_STARS}")
                # You can integrate an achievement animation here.
            save_merit_data()
    else:
        print(f"Achievement '{ach_name}' not defined.")


def get_achievement_status():
    """
    Returns a summary string that lists each achievement, its progress, and whether it is completed.
    """
    lines = []
    for key, ach in ACHIEVEMENTS.items():
        status = "Completed" if ach["completed"] else "Incomplete"
        lines.append(f"{ach['description']}: {ach['progress']}/{ach['target']} - {status}")
    return "\n".join(lines)


def check_mrcheese_only(round_towers):
    # PLAIN WITH CHEESE
    """
    Checks if all towers placed during the round are of type 'MrCheese'.
    Returns True if the condition is met, otherwise False.
    """
    # Assuming that each tower has a __class__.__name__ attribute.
    if not round_towers:
        return False  # No towers placed means the condition isn't met.
    return all(tower.__class__.__name__ == "MrCheese" for tower in round_towers)



