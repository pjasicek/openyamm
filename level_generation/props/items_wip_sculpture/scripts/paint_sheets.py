"""Pack six exact mesh guides into one paint atlas per design; split returned paintings and check registration.

Usage: paint_sheets.py prepare|split <design>. Painting layout: front/back/left; right/top/bottom.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
VIEWS = ['front', 'back', 'left', 'right', 'top', 'bottom']


def prepare(name):
    folder = HERE / 'codex_tex' / name
    atlas = Image.new('RGBA', (1536, 1024))
    for n, view in enumerate(VIEWS):
        guide = Image.open(folder / ('guide_' + view + '.png')).convert('RGBA')
        guide = guide.resize((512, 512), Image.Resampling.LANCZOS)
        atlas.alpha_composite(guide, ((n % 3) * 512, (n // 3) * 512))
    atlas.save(folder / 'guide_atlas.png')
    print(folder / 'guide_atlas.png')


def split(name):
    folder = HERE / 'codex_tex' / name
    atlas = Image.open(folder / 'paint_atlas.png').convert('RGBA')
    assert abs(atlas.width / atlas.height - 1.5) < 0.02, (name, atlas.size)
    assert (np.asarray(atlas)[:, :, 3] < 100).mean() > 0.15, 'Painting lacks transparent background'
    report = {}
    for n, view in enumerate(VIEWS):
        x, y = n % 3, n // 3
        crop = atlas.crop((round(x * atlas.width / 3), round(y * atlas.height / 2),
                           round((x + 1) * atlas.width / 3), round((y + 1) * atlas.height / 2)))
        if name in ('sculpture_statuet2', 'sculpture_statuet3'):
            # Neighbouring atlas cells leave disconnected edge fragments outside these two animals.
            rgba = np.array(crop)
            labels, count = ndimage.label(rgba[:, :, 3] > 127)
            sizes = np.bincount(labels.ravel())
            selected = labels == (np.argmax(sizes[1:]) + 1)
            rgba[:, :, 3] = np.where(ndimage.binary_dilation(selected, iterations=2), rgba[:, :, 3], 0)
            crop = Image.fromarray(rgba)
        crop.save(folder / ('paint_' + view + '.png'))
        paint = crop.resize((1024, 1024), Image.Resampling.LANCZOS)
        guide = Image.open(folder / ('guide_' + view + '.png')).convert('RGBA')
        p = np.asarray(paint)[:, :, 3] > 127
        g = np.asarray(guide)[:, :, 3] > 127
        py, px = np.nonzero(p)
        gy, gx = np.nonzero(g)
        assert len(px) and len(gx), (name, view, 'empty view')
        sx = (px.max() - px.min()) / max(gx.max() - gx.min(), 1)
        sy = (py.max() - py.min()) / max(gy.max() - gy.min(), 1)
        iou = (p & g).sum() / max((p | g).sum(), 1)
        report[view] = {'scale_x': float(sx), 'scale_y': float(sy), 'unregistered_iou': float(iou)}
    (folder / 'registration.json').write_text(json.dumps(report, indent=2) + '\n')
    print(name, report)


if __name__ == '__main__':
    {'prepare': prepare, 'split': split}[sys.argv[1]](sys.argv[2])
