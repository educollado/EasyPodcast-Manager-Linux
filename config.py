import configparser
import os
import uuid
from urllib.parse import urlparse

CONFIG_DIR = os.path.expanduser("~/.config/easypodcast")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")
SETTINGS_SECTION = "easypodcast"
PROFILE_PREFIX = "profile:"


def load_config():
    config = configparser.ConfigParser(interpolation=None)
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config


def _profile_name_from_url(base_url):
    parsed = urlparse(base_url)
    path_name = parsed.path.strip("/").split("/")[-1] if parsed.path.strip("/") else ""
    return path_name or parsed.hostname or "Podcast"


def get_profiles():
    """Devuelve los perfiles configurados, incluyendo el formato antiguo."""
    config = load_config()
    profiles = []
    for section in config.sections():
        if not section.startswith(PROFILE_PREFIX):
            continue
        profile_id = section[len(PROFILE_PREFIX):]
        base_url = config[section].get("base_url", "").strip().rstrip("/")
        token = config[section].get("token", "").strip()
        if not profile_id or not base_url or not token:
            continue
        profiles.append({
            "id": profile_id,
            "name": config[section].get("name", "").strip()
            or _profile_name_from_url(base_url),
            "base_url": base_url,
            "token": token,
        })

    # Compatibilidad y migración diferida desde el antiguo perfil único.
    if not profiles and SETTINGS_SECTION in config:
        base_url = config[SETTINGS_SECTION].get("base_url", "").strip().rstrip("/")
        token = config[SETTINGS_SECTION].get("token", "").strip()
        if base_url and token:
            profiles.append({
                "id": "legacy",
                "name": config[SETTINGS_SECTION].get("name", "").strip()
                or _profile_name_from_url(base_url),
                "base_url": base_url,
                "token": token,
            })
    return profiles


def get_active_profile():
    profiles = get_profiles()
    if not profiles:
        return None
    config = load_config()
    active_id = ""
    if SETTINGS_SECTION in config:
        active_id = config[SETTINGS_SECTION].get("active_profile", "").strip()
    return next((profile for profile in profiles if profile["id"] == active_id), profiles[0])


def get_credentials():
    profile = get_active_profile()
    if profile:
        return profile["base_url"], profile["token"]
    return None, None


def _write_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as config_file:
        config.write(config_file)


def save_profile(name, base_url, token, profile_id=None, make_active=True):
    """Crea o actualiza un perfil y devuelve su identificador."""
    config = load_config()
    profile_id = profile_id or uuid.uuid4().hex[:12]
    section = f"{PROFILE_PREFIX}{profile_id}"
    config[section] = {
        "name": name.strip() or _profile_name_from_url(base_url),
        "base_url": base_url.strip().rstrip("/"),
        "token": token.strip(),
    }
    if SETTINGS_SECTION not in config:
        config.add_section(SETTINGS_SECTION)
    # Al editar el perfil antiguo, queda migrado al nuevo formato.
    if profile_id == "legacy":
        for key in ("name", "base_url", "token"):
            config[SETTINGS_SECTION].pop(key, None)
    if make_active:
        config[SETTINGS_SECTION]["active_profile"] = profile_id
    _write_config(config)
    return profile_id


def delete_profile(profile_id):
    config = load_config()
    config.remove_section(f"{PROFILE_PREFIX}{profile_id}")
    if profile_id == "legacy" and SETTINGS_SECTION in config:
        for key in ("name", "base_url", "token"):
            config[SETTINGS_SECTION].pop(key, None)
    if SETTINGS_SECTION in config:
        active_id = config[SETTINGS_SECTION].get("active_profile", "")
        if active_id == profile_id:
            remaining = [
                section[len(PROFILE_PREFIX):]
                for section in config.sections()
                if section.startswith(PROFILE_PREFIX)
            ]
            if remaining:
                config[SETTINGS_SECTION]["active_profile"] = remaining[0]
            else:
                config[SETTINGS_SECTION].pop("active_profile", None)
    _write_config(config)


def set_active_profile(profile_id):
    if not any(profile["id"] == profile_id for profile in get_profiles()):
        return False
    config = load_config()
    if SETTINGS_SECTION not in config:
        config.add_section(SETTINGS_SECTION)
    config[SETTINGS_SECTION]["active_profile"] = profile_id
    _write_config(config)
    return True


def save_credentials(base_url, token):
    """API antigua: conserva un único perfil para clientes existentes."""
    config = configparser.ConfigParser(interpolation=None)
    config[SETTINGS_SECTION] = {
        "base_url": base_url.rstrip("/"),
        "token": token,
    }
    _write_config(config)


def has_config():
    return get_active_profile() is not None
