"""DLC helpers: paths, detection, opening folders in Explorer."""
import os
import subprocess
import sys


def get_dlc_root(project):
    """Return packs dir for a project ('wargaming' | 'lesta')."""
    home = os.path.expanduser("~")
    if project == 'lesta':
        return os.path.join(home, "Documents", "TanksBlitz", "packs")
    return os.path.join(home, "AppData", "Local", "wotblitz", "packs")


def open_folder_in_explorer(path):
    """Open a folder in the OS file manager; create it if missing."""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    try:
        if sys.platform == 'win32':
            os.startfile(path)  # noqa: S606 -- local user path by design
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
        return True, None
    except Exception as e:
        return False, str(e)


def find_existing_dlc_files(dlc_root, rel_paths):
    """Return subset of rel_paths that exist as DLC files (<dlc_root>/<rel>.dvpl)."""
    found = []
    if not dlc_root:
        return found
    for rel in rel_paths:
        cand = os.path.join(dlc_root, rel) + ".dvpl"
        if os.path.exists(cand):
            found.append(rel)
    return found
