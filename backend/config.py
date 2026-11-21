import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = BASE_DIR / "config.json"
DB_FILE = DATA_DIR / "smartdesk.db"

APP_NAME = "SmartDesk 3.15"

DEFAULT_CONFIG = {
    "theme": "dark",
    "api_key": "",
    "api_endpoint": "https://api.openai.com/v1/chat/completions",
    "model": "gpt-4.1-mini"
}

def load_config():
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG.copy())
    try:
        return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )