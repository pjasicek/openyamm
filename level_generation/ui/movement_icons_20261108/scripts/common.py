"""Shared helpers for the movement indicator frames (Fly sp21a, Water Walk sp27a).

Native frames: 64x64 paletted BMP, palette index 0 is the transparent key. HD frames: 128x128 RGBA.
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

REPO = Path(__file__).resolve().parents[4]
NATIVE_DIR = REPO / "assets_legacy/icons_20260926/engine/icons"
HD_DIR = REPO / "assets_dev/engine/icons_x2"
HERE = Path(__file__).resolve().parents[1]
OUT_DIR = HERE / "out"
PREVIEW_DIR = HERE / "preview"
FRAME_COUNT = 8
SCALE = 2
# Game pace: data frame 1 unit = 8/128 s, slowed to 50/128 by the HUD -> 0.16 s per frame.
FRAME_SECONDS = (8 / 128) / (50 / 128)


def load_native(base, k):
    """RGB (int) and opaque mask of native frame k (1-based)."""
    im = Image.open(NATIVE_DIR / f"{base}{k}0.bmp")
    idx = np.asarray(im)
    rgb = np.asarray(im.convert("RGB")).astype(np.float32)
    return rgb, idx != 0


def load_hd(base, k):
    return np.asarray(Image.open(HD_DIR / f"{base}{k}0.png").convert("RGBA")).astype(np.float32) / 255.0


def up(mask, scale=SCALE):
    return np.kron(mask.astype(np.uint8), np.ones((scale, scale), np.uint8)).astype(bool)


def main_component(mask):
    lab, n = nd.label(mask)
    if n == 0:
        return mask
    sizes = nd.sum(mask, lab, range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


def luma(rgb):
    return rgb[..., 0] * 0.3 + rgb[..., 1] * 0.59 + rgb[..., 2] * 0.11


def over(dst, src):
    """Premultiplied-free 'over' of straight-alpha float RGBA images."""
    sa = src[..., 3:4]
    da = dst[..., 3:4]
    oa = sa + da * (1 - sa)
    rgb = np.where(oa > 1e-6, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    return np.concatenate([rgb, oa], -1)


def save_rgba(arr, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(path)
    path.chmod(0o644)


def detect_sparkles(rgb, opaque, body):
    """Sparkle blobs of a native frame: components off the body, as (cx, cy, radius, colour, peak)."""
    off = opaque & ~body
    lab, n = nd.label(off, structure=np.ones((3, 3)))
    result = []
    for i in range(1, n + 1):
        m = lab == i
        ys, xs = np.nonzero(m)
        w = luma(rgb)[m] + 1.0
        cx = float((xs * w).sum() / w.sum())
        cy = float((ys * w).sum() / w.sum())
        extent = max(xs.max() - xs.min(), ys.max() - ys.min()) + 1
        colour = rgb[m].max(0) / 255.0
        ox, oy = xs - cx, ys - cy
        axis = float(((ox * ox - oy * oy) ** 2).mean())
        diag = float(((2 * ox * oy) ** 2).mean())
        result.append((cx, cy, float(extent), colour, float(luma(rgb)[m].max() / 255.0), diag > axis * 1.2))
    return result


def draw_sparkle(canvas, cx, cy, extent, colour, peak, scale=SCALE, diagonal=False):
    """A crisp four-point star with a soft glow, centred on native (cx, cy), drawn into an HD RGBA canvas."""
    h, w = canvas.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x0 = (cx + 0.5) * scale - 0.5
    y0 = (cy + 0.5) * scale - 0.5
    dx = np.abs(xx - x0)
    dy = np.abs(yy - y0)
    if diagonal:
        u = (xx - x0 + yy - y0) / np.sqrt(2)
        v = (xx - x0 - (yy - y0)) / np.sqrt(2)
        dx, dy = np.abs(u), np.abs(v)
    arm = max(1.0, (extent * 0.5 + 0.5) * scale)
    if extent <= 2:
        # a dot: soft round glint
        r = np.sqrt(dx * dx + dy * dy)
        a = np.exp(-(r / (0.55 * scale * max(extent, 1))) ** 2)
    else:
        thin = 0.75
        star = np.maximum(np.exp(-(dy / thin) ** 2) * np.clip(1 - dx / arm, 0, 1) ** 0.8,
                          np.exp(-(dx / thin) ** 2) * np.clip(1 - dy / arm, 0, 1) ** 0.8)
        r = np.sqrt(dx * dx + dy * dy)
        glow = 0.55 * np.exp(-(r / (arm * 0.28)) ** 2)
        a = np.clip(np.maximum(star, glow), 0, 1)
    a = a * min(1.0, peak * 1.05)
    core = np.clip(1 - np.sqrt(dx * dx + dy * dy) / (arm * 0.35 + 0.8), 0, 1)
    col = colour[None, None, :] * (1 - core[..., None]) + core[..., None]
    src = np.concatenate([np.broadcast_to(col, (h, w, 3)), a[..., None]], -1)
    return over(canvas, src)
