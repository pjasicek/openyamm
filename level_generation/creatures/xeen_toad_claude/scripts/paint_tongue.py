#!/usr/bin/env python3
"""D-126 tongue paint: textures/toad_tongue.png (512 x 1024, the layout of scripts/tongue_uv.py) and
textures/toad_tongue_material_classes.png (7, mouth interior, on every island texel; 0 outside), procedural from the
native attack frames (native/att_000[0-3].png, Clouds of Xeen 013.att) so it reproduces.

The colours are the native tongue's own 16-step turquoise ramp (every teal pixel of the four attack frames, sorted by
brightness, from 28,68,76 to 188,248,252). A tone per texel picks along it:
  - mid turquoise (the native frames' commonest steps 4-6) as the base;
  - darker teal mottling (3D value-noise blotches, 3-6 cm) and darker veins (ridged noise, stretched along the tongue);
  - pale wet highlights: thin lengthwise streaks on the upper half and the flanks, and a crescent on the cap's upper
    rim (the native frames' pale glints along the tongue's top and edges);
  - a darker, more saturated tip (the last 15 cm of surface around the tip, the end cap the player sees head-on) and
    a darker root where it leaves the mouth.
Every texel is painted from its rest-pose 3D position (rasterised from work/tongue_uv3d.npz), so the tube, the cap
disc and their shared rim are seamless. Texels outside the islands take the nearest island texel (the gutter re-fill
of claude_shared/gutter_fill.py, done here on this small map's own raster). No ramps: one tongue for every tier."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
W, H = 512, 1024
SEED = 1307


def native_ramp():
    pix = []
    for k in range(4):
        a = np.asarray(Image.open(ROOT / f'native/att_{k:04d}.png').convert('RGBA')).reshape(-1, 4)
        rgb = a[a[:, 3] > 0, :3].astype(np.float64) / 255.0
        mx, mn = rgb.max(1), rgb.min(1)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        teal = (rgb[:, 1] > rgb[:, 0] + 0.08) & (rgb[:, 2] > rgb[:, 0] + 0.08) & (sat > 0.2)
        pix.append(rgb[teal])
    cols = np.unique(np.round(np.concatenate(pix) * 255).astype(int), axis=0)
    return cols[np.argsort(cols.sum(1))] / 255.0


def rasterise(uv, xyz):
    """Per texel: rest position (H, W, 3) and coverage (H, W), image row 0 = UV v 1."""
    pos = np.zeros((H, W, 3)); cov = np.zeros((H, W), bool)
    px = np.stack([uv[..., 0] * W - 0.5, (1.0 - uv[..., 1]) * H - 0.5], -1)
    for t in range(len(px)):
        p = px[t]
        x0, y0 = np.floor(p.min(0)).astype(int) - 1
        x1, y1 = np.ceil(p.max(0)).astype(int) + 1
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W - 1), min(y1, H - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-9:
            continue
        l0 = ((p[1, 1] - p[2, 1]) * (gx - p[2, 0]) + (p[2, 0] - p[1, 0]) * (gy - p[2, 1])) / d
        l1 = ((p[2, 1] - p[0, 1]) * (gx - p[2, 0]) + (p[0, 0] - p[2, 0]) * (gy - p[2, 1])) / d
        l2 = 1 - l0 - l1
        inside = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)   # a hair conservative: no pinholes on shared edges
        if not inside.any():
            continue
        b = np.stack([l0, l1, l2], -1)[inside]
        pos[gy[inside], gx[inside]] = b @ xyz[t]
        cov[gy[inside], gx[inside]] = True
    return pos, cov


def value_noise(p, freq, seed):
    """3D value noise in 0..1 at points p (N, 3), lattice spacing 1 / freq metres, smoothstep interpolation."""
    q = p * freq
    i = np.floor(q).astype(np.int64); f = q - i
    f = f * f * (3 - 2 * f)

    def h(ix, iy, iz):
        n = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = ((f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1])
                     * (f[:, 2] if dz else 1 - f[:, 2]))
                out = out + w * h(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz)
    return out


def fbm(p, freq, seed, octaves=4):
    s, a, tot = 0, 1.0, 0
    for o in range(octaves):
        s = s + a * value_noise(p, freq * 2 ** o, seed + 17 * o); tot += a; a *= 0.5
    return s / tot


def ridged(p, freq, seed, octaves=3, sharp=6.0):
    """Thin lines where the noise crosses its middle (veins, streaks), 0..1."""
    s, a, tot = 0, 1.0, 0
    for o in range(octaves):
        n = value_noise(p, freq * 2 ** o, seed + 31 * o)
        s = s + a * (1 - np.abs(2 * n - 1)) ** sharp; tot += a; a *= 0.55
    return s / tot


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def main():
    ramp = native_ramp()
    data = np.load(ROOT / 'work/tongue_uv3d.npz')
    pos, cov = rasterise(data['uv'], data['xyz'])
    tip = data['tip']
    # gutter: nearest island texel (rest position too, so the paint itself carries into the gutter)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    pos = pos[iy, ix]
    p = pos.reshape(-1, 3)
    y0, y1 = -0.72, float(tip[1])
    along = np.clip((y0 - p[:, 1]) / (y0 - y1), 0, 1)                 # 0 root .. 1 tip
    axis_z = 0.58 + 0.02 * along
    up = (p[:, 2] - axis_z) / 0.12                                     # > 0 on the upper half
    flank = np.abs(p[:, 0]) / 0.2
    d_tip = np.linalg.norm(p - tip, axis=1)                            # surface-ish distance to the tip, m
    # lengthwise anisotropy for veins and streaks: squash y
    pa = p * np.array([1.0, 0.33, 1.0])

    tone = np.full(len(p), 5.6)
    tone += 1.1 * (fbm(p, 9.0, SEED) - 0.5)                            # broad unevenness
    blot = smooth(0.52, 0.70, fbm(p, 22.0, SEED + 1))
    tone -= 2.4 * blot                                                 # darker teal mottling
    vein = ridged(pa, 14.0, SEED + 2, sharp=9.0)
    tone -= 3.0 * smooth(0.25, 0.65, vein)                             # darker veins
    tone += 0.8 * (fbm(p, 60.0, SEED + 3, 2) - 0.5)                   # fine grain
    streak = ridged(p * np.array([1.0, 0.18, 1.0]), 18.0, SEED + 4, octaves=2, sharp=14.0)
    side = np.clip(0.35 + 0.65 * smooth(-0.3, 0.6, up) + 0.4 * smooth(0.55, 0.9, flank), 0, 1)
    wet = smooth(0.35, 0.8, streak) * side
    tone += 7.0 * wet                                                  # pale wet streaks
    speck = smooth(0.80, 0.92, value_noise(p, 90.0, SEED + 5)) * smooth(-0.2, 0.5, up)
    tone += 5.0 * speck
    # the cap: a pale crescent on the upper rim, darker saturated centre
    tipw = smooth(0.20, 0.03, d_tip)
    crescent = smooth(0.06, 0.09, d_tip) * smooth(0.15, 0.10, d_tip) * smooth(0.1, 0.6, up)
    tone += 5.5 * crescent * (0.6 + 0.4 * fbm(p, 40.0, SEED + 6, 2))
    tone -= 3.2 * tipw * (1 - crescent)
    tone -= 2.2 * smooth(0.10, 0.0, along)                             # root, in the mouth's shadow
    tone = np.clip(tone, 0, len(ramp) - 1)

    i0 = np.floor(tone).astype(int); fr = (tone - i0)[:, None]
    i1 = np.minimum(i0 + 1, len(ramp) - 1)
    col = ramp[i0] * (1 - fr) + ramp[i1] * fr
    # saturate the tip: push away from grey by up to 35 %
    grey = col.mean(1, keepdims=True)
    col = np.clip(grey + (col - grey) * (1 + 0.35 * tipw[:, None]), 0, 1)
    img = (col.reshape(H, W, 3) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(img, 'RGB').save(ROOT / 'textures/toad_tongue.png', optimize=True)
    classes = np.where(cov, 7, 0).astype(np.uint8)
    Image.fromarray(classes, 'L').save(ROOT / 'textures/toad_tongue_material_classes.png', optimize=True)
    lum = col @ np.array([0.2126, 0.7152, 0.0722])
    print('TONGUE island texels', int(cov.sum()), 'of', W * H, f'({cov.mean():.1%})',
          'mean rgb', (col[cov.ravel()].mean(0) * 255).round(1).tolist(),
          'tip rgb', (col[(d_tip < 0.05) & cov.ravel()].mean(0) * 255).round(1).tolist(),
          'lum p5/p50/p95', np.percentile(lum[cov.ravel()], [5, 50, 95]).round(3).tolist())


if __name__ == '__main__':
    main()
