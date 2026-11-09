"""MM8 descriptor-schema preparation using shared native decoding and full-cycle grid helpers.

The shared packed preparer requires MM6 config/manifest files absent from these MM8 inventories.
This session-local operation bridges preparation only; older projects and shared tools stay read-only.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import yaml

REPO = Path('/home/pjasicek/github/OpenYAMM')
CREATURES = REPO / 'level_generation/creatures'
STAGE = CREATURES / 'mm7_mm8_packed_outline/session_mm8_03'
sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
from prepare_packed_outline import best_grid, native_2x
from whole_animation_resolution import METHOD, DEFAULT_POLICY

STEMS = [464, 468, 472, 476, 480, 484, 488, 492]
HEADER = ('TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration of an '
          'EXISTING Might and Magic VIII (MM8) fantasy role-playing game sprite asset, using the supplied original '
          'animation bitmaps. Restore the existing fantasy-game character and its original animation; preserve its '
          'native costume, material coverage, anatomy and poses. The request is game-art restoration.')
ROLES = ['untouched_native_complete_animation', 'outline_only_geometry_no_shading',
         'same_family_detailed_appearance_not_pose']


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jobs_for(sources, stem):
    seen = {}
    represented = set()
    aliases = sources['pixel_aliases']
    for descriptor, actor in sources['bindings'].items():
        for action in ['walk', 'standing', 'attack', 'attack2', 'hit', 'fidget', 'death', 'corpse']:
            for view, steps in actor['actions'][action]['views'].items():
                if not steps or any(step['mirrored'] for step in steps) or all(step['frame'] is None for step in steps):
                    continue
                assert all(step['frame'] is not None for step in steps), 'Mixed null sequence needs explicit handling'
                frames = [aliases.get(step['frame'], step['frame']) for step in steps]
                binding = dict(descriptor_id=int(descriptor), action=action, view=int(view),
                               native_frames=[step['frame'] for step in steps])
                signature = tuple(frames)
                if signature in seen:
                    seen[signature]['bindings'].append(binding)
                    continue
                job_id = f'{action}_{view}_sheet'
                if any(job['id'] == job_id for job in seen.values()):
                    job_id = f'{action}_{view}_descriptor{descriptor}_sheet'
                seen[signature] = dict(id=job_id, action=action, view=int(view), frames=frames,
                                       bindings=[binding], native_sequence=True, status='pending', attempts=[])
                represented.update(frames)
    unused = defaultdict(list)
    for name in sorted(set(sources['sources']) - represented - set(aliases)):
        match = re.fullmatch(f'm{stem}' + r'([a-z]+?)([a-z])([0-7])', name)
        assert match, name
        unused[(match[1], int(match[3]))].append(name)
    jobs = list(seen.values())
    for (code, view), frames in unused.items():
        jobs.append(dict(id=f'unused_{code}_{view}_sheet', action='unused_native', view=view, frames=frames,
                         bindings=[], native_sequence=False, status='pending', attempts=[]))
    assert set(name for job in jobs for name in job['frames']) == set(sources['sources']) - set(aliases)
    return jobs


def prepare(stem, groups, group_paths, descriptors):
    original = CREATURES / f'mm8_m{stem}'
    root = STAGE / original.name
    out = root / 'redo_2x'
    if (out / 'run.json').exists():
        run = read(out / 'run.json')
        for job in run['jobs']:
            assert all(sha(REPO / item['path']) == item['sha256'] for item in job['prepared_assets'])
        print(stem, 'resumed', len(run['jobs']), 'jobs')
        return
    sources = read(original / 'sources.json')
    inventory = read(CREATURES / 'remaining_inventory.json')
    family = next(row for row in inventory['families']
                  if row['world'] == 'mm8' and f'm{stem}sa0' in row['standing_images'])
    assert family['label'] == sources['label']
    assert {str(item['id']) for item in family['descriptors']} == set(sources['bindings'])
    used_groups = set()
    for descriptor, actor in sources['bindings'].items():
        assert actor['native_descriptor'] == descriptors[int(descriptor)]
        assert actor['label'] == descriptors[int(descriptor)][1]
        for action in actor['actions'].values():
            assert action['native_group_record'] == groups[action['native_group']]
            used_groups.add(action['native_group'])
    sources['source_tables'] = [dict(path=str(path.relative_to(REPO)), sha256=sha(path))
                                for path in sorted({group_paths[group] for group in used_groups})]
    descriptor_path = REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt'
    sources['descriptor_table'] = dict(path=str(descriptor_path.relative_to(REPO)), sha256=sha(descriptor_path))
    canvas = [max(source['size'][axis] for source in sources['sources'].values()) for axis in (0, 1)]
    assert all(source['anchors'] in ([], ['bottom-center']) for source in sources['sources'].values())
    sources.update(logical_canvas=canvas, logical_pivot=[canvas[0] / 2, canvas[1]])
    for folder in ['references', 'prompts', 'raw', 'review']:
        (out / folder).mkdir(parents=True, exist_ok=True)
    save(root / 'sources.json', sources)
    native = {name: native_2x(source, sources, sources['base_palette'])[0]
              for name, source in sources['sources'].items()}
    offsets = {name: [(canvas[0] - source['size'][0]) / 2, canvas[1] - source['size'][1]]
               for name, source in sources['sources'].items()}
    jobs = jobs_for(sources, stem)
    for job in jobs:
        images = [native[name] for name in job['frames']]
        boxes = [image.getbbox() for image in images]
        assert all(boxes)
        crop_2x = [min(box[0] for box in boxes) - 4, min(box[1] for box in boxes) - 4,
                   max(box[2] for box in boxes) + 4, max(box[3] for box in boxes) + 4]
        cell = [(crop_2x[2] - crop_2x[0]) // 2, (crop_2x[3] - crop_2x[1]) // 2]
        budget, _, columns, rows, envelope = best_grid(len(images), *cell)
        color = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
        outline = Image.new('RGB', color.size, 'white')
        for index, image in enumerate(images):
            part = image.crop(crop_2x)
            rebuilt = Image.new('RGBA', image.size)
            rebuilt.paste(part, tuple(crop_2x[:2]))
            assert np.array_equal(np.array(image), np.array(rebuilt))
            xy = (index % columns * part.width, index // columns * part.height)
            color.paste(part, xy)
            inside = np.array(part.getchannel('A'))[::2, ::2] > 0
            boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[boundary] = 0
            outline.paste(Image.fromarray(guide).resize(part.size, Image.Resampling.NEAREST), xy)
        paths = [out / 'references' / f'{job["id"]}_{role}.png' for role in ['native', 'outline']]
        color.save(paths[0])
        outline.save(paths[1])
        prior = original / 'redo_2x/cleaned' / (job['frames'][0] + '.png')
        if prior.exists():
            detail = Image.open(prior).convert('RGBA')
            box = detail.getbbox()
            assert box
            path = out / 'references' / f'{job["id"]}_detail.png'
            detail.crop((max(0, box[0] - 6), max(0, box[1] - 6),
                         min(detail.width, box[2] + 6), min(detail.height, box[3] + 6))).save(path)
            paths.append(path)
            job['appearance_source'] = dict(path=str(prior.relative_to(REPO)), sha256=sha(prior))
        target = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows * cell[1] * 2.8)]
        anatomy = ('Preserve shoulder/elbow/wrist/finger and hip/knee/ankle/toe chains, exact joint bends, lengths, '
                   'widths, near/far ownership, crossings, foreshortening, original lifted/planted feet, body bob, '
                   'head angle, costume coverage and each original equipment grip and orientation.')
        if stem == 492:
            anatomy = ('Preserve native dragon head/jaw/neck/body/tail, both articulated wing chains and membrane '
                       'folds, near/far ownership, crossings and every wingbeat extreme, each visible leg and claw, '
                       'horn roots/tips, original body bob, head direction and tail curves. No invented flight steps.')
        prompt = f'''{HEADER}
Use case: style-transfer. Generate exactly ONE COMPLETE {sources['label']} {job['action']} animation for stored view {job['view']}: ALL {len(images)} original steps together on ONE RGBA sheet, {columns} columns by {rows} rows, chronological row-major order. A one-frame action is ONE SINGLE SPRITE. No invented in-between steps, extra panels or poses.
Image 1 is the attached untouched correctly paletted native-colour complete animation: sole authority for every step's geometry, pose, anatomy, proportions, costume/material coverage, camera, equipment ownership, base colours and position/scale.
Image 2 is the attached matching separate OUTLINE-ONLY anatomy sheet: thin inward alpha silhouette contours and transparent limb gaps, white interior and exterior. Geometry ONLY; no lighting, texture or shading information. No copied black strokes, guide bands, dark grooves or flat white fill. No internal contrast guide.
{('Image 3 is attached detailed enhanced SAME-FAMILY appearance, for fine face/material finish and coherent natural lighting ONLY. Never copy its pose, broadened proportions, added bulk, alternate palette or equipment absent from Image 1.' if len(paths) == 3 else 'BOOTSTRAP EXCEPTION: no adequate enhanced same-family detail exists. This FIRST useful COMPLETE animation sheet establishes identity from attached Images 1 and 2. Reconstruct faithful fine face/material detail and native lighting; its selected detailed result will be attached as Image 3 on subsequent calls.')}
Anatomy in EVERY cell: {anatomy} No fused, swapped or extra limbs, disconnected joints, duplicated poses, new gait or added bulk. Rear heads show their native rear surfaces, never pasted frontal faces. Do not normalize crouched/prone pose heights.
Preserve detailed painted/pre-rendered fantasy-game rendering and native material colours, rich fine texture and natural contrast: existing wrinkles, hair, scales, cloth folds/seams, leather grain, rivets, metal wear or wing membranes as actually present. No washed-out contrast, waxy/plastic smoothing, blur, flat surfaces, enlarged pixel blocks, dithering, sharpened halos or noisy pseudo-detail. Outlines control geometry only; fine material reconstruction and natural shading remain required.
Palette: ONLY the base native palette {sources['base_palette']} in Image 1. Preserve existing colour/material separation and protected highlights; do not borrow another palette from detail art. Output material/recolour masks are separate later work.
Layout: row-major {', '.join(job['frames'])}. Shared native crop {[value / 2 for value in crop_2x]} (exclusive right/bottom), padded cell {cell}, actor canvas {canvas}, pivot {sources['logical_pivot']}. Identical native crop, scale and coordinates for every pose. No independent centering, zoom, silhouette fit, axis stretching or limb warping. Keep 2 NATIVE pixels of transparent safety padding, complete extremities and native gaps. Fill the planned grid without added exterior whitespace; unused cells stay empty.
Request LARGE {target[0]}x{target[1]} master, >=2x actual generated detail, preferably >=2.2x. The COMPLETE animation/view on ONE submitted and ONE returned sheet takes priority. Never split or enlarge an earlier return to claim generated detail.
Exactly ONE genuinely transparent RGBA image. No painted checkerboard, opaque backdrop, paper, grid, labels, floor or cast shadows. Follow original non-graphic falling/resting or residue/effect stages where present; no added injuries, blood or effects. Unused native art has no invented playback.
'''
        prompt_path = out / 'prompts' / (job['id'] + '_v1.txt')
        prompt_path.write_text(prompt)
        job.update(native_crop=[value / 2 for value in crop_2x], cell_native_size=cell,
                   columns=columns, rows=rows, observed_envelope=list(envelope), planned_sampling=budget,
                   requested_master=target, logical_canvas=canvas, reference_scale=2,
                   exact_native_placement=True, references=[str(path.relative_to(REPO)) for path in paths],
                   reference_roles=ROLES[:len(paths)], prompt=str(prompt_path.relative_to(REPO)),
                   bootstrap_detail_pending=len(paths) == 2,
                   prepared_assets=[dict(path=str(path.relative_to(REPO)), sha256=sha(path))
                                    for path in [*paths, prompt_path]])
    # Compare all native palettes before selecting the descriptor-A base; include old detail where available.
    names = [f'm{stem}sa{view}' for view in range(5)]
    palette_ids = list(sources['palette_sources'])
    contact = Image.new('RGB', (256 * 5, 278 * (len(palette_ids) + 1)), '#353a3f')
    draw = ImageDraw.Draw(contact)
    for row, palette in enumerate(palette_ids):
        draw.text((4, row * 278 + 4), f'{sources["label"]}; native palette {palette}', fill='white')
        for view, name in enumerate(names):
            image = native_2x(sources['sources'][name], sources, int(palette))[0]
            image = image.resize((256, 256), Image.Resampling.NEAREST)
            contact.paste(image, (view * 256, row * 278 + 22), image)
    for view, name in enumerate(names):
        prior = original / 'redo_2x/cleaned' / (name + '.png')
        if prior.exists():
            image = Image.open(prior).convert('RGBA')
            image.thumbnail((256, 256))
            contact.paste(image, (view * 256, len(palette_ids) * 278 + 22), image)
    draw.text((4, len(palette_ids) * 278 + 4), 'Prior detailed appearance where available; geometry stays native', fill='white')
    contact.save(out / 'review/reference_selection.png')
    save(out / 'run.json', dict(project=str(root.relative_to(REPO)), source_project=str(original.relative_to(REPO)),
         method=METHOD, status='prepared_not_generated', padding_native_px=2, reference_enlargement=2,
         target_sampling=2.2, native_offsets=offsets, jobs=jobs,
         source_metadata=[dict(path=str((original / 'sources.json').relative_to(REPO)),
                               sha256=sha(original / 'sources.json'))],
         preparation_checks=dict(native_foreground_and_alpha_reconstruction_exact=True,
             all_current_descriptors_and_groups_match=True, stored_views_and_aliases_preserved=True,
             physical_unique_frames=len(sources['sources']) - len(sources['pixel_aliases']),
             all_native_files=len(sources['sources']), unused_native_files=len(family['unreferenced_family_images'])),
         tooling_limitation='MM8 descriptor-schema preparation is session-local; shared decoder and full-cycle grid used.'))
    save(out / 'processing.json', dict(preserve_matte_hued_materials=True, supplied_alpha_noise_floor=0,
         whole_animation_resolution_policy=DEFAULT_POLICY))
    print(stem, sources['label'], len(jobs), 'whole-sheet jobs;', len(sources['sources']), 'native files')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stems', type=int, nargs='*', default=STEMS)
    args = parser.parse_args()
    table = REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt'
    descriptors = {int(cells[0]): cells for line in table.read_text().splitlines()
                   if (cells := line.split('\t'))[0].isdigit()}
    needed = {key for stem in args.stems
              for descriptor in read(CREATURES / f'mm8_m{stem}/sources.json')['bindings']
              for key in descriptors[int(descriptor)][11:19]}
    groups, paths = {}, {}
    tables = [REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml',
              *sorted((REPO / 'assets_dev/engine/rendering/sprite_frames/monsters').glob('*.yml'))]
    for path in tables:
        for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            if group['sprite_name'] in needed:
                groups[group['sprite_name']], paths[group['sprite_name']] = group, path
    assert set(groups) == needed
    for stem in args.stems:
        assert stem in STEMS
        prepare(stem, groups, paths, descriptors)


if __name__ == '__main__':
    main()
