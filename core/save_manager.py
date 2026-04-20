import json
import os
import datetime

SAVE_FILE = "save_game.json"

def save_session(world_data, current_date, balance=1000000):
    """
    Saves the game state to a JSON file.
    :param world_data: 3D world array list.
    :param current_date: datetime object.
    :param balance: Current budget balance.
    """
    data = {
        "world_data": world_data,
        "current_date": current_date.strftime("%Y-%m-%d %H:%M:%S"),
        "balance": balance
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)
    print(f"Game saved to {SAVE_FILE}")

def load_session():
    """
    Loads the game state from the JSON file.
    :return: dict with 'world_data' and 'current_date' or None.
    """
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                data["current_date"] = datetime.datetime.strptime(data["current_date"], "%Y-%m-%d %H:%M:%S")
                return data
        except Exception as e:
            print(f"Error loading save: {e}")
    return None

def has_save():
    return os.path.exists(SAVE_FILE)

def delete_save():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
