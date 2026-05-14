import json
import os

_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'demo_thresholds.json')

DEFAULTS = {
    "group1_min": 80,    # min confidence for allowed (groups 1 & 2)
    "group3_low": 50,    # lower bound for warning zone (group 3)
    "lockout_count": 3,  # failed attempts before lockout (rule 31)
}


def get():
    try:
        with open(_CONFIG_FILE, encoding='utf-8') as f:
            cfg = json.load(f)
        return {**DEFAULTS, **cfg}
    except Exception:
        return DEFAULTS.copy()


def save(data):
    merged = {**DEFAULTS, **data}
    with open(_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
