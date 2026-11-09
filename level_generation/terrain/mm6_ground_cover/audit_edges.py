"""Grass-specific contour check following DIRECT_SPRITE_WORKFLOW's residual-spill procedure."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion

P = Path(__file__).resolve().parent
NAMES = ['grass_tuft', 'grass_fine', 'grass_wispy', 'grass_dry']


def measure(image, band):
    rgba = np.asarray(image.convert('RGBA'), dtype=float)
    alpha = rgba[:, :, 3] / 255
    edge = (alpha > 0) & ~binary_erosion(alpha > 0.98, iterations=band)
    score = alpha * np.maximum(0, np.minimum(rgba[:, :, 0], rgba[:, :, 2]) - rgba[:, :, 1])
    score[~edge] = 0
    y, x = np.unravel_index(np.argmax(score), score.shape)
    return dict(edge_pixels=int(edge.sum()), over8=int(((score > 8) & edge).sum()),
                max_visible_magenta=float(score.max()), max_xy=[int(x), int(y)])


def composite(image, color):
    base = Image.new('RGBA', image.size, color + (255,))
    return Image.alpha_composite(base, image).convert('RGB')


def audit(atlas):
    out = P / 'review/v3'
    out.mkdir(parents=True, exist_ok=True)
    sheet = Image.new('RGB', (1024, 880), '#282828')
    draw = ImageDraw.Draw(sheet)
    rows = []
    for index, name in enumerate(NAMES):
        raw = Image.open(P / 'generated' / (name + '.png')).convert('RGBA')
        cell = atlas.crop(((index % 2) * 256, (index // 2) * 192,
                           (index % 2 + 1) * 256, (index // 2 + 1) * 192))
        record = dict(name=name, raw=measure(raw, 4), exported=measure(cell, 2))
        rows.append(record)
        x, y = record['raw']['max_xy']
        detail = raw.crop((x-24, y-24, x+24, y+24)).resize((192, 192), Image.Resampling.NEAREST)
        for col, (label, img, color) in enumerate([
                ('export / dark', cell, (25, 25, 25)), ('export / light', cell, (238, 238, 238)),
                ('raw edge / dark', detail, (25, 25, 25)), ('raw edge / light', detail, (238, 238, 238))]):
            draw.text((col*256+4, index*220+4), name + ' ' + label, fill='white')
            sheet.paste(composite(img, color), (col*256, index*220+24))
    report = dict(method='alpha * max(0, min(R,B)-G), transparent padding excluded; opaque contours included',
                  raw_band_pixels=4, export_band_pixels=2,
                  palette='Olive/tan grass contains no intentional magenta; 8/255 is an audit threshold here only',
                  cleanup='Delivered alpha preserved; premultiplied resize. No magenta correction needed.', records=rows)
    (out / 'edge_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    sheet.save(out / 'edge_audit.png')
    assert all(row[stage]['over8'] == 0 for row in rows for stage in ['raw', 'exported']), 'Review grass matte spill'
    return report


if __name__ == '__main__':
    audit(Image.open(P.parents[2] / 'assets_dev/worlds/mm6/terrain_decorations/grass_variants.png').convert('RGBA'))
