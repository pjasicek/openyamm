"""Target check before generating: per piece, each master's reference cut to its target, worn on its doll, with the
removed part tinted red, plus the new icon.

    python3 scripts/targets.py <out.png> <piece> [...]      (after `mm9_paperdoll.py prepare`)
"""
import sys, json
import mm9_paperdoll as M
from PIL import Image, ImageDraw
import numpy as np
P, D = M.P, M.P.D
OUT = sys.argv[1]
names = sys.argv[2:]
rows = []
for name in names:
    piece = P.pieces()[name]
    cells = []
    for t in P.master_types(piece):
        job = P.WORK / name / f't{t}'
        meta = json.loads((job / 'job.json').read_text())
        target = np.asarray(Image.open(job / 'target.png'))[:, :, 3]
        ref = D.ENGINE_ITEMS[piece['reference']]
        layer = np.asarray(D.layer(ref.icon_name + meta['suffix'])).copy()
        cut = layer.copy(); cut[:, :, 3] = np.minimum(cut[:, :, 3], target)
        removed = (layer[:, :, 3] > 0) & (target == 0)
        tint = np.zeros_like(layer); tint[removed] = (255, 0, 0, 160)
        x, y = meta['point'][0] * D.SCALE, meta['point'][1] * D.SCALE
        worn = D.doll(t).copy()
        worn.alpha_composite(Image.fromarray(cut), (x, y))
        worn.alpha_composite(Image.fromarray(tint), (x, y))
        ys, xs = np.nonzero(layer[:, :, 3])
        box = (max(0, x + xs.min() - 30), max(0, y + ys.min() - 30), min(D.WIDTH, x + xs.max() + 30), min(D.HEIGHT, y + ys.max() + 30))
        cell = worn.crop(box).convert('RGB')
        cell.thumbnail((300, 420))
        ImageDraw.Draw(cell).text((3, 3), f't{t}', fill=(255, 255, 0))
        cells.append(cell)
    icon = Image.open(P.ICONS_X2 / f'{name}.png').convert('RGBA')
    bg = Image.new('RGBA', icon.size, (40, 40, 40, 255)); bg.alpha_composite(icon)
    cells.append(bg.convert('RGB'))
    h = max(c.height for c in cells)
    row = Image.new('RGB', (sum(c.width for c in cells) + 10 * len(cells), h + 16), (20, 20, 20))
    ImageDraw.Draw(row).text((3, h + 2), f"{name} {piece['name']} ref {piece['reference']} {piece.get('coverage','')}", fill=(255, 255, 255))
    o = 0
    for c in cells:
        row.paste(c, (o, 0)); o += c.width + 10
    rows.append(row)
sheet = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)), (20, 20, 20))
o = 0
for r in rows:
    sheet.paste(r, (0, o)); o += r.height
sheet.save(OUT)
print(OUT, sheet.size)
