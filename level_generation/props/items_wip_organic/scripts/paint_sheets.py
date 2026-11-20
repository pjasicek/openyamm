"""Pack six exact mesh guides for one paint pass, or unpack its returned texture sheet.

Each row is three 512-square orthographic views; saved split images retain the full framing.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
VIEWS = ('front', 'back', 'left', 'right', 'top', 'bottom')
TILE = 512


def pack(name):
    folder = PROJECT / 'codex_tex' / name
    canvas = Image.new('RGBA', (TILE * 3, TILE * 2))
    for n, view in enumerate(VIEWS):
        guide = Image.open(folder / f'guide_{view}.png').convert('RGBA')
        assert guide.size == (TILE, TILE)
        canvas.alpha_composite(guide, (n % 3 * TILE, n // 3 * TILE))
    canvas.save(folder / 'guide_sheet.png')


def split(name, kind):
    assert kind in ('paint', 'metal')
    folder = PROJECT / 'codex_tex' / name
    source = folder / f'{kind}_sheet_raw.png'
    raw = Image.open(source).convert('RGBA')
    receipts = []
    for n, view in enumerate(VIEWS):
        x, y = n % 3, n // 3
        tile = raw.crop((round(x * raw.width / 3), round(y * raw.height / 2),
                         round((x + 1) * raw.width / 3), round((y + 1) * raw.height / 2)))
        tile = tile.resize((TILE, TILE), Image.Resampling.LANCZOS)
        guide = Image.open(folder / f'guide_{view}.png').convert('RGBA')
        ga = np.array(guide.getchannel('A')) > 128
        pa = np.array(tile.getchannel('A')) > 128
        assert ga.any() and pa.any(), (name, kind, view, 'empty silhouette')
        gy, gx = np.nonzero(ga)
        py, px = np.nonzero(pa)
        scale = [(px.max() - px.min()) / max(1, gx.max() - gx.min()),
                 (py.max() - py.min()) / max(1, gy.max() - gy.min())]
        # Correct whole-panel framing only; the generated surface detail stays intact.
        region = tile.crop((px.min(), py.min(), px.max() + 1, py.max() + 1))
        region = region.resize((gx.max() - gx.min() + 1, gy.max() - gy.min() + 1), Image.Resampling.LANCZOS)
        aligned = Image.new('RGBA', (TILE, TILE))
        aligned.paste(region, (int(gx.min()), int(gy.min())))
        aa = np.array(aligned.getchannel('A')) > 128
        iou = float((aa & ga).sum() / max(1, (aa | ga).sum()))
        # The guide is the authoritative edge: no invented outline or backdrop enters the bake.
        aligned.putalpha(guide.getchannel('A'))
        target = folder / f'{kind}_{view}.png'
        aligned.save(target)
        receipts.append({'view': view, 'source_scale': scale, 'aligned_silhouette_iou': iou,
                         'output': str(target.relative_to(PROJECT)),
                         'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    (folder / f'{kind}_split_receipt.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(name, kind, 'minimum silhouette IoU', round(min(r['aligned_silhouette_iou'] for r in receipts), 3))


if __name__ == '__main__':
    action, name = sys.argv[1:3]
    if action == 'pack':
        pack(name)
    else:
        assert action == 'split'
        split(name, sys.argv[3])
