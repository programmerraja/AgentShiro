import os
import json
import uuid
import datetime

# Determine base dir
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "life-system"))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
OBSERVABILITY_DIR = os.path.join(BASE_DIR, "observability")
OBSERVABILITY_FILE = os.path.join(OBSERVABILITY_DIR, "finetuning_logs.jsonl")

class SessionManager:
    def __init__(self, observability_enabled: bool = True):
        self.observability_enabled = observability_enabled
        self.session_id = None
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        if self.observability_enabled:
            os.makedirs(OBSERVABILITY_DIR, exist_ok=True)
            
    def create_session(self) -> str:
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:4]
        return self.session_id
        
    def set_session(self, session_id: str):
        self.session_id = session_id
        
    def get_session_path(self, session_id: str) -> str:
        return os.path.join(SESSIONS_DIR, f"session_{session_id}.json")
        
    def load_session(self, session_id: str) -> list:
        path = self.get_session_path(session_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Session {session_id} does not exist.")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.session_id = session_id
            return data.get("messages", [])
            
    def save_session(self, messages: list):
        if not self.session_id:
            self.create_session()
        path = self.get_session_path(self.session_id)
        data = {
            "session_id": self.session_id,
            "last_updated": datetime.datetime.now().isoformat(),
            "messages": messages
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
    def list_sessions(self) -> list:
        sessions = []
        if os.path.exists(SESSIONS_DIR):
            for filename in os.listdir(SESSIONS_DIR):
                if filename.startswith("session_") and filename.endswith(".json"):
                    sid = filename[len("session_"):-len(".json")]
                    path = os.path.join(SESSIONS_DIR, filename)
                    mtime = os.path.getmtime(path)
                    sessions.append({
                        "session_id": sid,
                        "last_updated": datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
        return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)

    def log_observability(self, messages: list):
        if not self.observability_enabled:
            return
        record = {
            "messages": messages
        }
        with open(OBSERVABILITY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
