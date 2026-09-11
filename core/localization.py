import json
import os

LOCALES_DIR = "locales"


def load_locales():
    locales = {}
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), LOCALES_DIR)
    if not os.path.exists(base):
        base = LOCALES_DIR
    if not os.path.exists(base):
        return locales
    for f in os.listdir(base):
        if f.endswith(".json"):
            code = f.replace(".json", "")
            try:
                with open(os.path.join(base, f), "r", encoding="utf-8") as fh:
                    locales[code] = json.load(fh)
            except Exception:
                continue
    return locales


def get_localized_string(locales_dict, lang, key, **kwargs):
    value = locales_dict.get(lang, {}).get(key)
    if value is None:
        value = locales_dict.get("en", {}).get(key, key)
    if kwargs:
        try:
            return value.format(**kwargs)
        except Exception:
            return value
    return value
