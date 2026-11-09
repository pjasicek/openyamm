"""Shared configuration of the MM7 flower batch (pure Python: imported by the atlas painter, the Blender builder and the
post-process). Sizes come from the restored x2 frames (opaque art, alpha > 128, halved to world units) and inventory
art heights; models are built in metres (81.7 world units per metre) at the sprite's width/height ratio, so the engine's
height scaling reproduces the sprite's proportions."""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
UNITS = 81.7

# Atlas layout (1024 px, image space, v down): two long blade strips, two large card regions, eight head slots and two
# thin strips (stems, wrapped bloom sides).
ATLAS = 1024
REGIONS = {
    'B0': (0, 0, 64, 1024), 'B1': (64, 0, 128, 1024),
    'T0': (128, 0, 576, 512), 'T1': (128, 512, 576, 1024),
    'S0': (576, 0, 800, 224), 'S1': (800, 0, 1024, 224), 'S2': (576, 224, 800, 448), 'S3': (800, 224, 1024, 448),
    'S4': (576, 448, 800, 672), 'S5': (800, 448, 1024, 672), 'S6': (576, 672, 800, 896), 'S7': (800, 672, 1024, 896),
    'R0': (576, 896, 1024, 960), 'R1': (576, 960, 1024, 1024),
}

# id: sprite, opaque art width and height in world units (x2 frame / 2), the atlas it uses (sprites with the same art
# share one), seeds, and the hue test separating flower pixels from foliage for grading.
SPECIES = {
    'flower01': {'width': 248, 'height': 91, 'what': 'magenta cosmos over arching grass blades', 'flower': 'magenta'},
    'flower02': {'width': 233, 'height': 98, 'what': 'yellow buttercups over dense grass blades', 'flower': 'yellow'},
    'flower03': {'width': 237, 'height': 107,
                 'what': 'two red roses with broad leaves in striped grass', 'flower': 'red'},
    'flower04': {'width': 222, 'height': 133,
                 'what': 'cream cabbage roses edged red, broad leaves, grass', 'flower': 'yellow'},
    'flower05': {'width': 217, 'height': 110,
                 'what': 'white peonies in olive cup leaves, needle sprays', 'flower': 'white'},
    'flower06': {'width': 244, 'height': 102,
                 'what': 'yellow rudbeckia daisies low between grass tufts', 'flower': 'yellow'},
    'flower07': {'width': 128, 'height': 94, 'what': 'foxglove spikes: white, coral, pink, lilac', 'flower': 'pink'},
    'flower08': {'width': 125, 'height': 118,
                 'what': 'magenta bearded irises on stalks over grass', 'flower': 'magenta'},
    'flower09': {'width': 125, 'height': 104,
                 'what': 'white star flowers, yellow centres, over grass', 'flower': 'white'},
    'flower10': {'width': 125, 'height': 88, 'what': 'white daisy dome over moss', 'flower': 'white'},
    'flower11': {'width': 125, 'height': 76, 'what': 'pink primulas on a leaf mound, grass in front', 'flower': 'pink',
                 'atlas': 'flower12'},
    'flower12': {'width': 127, 'height': 72, 'what': 'pink primulas on a leaf mound', 'flower': 'pink'},
    'flower13': {'width': 125, 'height': 76, 'what': 'white water lilies on pads, grass behind', 'flower': 'white',
                 'atlas': 'flower16'},
    'flower16': {'width': 124, 'height': 54, 'what': 'white water lilies on pads', 'flower': 'white'},
}
ORDER = ['flower01', 'flower02', 'flower03', 'flower04', 'flower05', 'flower06', 'flower07', 'flower08', 'flower09',
         'flower10', 'flower11', 'flower12', 'flower13', 'flower16']


def dims(sid):
    s = SPECIES[sid]
    return s['width'] / UNITS, s['height'] / UNITS


def atlas_of(sid):
    return SPECIES[sid].get('atlas', sid)


def seed(sid, salt=0):
    return int(sid[-2:]) * 1009 + salt


def work(sid):
    path = os.path.join(HERE, 'work', sid)
    os.makedirs(path, exist_ok=True)
    return path


def region_uv(name):
    """Region as (u0, v0, u1, v1) in image-space texture coordinates (v down)."""
    x0, y0, x1, y1 = REGIONS[name]
    return x0 / ATLAS, y0 / ATLAS, x1 / ATLAS, y1 / ATLAS


def sprite_path(sid):
    # The restored x2 frames moved out of the runtime tree on 2026-10-16 (decorations are 3D now).
    for folder in (os.path.join('assets_legacy', 'decorations_x2_20261016'),
                   os.path.join('assets_dev', 'engine', 'decorations_x2')):
        path = os.path.join(REPO, folder, sid + '_p122.png')
        if os.path.exists(path):
            return path
    raise FileNotFoundError(sid)


def flower_mask(sid, rgb):
    """Boolean mask of flower pixels in an (n, 3) array of 0..1 colours (the rest is foliage). Used for grading."""
    import numpy as np
    mx, mn = rgb.max(1), rgb.min(1)
    d = mx - mn + 1e-6
    r, g, b = rgb.T
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    sat = d / (mx + 1e-6)
    kind = SPECIES[sid]['flower']
    if kind == 'white':
        return (sat < 0.32) & (mx > 0.55)
    if kind == 'yellow':
        return (hue > 30) & (hue < 62) & (sat > 0.3) & (mx > 0.45)
    if kind == 'red':
        return ((hue < 25) | (hue > 330)) & (sat > 0.35) & (mx > 0.25)
    # magenta / pink
    return ((hue > 270) | (hue < 20)) & (sat > 0.2) & (mx > 0.3)
