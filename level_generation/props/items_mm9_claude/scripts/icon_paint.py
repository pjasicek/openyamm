"""Fallback paint for a design OpenAI's image filter keeps refusing ("violence" at the output stage, 2026-11-05):
writes codex_tex/<d>/paint_mask_raw_v1.png in the paint-brief atlas layout from the icon project's HD painting, so
register_views.py and the bake run as usual.

Only for icon-silhouette builds (the item lies on its back, so the TOP view is the icon): the top cell is the
painting stretched onto the top guide; a side view takes, per column, the painting row at the same height and samples
across that row's width over the view's thickness; the front and back cells (edge-on slivers the bake skips) take the
row colours too. The material mask comes from per-design rules (FALLBACK below), not from the painting's brightness.

    python3 -I scripts/icon_paint.py <design> [...]"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
VIEWS = ('front', 'back', 'left', 'right', 'top')
CLASS_COLOURS = {'metal': (255, 0, 0), 'leather': (0, 255, 0), 'cloth': (0, 0, 255), 'horn': (255, 255, 0),
                 'gem': (0, 0, 0)}


def all_metal(rgb, rows):
    return np.full(rgb.shape[:2], 'metal', dtype=object)


def wood_stock_below(split):
    """Metal above `split` (a fraction of the painting's height); below it saturated orange-brown is wood and grey is
    metal (Blackpowder: copper barrel and steel bands over a wooden stock with a steel side lever)."""
    def rule(rgb, rows):
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        saturation = (np.max(rgb, -1) - np.min(rgb, -1)) / np.maximum(np.max(rgb, -1), 1)
        classes = np.full(rgb.shape[:2], 'metal', dtype=object)
        wood = (rows[:, None] >= split) & (saturation > 0.35) & (r > b)
        classes[wood] = 'horn'
        return classes
    return rule


FALLBACK = {'d10067': all_metal, 'd10188': wood_stock_below(0.43)}


def load(path):
    return np.asarray(Image.open(path).convert('RGBA'), np.float64)


def bbox(alpha):
    ys, xs = np.nonzero(alpha > 127)
    return xs.min(), xs.max(), ys.min(), ys.max()


def paint_design(design):
    folder = os.path.join(HERE, 'codex_tex', design)
    painting = load(os.path.join(HERE, 'meshy', design, 'references_hd', 'design_painting.png'))
    px0, px1, py0, py1 = bbox(painting[..., 3])
    painting = painting[py0:py1 + 1, px0:px1 + 1]
    height, width = painting.shape[:2]
    rows = (np.arange(height) / max(height - 1, 1))[:, None] * np.ones((1, width))
    classes = FALLBACK[design](painting[..., :3], rows[:, 0])
    mask_rgb = np.zeros(painting.shape[:2] + (3,))
    for name, colour in CLASS_COLOURS.items():
        mask_rgb[classes == name] = colour
    opaque = painting[..., 3] > 127
    spans = []
    for y in range(height):
        xs = np.nonzero(opaque[y])[0]
        spans.append((xs.min(), xs.max()) if len(xs) else None)
    # Rows without paint take the nearest painted row.
    filled = [s for s in spans if s]
    last = filled[0]
    for y in range(height):
        last = spans[y] or last
        spans[y] = last
    widths = np.array([b - a + 1 for a, b in spans], np.float64)

    top_guide = load(os.path.join(folder, 'guide_top.png'))
    size = top_guide.shape[0]
    cells = {}
    for view in VIEWS:
        guide = load(os.path.join(folder, f'guide_{view}.png'))
        alpha = guide[..., 3] > 127
        gx0, gx1, gy0, gy1 = bbox(guide[..., 3])
        paint = np.zeros((size, size, 4))
        mask = np.zeros((size, size, 4))
        ys, xs = np.nonzero(alpha)
        if view == 'top':
            u = (xs - gx0) / max(gx1 - gx0, 1)
            v = (ys - gy0) / max(gy1 - gy0, 1)
            sy = np.clip((v * (height - 1)).round().astype(int), 0, height - 1)
            sx = np.clip((u * (width - 1)).round().astype(int), 0, width - 1)
        else:
            # The long image axis is the model's Y (the painting's rows); pick its direction by matching the view's
            # thickness profile to the painting's width profile.
            horizontal = (gx1 - gx0) >= (gy1 - gy0)
            along = (xs - gx0) / max(gx1 - gx0, 1) if horizontal else (ys - gy0) / max(gy1 - gy0, 1)
            across = (ys - gy0) / max(gy1 - gy0, 1) if horizontal else (xs - gx0) / max(gx1 - gx0, 1)
            length = (gx1 - gx0 + 1) if horizontal else (gy1 - gy0 + 1)
            profile = (alpha[gy0:gy1 + 1].sum(0)[gx0:gx1 + 1] if horizontal
                       else alpha[:, gx0:gx1 + 1].sum(1)[gy0:gy1 + 1])
            reference = np.interp(np.linspace(0, height - 1, length), np.arange(height), widths)
            flip = np.corrcoef(profile, reference[::-1])[0, 1] > np.corrcoef(profile, reference)[0, 1]
            if flip:
                along = 1 - along
            sy = np.clip((along * (height - 1)).round().astype(int), 0, height - 1)
            starts = np.array([spans[y][0] for y in sy])
            ends = np.array([spans[y][1] for y in sy])
            sx = np.clip((starts + across * (ends - starts)).round().astype(int), 0, width - 1)
        colour = painting[sy, sx, :3]
        # Transparent holes inside the painting (the cage's gaps) take the row's mean opaque colour.
        hole = painting[sy, sx, 3] <= 127
        if hole.any():
            row_mean = np.array([painting[y][opaque[y]][:, :3].mean(0) if opaque[y].any() else (128, 128, 128)
                                 for y in range(height)])
            colour[hole] = row_mean[sy[hole]]
        paint[ys, xs, :3] = colour
        paint[ys, xs, 3] = 255
        mask_colour = mask_rgb[sy, sx]
        if hole.any():
            row_class = np.array([np.bincount([list(CLASS_COLOURS).index(c) for c in classes[y][opaque[y]]] or [0],
                                              minlength=5).argmax() for y in range(height)])
            mask_colour[hole] = np.array(list(CLASS_COLOURS.values()))[row_class[sy[hole]]]
        mask[ys, xs, :3] = mask_colour
        mask[ys, xs, 3] = 255
        cells[view] = (paint, mask)

    cell = 512
    atlas = Image.new('RGBA', (cell * 3, cell * 4), (0, 0, 0, 0))
    for index, view in enumerate(VIEWS):
        column, row = index % 3, index // 3
        for offset, image in ((0, cells[view][0]), (2, cells[view][1])):
            tile = Image.fromarray(image.astype(np.uint8), 'RGBA').resize((cell, cell), Image.NEAREST)
            atlas.paste(tile, (column * cell, (row + offset) * cell))
    output = os.path.join(folder, 'paint_mask_raw_v1.png')
    atlas.save(output)
    with open(os.path.join(folder, 'generation_paint.json'), 'w') as handle:
        json.dump({'generator': 'scripts/icon_paint.py (OpenAI image filter refused every brief)',
                   'source': os.path.relpath(os.path.join(HERE, 'meshy', design, 'references_hd',
                                                          'design_painting.png'), HERE),
                   'mask_rule': FALLBACK[design].__name__ if hasattr(FALLBACK[design], '__name__') else 'rule',
                   'output': os.path.relpath(output, HERE)}, handle, indent=1)
    print('PAINTED', design, output)


if __name__ == '__main__':
    for name in sys.argv[1:]:
        paint_design(name)
