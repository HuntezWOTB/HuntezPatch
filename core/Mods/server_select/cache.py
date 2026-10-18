"""Region-cache locations: the client reads the server list from LocalAppData.

Order everywhere: WOT BLITZ first, TANKS BLITZ second.

  Wargaming (WoT Blitz): %LocalAppData%/wotblitz/DAVAProject/region_cache/
  Lesta (Tanks Blitz):   %userprofile%/Documents/TanksBlitz/region_cache/

File: regions_<ver>.yaml where <ver> comes from Data/version (e.g.
"11.21.0.1235_7376187 ..." -> "11.21.0"; Lesta uses suffixed variants like
"26.8.0_ruby", matched by version prefix, else every regions_*.yaml).
"""
import glob
import os
import re


def local_appdata():
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        base = os.path.join(profile, "AppData", "Local")
    return base


def documents_dir():
    profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return os.path.join(profile, "Documents")


def region_cache_dir(project="wargaming"):
    if (project or "wargaming") == "lesta":
        return os.path.join(documents_dir(), "TanksBlitz", "region_cache")
    return os.path.join(local_appdata(), "wotblitz", "DAVAProject", "region_cache")


def game_version_short(game_path):
    """'11.21.0' from the Data/version first line. None when unreadable."""
    for cand in (os.path.join(game_path, "Data", "version.txt"),
                 os.path.join(game_path, "Data", "version.txt.dvpl")):
        if not os.path.isfile(cand):
            continue
        try:
            from core.file_ops import read_physical
            info = read_physical(cand)
            first = (info["text"].splitlines() or [""])[0]
            m = re.search(r"(\d+)\.(\d+)\.(\d+)", first)
            if m:
                return "%s.%s.%s" % m.groups()
        except Exception:
            continue
    return None


def find_region_cache_files(game_path, project="wargaming"):
    """Absolute cache files to patch: exact version, version prefix, else all."""
    d = region_cache_dir(project)
    if not os.path.isdir(d):
        return []
    ver = game_version_short(game_path)
    if ver:
        exact = os.path.join(d, "regions_%s.yaml" % ver)
        if os.path.isfile(exact):
            return [exact]
        # Suffixed builds (e.g. regions_26.8.0_ruby.yaml): same version
        # prefix followed by a separator, never a longer version number.
        suffixed = sorted(
            os.path.join(d, f) for f in os.listdir(d)
            if f.startswith("regions_%s" % ver) and f.endswith(".yaml")
            and f not in ("regions_%s.yaml" % ver,)
            and len(f) > len("regions_%s.yaml" % ver)
            and f[len("regions_%s" % ver)] in ".-_")
        if suffixed:
            return [f for f in suffixed if os.path.isfile(f)]
    return sorted(glob.glob(os.path.join(d, "regions_*.yaml")))
