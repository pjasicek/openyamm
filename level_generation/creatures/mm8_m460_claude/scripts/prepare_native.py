"""Extract verified native Cleric evidence; preserve the 256-pixel source canvas."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
import yaml

ROOT = Path('/home/pjasicek/github/OpenYAMM')
PROJECT = ROOT / 'level_generation/creatures/mm8_m460_claude'
SOURCE = ROOT / 'level_generation/creatures/mm8_m460/sources.json'
data = json.loads(SOURCE.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for directory in ('native', 'references', 'references_hd', 'scripts'):
    (PROJECT / directory).mkdir(exist_ok=True)

for record in [*data['sources'].values(), *data['palette_sources'].values()]:
    assert sha(ROOT / record['path']) == record['sha256'], record['path']

for descriptor in data['bindings'].values():
    for action in descriptor['actions'].values():
        group = action['native_group']
        table = ROOT / f'assets_dev/engine/rendering/sprite_frames/monsters/{group[:-1]}.yml'
        current = next(g for g in yaml.safe_load(table.read_text())['sprites'] if g['sprite_name'] == group)
        assert current == action['native_group_record'], group

frames = {}
for palette, palette_record in data['palette_sources'].items():
    colors = np.frombuffer((ROOT / palette_record['path']).read_bytes()[:768], dtype=np.uint8).reshape(256, 3)
    for name, source in data['sources'].items():
        if not source['referenced']:
            continue
        original = Image.open(ROOT / source['path'])
        assert original.mode == 'P' and original.size == (256, 256)
        indices = np.asarray(original)
        pixels = np.dstack((colors[indices], np.where(indices == source['transparent_index'], 0, 255))).astype('uint8')
        image = Image.fromarray(pixels)
        output = PROJECT / 'native' / f'{name}_{palette}.png'
        image.save(output)
        frames[name, palette] = image

def sheet(name, rows, columns):
    canvas = Image.new('RGB', (columns * 256, len(rows) * 284), '#30343c')
    draw = ImageDraw.Draw(canvas)
    for row, entries in enumerate(rows):
        for column, (frame, palette, label) in enumerate(entries):
            image = frames[frame, palette]
            canvas.paste(image, (column * 256, row * 284 + 28), image)
            draw.text((column * 256 + 8, row * 284 + 8), label, fill='white')
    canvas.save(PROJECT / 'references' / name)

sheet('standing_tiers.png', [[(f'm460sa{v}', p, f'{p}: view {v}') for v in range(5)] for p in ('461','462','463')], 5)
base = data['bindings']['46']['actions']
for name, action in base.items():
    if name == 'attack2':
        continue
    views = ('0', '1', '2', '3', '4') if name in ('standing','walk','attack','hit') else ('0',)
    rows = [[(f['frame'], '461', f"view {v}: {f['frame']} ({f['duration_ms']}ms)") for f in action['views'][v]] for v in views]
    sheet(f'{name}.png', rows, max(map(len, rows)))

inventory = {
    'identity': 'mm8:m460',
    'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': sha(SOURCE),
    'sources': data['sources'], 'palettes': data['palette_sources'], 'bindings': data['bindings'],
    'referenced_frame_count': len(frames) // 3, 'extracted_png_count': len(frames),
    'orphan_images': data['orphan_images'],
    'canvas': [256,256], 'transparent_index': 0,
    'validation': 'Every BMP/palette hash and every active YAML group matches the native source manifest.',
}
(PROJECT / 'native_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
assert len(frames) == 3 * sum(bool(s["referenced"]) for s in data["sources"].values())
assert sum(f['duration_ms'] for f in base['attack']['views']['0']) == 1000
assert sum(f['duration_ms'] for f in base['hit']['views']['0']) == 625
print(json.dumps({'pngs':len(frames), 'references':str(PROJECT/'references'), 'checks':'source hashes, YAML groups, counts, repeated attack holds passed'}))
