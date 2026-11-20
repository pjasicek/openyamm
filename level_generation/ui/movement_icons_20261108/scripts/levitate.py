"""Levitate indicator (sp109-01..06): one HD figure bobbing by the native frames' first-harmonic bob (whole HD pixels, no
resampling), over one HD mist that billows through a small periodic warp. The six frames loop seamlessly 06 -> 01.

python3 levitate.py   (writes ../out/levitate/sp109-01.png .. sp109-06.png)
"""
import numpy as np
from PIL import Image
from scipy import ndimage as nd

from common import HD_DIR, NATIVE_DIR, OUT_DIR, SCALE, main_component, over, save_rgba

FRAMES = 6
SIZE = 128


def native(k):
    im = Image.open(NATIVE_DIR / f"sp109-0{k}.bmp")
    return np.asarray(im) != 0


def native_bob():
    rows = np.arange(64)[:, None]
    centres = np.array([nd.center_of_mass(main_component(native(k) & (rows < 44)))[0] for k in range(1, FRAMES + 1)])
    phase = 2 * np.pi * np.arange(FRAMES) / FRAMES
    basis = np.stack([np.ones(FRAMES), np.cos(phase), np.sin(phase)], -1)
    coeffs, *_ = np.linalg.lstsq(basis, centres, rcond=None)
    return centres, basis @ coeffs


def split(master):
    alpha = master[..., 3]
    rows = np.arange(SIZE)[:, None]
    figure = main_component((alpha > 0.08) & (rows < 88))
    figure = nd.binary_dilation(figure, iterations=2) & (rows < 88)
    fig = master.copy()
    fig[..., 3] *= figure
    mist = master.copy()
    mist[..., 3] *= ~figure
    return fig, mist


def shift_rows(rgba, dy):
    out = np.zeros_like(rgba)
    if dy >= 0:
        out[dy:] = rgba[:SIZE - dy]
    else:
        out[:dy] = rgba[-dy:]
    return out


def billow(mist, k):
    """The mist sampled through a smooth warp whose phase makes one turn over the loop."""
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    phi = 2 * np.pi * k / FRAMES
    dx = 1.6 * np.sin(yy * 0.35 + xx * 0.08 + phi) + 0.9 * np.sin(xx * 0.21 - phi)
    dy = 0.7 * np.cos(xx * 0.27 + phi) + 0.4 * np.sin(xx * 0.11 + yy * 0.3 - phi)
    pm = mist.copy()
    pm[..., :3] *= pm[..., 3:4]
    out = np.stack([nd.map_coordinates(pm[..., i], [yy + dy, xx + dx], order=3, mode="constant")
                    for i in range(4)], -1)
    out = np.clip(out, 0, None)
    rgb = np.where(out[..., 3:4] > 1e-4, out[..., :3] / np.maximum(out[..., 3:4], 1e-4), 0)
    return np.concatenate([np.clip(rgb, 0, 1), np.clip(out[..., 3:4], 0, 1)], -1)


def main():
    out_dir = OUT_DIR / "levitate"
    master = np.asarray(Image.open(HD_DIR / "sp109-01.png").convert("RGBA")).astype(np.float32) / 255
    figure, mist = split(master)
    centres, smooth = native_bob()
    offsets = np.round((smooth - centres[0]) * SCALE).astype(int)
    print("native figure centre rows", np.round(centres, 2).tolist())
    print("smooth bob rows", np.round(smooth, 2).tolist(), "HD offsets", offsets.tolist())
    for k in range(FRAMES):
        canvas = billow(mist, k)
        canvas = over(canvas, shift_rows(figure, int(offsets[k])))
        save_rgba(canvas, out_dir / f"sp109-0{k + 1}.png")


if __name__ == "__main__":
    main()
