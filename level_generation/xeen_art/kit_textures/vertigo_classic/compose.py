#!/usr/bin/env python3
"""The Vertigo classic kit (variant A, chosen 2026-11-24) composed so every bay meets every other seamlessly.

The generated bays (finished/xva*.png from xtex.py) each paint their own posts, beams and plaster, so their edges
differ (posts 36-76 px wide at the master size, beams 64-79 px, edge colours 25 % apart). Here every bay gets one
frame and one plaster:

- the frame: posts and beams cut from the seamless beam tile (xvabeam, 256 x 128 at the master, grain along, period
  256 in x, so a strip 512 wide repeats at the bay). A post of POST px is cut once; each bay's left edge carries its
  right half and its right edge its left half, so two bays side by side make that one post. A beam of BEAM px the
  same way: the top edge carries its lower half and the bottom edge its upper half, so stacked storeys meet in one
  beam. Beams run over the posts, as on the original wall. Dark joint lines and a soft shadow on the plaster give
  the original's outlined, recessed look.
- the plaster: the plain bay's own panel (xvawall), the same in every bay.
- the door and the window: the painted door (leaf, jambs and lintel) and window (frame and sill) cut out of their
  bays (where they differ from plaster) and set into the frame and plaster at the same place.
- the corners: post_left with a whole post along its left edge, post_right with one along its right edge, the other
  edge as every bay's (built each way, not mirrored, so the inner edge still meets its neighbour).

Writes finished/<name>.png (x4) and _x2, _x1 for xvwall, xvwin, xvdoor, xvdoorw, xvcornl, xvcornr, xvbeam, xvridge,
xvshgl, xvthat (the roofs and the beam are the A tiles as they are; the gable is the wall itself). Sheets: sheets/compose_*.png.

  python3 compose.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
FINISHED = HERE / 'finished'
SHEETS = HERE / 'sheets'
W, H = 512, 1024          # one bay at the master size (128 x 256 texels)
POST = 96                 # a whole post (24 texels); each bay edge shows half
BEAM = 112                # a whole beam (28 texels); each top and bottom edge shows half
DOOR_TOP = 216            # the lintel's top over the door (the door 202 units high with its lintel)
# The door in finished/xvadoor.png (v1, squeezed to 512 x 1024), measured: its lintel's top at 180, the leaf down to the
# bottom beam at 950, between the painted posts' inner edges at 46 and 462.
DOOR_SOURCE = (46, 180, 462, 950)


def load(name):
    return np.asarray(Image.open(FINISHED / f'{name}.png').convert('RGB'), float)


def save(rgb, name):
    image = Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))
    image.save(FINISHED / f'{name}.png')
    image.resize((image.width // 2, image.height // 2), Image.LANCZOS).save(FINISHED / f'{name}_x2.png')
    image.resize((image.width // 4, image.height // 4), Image.LANCZOS).save(FINISHED / f'{name}_x1.png')
    print(name, image.size)


def timber():
    """A beam strip (BEAM x W, grain along) and a post strip (H x POST, grain up), both from the beam tile."""
    tile = load('xvabeam')                                    # 256 x 128, seamless both ways
    assert tile.shape[:2] == (128, 256), tile.shape
    beam = np.tile(tile, (1, W // tile.shape[1], 1))[:BEAM]    # period 256 in x: the bay repeats it exactly
    post = np.rot90(np.tile(tile, (1, H // tile.shape[1], 1)), 1)[:, :POST]
    return beam, post


def bevel(member, axis):
    """Darker edges across a member (axis 0: rows, a beam; 1: columns, a post): a squared timber's outline."""
    n = member.shape[axis]
    d = np.minimum(np.arange(n), np.arange(n)[::-1]).astype(float)
    shade = 1.0 - 0.38 * np.exp(-d / 2.5) - 0.12 * np.exp(-d / 12.0)
    shape = [1, 1, 1]
    shape[axis] = n
    return member * shade.reshape(shape)


def plaster_panel(source):
    """The plain bay's plaster: the bright region inside its own timber, cropped a little inside it."""
    lum = source.mean(2)
    bright = lum > (np.percentile(lum, 90) + np.percentile(lum, 10)) / 2
    cols = np.where(bright[200:800].mean(0) > 0.5)[0]
    rows = np.where(bright[:, 150:360].mean(1) > 0.5)[0]
    x0, x1, y0, y1 = cols.min() + 10, cols.max() - 10, rows.min() + 10, rows.max() - 10
    return source[y0:y1, x0:x1], (x0, y0, x1, y1)


def even_plaster(panel):
    """The panel repeats in every bay, so its marks must not stand out: the fine grain kept, cracks and stains
    (deviations past CLIP from the local mean) clipped, and the broad blotches brought toward the mean."""
    low = ndimage.gaussian_filter(panel, (24, 24, 0))
    high = np.clip(panel - low, -10, 10)
    mean = panel.reshape(-1, 3).mean(0)
    return mean + (low - mean) * 0.45 + high


def frame(left_whole=False, right_whole=False):
    """The bay's frame over a plaster panel: (rgb, the panel's box inside it)."""
    beam, post = timber()
    beam, post = bevel(beam, 0), bevel(post, 1)
    half = POST // 2
    left = post if left_whole else post[:, half:]
    right = post if right_whole else post[:, :half]
    out = np.zeros((H, W, 3))
    px0, px1 = left.shape[1], W - right.shape[1]
    py0, py1 = BEAM // 2, H - BEAM // 2
    panel = even_plaster(plaster_panel(load('xvawall'))[0])
    plaster = Image.fromarray(np.clip(panel, 0, 255).astype(np.uint8))
    out[py0:py1, px0:px1] = np.asarray(plaster.resize((px1 - px0, py1 - py0), Image.LANCZOS), float)
    out[:, :px0] = left
    out[:, px1:] = right
    out[:BEAM // 2] = beam[BEAM // 2:]
    out[H - BEAM // 2:] = beam[:BEAM // 2]
    return out, (px0, py0, px1, py1)


def recess(rgb, box):
    """A soft shadow on the plaster along the timber (the panel sits behind the frame)."""
    x0, y0, x1, y1 = box
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.minimum.reduce([xx - x0, x1 - 1 - xx, yy - y0, y1 - 1 - yy]).astype(float)
    shade = 1.0 - 0.22 * np.exp(-d / 6.0)
    rgb[y0:y1, x0:x1] *= shade[..., None]
    return rgb


def insert_box(source, panel_box):
    """Where a generated bay's window is: what differs from plaster inside its panel (the largest part); its box and
    its mask (in the source's pixels)."""
    plaster, _ = plaster_panel(load('xvawall'))
    colour = np.median(plaster.reshape(-1, 3), axis=0)
    x0, y0, x1, y1 = panel_box
    region = source[y0:y1, x0:x1]
    differs = np.sqrt(((region - colour) ** 2).sum(2)) > 60
    differs = ndimage.binary_closing(ndimage.binary_opening(differs, iterations=2), iterations=6)
    labels, count = ndimage.label(differs)
    sizes = ndimage.sum(np.ones_like(labels), labels, range(1, count + 1))
    part = labels == 1 + int(np.argmax(sizes))
    ys, xs = np.nonzero(part)
    mask = np.zeros(source.shape[:2], bool)
    mask[y0:y1, x0:x1] = ndimage.binary_fill_holes(part)
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1), mask


def generated_panel(source):
    """The panel box of a generated bay (inside its own posts and beams), read like plaster_panel's."""
    lum = source.mean(2)
    bright = lum > (np.percentile(lum, 90) + np.percentile(lum, 10)) / 2
    cols = np.where(bright[100:950].mean(0) > 0.25)[0]
    rows = np.where(bright[:, 60:452].mean(1) > 0.25)[0]
    return cols.min(), rows.min(), cols.max() + 1, rows.max() + 1


def paste_masked(target, source, mask, box, at):
    """The insert by its own outline (the window and its wider sill), feathered a texel, a dark line round it."""
    x0, y0, x1, y1 = box
    ax0, ay0, ax1, ay1 = at
    size = (ax1 - ax0, ay1 - ay0)
    piece = np.asarray(Image.fromarray(np.clip(source[y0:y1, x0:x1], 0, 255).astype(np.uint8)).resize(
        size, Image.LANCZOS), float)
    inside = np.asarray(Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8)).resize(size, Image.LANCZOS),
                        float) / 255 > 0.5
    inside = ndimage.binary_erosion(inside, iterations=2)
    alpha = ndimage.gaussian_filter(inside.astype(float), 1.5)[..., None]
    outline = ndimage.binary_dilation(inside, iterations=3) & ~ndimage.binary_erosion(inside, iterations=1)
    region = target[ay0:ay1, ax0:ax1]
    region *= (1 - 0.3 * ndimage.gaussian_filter(outline.astype(float), 1.2))[..., None]
    target[ay0:ay1, ax0:ax1] = region * (1 - alpha) + piece * alpha
    return target


def paste(target, source, box, at):
    x0, y0, x1, y1 = box
    ax0, ay0, ax1, ay1 = at
    piece = Image.fromarray(np.clip(source[y0:y1, x0:x1], 0, 255).astype(np.uint8)).resize((ax1 - ax0, ay1 - ay0),
                                                                                          Image.LANCZOS)
    target[ay0:ay1, ax0:ax1] = np.asarray(piece, float)
    # The joint between the insert and the plaster or timber round it: a thin dark line, as round the timber.
    shade = np.ones((ay1 - ay0, ax1 - ax0))
    yy, xx = np.mgrid[0:ay1 - ay0, 0:ax1 - ax0]
    d = np.minimum.reduce([xx, ax1 - ax0 - 1 - xx, yy, ay1 - ay0 - 1 - yy]).astype(float)
    shade -= 0.35 * np.exp(-d / 1.8)
    target[ay0:ay1, ax0:ax1] *= shade[..., None]
    return target


def main():
    SHEETS.mkdir(exist_ok=True)
    wall, box = frame()
    save(recess(wall.copy(), box), 'xvwall')

    # The window: kept at its painted size relative to the panel, at the same place.
    source = load('xvawin')
    gbox = generated_panel(source)
    wbox, wmask = insert_box(source, gbox)
    sx, sy = (box[2] - box[0]) / (gbox[2] - gbox[0]), (box[3] - box[1]) / (gbox[3] - gbox[1])
    at = (round(box[0] + (wbox[0] - gbox[0]) * sx), round(box[1] + (wbox[1] - gbox[1]) * sy),
          round(box[0] + (wbox[2] - gbox[0]) * sx), round(box[1] + (wbox[3] - gbox[1]) * sy))
    window = recess(wall.copy(), box)
    save(paste_masked(window, source, wmask, wbox, at), 'xvwin')
    print('window', wbox, '->', at)

    # The door: its lintel, jambs and leaf (DOOR_SOURCE, inside the painted bay's own posts and beams) fill the
    # panel's width from the bottom beam up to DOOR_TOP; the plaster above it is the wall's.
    source = load('xvadoor')
    dbox = DOOR_SOURCE
    door = recess(wall.copy(), box)
    save(paste(door, source, dbox, (box[0], DOOR_TOP, box[2], box[3])), 'xvdoor')
    print('door', dbox)

    for name, kwargs in (('xvcornl', {'left_whole': True}), ('xvcornr', {'right_whole': True})):
        corner, cbox = frame(**kwargs)
        save(recess(corner, cbox), name)

    beam = load('xvabeam')
    save(beam, 'xvbeam')
    save(np.rot90(beam, 1), 'xvridge')
    # The town hall's double door: one wing of the original's (finished/xvadoorw), the second leaf its mirror.
    save(load('xvadoorw'), 'xvdoorw')
    save(load('xvashgl'), 'xvshgl')
    save(load('xvathat'), 'xvthat')
    sheet()


def sheet():
    """Two storeys of bays side by side (the joins this composition is for), the original's colours."""
    rows = [['xvcornl', 'xvwall', 'xvwin', 'xvdoor', 'xvwall', 'xvcornr'],
            ['xvcornl', 'xvwin', 'xvwall', 'xvwin', 'xvwall', 'xvcornr']]
    scale = 0.5
    bw, bh = int(W * scale), int(H * scale)
    out = Image.new('RGB', (bw * 6, bh * 2))
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            out.paste(Image.open(FINISHED / f'{name}.png').resize((bw, bh), Image.LANCZOS), (c * bw, (1 - r) * bh))
    out.save(SHEETS / 'compose_facade.png')
    # The joins at full size: the right edge of one bay against the left edge of the next, and storey on storey.
    crop = Image.new('RGB', (512, 512))
    a, b = Image.open(FINISHED / 'xvwall.png'), Image.open(FINISHED / 'xvdoor.png')
    crop.paste(a.crop((256, 0, 512, 256)), (0, 256))
    crop.paste(b.crop((0, 0, 256, 256)), (256, 256))
    crop.paste(a.crop((256, 768, 512, 1024)), (0, 0))
    crop.paste(b.crop((0, 768, 256, 1024)), (256, 0))
    ImageDraw.Draw(crop).text((4, 4), 'joins at full size: upper storey above, bays left/right', fill=(255, 255, 0))
    crop.save(SHEETS / 'compose_joins.png')


if __name__ == '__main__':
    main()
