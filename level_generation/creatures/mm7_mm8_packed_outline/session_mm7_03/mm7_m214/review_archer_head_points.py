"""Prepare explicit hair-crown correspondence candidates for the session's prop-confused poses."""
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, 'level_generation/creatures/mm6_remaining/redo_2x')
from prepare_packed_outline import native_2x

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'redo_2x'
REGIONS = {
    'm214ab0': [255, 96, 280, 118], 'm214ag0': [228, 106, 260, 130],
    'm214ab1': [270, 97, 291, 118], 'm214ac1': [276, 104, 301, 124],
    'm214ag1': [217, 109, 243, 130], 'm214ab2': [267, 106, 290, 127],
    'm214ag2': [218, 107, 244, 130], 'm214ab3': [240, 101, 265, 124],
    'm214af3': [244, 97, 274, 112], 'm214ag3': [234, 110, 260, 128],
    'm214ab4': [215, 99, 242, 119], 'm214ac4': [238, 105, 267, 132],
    'm214ae4': [246, 99, 277, 119], 'm214af4': [235, 97, 265, 122],
    'm214ag4': [264, 110, 284, 130], 'm214na0': [250, 122, 281, 145],
    'm214nb0': [290, 150, 326, 184], 'm214nb1': [208, 150, 238, 186],
    'm214nb2': [132, 148, 161, 173], 'm214na3': [188, 120, 218, 140],
    'm214nb3': [136, 150, 172, 170], 'm214na4': [240, 120, 264, 150],
    'm214nb4': [200, 151, 225, 171],
    'm214af0': [240, 98, 280, 136], 'm214af2': [240, 98, 280, 134],
}


def crown(im, region, component=False):
    a = np.array(im)
    rgb = a[:, :, :3].astype(int)
    selected = (a[:, :, 3] >= 128) & (rgb.min(axis=2) > 65) & (np.ptp(rgb, axis=2) < 42)
    yy, xx = np.indices(selected.shape)
    x0, y0, x1, y1 = region
    selected &= (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    if component:
        labels, count = ndimage.label(ndimage.binary_closing(selected, iterations=1))
        sizes = np.bincount(labels.ravel()); sizes[0] = 0
        assert count and sizes.max() > 20
        selected &= labels == sizes.argmax()
    profile = selected.sum(axis=1)
    cap = np.flatnonzero(profile >= 3)[0]
    ys, xs = np.where(selected[cap:cap + 2])
    return [float(np.median(xs)), float(cap)]


sources = json.loads((ROOT / 'sources.json').read_text())
registration = json.loads((OUT / 'registration.json').read_text())
rows, points = [], {}
for name, region in REGIONS.items():
    entry = registration[name]
    native = native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
    clean = Image.open(entry['clean_path']).convert('RGBA')
    try:
        npnt = crown(native, region, component=True)
    except Exception:
        raise ValueError('No native hair crown in reviewed region: ' + name)
    effective = np.array([round(v * entry['scale']) / v for v in clean.size])
    guess = (np.array(npnt) - entry['translate']) / effective
    radius = 52 / effective
    manual_clean_regions = {'m214nb2': [50, 95, 92, 135], 'm214na0': [195, 50, 233, 77]}
    clean_region = manual_clean_regions.get(name, [*(guess - radius), *(guess + radius)])
    cpnt = crown(clean, clean_region, component=True)
    points[name] = dict(native=[v / 2 for v in npnt], clean=cpnt,
                        raw_sha256=entry['raw_sha256'], clean_sha256=entry['clean_sha256'])
    tile = Image.new('RGB', (480, 225), '#252525'); draw = ImageDraw.Draw(tile)
    draw.text((3, 5), name + ' / hair crown candidates / original pixels', fill='white')
    for im, point, x in ((native, npnt, 0), (clean, cpnt, 240)):
        origin = [round(point[0] - 105), round(point[1] - 20)]
        crop = im.crop((*origin, origin[0] + 210, origin[1] + 175))
        tile.paste(crop, (x, 30), crop)
        cx, cy = x + point[0] - origin[0], 30 + point[1] - origin[1]
        draw.line((cx - 4, cy, cx + 4, cy), fill='cyan')
        draw.line((cx, cy - 4, cx, cy + 4), fill='cyan')
        draw.text((x + 3, 207), str(point), fill='white')
    rows.append(tile)
for start in range(0, len(rows), 6):
    page = Image.new('RGB', (960, 675), '#252525')
    for i, row in enumerate(rows[start:start + 6]):
        page.paste(row, (i % 2 * 480, i // 2 * 225))
    page.save(OUT / f'review/archer_head_correspondence_{start // 6}.png')
(OUT / 'review/archer_head_correspondence_candidates.json').write_text(json.dumps(points, indent=2) + '\n')
