"""Prepare visually verified head correspondences from explicit native and delivered pixel coordinates."""
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'level_generation/creatures/mm6_remaining/redo_2x')
from prepare_packed_outline import native_2x

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'redo_2x'
sources = json.loads((ROOT / 'sources.json').read_text())
registration = json.loads((OUT / 'registration.json').read_text())
rows, points = [], {}
manual = json.loads((OUT / 'review/chain_manual_head_points.json').read_text())
for name, correspondence in manual.items():
    entry = registration[name]
    native = native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
    clean = Image.open(entry['clean_path']).convert('RGBA')
    npnt = correspondence['native_2x']
    cpnt = correspondence['clean']
    points[name] = dict(native=[v / 2 for v in npnt], clean=cpnt,
                        feature=correspondence['feature'],
                        raw_sha256=entry['raw_sha256'], clean_sha256=entry['clean_sha256'])
    tile = Image.new('RGB', (480, 225), '#252525'); draw = ImageDraw.Draw(tile)
    draw.text((3, 5), name + ' / visible forehead candidates / original pixels', fill='white')
    for im, point, x in ((native, npnt, 0), (clean, cpnt, 240)):
        origin = [round(point[0] - 105), round(point[1] - 60)]
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
    page.save(OUT / f'review/chain_head_correspondence_{start // 6}.png')
(OUT / 'review/chain_head_correspondence_candidates.json').write_text(json.dumps(points, indent=2) + '\n')
