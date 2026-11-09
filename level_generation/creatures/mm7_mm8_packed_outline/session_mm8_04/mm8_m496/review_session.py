"""MM8 session-local atlas schema bridge; uses shared edge review and does not approve art."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('family')
ROOT = Path(__file__).resolve().parent.parent / parser.parse_args().family
sys.path.insert(0, str(ROOT.parents[2] / 'mm8_remaining'))
from process_detail import edge_candidates


def composite(image, colour):
    out = Image.new('RGBA', image.size, colour)
    out.alpha_composite(image)
    return out.convert('RGB')


manifest = json.loads((ROOT / 'draft_manifest.json').read_text())
palettes = list(map(int, manifest['variants']['palette_deltas']))
base_palette = manifest['variants']['base_palette']
pages = {i: Image.open(ROOT / p['base']).convert('RGBA') for i, p in enumerate(manifest['pages'])}
mask_pages = {i: Image.open(ROOT / p['mask']).convert('L') for i, p in enumerate(manifest['pages'])}
tiles, scores, mask_panels = {}, [], []
for name, record in sorted(manifest['frames'].items()):
    x, y, w, h = record['atlas_xywh']
    tile = pages[record['page']].crop((x, y, x + w, y + h))
    mask = mask_pages[record['page']].crop((x, y, x + w, y + h))
    master = Image.open(ROOT / 'runtime_aligned_2x' / (name + '.png')).convert('RGBA')
    assert np.array_equal(tile, master.crop(record['crop_in_aligned_px']))
    if len(palettes) == 1:
        assert not np.asarray(mask).any(), name
    preview = Image.open(ROOT / 'previews' / f'{name}_{base_palette}.png').convert('RGBA')
    assert np.array_equal(np.asarray(preview)[np.asarray(master)[:, :, 3] > 0],
                          np.asarray(master)[np.asarray(master)[:, :, 3] > 0])
    score, _ = edge_candidates(tile)
    scores.append((float(score.max()), name, np.unravel_index(score.argmax(), score.shape)))
    tiles[name] = tile
    panel = Image.new('RGB', (112, 76), '#343434')
    ImageDraw.Draw(panel).text((3, 2), name, fill='white')
    panel.paste(mask.resize((100, 54)), (6, 19))
    mask_panels.append(panel)

evidence = []
names = list(tiles)
for start in range(0, len(names), 8):
    subset = names[start:start + 8]
    width = max(tiles[n].width for n in subset) + 8
    height = max(tiles[n].height for n in subset) + 22
    contact = Image.new('RGB', (width * 4, height * 4), '#343434')
    draw = ImageDraw.Draw(contact)
    for i, name in enumerate(subset):
        x, y = (i % 4) * width, (i // 4) * height * 2
        for offset, colour in [(0, '#eeeeee'), (height, '#202024')]:
            draw.text((x + 3, y + offset + 2), name + ' atlas 2x', fill='white')
            contact.paste(composite(tiles[name], colour), (x + 4, y + offset + 18))
    file = f'review/atlas_poses_{start // 8:02d}.png'
    contact.save(ROOT / file)
    evidence.append(file)

contact = Image.new('RGB', (112 * 8, 76 * ((len(mask_panels) + 7) // 8)), '#343434')
for i, panel in enumerate(mask_panels):
    contact.paste(panel, (i % 8 * 112, i // 8 * 76))
contact.save(ROOT / 'review/all_masks.png')
worst = Image.new('RGB', (160 * 6, 160 * 2), '#202024')
for i, (_, name, (y, x)) in enumerate(sorted(scores, reverse=True)[:6]):
    patch = tiles[name].crop((x - 40, y - 40, x + 40, y + 40)).resize((160, 160), Image.Resampling.NEAREST)
    for row, colour in enumerate(['#eeeeee', '#202024']):
        worst.paste(composite(patch, colour), (i * 160, row * 160))
worst.save(ROOT / 'review/atlas_worst_edges.png')
record = dict(stage='Actual exported atlas tiles after 2x resize and hidden RGB bleed',
    frames=len(tiles), palettes=palettes, all_zero_masks=len(palettes) == 1, exact_base_bypass=True,
    worst=[dict(frame=name, score=score, xy=[int(x), int(y)]) for score, name, (y, x) in sorted(scores, reverse=True)[:6]],
    visual_review='pending', evidence=evidence + ['review/all_masks.png', 'review/atlas_worst_edges.png'])
(ROOT / 'review/atlas_edge_scan.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
