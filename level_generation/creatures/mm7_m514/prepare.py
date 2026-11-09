"""Prepare the native MM7 ambient rat, keeping descriptor bindings authoritative."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent.parent / 'sprites'))
from inventory import frame_images


def run():
    inventory = json.loads((HERE.parent / 'remaining_inventory.json').read_text())
    family = next(f for f in inventory['families'] if f['world'] == 'mm7' and f['label'] == 'zrat a')
    groups = {}
    group_paths = {}
    for path in (REPO / 'assets_dev/engine/rendering/sprite_frames/monsters').glob('*.yml'):
        for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            groups[group['sprite_name'].lower()] = group
            group_paths[group['sprite_name'].lower()] = path
    descriptors = []
    bindings = {}
    actions = ['standing', 'walk', 'attack', 'shoot', 'hit', 'death', 'corpse', 'fidget']
    for line in (REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt').read_text().splitlines():
        row = line.split('\t')
        if row[0] in {str(d['id']) for d in family['descriptors']}:
            descriptors.append(row)
            bindings[row[0]] = dict(zip(actions, [n.lower() for n in row[11:19]]))
    selected = {n: groups[n] for binding in bindings.values() for n in binding.values()}
    palette_path = REPO / 'assets_dev/worlds/mm7/textures/pal545.act'
    palette = np.frombuffer(palette_path.read_bytes()[:768], np.uint8).reshape(256, 3)
    sources = {}
    natives = {}
    for directory in ['native', 'references', 'prompts', 'raw', 'review']:
        (HERE / directory).mkdir(exist_ok=True)
    for relative in family['existing_images']:
        path = REPO / relative
        original = Image.open(path)
        indices = np.array(original)
        assert original.mode == 'P'
        native = Image.fromarray(np.dstack((palette[indices], (indices != 0).astype(np.uint8) * 255)))
        native.save(HERE / f'native/{path.stem}.png')
        natives[path.stem] = native
        sources[path.stem] = dict(path=relative, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                  size=list(native.size), visible_bounds=native.getbbox(), transparency_index=0)
    # One common window exposes the small animal without fitting individual silhouettes.
    boxes = [im.getbbox() for im in natives.values()]
    window = [min(b[0] for b in boxes)-12, min(b[1] for b in boxes)-12,
              max(b[2] for b in boxes)+12, max(b[3] for b in boxes)+12]
    batches = {'standing': dict(frames=family['standing_images'], columns=2)}
    for view in range(5):
        batches[f'walk_{view}'] = dict(frames=[f'm514w{letter}{view}' for letter in 'abcd'], columns=2)
    batches['death_corpse'] = dict(frames=[f'm514d{letter}0' for letter in 'abc']+['m514xa0'], columns=2)
    assert sorted(n for b in batches.values() for n in b['frames']) == sorted(sources)
    for key, batch in batches.items():
        cols = batch['columns']
        rows = (len(batch['frames'])+cols-1)//cols
        cell = [(window[2]-window[0])*4, (window[3]-window[1])*4]
        sheet = Image.new('RGB', (cell[0]*cols, cell[1]*rows), (255, 0, 255))
        for i, name in enumerate(batch['frames']):
            im = natives[name].crop(window).resize(cell, Image.Resampling.NEAREST)
            sheet.paste(im, (i%cols*cell[0], i//cols*cell[1]), im)
        sheet.save(HERE / f'references/{key}.png')
        batch.update(rows=rows, cell_size=cell, native_window=window, reference_scale=4)
        prompt = f'''Use case: style-transfer. Restore the supplied Might and Magic VII native ambient rat sprites into detailed faithful dark fantasy game sprites.
Input 1 is the exact pose/view/layout authority: {cols} columns by {rows} rows, {len(batch['frames'])} occupied cells, row-major. Batch: {key}. Standing views are front, front-right oblique, right profile, rear-right oblique, back. Leave unused cells empty.
Preserve this same squat small ordinary rat: olive brown and dark gray coarse fur, round heavy haunches, low pointed snout, small round ears, tiny black eyes, delicate pale whiskers, pinkish gray bare tail and small paws. Keep the original muted dark tonal weight, restrained upper-left illumination, proportions, native camera angles, tail curvature, foot positions and each pose's silhouette. Fine believable fur, no new accessories, no monster teeth, no cartoon redesign, no glossy or bright fur.
Keep equal cells and precisely the native relative placement and common anatomical scale. Do not independently enlarge or recenter figures. Preserve all tail tips, paws and whiskers with empty gutters. Clarify continuous fine detail without retaining enlarged pixel steps. Aim for useful high resolution, approximately 2048 pixels wide. No labels, text, grid lines or extra figures.
Background is perfectly flat magenta RGB(255,0,255), without gradients, ground shadows, colored reflections, halos or checkerboard. The rat has no magenta or purple material; preserve its natural muted pink-gray tail.
'''
        if key != 'standing':
            prompt += 'Input 2 is accepted enhanced standing art, identity and materials only. Input 1 controls all action poses.\n'
        if key == 'death_corpse':
            prompt += 'Follow the native gentle collapse and prone resting poses exactly, including rotation and foreshortening; no added blood or injuries.\n'
        (HERE / f'prompts/{key}.txt').write_text(prompt)
    source_paths = set(group_paths[n] for n in selected)
    provenance = lambda p: dict(path=str(p.relative_to(REPO)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (HERE / 'sources.json').write_text(json.dumps(dict(sources=sources, groups=selected,
        descriptor_rows=descriptors, descriptor_bindings=bindings, base_palette=545, palettes=[545],
        palette_sources={'545': provenance(palette_path)}, group_sources=[provenance(p) for p in source_paths],
        generation_window=window, palette_note='All three native descriptors use the identical palette; no recolor regions.',
        logical_canvases=sorted({tuple(s['size']) for s in sources.values()})), indent=2)+'\n')
    (HERE / 'batches.json').write_text(json.dumps(batches, indent=2)+'\n')
    print(f'{len(sources)} referenced files, {len(batches)} batches; common window {window}')


if __name__ == '__main__':
    run()
