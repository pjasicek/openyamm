#!/usr/bin/env python3
"""The solo alert gem's five states from the one painted green master (masters/gem_green.png).

Only the stone changes: its pixels are those of the green hue band (the brass bezel, the dark collar and the white
highlight fall outside it), recoloured by a hue turn with per-state saturation and value, so every state keeps the
same bezel, shape and lighting. Writes masters/gem_<state>.png, the runtime sources
assets_source/engine/icons_x2/obsidian_solo_alert_<state>.png (128 x 128, mipped by the cooker: a 34-unit gem is
about 64 pixels at 1600 x 900 and 128 at 4K) and checks/states.png. Then run tools/cook_ui_textures.py.

    python3 level_generation/ui/solo_alert_gem_20261114/make_states.py
"""
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNTIME = ROOT / "assets_source/engine/icons_x2"
RUNTIME_SIZE = 128

# state: (target hue in degrees or None to keep, saturation factor, value factor)
STATES = {
    "green": (None, 1.0, 1.0),
    "yellow": (40.0, 1.08, 1.4),
    "red": (356.0, 1.05, 1.0),
    "blue": (208.0, 1.0, 1.05),
    "unlit": (200.0, 0.18, 0.42),
}


def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-6
    rm = nz & (mx == r)
    gm = nz & (mx == g) & ~rm
    bm = nz & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    h = h * 60.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def hsv_to_rgb(h, s, v):
    h = (h % 360.0) / 60.0
    i = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    out = np.zeros(h.shape + (3,))
    for k, (a, b, c) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        m = i == k
        out[m, 0], out[m, 1], out[m, 2] = a[m], b[m], c[m]
    return out


def main():
    master = Image.open(HERE / "masters/gem_green.png").convert("RGBA")
    a = np.asarray(master).astype(np.float64) / 255.0
    rgb, alpha = a[..., :3], a[..., 3]
    h, s, v = rgb_to_hsv(rgb)
    # The stone: the green band, weighted by saturation so the highlight's white edge blends rather than cuts.
    band = np.clip(1.0 - np.abs(((h - 125.0 + 180.0) % 360.0) - 180.0) / 55.0, 0, 1)
    weight = band * np.clip((s - 0.12) / 0.2, 0, 1)
    sheet = []
    RUNTIME.mkdir(parents=True, exist_ok=True)
    for state, (hue, sat, val) in STATES.items():
        if hue is None:
            out = rgb
        else:
            nh = h + (hue - 125.0)
            ns = np.clip(s * sat, 0, 1)
            nv = np.clip(v * val, 0, 1)
            turned = hsv_to_rgb(nh, ns, nv)
            out = rgb * (1 - weight[..., None]) + turned * weight[..., None]
        img = Image.fromarray((np.dstack([out, alpha]) * 255 + 0.5).astype(np.uint8), "RGBA")
        img.save(HERE / f"masters/gem_{state}.png")
        img.resize((RUNTIME_SIZE, RUNTIME_SIZE), Image.Resampling.LANCZOS).save(
            RUNTIME / f"obsidian_solo_alert_{state}.png")
        sheet.append(img)
    # A check sheet: each state at master size and at 32 px, on light and dark grounds.
    w = master.width
    check = Image.new("RGBA", (len(sheet) * (w + 16), w + 120), (40, 40, 40, 255))
    for i, img in enumerate(sheet):
        check.alpha_composite(img, (i * (w + 16), 0))
        small = img.resize((32, 32), Image.Resampling.LANCZOS)
        check.alpha_composite(small, (i * (w + 16) + 20, w + 20))
        light = Image.new("RGBA", (40, 40), (190, 180, 160, 255))
        light.alpha_composite(small, (4, 4))
        check.alpha_composite(light, (i * (w + 16) + 80, w + 16))
    (HERE / "checks").mkdir(exist_ok=True)
    check.convert("RGB").save(HERE / "checks/states.png")


if __name__ == "__main__":
    main()
