"""File primitives: encodings, resolve game/DLC physical files, staged install."""
import os
import shutil
import stat
import tempfile

from core.dvpl_utils import read_dvpl, compress_text_to_dvpl

ENCODINGS = ('utf-8-sig', 'utf-8', 'cp1251', 'latin-1', 'cp866')


def decode_bytes(data):
    for enc in ENCODINGS:
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='replace'), 'utf-8'


def resolve_game_physical(game_path, rel, dvpl_mode):
    """Find the physical game file for logical rel (relative to Data/).

    Strict per mode:
      'DVPL'     -> '<rel>.dvpl' preferred, plain file as fallback.
      'NON-DVPL' -> plain '<rel>' ONLY, '.dvpl' files are never touched.
    DLC files are resolved separately (always '<rel>.dvpl').
    Returns path or None.
    """
    plain = os.path.join(game_path, "Data", rel)
    dvpl = plain + ".dvpl"
    if dvpl_mode == 'DVPL':
        if os.path.exists(dvpl):
            return dvpl
        if os.path.exists(plain):
            return plain
        return None
    # NON-DVPL: plain game files only, never .dvpl
    if os.path.exists(plain):
        return plain
    return None


def dlc_physical(dlc_root, rel):
    """DLC files are always '<dlc_root>/<rel>.dvpl'."""
    if not dlc_root:
        return None
    cand = os.path.join(dlc_root, rel) + ".dvpl"
    return cand if os.path.exists(cand) else None


def read_physical(path, log_func=None, tr=None):
    """Read any physical file (DVPL auto-detected). Returns dict."""
    with open(path, 'rb') as f:
        raw = f.read()
    payload, comp = read_dvpl(path)
    if comp is not None:
        text, enc = decode_bytes(payload)
        if enc == 'utf-8-sig':
            enc = 'utf-8'
        return {'text': text, 'encoding': enc, 'is_dvpl': True, 'comp': comp}
    text, enc = decode_bytes(raw)
    if enc == 'utf-8-sig':
        enc = 'utf-8'
    return {'text': text, 'encoding': enc, 'is_dvpl': False, 'comp': None}


def write_physical(path, text, encoding, is_dvpl, comp=None, log_func=None):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    # make writable if exists
    if os.path.exists(path):
        try:
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass
    if is_dvpl:
        compress_text_to_dvpl(path, text, encoding, comp if comp is not None else 2)
    else:
        with open(path, 'wb') as f:
            f.write(text.encode(encoding))


def make_staging():
    return tempfile.mkdtemp(prefix="blitzmods_")


def backup_one(src, backup_path, log_func=print):
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(src, backup_path)


def install_one(src_staged, dst, set_readonly=False):
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    if os.path.exists(dst):
        try:
            os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass
    shutil.copy2(src_staged, dst)
    if set_readonly:
        try:
            os.chmod(dst, stat.S_IREAD)
        except Exception:
            pass


def get_game_version(game_path):
    for cand in (os.path.join(game_path, "Data", "version.txt.dvpl"),
                 os.path.join(game_path, "Data", "version.txt")):
        if os.path.exists(cand):
            try:
                info = read_physical(cand)
                first = (info['text'].splitlines() or ["unknown"])[0]
                ver = (first.split() or ["unknown"])[0].strip()
                return "".join(c for c in ver if c.isalnum() or c in (".", "-", "_")) or "unknown"
            except Exception:
                return "unknown"
    return "unknown"
