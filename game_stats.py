# game_stats.py

import json
import os
import time

global_kill_total = {"count": 0}

# Path to the stats JSON file.
STATS_FILE = "game_stats.json"

# Global dictionary to hold cumulative stats.
# total_money: cumulative money earned (even if spent during a game)
# total_kills: cumulative enemy kill count
# total_playtime: cumulative play time in seconds
stats = {
    "total_money": 0,
    "total_kills": 0,
    "total_playtime": 0.0
}

# Global timer variable to track when playtime was last updated.
last_update_time = None


def load_game_stats():
    """
    Loads the game stats from STATS_FILE into the global stats dictionary.
    Also initializes last_update_time to the current time.
    """
    global stats, last_update_time
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
    else:
        save_game_stats()  # Creates the file with default stats if it doesn't exist.
    # Initialize the playtime timer.
    last_update_time = time.time()


def save_game_stats():
    """
    Saves the current stats dictionary to STATS_FILE.
    """
    global stats
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)


def add_money(amount):
    """
    Adds the specified amount to the total money earned.
    :param amount: Number of money units to add.
    """
    global stats
    stats["total_money"] += amount
    print(f"Added {amount} money. Total money earned: {stats['total_money']}")
    save_game_stats()


def add_kill(count=1):
    """
    Adds the specified kill count to the total kill tally.
    :param count: Number of kills to add (default is 1).
    """
    global stats
    stats["total_kills"] += count
    print(f"Added {count} kill(s). Total kills: {stats['total_kills']}")
    save_game_stats()


def update_playtime():
    """
    Updates the cumulative total playtime. This function calculates the elapsed time
    since the last call, adds it to total_playtime, updates the timer, and saves the updated stats.

    This function should be called periodically in your game loop.
    """
    global stats, last_update_time
    if last_update_time is None:
        last_update_time = time.time()
        return
    current_time = time.time()
    elapsed = current_time - last_update_time
    stats["total_playtime"] += elapsed
    last_update_time = current_time
    print(f"Playtime updated by {elapsed:.2f} seconds. Total playtime: {stats['total_playtime']:.2f} seconds")
    save_game_stats()


def get_game_stats():
    """
    Returns the current cumulative stats.
    """
    return stats


# For testing purposes, run this module directly.
if __name__ == "__main__":
    load_game_stats()
    print("Initial Stats:", stats)

    # Simulate game progress:
    print("Simulating gameplay for 5 seconds...")
    time.sleep(5)
    update_playtime()

    add_money(100)
    add_kill(5)

    print("Updated Stats:", get_game_stats())
