import json
import os

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
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
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "locales")
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


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(cfg)
            return merged
        except Exception:
            pass
    cfg = DEFAULT_CONFIG.copy()
    cfg["language"] = get_system_language()
    cfg["theme"] = get_system_theme()
    return cfg


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
