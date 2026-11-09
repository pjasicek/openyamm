"""MM8 descriptor-schema preparation bridge, reusing native decoding and full-cycle packing.

Owns only the eight session_mm8_04 family directories. No generation or acceptance.
"""
import copy
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

REPO = Path(__file__).resolve().parents[5]
CREATURES = REPO / 'level_generation/creatures'
SESSION = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CREATURES))
sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
from mm8_restore_queue import native, resolve
from prepare_packed_outline import best_grid

FAMILIES = {496: 73, 500: 76, 504: 79, 512: 85, 516: 88, 520: 91, 524: 94, 528: 97}
CONTEXT = ('TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration '
           'of an EXISTING Might and Magic VIII (MM8) fantasy role-playing game sprite asset, using the supplied '
           'original animation bitmaps. Restore the existing fantasy-game character and its original animation; '
           'preserve its native costume, material coverage, anatomy and poses. The request is game-art restoration.')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def rel(path):
    return str(path.relative_to(REPO))


def prepare():
    inventory_path = CREATURES / 'remaining_inventory.json'
    inventory = read(inventory_path)['families']
    descriptor_path = REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt'
    rows = {line.split('\t')[0]: line.split('\t') for line in descriptor_path.read_text().splitlines()}
    rendering = REPO / 'assets_dev/engine/rendering'
    groups = {}
    for path in [rendering / 'sprite_frame_data_common.yml',
                 *sorted((rendering / 'sprite_frames/monsters').glob('*.yml'))]:
        for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            groups[group['sprite_name'].lower()] = (group, path)
    for number, descriptor_id in FAMILIES.items():
        family = f'mm8_m{number}'
        old, root = CREATURES / family, SESSION / family
        if (root / 'run.json').exists():
            run = read(root / 'run.json')
            for job in run['jobs']:
                for reference in job['prepared_assets']:
                    assert sha(REPO / reference['path']) == reference['sha256']
            print(f'{family}: resumed {len(run["jobs"])} complete sheets')
            continue
        row = next(r for r in inventory if r['world'] == 'mm8' and r['descriptors'][0]['id'] == descriptor_id)
        sources = copy.deepcopy(read(old / 'sources.json'))
        assert sources['label'] == row['label']
        assert set(map(int, sources['bindings'])) == {r['id'] for r in row['descriptors']}
        assert set(sources['sources']) == set(row['all_native_family_images'])
        assert set(sources['orphan_images']) == set(row['unreferenced_family_images'])
        assert set(map(int, sources['palette_sources'])) == set(row['palettes'])
        current_art = {p.stem.lower() for folder in ('assets_dev/engine/sprites', 'assets_dev/worlds/mm8/sprites')
                       for p in (REPO / folder).glob('*')
                       if p.suffix.lower() == '.bmp' and re.fullmatch(f'm{number}[a-z]+[0-7]', p.stem.lower())}
        assert current_art == set(sources['sources'])
        group_paths = set()
        runtime_aliases = []
        for descriptor, binding in sources['bindings'].items():
            assert rows[descriptor] == binding['native_descriptor']
            for action in binding['actions'].values():
                group, path = groups[action['native_group'].lower()]
                prior_group = action['native_group_record']
                if group != prior_group:
                    # Current mounts explicitly namespace one shared Fire corpse into mm6_wdm.
                    # Validate that exact mounted alias; never treat arbitrary table changes as compatible.
                    assert number == 496 and action['native_group'] == 'm498x'
                    assert len(group['frames']) == len(prior_group['frames']) == 1
                    current_frame, prior_frame = group['frames'][0], prior_group['frames'][0]
                    assert current_frame['texture_name'] == 'atlas:mm6_wdm/m496xa'
                    assert prior_frame['texture_name'] == 'm496xa'
                    assert {k: v for k, v in current_frame.items() if k != 'texture_name'} == {
                        k: v for k, v in prior_frame.items() if k != 'texture_name'}
                    mounted_path = REPO / 'assets_dev/engine/sprites_new/mm6_wdm/manifest.json'
                    mounted = read(mounted_path)
                    assert all(f'm496xa{v}' in mounted['frames'] for v in range(5))
                    runtime_aliases.append(dict(group=action['native_group'],
                        mounted_texture='atlas:mm6_wdm/m496xa', native_art_texture='m496xa',
                        manifest=rel(mounted_path), manifest_sha256=sha(mounted_path)))
                    action['native_group_record'] = copy.deepcopy(group)
                group_paths.add(path)
                for view, steps in action['views'].items():
                    for step, frame in zip(steps, group['frames'], strict=True):
                        texture, mirror = resolve(frame, int(view))
                        native_texture = texture.split('/', 1)[1] if texture.startswith('atlas:mm6_wdm/') else texture
                        assert step['native_texture'] == native_texture and step['mirrored'] == mirror
                        if texture != native_texture:
                            step['source_texture'] = native_texture
                            step['native_texture'] = texture
                        assert step['duration_raw'] == frame['frame_length_raw']
                        assert step['palette'] == frame.get('palette_id', 0)
                        assert step['flags'] == frame.get('flags', [])
                        assert step['scale'] == frame.get('scale', 1)
        for source in [*sources['sources'].values(), *sources['palette_sources'].values()]:
            assert sha(REPO / source['path']) == source['sha256'], source['path']
        for folder in ('references', 'prompts', 'raw', 'review'):
            (root / folder).mkdir(parents=True, exist_ok=True)
        sources['source_tables'] = [dict(path=rel(p), sha256=sha(p)) for p in sorted(group_paths)]
        sources['descriptor_table'] = dict(path=rel(descriptor_path), sha256=sha(descriptor_path))
        sources['inventory_source'] = dict(path=rel(inventory_path), sha256=sha(inventory_path))
        sources['verified_runtime_native_aliases'] = runtime_aliases
        sizes = {tuple(source['size']) for source in sources['sources'].values()}
        assert len(sizes) == 1, 'Different native sizes need explicit mixed-anchor placement support'
        canvas = list(next(iter(sizes)))
        center = number in (496, 500, 504, 528)
        pivot = [canvas[0] / 2, canvas[1] / 2 if center else canvas[1]]
        sources.update(logical_canvas=canvas, logical_pivot=pivot,
                       native_actor_anchor='center' if center else 'bottom-center')
        write(root / 'sources.json', sources)
        write(root / 'inventory.json', row)
        images = {name: native(root, name, sources['base_palette']) for name in sources['sources']}
        for name, image in images.items():
            pixels = np.array(image)
            pixels[pixels[:, :, 3] == 0] = 0
            images[name] = Image.fromarray(pixels)
        # Palette comparison and geometry orientation contact: native RGB remains untouched.
        first = next(iter(sources['bindings'].values()))['actions']
        sample_names = [first['standing']['views'][str(v)][0]['frame'] for v in (0, 2, 4)]
        palette_ids = sorted(map(int, sources['palette_sources']))
        contact = Image.new('RGB', (canvas[0] * 3, (canvas[1] + 22) * len(palette_ids)), '#303038')
        draw = ImageDraw.Draw(contact)
        for row_index, palette in enumerate(palette_ids):
            for column, name in enumerate(sample_names):
                image = native(root, name, palette)
                xy = (column * canvas[0], row_index * (canvas[1] + 22) + 22)
                contact.paste(image, xy, image)
                draw.text((xy[0] + 4, xy[1] - 19), f'{name} pal {palette}', fill='white')
        contact.save(root / 'review/native_palette_contact.png')
        jobs, signatures, represented = [], {}, set()
        aliases = sources['pixel_aliases']
        for descriptor, binding in sources['bindings'].items():
            for action_name, action in binding['actions'].items():
                for view, steps in action['views'].items():
                    if not steps or all(step['frame'] is None for step in steps):
                        continue
                    assert all(step['frame'] is not None for step in steps)
                    if any(step['mirrored'] for step in steps):
                        continue
                    names = [aliases.get(step['frame'], step['frame']) for step in steps]
                    signature = tuple(names)
                    use = dict(descriptor_id=int(descriptor), action=action_name, view=int(view),
                               native_frames=[step['frame'] for step in steps], native_group=action['native_group'])
                    if signature in signatures:
                        signatures[signature]['bindings'].append(use)
                        continue
                    job = dict(id=f'{action_name}_{view}_sheet', action=action_name, view=int(view),
                               frames=names, native_sequence=True, bindings=[use])
                    signatures[signature] = job
                    jobs.append(job)
                    represented.update(names)
        unused = set(sources['sources']) - represented - set(aliases)
        grouped = {}
        for name in sorted(unused):
            match = re.fullmatch(r'm\d+([a-z])([a-z])([0-7])', name)
            assert match, name
            grouped.setdefault((match[1], int(match[3])), []).append(name)
        for (code, view), names in grouped.items():
            jobs.append(dict(id=f'unused_{code}_{view}_sheet', action='unused_native', native_art_action=code,
                             view=view, frames=names, native_sequence=False, bindings=[]))
        assert {name for job in jobs for name in job['frames']} == set(sources['sources']) - set(aliases)
        for job in jobs:
            placed = [images[name].resize(tuple(v * 2 for v in canvas), Image.Resampling.NEAREST)
                      for name in job['frames']]
            boxes = [image.getbbox() for image in placed]
            assert all(boxes), 'Empty native artwork requires a transparent-frame export path'
            crop2 = [min(b[0] for b in boxes) - 4, min(b[1] for b in boxes) - 4,
                     max(b[2] for b in boxes) + 4, max(b[3] for b in boxes) + 4]
            crop = [v / 2 for v in crop2]
            cell = [(crop2[2] - crop2[0]) // 2, (crop2[3] - crop2[1]) // 2]
            sampling, _, columns, rows_count, envelope = best_grid(len(placed), *cell)
            colour = Image.new('RGBA', (columns * cell[0] * 2, rows_count * cell[1] * 2))
            outline = Image.new('RGB', colour.size, 'white')
            for i, image in enumerate(placed):
                piece = image.crop(crop2)
                reconstruction = Image.new('RGBA', image.size)
                reconstruction.paste(piece, crop2[:2])
                assert np.array_equal(image, reconstruction), job['frames'][i]
                xy = (i % columns * piece.width, i // columns * piece.height)
                colour.paste(piece, xy)
                inside = np.asarray(piece.getchannel('A'))[::2, ::2] > 0
                boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
                guide = np.full((*inside.shape, 3), 255, np.uint8)
                guide[boundary] = 0
                outline.paste(Image.fromarray(guide).resize(piece.size, Image.Resampling.NEAREST), xy)
            paths = [root / f'references/{job["id"]}_native.png', root / f'references/{job["id"]}_outline.png']
            colour.save(paths[0])
            outline.save(paths[1])
            roles = ['untouched_native_colour_complete_animation', 'matching_outline_only_geometry']
            if number == 528:
                name = job['frames'][0]
                candidates = [old / f'final_cleaned/{name}.png', old / f'cleaned/{name}.png']
                detail_source = next(p for p in candidates if p.exists())
                detail = Image.open(detail_source).convert('RGBA')
                box = detail.getbbox()
                detail_path = root / f'references/{job["id"]}_detail.png'
                detail.crop((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6)).save(detail_path)
                paths.append(detail_path)
                roles.append('same_family_detailed_appearance_only')
                job['detail_source'] = dict(path=rel(detail_source), sha256=sha(detail_source))
            requested = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows_count * cell[1] * 2.8)]
            prompt = (CONTEXT + '\n\n' +
                      f'Restore ONE COMPLETE native {row["label"]} {job["action"]} animation at stored rotation '
                      f'{job["view"]}. Exactly {len(placed)} original steps together on ONE returned sheet: '
                      f'{columns} columns by {rows_count} rows, chronological row-major order '
                      f'{", ".join(job["frames"])}. Do not omit native repeats/holds; identical original steps '
                      'retain identical poses. No extra panels, interpolated steps, invented cycle or split return.\n'
                      'Image 1 is untouched native colour and alpha: the sole authority for every step\'s pose, '
                      'anatomy, proportions, visible materials, equipment, camera, colours, scale and placement.\n'
                      'Image 2 is the ACTUALLY ATTACHED matching separate OUTLINE-ONLY anatomy sheet, derived '
                      'only from inward native alpha boundaries and transparent gaps. Its thin black contours '
                      'on white guide GEOMETRY ONLY. Both interior and exterior are white; they supply no shading '
                      'or material colour. Never reproduce guide strokes, dark grooves or contrast bands.\n')
            if len(paths) == 3:
                prompt += ('Image 3 is detailed previously restored artwork for this SAME family: appearance and '
                           'material finish ONLY. Preserve fine texture and natural lighting, never copy its pose, '
                           'altered bulk or proportions. Native colour and outline remain geometry authority.\n')
            else:
                prompt += ('BOOTSTRAP EXCEPTION: no adequate same-family detailed art exists yet. This first useful '
                           'complete native animation sheet establishes faithful detailed appearance from Images 1 '
                           'and 2; it will be inspected and attached as Image 3 on subsequent requests.\n')
            prompt += (f'Keep the original {row["label"]} design and every native action step. Trace each visible '
                       'limb/effect chain, its joint bends and near/far ownership, crossings, foreshortening, grips, '
                       'planted or raised extremities, head angle, body bob and all thin features. Do not introduce '
                       'humanoid feet or a humanoid gait into a floating elemental, quadruped, serpent or wisp. '
                       'Preserve native costume coverage, proportions and equipment; invent nothing.\n'
                       'Reconstruct rich fine material texture with continuous natural shading and the native '
                       'tonal weight. Keep clear contrast and fine detail. No enlarged pixel blocks, dithering, '
                       'waxy smoothing, blur, washed-out flattening, noisy pseudo-detail, sharpening halos, '
                       'exaggerated dark muscle grooves or copied outline bands.\n'
                       f'Generate only base palette {sources["base_palette"]}, as shown in Image 1. Other native '
                       'palettes will be derived after generation with enhanced-pixel material masks.\n'
                       f'Layout uses common native actor canvas {canvas}, pivot {pivot}, shared whole-animation '
                       f'union crop {crop} (exclusive right/bottom), cell size {cell} and 2-native-pixel alpha '
                       'padding. Keep exactly the same reversible native-coordinate placement for every step. '
                       'Never independently recenter, zoom, stretch, warp or fit individual silhouette bounds. '
                       'Retain every movement extreme and thin tip, with genuine transparent limb/effect gaps.\n'
                       f'Request a large {requested[0]}x{requested[1]} master, at least 2x actual generated detail '
                       'in both axes, preferably 2.2x or higher. The WHOLE cycle on one sheet takes priority: '
                       'retain every native step if output dimensions are smaller. Interpolation is not new detail. '
                       'Return one RGBA image with true transparent background and empty unused grid cells. '
                       'No grid, labels, paper, opaque or painted checkerboard, floor, cast shadow or matte spill.\n')
            if job['action'] in ('death', 'corpse'):
                prompt += ('Follow the original non-graphic falling/resting/dissipating sequence. Preserve its '
                           'effect/residue stages and detached particles; add no injuries or gore.\n')
            if not job['native_sequence']:
                prompt += ('These are unused original native images in their stored art order, retained without '
                           'adding any timing or playback binding. Do not invent playback.\n')
            prompt_path = root / f'prompts/{job["id"]}_v1.txt'
            prompt_path.write_text(prompt)
            job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=rows_count,
                       reference_scale=2, padding_native_px=2, logical_canvas=canvas, logical_pivot=pivot,
                       exact_native_offsets={name: [0, 0] for name in job['frames']},
                       planned_sampling=sampling, observed_envelope=list(envelope), requested_size=requested,
                       references=[rel(p) for p in paths], prompt=rel(prompt_path), prompt_sha256=sha(prompt_path),
                       prepared_assets=[dict(path=rel(p), role=role, sha256=sha(p)) for p, role in zip(paths, roles)],
                       bootstrap_exception=len(paths) == 2, status='pending', attempts=[])
        write(root / 'run.json', dict(schema_version=1, project=rel(root), source_project=rel(old),
              source_manifest_sha256=sha(root / 'sources.json'), status='prepared_generation_pending',
              method='packed_whole_animation_with_attached_outline_only', jobs=jobs,
              coverage=dict(native_files=len(sources['sources']), referenced_files=len(row['images']),
                            unused_files=len(sources['orphan_images']), aliases=len(aliases),
                            restored_files=0, accepted_files=0, complete=False),
              native_checks=dict(current_descriptors=True, current_group_bindings=True, native_hashes=True,
                                 exact_native_foreground_reconstruction=True, alpha_outline_only=True,
                                 full_frame_and_alias_coverage=True, native_timing_mirrors_scales_preserved=True),
              resolution_policy='whole_cycle_priority; report actual generated sampling separately from 2x export',
              installed=False))
        print(f'{family}: {len(sources["sources"])} native files; {len(jobs)} complete-sheet jobs; '
              f'{len(sources["orphan_images"])} unused; palettes {palette_ids}')


if __name__ == '__main__':
    prepare()
