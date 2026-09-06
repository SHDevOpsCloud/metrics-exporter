import yaml
import os

DEFAULT_CONFIG = {
    "refresh_interval": 5,
    "server": {
        "host": "0.0.0.0",
        "port": 8000
    },
    "disk": {
        "path": "/"
    },
    "file_checker": {
        "local_directory": "",
        "remote_directory": "",
        "include_patterns": [],
        "exclude_patterns": []
    }
}

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

    if not os.path.exists(config_path):
        print("[warning] config.yaml not found, using defaults")
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[warning] failed to read config.yaml ({e}), using defaults")
        return DEFAULT_CONFIG

    # Merge user config with defaults
    merged = DEFAULT_CONFIG.copy()

    for key, value in user_config.items():
        if isinstance(value, dict) and key in merged:
            merged[key].update(value)
        else:
            merged[key] = value

    return merged
