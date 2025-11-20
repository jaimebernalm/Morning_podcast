# Helper functions to load/save JSONs
import json

def get_user_profile(user_id: str):
    with open("db/preferences.json", "r") as f:
        data = json.load(f)
    return data.get(user_id, {}) # Returns empty dict if user not found