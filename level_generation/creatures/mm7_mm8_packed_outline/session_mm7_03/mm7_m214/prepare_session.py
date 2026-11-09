"""Session-local MM7 metadata preparation; reuse shared packing and native decoding."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
import yaml

REPO = Path.cwd().resolve()
CREATURES = REPO / 'level_generation/creatures'
SESSION = CREATURES / 'mm7_mm8_packed_outline/session_mm7_03'
sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
from prepare_packed_outline import best_grid, native_2x
from whole_animation_resolution import DEFAULT_POLICY

STEMS = (214, 218, 222, 226, 230, 234, 238, 242)
ACTIONS = ('standing', 'walk', 'attack', 'shoot', 'hit', 'death', 'corpse', 'fidget')
CONTEXT = ('TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration '
           'of an EXISTING Might and Magic VII (MM7) fantasy role-playing game sprite asset, using the supplied '
           'original animation bitmaps. Restore the existing fantasy-game character and its original animation; '
           'preserve its native costume, material coverage, anatomy and poses. The request is game-art restoration.')


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def asset(path):
    return dict(path=str(path.relative_to(REPO)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def prepare(stem):
    family = f'mm7_m{stem}'
    prior, root = CREATURES / family, SESSION / family
    out = root / 'redo_2x'
    if (out / 'run.json').exists():
        run = read(out / 'run.json')
        assert run['method'] == 'packed_complete_animation_outline_only_detailed_appearance'
        for job in run['jobs']:
            for item in job['prepared_assets']:
                assert asset(REPO / item['path'])['sha256'] == item['sha256']
        print(f'{family}: resumed {len(run["jobs"])} prepared jobs', flush=True)
        return
    inventory = read(CREATURES / 'remaining_inventory.json')
    entry = next(row for row in inventory['families'] if row['world'] == 'mm7'
                 and any(name.startswith(f'm{stem}') for name in row['standing_images']))
    old = read(prior / 'sources.json')
    assert set(old['sources']) == set(entry['all_native_family_images'])
    descriptor_path = REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt'
    ids = {str(row['id']): row['label'] for row in entry['descriptors']}
    rows = [line.split('\t') for line in descriptor_path.read_text().splitlines()
            if line.split('\t')[0] in ids]
    assert len(rows) == len(ids)
    assert all(row[1] == ids[row[0]] for row in rows)
    bindings = {row[0]: dict(zip(ACTIONS, [value.lower() for value in row[11:19]])) for row in rows}
    group_paths = [REPO / value['path'] for value in old.get('group_sources', [])]
    if not group_paths:
        group_paths = [REPO / f'assets_dev/engine/rendering/sprite_frames/monsters/{name}.yml'
                       for name in old['groups']]
    groups = {}
    for path in group_paths:
        for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            groups[group['sprite_name'].lower()] = group
    wanted = {name for binding in bindings.values() for name in binding.values()}
    if 'null' in wanted and 'null' not in groups:
        common = REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml'
        for group in yaml.load(common.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            groups[group['sprite_name'].lower()] = group
        group_paths.append(common)
    groups = {name: groups[name] for name in sorted(wanted)}
    palettes = sorted({frame['palette_id'] for group in groups.values() for frame in group['frames']
                       if group['sprite_name'].lower() != 'null'})
    assert palettes == entry['palettes']
    base = old.get('base_palette', 54)
    canvas = [max(source['size'][axis] for source in old['sources'].values()) for axis in (0, 1)]
    for folder in ('native', 'redo_2x/references', 'redo_2x/prompts', 'redo_2x/raw', 'redo_2x/review'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    palette_sources = {str(p): asset(REPO / f'assets_dev/worlds/mm7/textures/pal{p:03d}.act') for p in palettes}
    sources = dict(old, groups=groups, descriptor_rows=rows, descriptor_bindings=bindings,
                   base_palette=base, palettes=palettes, palette_sources=palette_sources,
                   group_sources=[asset(path) for path in group_paths], logical_canvas=canvas,
                   logical_canvases=[canvas], logical_pivot=[canvas[0] / 2, canvas[1]],
                   anchor='bottom-center', pixel_aliases={})
    native, offsets, frames = {}, {}, {}
    for name, source in sources['sources'].items():
        image, offset = native_2x(source, sources, base)
        native[name], offsets[name] = image, offset
        box = image.getbbox()
        assert box, f'Explicit empty endpoint handling required: {name}'
        source['aligned_bounds'] = [value / 2 for value in box]
        source['native_offset'] = offset
        source['referenced'] = name not in entry['unreferenced_family_images']
        frames[name] = dict(native_offset=offset, source_canvas=source['size'])
        image.resize(tuple(canvas), Image.Resampling.NEAREST).save(root / 'native' / (name + '.png'))
    write(root / 'sources.json', sources)
    write(root / 'manifest.json', dict(logical_canvas=canvas, logical_pivot=sources['logical_pivot'],
                                      anchor='bottom-center', frames=frames))
    previous_config = read(prior / 'config.json') if (prior / 'config.json').exists() else {}
    description = previous_config.get('description')
    if not description:
        description = ('The original slim adult Fighter Plate A, cylindrical closed visor with narrow eye slit, '
                       'green/white plume, silver plates and chainmail, restrained gold edges, forest-green surcoat '
                       'with white heraldry and diagonal white bands, dark leather joints, steel boots and native sword. '
                       'Preserve slender proportions, native armor coverage and all equipment angles.')
    config = dict(previous_config, family=f'm{stem}', title=entry['label'], label=entry['label'],
                  creature=previous_config.get('creature', 'plate_fighter'), description=description,
                  matte='magenta', mask_kind='green', base_palette=base)
    write(root / 'config.json', config)
    jobs, seen, represented = [], {}, set()
    for action in ('walk', 'standing', 'attack', 'shoot', 'hit', 'fidget', 'death', 'corpse'):
        for descriptor, binding in bindings.items():
            group = groups[binding[action]]
            if group['sprite_name'].lower() == 'null':
                continue
            for view in range(8):
                steps = group['frames']
                if any(f'Mirror{view}' in step['flags'] and 'Image1' not in step['flags'] for step in steps):
                    continue
                names = [step['texture_name'].lower() + ('' if 'Image1' in step['flags'] else str(view))
                         for step in steps]
                assert set(names) <= set(native)
                signature = tuple(names)
                record = dict(descriptor=int(descriptor), action=action, view=view, native_frames=names,
                              native_group=group['sprite_name'])
                if signature in seen:
                    seen[signature]['bindings'].append(record)
                    continue
                key = f'{action}_{view}_sheet'
                if any(job['id'] == key for job in jobs):
                    key = f'{action}_{view}_descriptor{descriptor}_sheet'
                job = dict(id=key, action=action, view=view, frames=names, bindings=[record], native_sequence=True)
                seen[signature] = job
                jobs.append(job)
                represented.update(names)
    for name in sorted(set(native) - represented):
        jobs.append(dict(id=f'unused_{name}_sheet', action='unused_native', view=int(name[-1]),
                         frames=[name], bindings=[], native_sequence=False))
    for job in jobs:
        boxes = [native[name].getbbox() for name in job['frames']]
        crop2 = [min(box[i] for box in boxes) - 4 if i < 2 else max(box[i] for box in boxes) + 4
                 for i in range(4)]
        crop = [value / 2 for value in crop2]
        cell = [(crop2[i + 2] - crop2[i]) // 2 for i in range(2)]
        budget, _, columns, row_count, envelope = best_grid(len(boxes), *cell)
        color = Image.new('RGBA', (columns * cell[0] * 2, row_count * cell[1] * 2))
        outline = Image.new('RGB', color.size, 'white')
        for index, name in enumerate(job['frames']):
            tile = native[name].crop(crop2)
            restored = Image.new('RGBA', native[name].size)
            restored.paste(tile, tuple(crop2[:2]))
            assert np.array_equal(np.array(restored), np.array(native[name]))
            position = (index % columns * tile.width, index // columns * tile.height)
            color.paste(tile, position)
            inside = np.array(tile.getchannel('A'))[::2, ::2] > 0
            boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[boundary] = 0
            outline.paste(Image.fromarray(guide).resize(tile.size, Image.Resampling.NEAREST), position)
        refs = [out / 'references' / (job['id'] + suffix + '.png') for suffix in ('_native', '_outline', '_detail')]
        color.save(refs[0])
        outline.save(refs[1])
        appearance = prior / 'cleaned' / (job['frames'][0] + '.png')
        detail = Image.open(appearance).convert('RGBA')
        detail.crop(detail.getbbox()).save(refs[2])
        target = [math.ceil(color.width * 1.4), math.ceil(color.height * 1.4)]
        anatomy = ('Preserve shoulder/elbow/wrist/finger and hip/knee/ankle/toe chains wherever present, exact joint '
                   'bends, limb ownership/crossings, equipment grip, body bob, head angle and foot contacts.')
        if stem == 214:
            anatomy += ' Preserve both bow limbs, delicate bowstring, nocked/loading arrow, arrow feathers, quiver and near/far hand ownership.'
        elif stem == 218:
            anatomy += ' Preserve long spear shaft, complete tip, precise shaft angle and both hands, leafy head crown and native slender body.'
        elif stem == 234:
            anatomy += ' Preserve bat wing roots, all finger struts/membrane gaps, curved horns, thin spade tail and clawed toes; follow native stone death stages.'
        elif stem in (238, 242):
            anatomy += ' The creature floats: NO invented legs, feet or walking gait. Preserve the exact native lower-body mist/robe silhouette, transparent gaps and fading/effect steps.'
        prompt = f'''{CONTEXT}

Use case: style-transfer. Restore exactly ONE COMPLETE {entry['label']} {job['action']} animation for stored view {job['view']}. ALL {len(boxes)} original steps belong on ONE returned RGBA sheet, {columns} columns by {row_count} rows, chronological row-major order: {', '.join(job['frames'])}. No added or omitted poses; unused cells stay transparent.
Image 1: untouched native colour sheet, sole authority for EACH step's anatomy, proportions, position, base colours, equipment, ownership, camera and motion.
Image 2: separate matching OUTLINE-ONLY geometry guide. Thin inward alpha boundaries and transparent gaps guide anatomy ONLY. Black strokes and white interior/exterior contain NO lighting, shading, creases or texture and MUST NOT appear in the restoration.
Image 3: detailed SAME-FAMILY appearance art, for fine face/material texture and natural painted shading ONLY. Preserve its detailed finish; do not copy its pose, changed bulk, costume additions or geometry.
Character: {description}
Every native step must remain faithful: {anatomy} No swapped/fused/extra limbs, altered costume coverage, invented joints/equipment or duplicated animation steps. Anatomy has priority over decoration.
Retain fine grain, cloth weave/folds/seams, metal wear/rivets, face/skin detail or stone/mist/bone detail as applicable, with rich native tonal weight and natural shading. Avoid copied guide bands, dark grooves, artificial blotchy shading, washed-out contrast, waxy smoothing, blur, pixel blocks, dithering, halos and noisy pseudo-detail.
Generate only native base palette {base} as shown in Image 1. Shared native-coordinate crop {crop}, padded cell {cell}, actor canvas {canvas}, pivot {sources['logical_pivot']}. Use identical scale/crop/position for EVERY step; never independently center, zoom or fit silhouettes. Keep the initial TWO native pixels of transparent padding and preserve all thin tips and separated particles.
Request {target[0]}x{target[1]} or greater, targeting >=2.5 actual generated pixels per native pixel, preferably >=2.2 after registration. Whole-cycle coverage takes priority if output sampling is smaller: retain all original frames together; never split cycles or enlarge a previous image to claim generated detail.
ONE genuinely transparent RGBA image, including gaps, with no background, floor, cast shadow, grid, labels, text, painted checkerboard or extra figures.
'''
        if len(boxes) == 1:
            prompt += 'FINAL COUNT: exactly ONE original sprite; this is the complete native single-bitmap action or unused asset. No storyboard or added cycle.\n'
        if not job['native_sequence']:
            prompt += 'This unreferenced native bitmap is preserved separately and receives NO playback binding.\n'
        if job['action'] in ('death', 'corpse'):
            prompt += 'Preserve the original non-graphic falling/resting or fading/effect stages, including small disconnected pieces. Add no blood or injury detail, and no intact body in a native residue/effect cell.\n'
        prompt_path = out / 'prompts' / (job['id'] + '_v1.txt')
        prompt_path.write_text(prompt)
        job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=row_count,
                   observed_envelope=list(envelope), planned_sampling=budget, requested_master=target,
                   references=[str(path.relative_to(REPO)) for path in refs],
                   reference_roles=['untouched_native_complete_animation', 'outline_only_geometry_no_shading',
                                    'previous_detailed_material_appearance_not_pose'],
                   appearance_source=asset(appearance), prompt=str(prompt_path.relative_to(REPO)),
                   status='pending', attempts=[], prepared_assets=[asset(path) for path in refs + [prompt_path]])
    write(out / 'run.json', dict(project=str(root.relative_to(REPO)), source_project=str(prior.relative_to(REPO)),
          method='packed_complete_animation_outline_only_detailed_appearance', status='prepared', target_sampling=2.5,
          padding_native_px=2, reference_enlargement=2, native_offsets=offsets,
          source_metadata=[asset(prior / name) for name in ('sources.json', 'manifest.json')]
                          + [asset(descriptor_path)] + sources['group_sources'], jobs=jobs))
    write(out / 'processing.json', dict(preserve_matte_hued_materials=True, supplied_alpha_noise_floor=0,
          whole_animation_resolution_policy=DEFAULT_POLICY,
          reason='Preserve generated alpha, thin structures and translucent effects. Cleanup needs visual evidence.'))
    print(f'{family}: {len(jobs)} complete sheets; {len(native)} source names; base {base}; palettes {palettes}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stems', nargs='+', type=int, default=list(STEMS))
    for value in parser.parse_args().stems:
        assert value in STEMS
        prepare(value)
