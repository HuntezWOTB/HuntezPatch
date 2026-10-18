"""Central paths + version for source and frozen (PyInstaller onefile) runs.

- APP_VERSION: single source of truth. Bumped manually per release.
- Resources (locales, bundled data): sys._MEIPASS when frozen, else project root.
- Writable data (config, result/): %LocalAppData%/HuntezProjects/HuntezPatch
  for both source and exe runs. The config is wiped whenever APP_VERSION
  changes (handled in core/config.py).
"""
import os
import sys

APP_VERSION = "v1.04"
CONFIG_NAME = "huntezpatch_cfg.json"


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_base():
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and os.path.isdir(str(meipass)):
        return str(meipass)
    return project_root()


def resource_path(*parts):
    return os.path.join(resource_base(), *parts)


def user_data_dir():
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        # Fallback: %userprofile%/AppData/Local
        profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        base = os.path.join(profile, "AppData", "Local")
    path = os.path.join(base, "HuntezProjects", "HuntezPatch")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def config_path():
    return os.path.join(user_data_dir(), CONFIG_NAME)


def game_key(game_path):
    """Stable per-install key so central backups of different game installs
    (Wargaming vs Lesta, Steam vs standalone) never mix: <FolderName>_<hash>."""
    import hashlib
    import re
    norm = os.path.normcase(os.path.abspath(game_path or ""))
    digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:10]
    tail = os.path.basename(norm.rstrip(os.sep)) or "game"
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", tail).strip("_") or "game"
    return f"{slug}_{digest}"


def backup_root(game_path):
    """Central backup root for one game install:
    %LocalAppData%/HuntezProjects/HuntezPatch/backups/<game>_<hash>."""
    return os.path.join(user_data_dir(), "backups", game_key(game_path))


def result_path(*parts):
    return os.path.join(user_data_dir(), "result", *parts)
