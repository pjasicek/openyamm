#!/usr/bin/env python3
"""The classic stone kit (2026-11-24): Clouds of Xeen's castle walls (fcstl1/fcstl2) as bays that join seamlessly.

The plain bay (finished/xvaswall, a marbled sandstone slab between a course of blocks along its top and its bottom) is
every bay's ground: its left and right edges are made one dark mortar joint (half each), so bays side by side meet in
a joint, and storeys stacked meet course on course. The door (its round-headed arch of voussoirs, the iron-banded oak
door) and the window (its arch and sill) are cut from their paintings by their outlines, their rows matched to the
plain bay's courses, and set into it. The corners: a whole column of quoins (finished/xvasquoin, seamless upward,
QUOIN wide, its blocks stretched upward to the original's proportion, repeating every 512 so storeys continue it) along the outer edge.

Writes finished/<name>.png (x4) and _x2, _x1 for xvswall, xvsdoor, xvswin, xvscornl, xvscornr; sheets/stone_facade.png.

  python3 compose_stone.py
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
FINISHED = HERE / 'finished'
SHEETS = HERE / 'sheets'
W, H = 512, 1024
JOINT = 3          # each edge's half of the mortar joint between bays, px at the master size
QUOIN = 64         # the corner column of quoins (16 texels)


def load(name):
    return np.asarray(Image.open(FINISHED / f'{name}.png').convert('RGB'), float)


def save(rgb, name):
    image = Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))
    image.save(FINISHED / f'{name}.png')
    image.resize((W // 2, H // 2), Image.LANCZOS).save(FINISHED / f'{name}_x2.png')
    image.resize((W // 4, H // 4), Image.LANCZOS).save(FINISHED / f'{name}_x1.png')
    print(name, image.size)


def courses(rgb):
    """The rows where the top course ends and the bottom course begins: the darkest mortar rows near each end."""
    lum = ndimage.uniform_filter1d(rgb.mean(2).mean(1), 3)
    top = 20 + int(np.argmin(lum[20:180]))
    bottom = H - 180 + int(np.argmin(lum[H - 180:H - 20]))
    return top, bottom


def matched_rows(source, target_courses):
    """The source picture resampled up and down so its courses lie where the target's do (three bands)."""
    st, sb = courses(source)
    tt, tb = target_courses
    out = np.zeros_like(source)
    for (s0, s1), (t0, t1) in (((0, st), (0, tt)), ((st, sb), (tt, tb)), ((sb, H), (tb, H))):
        band = Image.fromarray(np.clip(source[s0:s1], 0, 255).astype(np.uint8)).resize((W, t1 - t0), Image.LANCZOS)
        out[t0:t1] = np.asarray(band, float)
    return out


def outline(source, slab_box):
    """What is not plain slab in a painted bay (an arch and its door, a window and its sill): differs from the
    slab's colour or carries strong edges, closed, holes filled, the largest part."""
    x0, y0, x1, y1 = slab_box
    colour = np.median(source[y0:y1, 8:40].reshape(-1, 3), axis=0)
    differs = np.sqrt(((source - colour) ** 2).sum(2)) > 45
    edges = ndimage.gaussian_gradient_magnitude(source.mean(2), 1.5) > 22
    mask = (differs | edges)
    mask[:, :24] = False
    mask[:, W - 24:] = False
    mask = ndimage.binary_closing(mask, iterations=10)
    mask = ndimage.binary_fill_holes(mask)
    mask = ndimage.binary_opening(mask, iterations=6)
    labels, count = ndimage.label(mask)
    sizes = ndimage.sum(np.ones_like(labels), labels, range(1, count + 1))
    return labels == 1 + int(np.argmax(sizes))


def set_in(ground, source, mask):
    """The source inside the mask over the ground, feathered a texel, a thin dark line round it (its joint)."""
    inside = ndimage.binary_erosion(mask, iterations=2)
    alpha = ndimage.gaussian_filter(inside.astype(float), 1.5)[..., None]
    ring = ndimage.binary_dilation(inside, iterations=3) & ~ndimage.binary_erosion(inside, iterations=1)
    out = ground * (1 - 0.25 * ndimage.gaussian_filter(ring.astype(float), 1.2))[..., None]
    return out * (1 - alpha) + source * alpha


def jointed(rgb):
    """Each side edge a half mortar joint, alike on every bay."""
    out = rgb.copy()
    for column in range(JOINT):
        shade = 0.45 + 0.15 * column
        out[:, column] *= shade
        out[:, W - 1 - column] *= shade
    return out


def quoin_column():
    tile = Image.open(FINISHED / 'xvasquoin.png').convert('RGB')
    # Twice as tall as the painting's proportion: blocks taller than the column is wide, as the original's quoins
    # (the painting's six blocks, 64 x 85 each); the period 512 still divides the bay.
    tile = tile.resize((QUOIN, 2 * round(tile.height * QUOIN / tile.width)), Image.LANCZOS)
    assert H % tile.height == 0, tile.size
    column = np.vstack([np.asarray(tile, float)] * (H // tile.height))
    # Its inner edge a mortar joint against the slab.
    return column


def main():
    SHEETS.mkdir(exist_ok=True)
    wall = load('xvaswall')
    lines = courses(wall)
    print('courses of the plain bay at', lines)
    plain = jointed(wall)
    save(plain, 'xvswall')

    for painted, name in (('xvasdoor', 'xvsdoor'), ('xvaswin', 'xvswin')):
        source = matched_rows(load(painted), lines)
        mask = outline(source, (0, lines[0], W, lines[1]))
        # Round the bay's middle line: no more of the slab than the insert's own width (a pale patch of marbling
        # beside a window would join its outline).
        ys, xs = np.nonzero(mask)
        reach = W // 2 - xs.min()
        mask[:, :W // 2 - reach] = False
        mask[:, W // 2 + reach:] = False
        ys, xs = np.nonzero(mask)
        print(painted, 'outline', xs.min(), ys.min(), xs.max(), ys.max())
        save(jointed(set_in(wall, source, mask)), name)

    # The double door's wing (finished/xvasdoorw: the left leaf of the original's arched pair), as it is.
    save(load('xvasdoorw'), 'xvsdoorw')
    column = quoin_column()
    for name, left in (('xvscornl', True), ('xvscornr', False)):
        bay = plain.copy()
        joint = np.ones((H, 1)) * 0.5
        if left:
            bay[:, :QUOIN] = column
            bay[:, QUOIN:QUOIN + 2] *= joint[..., None]
        else:
            bay[:, W - QUOIN:] = column
            bay[:, W - QUOIN - 2:W - QUOIN] *= joint[..., None]
        save(bay, name)
    sheet()


def sheet():
    rows = [['xvscornl', 'xvswall', 'xvswin', 'xvsdoor', 'xvswall', 'xvscornr'],
            ['xvscornl', 'xvswin', 'xvswall', 'xvswin', 'xvswall', 'xvscornr']]
    bw, bh = W // 2, H // 2
    out = Image.new('RGB', (bw * 6, bh * 2))
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            out.paste(Image.open(FINISHED / f'{name}.png').resize((bw, bh), Image.LANCZOS), (c * bw, (1 - r) * bh))
    out.save(SHEETS / 'stone_facade.png')


if __name__ == '__main__':
    main()
