"""Prepare reviewed single-material MM6 families from explicit configs; no AI calls."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from prepare import ACTIONS, ASSETS, CREATURES, REPO, frame_images, load_native_tables, sha, write


def main(family):
    root = CREATURES / ('mm6_' + family)
    config = json.loads((root / 'config.json').read_text())
    descriptors, groups = load_native_tables()
    for folder in ['native', 'references', 'prompts', 'raw', 'review']:
        (root / folder).mkdir(exist_ok=True)
    variants, used = {}, set()
    for mid in config['descriptor_ids']:
        d = descriptors[mid]
        actions = {a: groups[n.lower()] for a, n in zip(ACTIONS, d[11:19])}
        palette = actions['standing']['frames'][0]['palette_id']
        assert palette not in variants
        variants[str(palette)] = dict(descriptor_id=mid, descriptor_label=d[1], actions=actions)
        used.update(n for g in actions.values() if g['sprite_name'].lower() != 'null'
                    for f in g['frames'] for n in frame_images(f))
    sources, duplicates = {}, defaultdict(list)
    paths = set((ASSETS / 'engine/sprites').glob(family + '*.bmp'))
    paths.update(REPO / entry['path'] for entry in config.get('extra_sources', {}).values())
    for path in sorted(paths):
        im = Image.open(path)
        pixel_hash = hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest()
        name = path.stem.lower()
        sources[name] = dict(path=str(path.relative_to(REPO)), sha256=sha(path), size=im.size,
                                  pixel_hash=pixel_hash, referenced=name in used)
        if 'palette' in config.get('extra_sources', {}).get(name, {}):
            sources[name]['fixed_palette'] = config['extra_sources'][name]['palette']
        duplicates[pixel_hash].append(name)
    assert used <= sources.keys(), 'Explicit source family does not cover all native bindings'
    aliases = {n: names[0] for names in duplicates.values() for n in names[1:]}
    canvas = [max(s['size'][0] for s in sources.values()), max(s['size'][1] for s in sources.values())]
    palette_paths = {str(p): f'assets_dev/worlds/mm6/textures/pal{p}.act' for p in variants}
    palette_paths.update(config.get('extra_palette_paths', {}))
    inv = dict(variants=variants, sources=sources, pixel_aliases=aliases, palette_paths=palette_paths,
               unreferenced=sorted(sources.keys() - used), logical_canvas=canvas)
    write(root / 'inventory.json', {family: inv})
    palettes = {p: np.frombuffer((REPO / path).read_bytes()[:768], np.uint8).reshape(256, 3)
                for p, path in palette_paths.items()}

    def native(name, palette):
        palette = sources[name].get('fixed_palette', palette)
        index = np.array(Image.open(REPO / sources[name]['path']))
        im = Image.fromarray(np.dstack([palettes[str(palette)][index], (index != 0).astype(np.uint8) * 255]))
        aligned = Image.new('RGBA', canvas)
        offset = [(canvas[0] - im.width) // 2, canvas[1] - im.height]
        aligned.paste(im, offset)
        return aligned, offset

    for name, source in sources.items():
        im, offset = native(name, config['base_palette'])
        im.save(root / 'native' / (name + '.png'))
        source.update(native_offset=offset, aligned_bounds=im.getbbox())
    actions = variants[str(config['base_palette'])]['actions']
    batches, seen = {}, set()

    def add(key, names, view):
        names = list(dict.fromkeys(aliases.get(n, n) for n in names))
        names = [n for n in names if n not in seen]
        seen.update(names)
        for start in range(0, len(names), 8):
            part = key if len(names) <= 8 else key + '_' + str(start // 8)
            batches[part] = dict(frames=names[start:start+8], view=view)

    standing_frames = actions['standing']['frames']
    if len(standing_frames) > 1:
        assert 'standing_reference_frame' in config, 'Animated standing needs a reviewed batching layout'
        # Identity sheet samples one native moment; remaining moments are batched below.
        assert actions['standing'] == actions['walk'] or config.get('batch_distinct_standing'), \
            'Distinct animated idle needs an explicitly reviewed batch'
    standing_index = config.get('standing_reference_frame', 0)
    identity_frames = actions[config.get('identity_reference_action', 'standing')]['frames']
    identity_names = frame_images(identity_frames[standing_index])
    identity_view = 'front, front-oblique, profile, rear-oblique, back in native stored order'
    if config.get('identity_full_sequence'):
        assert all('Image1' in f['flags'] for f in identity_frames)
        identity_names = [n for f in identity_frames for n in frame_images(f)]
        identity_view = 'native front-only animation, consecutive moments, not different directions'
    add('standing', identity_names, identity_view)
    action_order = ['walk', 'attack', 'hit', 'fidget', 'death']
    if config.get('batch_distinct_standing'):
        action_order.insert(0, 'standing')
    separate_corpse = config.get('separate_corpse_batch', False)
    if separate_corpse: action_order.append('corpse')
    for action in action_order:
        frames = [] if actions[action]['sprite_name'].lower() == 'null' else list(actions[action]['frames'])
        if action == 'death' and not separate_corpse:
            if actions['corpse']['sprite_name'].lower() != 'null':
                frames += actions['corpse']['frames']
        if not frames:
            continue
        single = 'Image1' in frames[0]['flags']
        assert all(('Image1' in f['flags']) == single for f in frames)
        for view in range(1 if single else 5):
            names = [f['texture_name'].lower() + ('' if single else str(view)) for f in frames]
            extras = config.get('extra_native_actions', {}).get(action, [])
            if extras:
                assert single
                names = sorted(set(names) | set(extras))
            key = 'idle' if action == 'standing' else ('death_corpse' if action == 'death' else action)
            add(key + ('' if single else '_' + str(view)),
                names, ['front', 'front-oblique', 'profile', 'rear-oblique', 'back'][view])
    add('unused_native', sorted(set(sources) - seen - set(aliases)), 'native unused poses; no new timeline bindings')
    assert seen | set(aliases) == set(sources)
    for key, batch in batches.items():
        columns = 3 if len(batch['frames']) > 4 else 2
        rows = (len(batch['frames']) + columns - 1) // columns
        cell = [canvas[0] * 2 + 64, canvas[1] * 2 + 64]
        sheet = Image.new('RGB', (columns * cell[0], rows * cell[1]), (255, 0, 255))
        for i, name in enumerate(batch['frames']):
            im = Image.open(root / 'native' / (name + '.png')).resize(
                (canvas[0] * 2, canvas[1] * 2), Image.Resampling.NEAREST)
            sheet.paste(im, (i % columns * cell[0] + 32, i // columns * cell[1] + 32), im)
        sheet.save(root / 'references' / (key + '.png'))
        batch.update(columns=columns, rows=rows, cell_size=cell)
        empty_slots = [i+1 for i, name in enumerate(batch['frames']) if sources[name]['aligned_bounds'] is None]
        prompt = f'''Use case: style-transfer. Faithful restoration of {config['title']} native game sprites.
Input 1 controls EXACT POSE, VIEW and LAYOUT: {columns} columns, {rows} rows, {len(batch['frames'])} native frame slots in row-major order, {len(batch['frames'])-len(empty_slots)} visible images. Action {key}; view {batch['view']}. Frame order: {', '.join(batch['frames'])}. Leave unused cells empty. Native transparent slots (one-based): {empty_slots}; these must also stay completely empty.
Identity and materials: {config['description']}
Preserve native proportions, silhouette, head angles, hand and foot positions, weapon perspective and every distinct animation pose. Clarify the original painted/pre-rendered fantasy artwork with crisp material detail and soft baked lighting. Keep the original muted dark tonal weight; no glossy plastic, modern redesign, new accessories, exaggerated anatomy or cartoon simplification. Same scale and source-relative position throughout, no independent cell zoom or recentering. Keep all thin features inside the cell.
Selective palette regions: {config['regions']}. Other materials stay protected and consistent.
Use a high-resolution sheet with useful per-pose detail and the same aspect ratio/grid as input 1. Perfectly uniform pure magenta RGB(255,0,255) background, including limb/equipment gaps. No gradient, ground shadow, checkerboard, labels, grid lines, watermark, colored spill or magenta edge halo.
'''
        if key != 'standing':
            prompt += 'Input 2 is accepted enhanced standing artwork, IDENTITY AND MATERIAL authority only. Input 1 controls each animation pose; do not replace it with the standing pose.\n'
        if key == 'death_corpse':
            prompt += 'Preserve falling and prone foreshortening and body mass; do not enlarge the fallen body to fill its cell. No added gore.\n'
        (root / 'prompts' / (key + '.txt')).write_text(prompt)
    write(root / 'batches.json', batches)
    write(root / 'sources.json', dict(inv, base_palette=config['base_palette'],
        palette_sources={p: dict(path=path, sha256=sha(REPO / path)) for p, path in palette_paths.items()},
        logical_pivot=[canvas[0]/2, canvas[1]], anchor='bottom-center; native offsets recorded'))
    contact = Image.new('RGB', (canvas[0]*max(5, len(batches['standing']['frames'])),
                              (canvas[1]+24)*len(variants)), (43,43,43))
    draw = ImageDraw.Draw(contact)
    for row, palette in enumerate(variants):
        for col, name in enumerate(batches['standing']['frames']):
            im, _ = native(name, palette)
            contact.paste(im, (col*canvas[0], row*(canvas[1]+24)+24), im)
            draw.text((col*canvas[0]+4, row*(canvas[1]+24)+4), f'{palette}: {name}', fill='white')
    contact.save(root / 'references/native_variants.png')
    print(f'{family}: {len(sources)} sources; {len(duplicates)} unique; {len(batches)} batches')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family')
    main(parser.parse_args().family)
