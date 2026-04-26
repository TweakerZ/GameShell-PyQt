import json
from .config import GAMESHELL_DIR, LIBRARY_FILE, SETTINGS_FILE

def read_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, data):
    GAMESHELL_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def uid():
    import random, string
    import time
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + hex(int(time.time()))[2:]
