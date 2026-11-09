#!/usr/bin/env python3
"""Register the Codex-painted weapon views to their exact-mesh guides (weapon_prep.py) and build the projection atlas.
Per view: foreground masks (guide: clay vs its flat background; paint: distance from its background colour), the
paint's foreground bounding box fitted onto the guide's (scale and offset per axis), every guide-silhouette pixel
then takes the paint colour at its mapped position, or the nearest painted foreground colour where the paint's
outline drifted inside. Atlas textures/weapons/<name>_basecolor.png (2048 x 1024: front | back, the guide frames) and
review/weapons/<name>_registered.png. Args: <name> [<name> ...]"""
import sys, json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, binary_opening, binary_fill_holes


def fg(img, bg_box=12, thr=40):
    a = img.astype(float); h, w = a.shape[:2]
    bg = np.median(np.concatenate([a[:bg_box, :].reshape(-1, 3), a[-bg_box:, :].reshape(-1, 3),
                                   a[:, :bg_box].reshape(-1, 3), a[:, -bg_box:].reshape(-1, 3)]), axis=0)
    m = np.linalg.norm(a - bg, axis=2) > thr
    return binary_fill_holes(binary_opening(m, iterations=2)) & m | (binary_opening(m, iterations=2))


for name in sys.argv[1:]:
    halves = []
    for view in ('front', 'back'):
        g = np.asarray(Image.open(f'review/weapons/{name}_guide_{view}.png').convert('RGB'))
        p = np.asarray(Image.open(f'textures/weapons/{name}_paint_{view}.png').convert('RGB').resize(g.shape[1::-1], Image.LANCZOS))
        gm, pm = fg(g, thr=30), fg(p, thr=35)
        gy, gx = np.nonzero(gm); py, px = np.nonzero(pm)
        sx = (px.max() - px.min()) / max(gx.max() - gx.min(), 1); sy = (py.max() - py.min()) / max(gy.max() - gy.min(), 1)
        yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
        mx = np.clip(np.round(px.min() + (xx - gx.min()) * sx), 0, g.shape[1] - 1).astype(int)
        my = np.clip(np.round(py.min() + (yy - gy.min()) * sy), 0, g.shape[0] - 1).astype(int)
        _, (iy, ix) = distance_transform_edt(~pm, return_indices=True)       # nearest painted pixel
        out = p[iy[my, mx], ix[my, mx]]
        out = np.where(gm[..., None], out, out)                              # (the whole frame: gutters padded)
        cover = pm[my, mx][gm].mean()
        print('REGISTER', name, view, 'scale', round(sx, 3), round(sy, 3), 'paint covers', round(float(cover) * 100, 1), '% of the silhouette')
        halves.append(out)
    atlas = np.concatenate(halves, axis=1)
    Image.fromarray(atlas.astype(np.uint8)).save(f'textures/weapons/{name}_basecolor.png')
    Image.fromarray(atlas.astype(np.uint8)).resize((1024, 512)).save(f'review/weapons/{name}_registered.png')
