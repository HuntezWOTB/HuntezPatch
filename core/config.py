import json
import os

from core.paths import APP_VERSION, config_path, resource_path

DEFAULT_CONFIG = {
    "version": APP_VERSION,
    "language": "ru",
    "theme": "dark",
    "dvpl_mode": "DVPL",
    "operation": "generate",
    "game_path": "",
    "use_dlc": False,
    "project": "wargaming",
    "mods": ["hidden_tanks"],
}


def _available_languages():
    """Language codes shipping in locales/*.json (e.g. {'ru', 'en'})."""
    try:
        base = resource_path("locales")
        if not os.path.isdir(base):
            base = "locales"
        return {f[:-5].lower() for f in os.listdir(base) if f.endswith(".json")}
    except Exception:
        return set()


def get_system_language():
    """System language code if the app ships it, else 'en'."""
    import locale
    available = _available_languages()
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            code = lang.replace("-", "_").split("_")[0].lower()
            if code in available:
                return code
    except Exception:
        pass
    return "en" if "en" in available else "ru"


def get_system_theme():
    import subprocess
    try:
        r = subprocess.run(
            ['reg', 'query',
             r'HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize',
             '/v', 'AppsUseLightTheme'],
            capture_output=True, text=True, timeout=5)
        if "0x0" in r.stdout:
            return "dark"
    except Exception:
        pass
    return "light"


def _fresh_config():
    """Defaults for the current version (system language/theme detected)."""
    cfg = DEFAULT_CONFIG.copy()
    cfg["version"] = APP_VERSION
    cfg["language"] = get_system_language()
    cfg["theme"] = get_system_theme()
    return cfg


def load_config():
    """Load config; wipe it entirely when the app version changed."""
    fresh = _fresh_config()
    path = config_path()
    if not os.path.exists(path):
        return fresh
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return fresh
    if cfg.get("version") != APP_VERSION:
        # Version changed -> drop the whole old config, start clean.
        try:
            os.remove(path)
        except Exception:
            pass
        return fresh
    merged = fresh
    merged.update(cfg)
    merged["version"] = APP_VERSION
    return merged


def save_config(config):
    config["version"] = APP_VERSION
    path = config_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
