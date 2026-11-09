"""Water Walk indicator (sp27a10..80): the rendered man turning on the spot (render_man.py) over one HD water disc that
turns with him in its own plane, a fixed contact shadow, a reflection made from the render, and procedural sparkles at
the native sparkle places.

python3 waterwalk.py   (needs ../out/waterwalk_man/man_1..8.png; writes ../out/waterwalk/sp27a10.png .. sp27a80.png)
"""
import numpy as np
from PIL import Image
from scipy import ndimage as nd

import water_disc
from common import (FRAME_COUNT, OUT_DIR, SCALE, detect_sparkles, draw_sparkle, load_hd, load_native, luma,
                    main_component, over, save_rgba)

BASE = "sp27a"
SIZE = 64 * SCALE


def native_man(rgb, opaque):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    blue = (b > r + 18) & (b > g + 18)
    man = opaque & ~blue & (np.arange(64)[:, None] < 42)
    return main_component(nd.binary_closing(man))


def native_sparkles(rgb, opaque, man):
    bright = opaque & (luma(rgb) > 175) & ~nd.binary_dilation(man, iterations=1)
    off = opaque & ~main_component(opaque)
    return bright | off


def man_layers():
    renders = [np.asarray(Image.open(OUT_DIR / "waterwalk_man" / f"man_{k}.png").convert("RGBA")).astype(np.float32)
               / 255 for k in range(1, FRAME_COUNT + 1)]
    natives = [native_man(*load_native(BASE, k)) for k in range(1, FRAME_COUNT + 1)]
    # one transform for all frames: mean native height and foot line, mean render height and foot line
    def stats(mask):
        ys, xs = np.nonzero(mask)
        return ys.min(), ys.max(), xs.mean()
    ns = np.array([stats(m) for m in natives], np.float32)
    rs = np.array([stats(r[..., 3] > 0.5) for r in renders], np.float32)
    scale = ((ns[:, 1] - ns[:, 0] + 1).mean() * SCALE) / (rs[:, 1] - rs[:, 0] + 1).mean()
    foot_render = rs[:, 1].mean()
    centre_render = rs[:, 2].mean()
    foot_hd = (ns[:, 1].mean() + 0.5) * SCALE
    centre_hd = (ns[:, 2].mean() + 0.5) * SCALE
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    layers = []
    for r in renders:
        # area-average downsample: sample the render with a box of 1/scale pixels per HD pixel
        pm = r.copy()
        pm[..., :3] *= pm[..., 3:4]
        blur = 0.5 / scale
        pm = np.stack([nd.gaussian_filter(pm[..., i], blur) for i in range(4)], -1)
        sy = (yy + 0.5 - foot_hd) / scale + foot_render
        sx = (xx + 0.5 - centre_hd) / scale + centre_render
        out = np.stack([nd.map_coordinates(pm[..., i], [sy, sx], order=1, mode="constant") for i in range(4)], -1)
        rgb = np.where(out[..., 3:4] > 1e-4, out[..., :3] / np.maximum(out[..., 3:4], 1e-4), 0)
        rgb = rgb * 0.9  # the original's shirt reads light grey, not paper white
        layers.append(np.concatenate([np.clip(rgb, 0, 1), np.clip(out[..., 3:4], 0, 1)], -1))
    return layers, foot_hd, centre_hd


def reflection(man, foot_hd, disc_alpha):
    """The man mirrored below his feet, squashed by the view, tinted to the water and faded."""
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    sy = foot_hd - (yy - foot_hd) / 0.55
    ripple = 0.8 * np.sin(yy * 0.9)
    pm = man.copy()
    pm[..., :3] *= pm[..., 3:4]
    out = np.stack([nd.map_coordinates(pm[..., i], [sy, xx + ripple], order=1, mode="constant") for i in range(4)], -1)
    out = np.stack([nd.gaussian_filter(out[..., i], (1.6, 0.6)) for i in range(4)], -1)
    rgb = np.where(out[..., 3:4] > 1e-4, out[..., :3] / np.maximum(out[..., 3:4], 1e-4), 0)
    tint = np.array([0.72, 0.74, 1.0])
    rgb = 0.35 * rgb * tint + 0.65 * np.array([0.78, 0.78, 1.0])
    fade = np.clip(1 - (yy - foot_hd) / 46.0, 0, 1)
    a = out[..., 3] * 0.42 * fade * (yy > foot_hd) * disc_alpha
    return np.concatenate([rgb, a[..., None]], -1)


def streak(foot_hd, centre_hd, disc_alpha):
    """The original's light band on the water below the man (his reflected light), fixed under him."""
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    across = np.exp(-((xx - centre_hd) / 3.2) ** 2)
    along = np.clip((yy - foot_hd) / 6.0, 0, 1) * np.clip(1 - (yy - foot_hd) / 44.0, 0, 1)
    a = 0.45 * across * along * disc_alpha
    colour = np.zeros((SIZE, SIZE, 3), np.float32) + [0.78, 0.76, 0.98]
    return np.concatenate([colour, a[..., None]], -1)


def shadow(foot_hd, centre_hd):
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    d = ((xx - centre_hd) / 20.0) ** 2 + ((yy - foot_hd + 1) / 6.0) ** 2
    a = 0.55 * np.exp(-d * 1.6)
    return np.concatenate([np.zeros((SIZE, SIZE, 3), np.float32) + [0.02, 0.02, 0.08], a[..., None]], -1)


def main():
    out_dir = OUT_DIR / "waterwalk"
    men, foot_hd, centre_hd = man_layers()
    for k in range(FRAME_COUNT):
        # the disc turns with the man: 45 degrees a frame, clockwise seen from above like his yaw
        disc = water_disc.disc(45.0 * k)
        canvas = disc
        canvas = over(canvas, streak(foot_hd, centre_hd, disc[..., 3]))
        canvas = over(canvas, reflection(men[k], foot_hd, disc[..., 3]))
        canvas = over(canvas, shadow(foot_hd, centre_hd))
        canvas = over(canvas, men[k])
        rgb, opaque = load_native(BASE, k + 1)
        man = native_man(rgb, opaque)
        for cx, cy, extent, colour, peak, diagonal in detect_sparkles(rgb, native_sparkles(rgb, opaque, man),
                                                                      np.zeros_like(opaque)):
            canvas = draw_sparkle(canvas, cx, cy, extent * 1.3, colour, peak, diagonal=diagonal)
        save_rgba(canvas, out_dir / f"{BASE}{k + 1}0.png")
    print("foot", foot_hd, "centre", centre_hd)


if __name__ == "__main__":
    main()
