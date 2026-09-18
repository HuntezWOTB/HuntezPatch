"""RandomTankSelector operation: generate the dice button icon.

Two dice, each face showing its own pip number (e.g. 2 and 5), on a
transparent background. Generated fresh (random faces) at build time as
WebP and installed as NEW game files (the engine resolves ~res:/Gfx/...
names to <name>.packed.webp.dvpl, like all game icons):
  Data/Gfx/Lobby/icons/randomtankselector_button_icon.packed.webp.dvpl       (32x32)
  Data/Gfx/Lobby/icons/randomtankselector_button_icon@2x.packed.webp.dvpl    (64x64)
There is no original to back up; restore deletes these added files.
"""
import io
import random

from .constants import ICON_2X_REL, ICON_2X_SIZE, ICON_BASE_REL, ICON_SIZE

# Standard pip layouts in unit-square coordinates.
_PIPS = {
    1: [(0.5, 0.5)],
    2: [(0.3, 0.3), (0.7, 0.7)],
    3: [(0.3, 0.3), (0.5, 0.5), (0.7, 0.7)],
    4: [(0.32, 0.32), (0.68, 0.32), (0.32, 0.68), (0.68, 0.68)],
    5: [(0.3, 0.3), (0.7, 0.3), (0.5, 0.5), (0.3, 0.7), (0.7, 0.7)],
    6: [(0.32, 0.3), (0.68, 0.3), (0.32, 0.5), (0.68, 0.5), (0.32, 0.7), (0.68, 0.7)],
}

_FACE = (242, 242, 242, 255)
_EDGE = (20, 20, 20, 255)
_PIP = (20, 20, 20, 255)


def _draw_die(draw_size, value, angle):
    """Render one die on a transparent square layer."""
    from PIL import Image, ImageDraw

    sup = 4  # supersample for smooth edges/dots
    big = draw_size * sup
    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pad = int(big * 0.06)
    radius = int(big * 0.18)
    d.rounded_rectangle([pad, pad, big - pad, big - pad], radius=radius, fill=_FACE)
    d.rounded_rectangle([pad, pad, big - pad, big - pad], radius=radius,
                        outline=_EDGE, width=max(2, int(big * 0.035)))
    inner = big - 2 * pad
    pip_r = big * 0.055
    for fx, fy in _PIPS[value]:
        cx = pad + fx * inner
        cy = pad + fy * inner
        d.ellipse([cx - pip_r, cy - pip_r, cx + pip_r, cy + pip_r], fill=_PIP)
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=False)
    return layer.resize((draw_size, draw_size), Image.LANCZOS)


def render_dice_icon(size, value1, value2):
    """Two overlapping dice on transparency; empty area stays transparent."""
    from PIL import Image

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    die = max(8, int(size * 0.52))
    # back die: top-right, front die: bottom-left (overlap in the middle)
    back = _draw_die(die, value2, angle=16)
    front = _draw_die(die, value1, angle=-13)
    back_pos = (size - die - max(1, size // 16), max(1, size // 16))
    front_pos = (max(1, size // 16), size - die - max(1, size // 16))
    canvas.alpha_composite(back, back_pos)
    canvas.alpha_composite(front, front_pos)
    return canvas


def icon_webp_bytes(size, value1, value2):
    """Encode the dice icon as WebP bytes (RGBA, crisp)."""
    img = render_dice_icon(size, value1, value2)
    buf = io.BytesIO()
    img.save(buf, format="WEBP", lossless=True, method=6)
    return buf.getvalue()


def roll_dice_values(rng=None):
    """Two dice faces; the second is re-rolled so each die shows its own number."""
    rng = rng or random.Random()
    v1 = rng.randint(1, 6)
    v2 = rng.randint(1, 6)
    for _ in range(10):
        if v2 != v1:
            break
        v2 = rng.randint(1, 6)
    return v1, v2


def make_icon_payloads(rng=None):
    """Return ({rel: webp_bytes}, (v1, v2)). Faces are rolled fresh each call."""
    v1, v2 = roll_dice_values(rng)
    return {
        ICON_BASE_REL: icon_webp_bytes(ICON_SIZE, v1, v2),
        ICON_2X_REL: icon_webp_bytes(ICON_2X_SIZE, v1, v2),
    }, (v1, v2)
