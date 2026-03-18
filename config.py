import configparser
import os

CONFIG_DIR = os.path.expanduser("~/.config/easypodcast")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")


def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config


def get_credentials():
    config = load_config()
    if "easypodcast" in config:
        base_url = config["easypodcast"].get("base_url", "").strip()
        token = config["easypodcast"].get("token", "").strip()
        if base_url and token:
            return base_url, token
    return None, None


def save_credentials(base_url, token):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    config = configparser.ConfigParser()
    config["easypodcast"] = {
        "base_url": base_url.rstrip("/"),
        "token": token,
    }
    with open(CONFIG_FILE, "w") as f:
        config.write(f)


def has_config():
    base_url, token = get_credentials()
    return bool(base_url and token)
