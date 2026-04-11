import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "life-system"))
SCORE_FILE = os.path.join(BASE_DIR, "system", "score.json")

def load_score():
    if not os.path.exists(SCORE_FILE):
        return {"points": 0, "streak": 0, "status": "IN GAME", "level": 1}
    with open(SCORE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"points": 0, "streak": 0, "status": "IN GAME", "level": 1}

def save_score(data):
    os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
    with open(SCORE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def update_score(aligned_count: int, misaligned_count: int, activity_logged: bool):
    data = load_score()
    
    if not activity_logged:
        # Missed a day
        data["streak"] = 0
        data["points"] -= 10
    else:
        # Did log activity
        data["points"] += (aligned_count * 10)
        data["points"] -= (misaligned_count * 5)
        if aligned_count > 0 and misaligned_count == 0:
            data["streak"] += 1
        elif misaligned_count > 0:
            data["streak"] = 0
            
    # Calculate level (Level 1 = 0-100, Level 2 = 100-300, etc.)
    data["level"] = max(1, (data["points"] // 100) + 1)
    
    if data["points"] < 0:
        data["status"] = "AT RISK"
    else:
        data["status"] = "IN GAME"
        
    save_score(data)
    return data
