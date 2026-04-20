import json
import os
import datetime

SAVE_FILE = "savegame.json"

def save_game(world_data, time_manager, cam_x, cam_y, zoom):
    """
    Serializes current game state to a JSON file.
    """
    state = {
        "world_data": world_data,
        "current_date": time_manager.current_date.isoformat(),
        "cam_x": cam_x,
        "cam_y": cam_y,
        "zoom": zoom
    }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(state, f)
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False

def load_game():
    """
    Loads game state from savegame.json.
    Returns state dict or None if no save exists.
    """
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r") as f:
            state = json.load(f)
        # Parse date
        state["current_date"] = datetime.datetime.fromisoformat(state["current_date"])
        return state
    except Exception as e:
        print(f"Error loading game: {e}")
        return None

def save_exists():
    return os.path.exists(SAVE_FILE)
