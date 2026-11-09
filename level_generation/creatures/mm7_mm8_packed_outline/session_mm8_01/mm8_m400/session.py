"""MM8 session bridge for descriptor-backed complete sheets; shared tools stay read-only.

The shared packed preparer requires MM6 animations_by_palette/config metadata.
This bridge reads MM8 bindings directly and reuses its native decoder/grid planner.
"""
import argparse
import fcntl
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import yaml

REPO = Path(__file__).resolve().parents[5]
SESSION = Path(__file__).resolve().parent.parent
CREATURES = REPO / 'level_generation/creatures'
sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
from prepare_packed_outline import best_grid, native_2x
from whole_animation_resolution import DEFAULT_POLICY, METHOD

FAMILIES = ['m400', 'm404', 'm408', 'm412', 'm416', 'm420', 'm424', 'm428']
CONTEXT = ('TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration of an '
           'EXISTING Might and Magic VIII (MM8) fantasy role-playing game sprite asset, using the supplied original '
           'animation bitmaps. Restore the existing fantasy-game character and its original animation; preserve its '
           'native costume, material coverage, anatomy and poses. The request is game-art restoration.')
ROLES = ['untouched_native_complete_animation', 'outline_only_geometry_no_shading',
         'detailed_same_family_appearance_not_pose']


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(REPO))


def scopes(sources):
    jobs, seen, represented = [], {}, set()
    for descriptor, binding in sources['bindings'].items():
        for action in ['walk', 'standing', 'attack', 'attack2', 'hit', 'fidget', 'death', 'corpse']:
            for view, steps in binding['actions'][action]['views'].items():
                if not steps or any(step['mirrored'] for step in steps) or all(step['frame'] is None for step in steps):
                    continue
                assert all(step['frame'] is not None for step in steps), 'Mixed empty sequence needs explicit handling'
                names = [step['frame'] for step in steps]
                signature = tuple(names)
                use = dict(descriptor_id=int(descriptor), action=action, view=int(view),
                           native_group=binding['actions'][action]['native_group'], native_frames=names)
                if signature in seen:
                    seen[signature]['bindings'].append(use)
                    continue
                job_id = f'{action}_{view}_sheet'
                if any(job['id'] == job_id for job in jobs):
                    job_id = f'{action}_{view}_descriptor{descriptor}_sheet'
                job = dict(id=job_id, action=action, view=int(view), frames=names,
                           bindings=[use], native_sequence=True)
                seen[signature] = job
                jobs.append(job)
                represented.update(names)
    unused = defaultdict(list)
    for name in sorted(set(sources['sources']) - represented):
        match = re.fullmatch(r'm\d{3}([a-z])([a-z]+)([0-7])', name)
        assert match, name
        unused[(match[1], int(match[3]))].append(name)
    for (code, view), names in unused.items():
        jobs.append(dict(id=f'unused_{code}_{view}_sheet', action='unused_native', native_art_action=code,
                         view=view, frames=names, bindings=[], native_sequence=False))
    assert set(name for job in jobs for name in job['frames']) == set(sources['sources'])
    return jobs


def prepare(stem, groups, descriptor_rows, inventory):
    old = CREATURES / ('mm8_' + stem)
    root = SESSION / old.name
    out = root / 'redo_2x'
    if (out / 'run.json').exists():
        run = read(out / 'run.json')
        for job in run['jobs']:
            assert all(sha(REPO / item['path']) == item['sha256'] for item in job['prepared_assets'])
        print(old.name, 'resumed', len(run['jobs']), 'complete sheets')
        return
    sources = read(old / 'sources.json')
    inv = next(row for row in inventory if row['world'] == 'mm8' and stem + 'sa0' in row['standing_images'])
    assert sources['label'] == inv['label']
    assert set(sources['sources']) == set(inv['all_native_family_images'])
    assert set(map(int, sources['bindings'])) == {row['id'] for row in inv['descriptors']}
    assert sorted(map(int, sources['palette_sources'])) == inv['palettes']
    for descriptor, binding in sources['bindings'].items():
        assert descriptor_rows[descriptor] == binding['native_descriptor']
        for action in binding['actions'].values():
            assert groups[action['native_group'].lower()] == action['native_group_record']
    for source in [*sources['sources'].values(), *sources['palette_sources'].values()]:
        assert sha(REPO / source['path']) == source['sha256'], source['path']
    canvas = [max(source['size'][axis] for source in sources['sources'].values()) for axis in [0, 1]]
    assert all(not source['anchors'] or source['anchors'] == ['bottom-center'] for source in sources['sources'].values())
    sources.update(logical_canvas=canvas, logical_pivot=[canvas[0] / 2, canvas[1]])
    sources['descriptor_table']['sha256'] = sha(REPO / sources['descriptor_table']['path'])
    for folder in ['references', 'prompts', 'raw', 'review']:
        (out / folder).mkdir(parents=True, exist_ok=True)
    save(root / 'sources.json', sources)
    save(root / 'inventory.json', inv)
    native, offsets = {}, {}
    for name, source in sources['sources'].items():
        native[name], offsets[name] = native_2x(source, sources, sources['base_palette'])
    jobs = scopes(sources)
    for job in jobs:
        images = [native[name] for name in job['frames']]
        boxes = [image.getbbox() for image in images]
        assert all(boxes), 'Empty source needs explicit handling'
        crop2 = [min(box[0] for box in boxes)-4, min(box[1] for box in boxes)-4,
                 max(box[2] for box in boxes)+4, max(box[3] for box in boxes)+4]
        cell = [(crop2[2]-crop2[0]) // 2, (crop2[3]-crop2[1]) // 2]
        sampling, _, columns, rows, envelope = best_grid(len(images), *cell)
        colour = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
        outline = Image.new('RGB', colour.size, 'white')
        for index, image in enumerate(images):
            part = image.crop(crop2)
            reconstructed = Image.new('RGBA', image.size)
            reconstructed.paste(part, tuple(crop2[:2]))
            assert np.array_equal(np.array(image), np.array(reconstructed)), job['frames'][index]
            xy = (index % columns * part.width, index // columns * part.height)
            colour.paste(part, xy)
            inside = np.array(part.getchannel('A'))[::2, ::2] > 0
            edge = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[edge] = 0
            outline.paste(Image.fromarray(guide).resize(part.size, Image.Resampling.NEAREST), xy)
        paths = [out / 'references' / f'{job["id"]}_{role}.png' for role in ['native', 'outline', 'detail']]
        colour.save(paths[0])
        outline.save(paths[1])
        name = sources['pixel_aliases'].get(job['frames'][0], job['frames'][0])
        prior = old / 'redo_2x/cleaned' / (name + '.png')
        if not prior.exists():
            prior = old / 'cleaned' / (name + '.png')
        assert prior.exists(), prior
        detail = Image.open(prior).convert('RGBA')
        bounds = detail.getbbox()
        assert bounds
        detail = detail.crop((max(0, bounds[0]-6), max(0, bounds[1]-6),
                              min(detail.width, bounds[2]+6), min(detail.height, bounds[3]+6)))
        detail.save(paths[2])
        anatomy = ('Preserve shoulder–elbow–wrist–finger and hip–knee–ankle–toe chains, exact joint locations/bends, '
                   'near/far limb ownership, crossings, grips, foreshortening, planted/raised feet, head angle and body bob.')
        if stem == 'm408':
            anatomy = ('Preserve the winged serpent head/jaw/neck, long coiling body and tail, paired feathered wings, '
                       'wing-root/elbow/wrist/primary-feather chains, exact folded/spread/flapping wing positions, '
                       'near/far ownership and overlaps. No invented human limbs, legs or changed tail coils.')
        elif stem in ['m400', 'm404']:
            anatomy += ' Preserve reptilian muzzle, head crest/fringe, claws, scales, tail and exact native equipment.'
        else:
            anatomy += ' Preserve all native clothing coverage, garment hems, hair/headwear and equipment exactly.'
        target = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows * cell[1] * 2.8)]
        crop = [value / 2 for value in crop2]
        prompt = f'''{CONTEXT}

Generate exactly ONE COMPLETE {sources['label']} {job['action']} animation sprite sheet at stored rotation {job['view']}. ALL {len(images)} original steps together on ONE returned RGBA image, in {columns} columns by {rows} rows, chronological row-major order. Native order: {', '.join(job['frames'])}. Repeated native steps are deliberate holds/reuse and must retain identical poses, never invented in-between steps. A one-frame action is ONE SINGLE SPRITE, not a storyboard.
Image 1 is untouched, correctly paletted native colour and alpha. It controls EVERY step's pose, anatomy, proportions, camera, placement, equipment ownership/coverage and base colours.
Image 2 is the separate matching OUTLINE-ONLY anatomy guide. Thin inward alpha boundaries and transparent gaps guide GEOMETRY ONLY. White interior/exterior supply NO shading, contrast or texture. No internal contrast guides. Never reproduce black lines, copied guide bands or dark carved grooves in the art.
Image 3 is selected DETAILED SAME-FAMILY enhanced appearance. Preserve fine face/material detail, natural small-scale shading, scales, wrinkles, feather structure, cloth/leather grain, seams, rivets and metal wear wherever present. Borrow finish only; never copy its pose, altered bulk/proportions or extra equipment. Native colour and outlines retain geometry authority.
Anatomy in EVERY cell: {anatomy} Preserve every original step and motion extreme. No fused/swapped/extra limbs, missing tips, duplicated motion, new gait, broader muscles or costume redesign. Preserve native material colours and coverage, tonal weight and coherent natural baked lighting with fine texture and natural contrast. Avoid artificial blotchy bands, waxy/plastic smoothing, washed-out contrast, blur, flat untextured surfaces, pixel blocks, dithering, halos and noisy pseudo-detail.
Every step uses common native-coordinate union crop {crop}, cell {cell}, actor canvas {canvas}, pivot {sources['logical_pivot']} and 2 native pixels of transparent padding. Match native position and scale; never independently center, zoom, stretch or fit silhouettes. All thin features must remain complete. Use the full planned grid aspect {columns * cell[0]}:{rows * cell[1]}, without oversized exterior margins. Trailing empty grid cells remain transparent.
Generate ONLY base palette {sources['base_palette']} from Image 1. The detail reference supplies finish, never alternative palette colours. Material/recolour masks are authored after generation; Image 2 is not a recolour mask.
Request a LARGE {target[0]}x{target[1]} master with reconstructed detail, aiming for >=2x actual generated pixels per native pixel, preferably >=2.2x. Whole-animation sheets take priority: do not split this cycle or omit steps if the delivered raster is smaller. Interpolated enlargement does not count as generated detail.
Exactly one complete-animation RGBA return with genuine transparency outside silhouettes and in native gaps. No background, paper, painted checkerboard, labels, grid lines, ground or cast shadows. Native non-graphic falling/resting poses retain their original forms and add no injuries.
'''
        if not job['native_sequence']:
            prompt += 'These UNUSED native bitmaps are retained as art at this stored rotation, without new playback bindings.\n'
        prompt_path = out / 'prompts' / (job['id'] + '_v1.txt')
        prompt_path.write_text(prompt)
        job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=rows,
                   logical_canvas=canvas, reference_scale=2, padding_native_px=2,
                   planned_sampling=sampling, observed_envelope=list(envelope), requested_master=target,
                   references=[rel(path) for path in paths], reference_roles=ROLES,
                   appearance_source=dict(path=rel(prior), sha256=sha(prior)), prompt=rel(prompt_path),
                   status='pending', attempts=[], prepared_assets=[dict(path=rel(path), sha256=sha(path))
                                                                 for path in [*paths, prompt_path]])
        previews = [colour.resize((colour.width // 2, colour.height // 2), Image.Resampling.NEAREST),
                    outline.resize((outline.width // 2, outline.height // 2), Image.Resampling.NEAREST), detail]
        contact = Image.new('RGB', (sum(image.width for image in previews), max(image.height for image in previews)+24),
                            (48, 48, 48))
        x = 0
        for image in previews:
            contact.paste(image, (x, 24), image if image.mode == 'RGBA' else None)
            x += image.width
        ImageDraw.Draw(contact).text((4, 4), old.name + ' ' + job['id'] + ': native | outline ONLY | appearance', fill='white')
        contact.save(out / 'review' / (job['id'] + '_inputs.png'))
    save(out / 'run.json', dict(project=rel(root), source_project=rel(old), method=METHOD, status='prepared',
         source_game='MM8', native_bitmap_count=len(sources['sources']), unused_native_count=len(sources['orphan_images']),
         descriptor_ids=list(map(int, sources['bindings'])), palette_ids=inv['palettes'], jobs=jobs,
         padding_native_px=2, target_sampling=2.2, physical_export_tier=2, native_offsets=offsets,
         source_metadata=[dict(path=rel(old / name), sha256=sha(old / name)) for name in ['sources.json', 'redo_2x/manifest.json']],
         technical_preparation=dict(current_descriptors_match=True, current_frame_groups_match=True,
                                    source_and_palette_hashes_match=True, exact_native_rgba_reconstruction=True,
                                    full_unique_bitmap_coverage=True, outlines_inward_alpha_boundary_only=True),
         visual_acceptance=False, installed=False))
    save(out / 'processing.json', dict(preserve_matte_hued_materials=True, supplied_alpha_noise_floor=0,
                                      whole_animation_resolution_policy=DEFAULT_POLICY))
    print(json.dumps(dict(family=old.name, native_bitmaps=len(sources['sources']), jobs=len(jobs), palettes=inv['palettes'])))


def submission(stem, job_id):
    root = SESSION / ('mm8_' + stem)
    path = root / 'redo_2x/run.json'
    run = read(path)
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    refs = [REPO / path for path in job['references']]
    assert len(refs) == 3 and '_native.png' in refs[0].name and '_outline.png' in refs[1].name
    assert Image.open(refs[0]).size == Image.open(refs[1]).size
    assert all(sha(REPO / asset['path']) == asset['sha256'] for asset in job['prepared_assets'])
    prompt = (REPO / job['prompt']).read_text()
    assert prompt.startswith(CONTEXT)
    arguments = dict(prompt=prompt, referenced_image_paths=[str(ref) for ref in refs], transparent_background=True)
    assert arguments['referenced_image_paths'][1] == str(refs[1])
    attempt = dict(status='submitting', started_utc=datetime.now(timezone.utc).isoformat(), tool='image_gen.imagegen',
                   actual_tool_arguments=arguments, prompt_sha256=sha(REPO / job['prompt']),
                   actual_submitted_inputs=[dict(path=str(ref), role=role, sha256=sha(ref))
                                            for ref, role in zip(refs, ROLES)])
    job['attempts'].append(attempt)
    job['status'] = 'submitting'
    run['status'] = 'in_progress'
    save(path, run)
    print(json.dumps(dict(family=stem, job=job_id, arguments=arguments)))


def prepare_retry(stem, job_id, reason, padding):
    """Repack the entire native sequence after a demonstrated visual failure.

    Geometry-only retries retain adequate padding; clipping retries enlarge it.
    """
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    sources, run = read(root / 'sources.json'), read(out / 'run.json')
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    assert reason and job.get('selected_raw') and padding >= job['padding_native_px']
    assert job['attempts'][-1]['status'] == 'returned_unreviewed'
    revision = len(job['attempts']) + 1
    keys = ['native_crop', 'cell_native_size', 'columns', 'rows', 'padding_native_px',
            'references', 'prompt', 'prepared_assets', 'selected_raw']
    job.setdefault('layout_revisions', []).append({key: job[key] for key in keys})
    job['attempts'][-1]['visual_review'] = dict(status='rejected', reason=reason)
    images = [native_2x(sources['sources'][name], sources, sources['base_palette'])[0] for name in job['frames']]
    boxes = [im.getbbox() for im in images]
    crop2 = [min(box[0] for box in boxes) - padding * 2, min(box[1] for box in boxes) - padding * 2,
             max(box[2] for box in boxes) + padding * 2, max(box[3] for box in boxes) + padding * 2]
    cell = [(crop2[2] - crop2[0]) // 2, (crop2[3] - crop2[1]) // 2]
    sampling, _, columns, rows, envelope = best_grid(len(images), *cell)
    colour = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
    outline = Image.new('RGB', colour.size, 'white')
    for index, im in enumerate(images):
        part = im.crop(crop2)
        reconstructed = Image.new('RGBA', im.size)
        reconstructed.paste(part, tuple(crop2[:2]))
        assert np.array_equal(im, reconstructed)
        xy = (index % columns * part.width, index // columns * part.height)
        colour.paste(part, xy)
        inside = np.array(part.getchannel('A'))[::2, ::2] > 0
        edge = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
        guide = np.full((*inside.shape, 3), 255, np.uint8)
        guide[edge] = 0
        outline.paste(Image.fromarray(guide).resize(part.size, Image.Resampling.NEAREST), xy)
    refs = [out / 'references' / f'{job_id}_retry{revision}_{role}.png' for role in ['native', 'outline']]
    colour.save(refs[0])
    outline.save(refs[1])
    refs.append(REPO / job['references'][2])
    prompt = (REPO / job['prompt']).read_text()
    prompt = prompt.replace(f"in {job['columns']} columns by {job['rows']} rows", f'in {columns} columns by {rows} rows')
    crop = [value / 2 for value in crop2]
    target = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows * cell[1] * 2.8)]
    prompt = re.sub(r'Every step uses common native-coordinate union crop .*?\n',
        f"Every step uses common native-coordinate union crop {crop}, cell {cell}, actor canvas {sources['logical_canvas']}, "
        f"pivot {sources['logical_pivot']} and {padding} native pixels of transparent padding. Match native position and scale; "
        'never independently center, zoom, stretch or fit silhouettes. Keep every feather, beak, boot, claw, blade and tail tip complete. '
        f'Use the complete planned grid aspect {columns * cell[0]}:{rows * cell[1]}. Preserve this extra safety padding around every cell. '
        'No touching or overlapping neighbouring sprites. Trailing empty grid cells remain transparent.\n', prompt)
    prompt = re.sub(r'Request a LARGE \d+x\d+ master', f'Request a LARGE {target[0]}x{target[1]} master', prompt)
    prompt += f'Complete-cycle retry for reviewed issue: {reason} Restore the entire original cycle together again; keep all native steps.\n'
    prompt_path = out / 'prompts' / f'{job_id}_retry{revision}.txt'
    prompt_path.write_text(prompt)
    job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=rows,
               padding_native_px=padding, planned_sampling=sampling, observed_envelope=list(envelope),
               requested_master=target, references=[rel(path) for path in refs], prompt=rel(prompt_path),
               prepared_assets=[dict(path=rel(path), sha256=sha(path)) for path in [*refs, prompt_path]],
               status='retry_prepared', reviewed_generation_issue=reason)
    del job['selected_raw']
    save(out / 'run.json', run)
    previews = [colour.resize((colour.width // 2, colour.height // 2), Image.Resampling.NEAREST),
                outline.resize((outline.width // 2, outline.height // 2), Image.Resampling.NEAREST), Image.open(refs[2])]
    card = Image.new('RGB', (sum(im.width for im in previews), max(im.height for im in previews) + 24), (48, 48, 48))
    x = 0
    for im in previews:
        card.paste(im, (x, 24), im if im.mode == 'RGBA' else None)
        x += im.width
    ImageDraw.Draw(card).text((4, 4), stem + ' ' + job_id + ' retry: native | outline ONLY | appearance', fill='white')
    card.save(out / 'review' / f'{job_id}_retry{revision}_inputs.png')
    print(stem, job_id, 'complete-cycle retry prepared', padding)


def failure(stem, job_id, reason):
    path = SESSION / ('mm8_' + stem) / 'redo_2x/run.json'
    run = read(path)
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    assert job['attempts'] and job['attempts'][-1]['status'] == 'submitting'
    job['attempts'][-1].update(status='failed', reason=reason, finished_utc=datetime.now(timezone.utc).isoformat())
    job['status'] = 'failed'
    save(path, run)
    print(stem, job_id, 'failed:', reason)


def returned(stem, job_id, source):
    from sheet_checks import screen
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    path = out / 'run.json'
    run = read(path)
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    attempt = job['attempts'][-1]
    assert attempt['status'] == 'submitting'
    destination = out / 'raw' / f'{job_id}_v{len(job["attempts"])}.png'
    assert not destination.exists()
    shutil.copy2(source, destination)
    checks = screen(destination, job['cell_native_size'], [job['columns'], job['rows']], len(job['frames']))
    attempt.update(status='returned_unreviewed', raw=rel(destination), sha256=sha(destination),
                   original_output=str(source), actual_size=list(Image.open(destination).size),
                   static_screen=checks, finished_utc=datetime.now(timezone.utc).isoformat())
    job.update(status='returned_unreviewed', selected_raw=rel(destination))
    save(path, run)
    print(json.dumps(dict(family=stem, job=job_id, raw=rel(destination), size=attempt['actual_size'],
                          sampling=checks['nominal_grid_sampling_xy'], failures=checks['failures'],
                          warnings=checks['warnings'])))


def extract_returned(stem):
    """Use the shared extractor; seed thresholds identify cores without discarding alpha."""
    from extract_run import extract, connected_cells
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    run = read(out / 'run.json')
    policy = read(out / 'processing.json')
    selected = []
    for job in run['jobs']:
        existing = out / 'review' / (job['id'] + '_extraction.json')
        if not job.get('selected_raw'):
            continue
        if existing.exists() and read(existing)['raw'] == job['selected_raw']:
            continue
        if existing.exists():
            previous = read(existing)
            save(out / 'review' / 'history' / (job['id'] + '_' + previous['raw_sha256'][:12] + '_extraction.json'), previous)
        # Extraction only prepares a candidate. Native-coordinate pose, fragment,
        # material and edge review must still be completed before acceptance.
        raw = REPO / job['selected_raw']
        im = Image.open(raw).convert('RGBA')
        threshold = None
        grid_groups = stem == 'm424' and job['action'] == 'fidget'
        for candidate in [0, 4, 8, 16, 32, 64]:
            try:
                connected_cells(im, job, grid_groups=grid_groups, seed_alpha_threshold=candidate)
            except AssertionError:
                continue
            threshold = candidate
            break
        if threshold is None:
            print(stem, job['id'], 'extraction pending: coherent body count needs review')
            continue
        modes = policy.setdefault('component_grid_extraction_jobs' if grid_groups
                                  else 'connected_body_extraction_jobs', [])
        if job['id'] not in modes:
            modes.append(job['id'])
        policy.setdefault('component_seed_alpha_threshold_by_job', {})[job['id']] = dict(
            threshold=threshold, raw_sha256=sha(raw),
            reason='Candidate complete-sheet separation from returned alpha with exact native step count. '
                   'Assign every original alpha pixel once, including detached equipment, thin tips and '
                   'near-transparent scatter. Independent visual acceptance remains pending.')
        selected.append(job['id'])
    save(out / 'processing.json', policy)
    if selected:
        for job_id in selected:
            try:
                extract(rel(root), [job_id])
            except AssertionError as error:
                save(out / 'review' / (job_id + '_extraction_failure.json'), dict(
                    job=job_id, reason=str(error), status='candidate_extraction_failed',
                    visual_acceptance=False))
                print(stem, job_id, 'candidate extraction failed:', error)


def register_returned(stem):
    """Shared sheet-coordinate registration followed by existing MM8 material authoring."""
    import importlib.util
    from types import SimpleNamespace
    import register_packed_outline as packed_registration
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    source = read(root / 'sources.json')
    old = CREATURES / ('mm8_' + stem)
    # Existing MM8 material modules import their old process owner. Supply only the
    # read-only source access they use; all generated output belongs to this session.
    prior_process = sys.modules.get('process')
    sys.modules['process'] = SimpleNamespace(ROOT=root, queue=SimpleNamespace(REPO=REPO), save=save)
    spec = importlib.util.spec_from_file_location('session_mm8_materials', old / 'materials.py')
    materials = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials)
    materials.ROOT = root
    materials.REPO = REPO
    if prior_process is None:
        del sys.modules['process']
    else:
        sys.modules['process'] = prior_process
    settings = materials.fit() if stem == 'm400' else materials.settings()
    settings['implementation_source'] = dict(path=rel(old / 'materials.py'), sha256=sha(old / 'materials.py'))
    settings['visual_acceptance'] = False
    save(out / 'material_settings.json', settings)
    def coverage(clean, config):
        assert config['mask_kind'] == 'session_mm8_native_palette'
        if stem == 'm400':
            weights = materials.masks(clean)
            return Image.fromarray(np.dstack([weights, np.zeros(weights.shape[:2], np.uint8)]), 'RGB')
        return Image.fromarray(materials.masks(clean, settings), 'L')
    config = read(root / 'config.json')
    config['mask_kind'] = 'session_mm8_native_palette'
    config['material_source'] = settings['implementation_source']
    save(root / 'config.json', config)
    # Shared registration has MM6 mask schemas. This explicit in-process MM8
    # operation supplies the existing native-palette coverage; shared files stay unchanged.
    previous_mask = packed_registration.process_family.mask
    packed_registration.process_family.mask = coverage
    try:
        packed_registration.register(rel(root))
    finally:
        packed_registration.process_family.mask = previous_mask
    records = read(out / 'registration.json')
    for folder in ['previews', 'native_variants']:
        (out / folder).mkdir(exist_ok=True)
    for name, record in records.items():
        im = Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBA')
        if stem == 'm400':
            weights = materials.masks(im, name)
            mask = Image.fromarray(np.dstack([weights, np.zeros(weights.shape[:2], np.uint8)]), 'RGB')
        else:
            weights = materials.masks(im, settings, name=name) if stem == 'm424' else materials.masks(im, settings)
            mask = Image.fromarray(weights, 'L')
        mask.save(out / 'masks_2x' / (name + '.png'))
        for pal in map(int, source['palette_sources']):
            variant = materials.recolor(im, weights, pal, settings)
            assert np.array_equal(np.asarray(im)[:, :, 3], np.asarray(variant)[:, :, 3]), name
            if pal == source['base_palette']:
                assert np.array_equal(im, variant), name
            protected = weights.sum(axis=2) == 0 if weights.ndim == 3 else weights == 0
            assert np.array_equal(np.asarray(im)[protected], np.asarray(variant)[protected]), name
            variant.save(out / 'previews' / f'{name}_{pal}.png')
            original, _ = native_2x(source['sources'][name], source, pal)
            original.resize(tuple(source['logical_canvas']), Image.Resampling.NEAREST).save(
                out / 'native_variants' / f'{name}_{pal}.png')
        record['aligned_size_px'] = list(im.size)
        record['material_mask_sha256'] = sha(out / 'masks_2x' / (name + '.png'))
        record['aligned_sha256'] = sha(out / 'aligned_2x' / (name + '.png'))
        record['material_review_status'] = 'pending_all_palette_and_mask_poses'
    save(out / 'registration.json', records)
    print(json.dumps(dict(family=stem, physical_2x_masters=len(records),
                          native_palettes=list(map(int, source['palette_sources'])), visual_acceptance=False)))


def review_candidate(stem):
    """Reuse shared visual contacts and expose the saved native coordinates for manual annotation."""
    from review_complete_sheets import contacts
    from review_detail_and_alpha import review
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    contacts(rel(root))
    review(rel(root))
    sources, run, records = read(root / 'sources.json'), read(out / 'run.json'), read(out / 'registration.json')
    grids = []
    for job in run['jobs']:
        if not job.get('selected_raw') or job['frames'][0] not in records:
            continue
        name = job['frames'][0]
        record = records[name]
        # A shared native canvas is retained. The grid is a measuring aid only;
        # neither side is independently fitted to its silhouette.
        native, _ = native_2x(sources['sources'][name], sources, sources['base_palette'])
        enhanced = Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBA')
        origin = record['canvas_origin_px']
        start = [min(0, origin[i]) for i in range(2)]
        end = [max(native.size[i], origin[i] + enhanced.size[i]) for i in range(2)]
        width, height = [end[i] - start[i] for i in range(2)]
        panel = Image.new('RGB', (width * 2 + 50, height + 40), (40, 43, 41))
        draw = ImageDraw.Draw(panel)
        for side, art in enumerate([native, enhanced]):
            px, py = 20 + side * (width + 10), 30
            pos = [0, 0] if side == 0 else origin
            panel.paste(art, (px + pos[0] - start[0], py + pos[1] - start[1]), art)
            for axis, extent in [(0, width), (1, height)]:
                first = math.ceil(start[axis] / 40) * 40
                for coord in range(first, end[axis], 40):
                    at = coord - start[axis]
                    xy = (px + at, py, px + at, py + height) if axis == 0 else (px, py + at, px + width, py + at)
                    draw.line(xy, fill=(75, 82, 78))
                    draw.text((px + at + 1, py + 1) if axis == 0 else (px + 1, py + at + 1),
                              str(coord / 2), fill=(175, 190, 180))
            draw.text((px, 5), job['id'] + (' native 2x' if side == 0 else ' registered 2x'), fill='white')
        path = out / 'review' / (job['id'] + '_landmark_grid.png')
        panel.save(path)
        grids.append(dict(job=job['id'], frame=name, path=rel(path), sha256=sha(path),
                          panel_origins=[[20, 30], [width + 30, 30]], physical_origin=start,
                          pixels_per_native_pixel=2, registration_sha256=sha(out / 'registration.json')))
    save(out / 'review' / 'landmark_grids.json', dict(status='manual_review_pending', grids=grids))


def review_material_candidates(stem):
    """MM8 palette adapter: native-coordinate palette/mask poses and actual delivered pixels."""
    sys.path.insert(0, str(CREATURES / 'mm6_peasants'))
    from package_family import overlay, edge_stats
    from annotate_packed_body import points
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    sources, run, records = read(root / 'sources.json'), read(out / 'run.json'), read(out / 'registration.json')
    palettes = list(map(int, sources['palette_sources']))
    palette_pages, pixel_pages, pixel_samples, seen = [], [], [], set()
    pixel_page = Image.new('RGB', (1536, 1540), (45, 45, 45))
    pixel_count = 0
    for job in run['jobs']:
        if not all(name in records for name in job['frames']):
            continue
        unique = list(dict.fromkeys(job['frames']))
        bounds = []
        for name in unique:
            native, _ = native_2x(sources['sources'][name], sources, sources['base_palette'])
            bounds.append([v / 2 for v in native.getbbox()])
            im = Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBA')
            origin = records[name]['canvas_origin_px']
            bounds.append([(v + origin[i % 2]) / 2 for i, v in enumerate(im.getbbox())])
        crop = [math.floor(min(b[0] for b in bounds))-4, math.floor(min(b[1] for b in bounds))-4,
                math.ceil(max(b[2] for b in bounds))+4, math.ceil(max(b[3] for b in bounds))+4]
        w, h = crop[2]-crop[0], crop[3]-crop[1]
        columns = len(palettes)*2+1
        per_page = max(1, 1650 // (h+24))
        for start in range(0, len(unique), per_page):
            names = unique[start:start+per_page]
            panel = Image.new('RGB', (columns*(w+4), len(names)*(h+24)+28), (40,43,41))
            draw = ImageDraw.Draw(panel)
            draw.text((3,3), job['id']+' | native/restored for each palette; last column material mask | native 1x', fill='white')
            for row, name in enumerate(names):
                origin = records[name]['canvas_origin_px']
                box = [crop[i]*2-origin[i%2] for i in range(4)]
                images = []
                for pal in palettes:
                    native, _ = native_2x(sources['sources'][name], sources, pal)
                    images.append(native.crop([v*2 for v in crop]).resize((w,h), Image.Resampling.NEAREST))
                    im = Image.open(out/'previews'/f'{name}_{pal}.png').convert('RGBA').crop(box)
                    images.append(im.convert('RGBa').resize((w,h), Image.Resampling.LANCZOS).convert('RGBA'))
                im = Image.open(out/'aligned_2x'/(name+'.png')).convert('RGBA')
                mask = Image.open(out/'masks_2x'/(name+'.png'))
                if mask.mode == 'RGB':
                    mask = Image.fromarray(np.dstack([np.array(mask), np.zeros((mask.height,mask.width), np.uint8)]), 'RGBA')
                images.append(overlay(im,mask).crop(box).convert('RGBa').resize((w,h),Image.Resampling.LANCZOS).convert('RGBA'))
                for col, image in enumerate(images):
                    px, py = col*(w+4),28+row*(h+24)
                    panel.paste(image,(px,py),image)
                    label = f'{name} {palettes[col//2]} '+('native' if col%2==0 else 'restored') if col<len(palettes)*2 else name+' mask'
                    draw.text((px,py+h+2),label,fill='white')
            path = out/'review'/f'{job["id"]}_palettes_{start//per_page}.png'
            panel.save(path)
            palette_pages.append(dict(job=job['id'],frames=names,palettes=palettes,path=rel(path),sha256=sha(path),crop=crop))
        report = read(out/'review'/(job['id']+'_extraction.json'))
        for frame in report['frames']:
            name = frame['frame']
            if name in seen:
                continue
            seen.add(name)
            path = REPO/frame['clean_path']
            im = Image.open(path).convert('RGBA')
            y,x = np.where(np.array(im.getchannel('A'))>=128)
            cap = points(im, 2)['body_cap']
            centers = [(cap[0],cap[1]+min(48,im.height*.15)), (float(np.median(x)),float(np.median(y))),
                       edge_stats(im, read(root/'config.json')['matte'])['position']]
            bx, by = (pixel_count%2)*768, ((pixel_count//2)%10)*154
            draw = ImageDraw.Draw(pixel_page)
            for i,(label,center) in enumerate(zip(['head/body cap','material interior','alpha contour'],centers)):
                cx,cy = map(round,center)
                rect = [cx-64,cy-64,cx+64,cy+64]
                patch = im.crop(rect)
                for side,bg in enumerate(['#262a28','#eee9df']):
                    background = Image.new('RGBA',(128,128),bg)
                    background.alpha_composite(patch)
                    pixel_page.paste(background,(bx+i*256+side*128,by+22))
                draw.text((bx+i*256+2,by+3),name+' '+label,fill='white')
                pixel_samples.append(dict(frame=name,job=job['id'],source=rel(path),source_sha256=sha(path),rect=rect,
                                          page=len(pixel_pages),pixel_scale=1))
            pixel_count+=1
            if pixel_count%20==0:
                dest=out/'review'/f'all_pose_detail_100pct_{len(pixel_pages):02d}.png'
                pixel_page.save(dest)
                pixel_pages.append(dict(path=rel(dest),sha256=sha(dest)))
                pixel_page=Image.new('RGB',(1536,1540),(45,45,45))
    if pixel_count%20:
        dest=out/'review'/f'all_pose_detail_100pct_{len(pixel_pages):02d}.png'
        pixel_page.crop((0,0,1536,math.ceil((pixel_count%20)/2)*154)).save(dest)
        pixel_pages.append(dict(path=rel(dest),sha256=sha(dest)))
    save(out/'review'/'all_palette_mask_poses.json',dict(status='visual_review_pending',pages=palette_pages,
         frames=sorted(seen),native_pixel_scale=1,registration_sha256=sha(out/'registration.json')))
    save(out/'review'/'all_pose_detail_100pct.json',dict(status='visual_review_pending',pages=pixel_pages,
         samples=pixel_samples,frames=sorted(seen),delivered_pixel_scale=1))
    print(json.dumps(dict(family=stem,material_pose_count=len(seen),palette_mask_pages=len(palette_pages),detail_pages=len(pixel_pages))))


def export_candidate(stem):
    """Reuse the shared shelf packer and exact placement checks with MM8 descriptor metadata."""
    import copy
    import importlib.util
    sys.path.insert(0, str(CREATURES))
    from exact_placement import export_placement, validate_manifest, validate_animation_bindings
    packer_path = CREATURES / 'mm6_goblin/direct_front_final/package.py'
    sys.path.insert(0, str(packer_path.parent))
    spec = importlib.util.spec_from_file_location('session_shared_sprite_packer', packer_path)
    packer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packer)
    root = SESSION / ('mm8_' + stem)
    out = root / 'redo_2x'
    sources, records, run = read(root / 'sources.json'), read(out / 'registration.json'), read(out / 'run.json')
    settings = read(out / 'material_settings.json')
    for folder in ['atlas', 'runtime_aligned_2x', 'runtime_masks_2x', 'trimmed_2x', 'trimmed_masks_2x']:
        (out / folder).mkdir(exist_ok=True)
    tiles, mask_tiles, frames = {}, {}, {}
    aliases = sources['pixel_aliases']
    for name, record in records.items():
        if name in aliases:
            continue
        source = sources['sources'][name]
        assert sha(REPO / source['path']) == source['sha256']
        im = Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBA')
        mask = Image.open(out / 'masks_2x' / (name + '.png'))
        assert mask.size == im.size
        pixels, weights = np.array(im), np.array(mask)
        solid = pixels[:, :, 3] > 0
        distance, nearest = ndimage.distance_transform_edt(~solid, return_indices=True)
        ring = (distance <= 3) & ~solid
        pixels[:, :, :3][~solid] = 0
        pixels[:, :, :3][ring] = pixels[nearest[0], nearest[1], :3][ring]
        weights[~solid] = 0
        weights[ring] = weights[nearest[0], nearest[1]][ring]
        im, mask = Image.fromarray(pixels), Image.fromarray(weights, mask.mode)
        im.save(out / 'runtime_aligned_2x' / (name + '.png'))
        mask.save(out / 'runtime_masks_2x' / (name + '.png'))
        bounds = im.getchannel('A').getbbox()
        box = [max(0, bounds[0]-4), max(0, bounds[1]-4), min(im.width, bounds[2]+4), min(im.height, bounds[3]+4)]
        tile, mt = im.crop(box), mask.crop(box)
        for item, original in [(tile, im), (mt, mask)]:
            rebuilt = Image.new(original.mode, original.size)
            rebuilt.paste(item, box[:2])
            assert np.array_equal(rebuilt, original), name
        tile.save(out / 'trimmed_2x' / (name + '.png'))
        mt.save(out / 'trimmed_masks_2x' / (name + '.png'))
        padded = Image.new('RGBA', (tile.width + 32, tile.height + 32))
        padded.paste(tile, (16, 16))
        tiles[name], mask_tiles[name] = padded, mt
        exact, origin, correction = export_placement(sources['logical_canvas'], source['size'],
            run['native_offsets'][name][:2], record['canvas_origin_px'])
        frames[name] = dict(source=name + '.bmp', source_canvas=source['size'], logical_size=source['size'],
            native_offset=exact, registration_native_offset=run['native_offsets'][name][:2],
            anchor_correction_px=correction, crop_origin_px=[origin[i]+box[i] for i in range(2)],
            crop_in_aligned_px=box, aligned_canvas_origin_px=origin, aligned_canvas_size_px=list(im.size),
            source_palette=sources['base_palette'], referenced=source['referenced'],
            raw_path=record['raw_path'], effective_sampling_xy=record['effective_sampling_xy'])
        for pal in map(int, sources['palette_sources']):
            variant = np.array(Image.open(out / 'previews' / f'{name}_{pal}.png'))
            assert np.array_equal(variant[:, :, 3], pixels[:, :, 3]), name
            if pal == sources['base_palette']:
                assert np.array_equal(variant[solid], pixels[solid]), name
    assert tiles
    groups, current = [], {}
    for name, tile in sorted(tiles.items(), key=lambda item: (-item[1].height, item[0])):
        assert tile.width + 2 <= 2048 and tile.height + 2 <= 2048, name
        trial = dict(current, **{name: tile})
        base, _ = packer.pack_atlas(trial, 2048)
        if base.height > 2048:
            assert current
            groups.append(current)
            current = {name: tile}
        else:
            current = trial
    if current:
        groups.append(current)
    pages = []
    mask_mode = next(iter(mask_tiles.values())).mode
    for page, group in enumerate(groups):
        base, positions = packer.pack_atlas(group, 2048)
        mask = Image.new(mask_mode, base.size)
        for name, rect in positions.items():
            tile = mask_tiles[name]
            xywh = [rect[0]+16, rect[1]+16, tile.width, tile.height]
            mask.paste(tile, xywh[:2])
            frames[name].update(page=page, atlas_xywh=xywh)
            box = (xywh[0], xywh[1], xywh[0]+xywh[2], xywh[1]+xywh[3])
            assert np.array_equal(base.crop(box), Image.open(out / 'trimmed_2x' / (name + '.png'))), name
            assert np.array_equal(mask.crop(box), tile), name
        bp, mp = f'atlas/base_{page}.png', f'atlas/mask_{page}.png'
        base.save(out / bp)
        mask.save(out / mp)
        pages.append(dict(base=bp, mask=mp, size=list(base.size), base_format='RGBA8',
            mask_format='RGB8' if mask_mode == 'RGB' else 'R8', base_color_space='sRGB',
            mask_color_space='linear coverage', gutter_px=16, mipmaps=False,
            base_sha256=sha(out / bp), mask_sha256=sha(out / mp)))
    for alias, canonical in aliases.items():
        if canonical not in frames:
            continue
        assert sources['sources'][alias]['pixel_hash'] == sources['sources'][canonical]['pixel_hash']
        frames[alias] = dict(copy.deepcopy(frames[canonical]), source=alias + '.bmp', pixel_alias_of=canonical,
            referenced=sources['sources'][alias]['referenced'])
    missing = sorted(set(sources['sources']) - set(frames))
    manifest = dict(schema_version=1, creature='mm8:' + stem, label=sources['label'],
        status='partial_candidate' if missing else 'awaiting_visual_acceptance', pixels_per_logical_pixel=2,
        logical_canvas=sources['logical_canvas'], logical_pivot=sources['logical_pivot'], anchor='bottom-center',
        frames=frames, pages=pages, animations=copy.deepcopy(sources['bindings']), variants=settings,
        regions=settings['regions'], missing_frames=missing, pixel_aliases=aliases, source_manifest='../sources.json',
        generation_manifest='run.json', registration_manifest='registration.json', method=run['method'],
        visual_acceptance=False, installed=False,
        filter_policy='One uniform scale per complete view; premultiplied Lanczos; 3px hidden RGB/mask bleed; 16px gutters; no mipmaps.')
    assert not validate_manifest(manifest, records)
    # Shared binding validator accepts palette-indexed actions. Here its index is
    # the descriptor ID, which also distinguishes duplicate native palette bindings.
    actions = {key: copy.deepcopy(actor['actions']) for key, actor in sources['bindings'].items()}
    for descriptor_actions in actions.values():
        for action in descriptor_actions.values():
            native = action['native_group_record']
            action['native_length_raw'] = native.get('animation_length_raw', 0)
            action['sequence_ms'] = sum(frame['frame_length_raw'] * 62.5 for frame in native['frames'])
            for steps in action['views'].values():
                for step in steps:
                    step['native_scale'] = step['scale']
            if action['native_group'].lower() == 'null':
                assert all(all(step['frame'] is None for step in steps) for steps in action['views'].values())
                action['no_image'] = True
                action['views'] = {str(view): [] for view in range(8)}
    first = next(iter(actions))
    proxy = dict(animations_by_palette=actions, animations=actions[first], frames=sources['sources'],
        variants={first: dict(exact_base_bypass=True)}, native_group_bindings={key: dict(actions={
        name: action['native_group_record'] for name, action in actor['actions'].items()})
        for key, actor in sources['bindings'].items()})
    binding_errors = validate_animation_bindings(proxy)
    assert not binding_errors, binding_errors
    save(out / 'draft_manifest.json', manifest)
    save(out / 'review/export_checks.json', dict(full_coverage=not missing, restored_frames=len(frames),
        expected_native_frames=len(sources['sources']), missing_frames=missing, exact_native_anchors=True,
        exact_native_animation_bindings=True, exact_crop_reconstruction=True, exact_atlas_extraction=True,
        base_mask_placement_identical=True, base_bypass_exact=True, all_variant_alpha_unchanged=True,
        packer=dict(path=rel(packer_path), sha256=sha(packer_path)), visual_review_complete=False, installed=False))
    print(json.dumps(dict(family=stem, exported=len(frames), missing=len(missing), atlas_pairs=len(pages),
                          status=manifest['status'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'retry', 'submission', 'failure', 'returned', 'extract', 'register', 'review', 'materials_review', 'export'])
    parser.add_argument('--family', choices=FAMILIES, action='append')
    parser.add_argument('--job', default='walk_0_sheet')
    parser.add_argument('--reason')
    parser.add_argument('--source')
    parser.add_argument('--padding', type=int, default=8)
    args = parser.parse_args()
    if args.operation in ['retry', 'submission', 'failure', 'returned']:
        assert args.family and len(args.family) == 1
        attempt_lock = open(SESSION / ('mm8_' + args.family[0]) / 'redo_2x' / 'run.lock', 'a')
        fcntl.flock(attempt_lock.fileno(), fcntl.LOCK_EX)
    if args.operation == 'prepare':
        tables = [REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml',
                  *sorted((REPO / 'assets_dev/engine/rendering/sprite_frames/monsters').glob('*.yml'))]
        groups = {group['sprite_name'].lower(): group for table in tables
                  for group in yaml.load(table.read_text(), Loader=yaml.CSafeLoader)['sprites']}
        descriptors = {row.split('\t')[0]: row.split('\t') for row in
                       (REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt').read_text().splitlines()}
        inventory = read(CREATURES / 'remaining_inventory.json')['families']
        for stem in args.family or FAMILIES:
            prepare(stem, groups, descriptors, inventory)
    elif args.operation == 'submission':
        assert args.family and len(args.family) == 1
        submission(args.family[0], args.job)
    elif args.operation == 'retry':
        assert args.family and len(args.family) == 1 and args.reason
        prepare_retry(args.family[0], args.job, args.reason, args.padding)
    elif args.operation == 'failure':
        assert args.family and len(args.family) == 1 and args.reason
        failure(args.family[0], args.job, args.reason)
    elif args.operation in ['extract', 'register', 'review', 'materials_review', 'export']:
        for stem in args.family or FAMILIES:
            dict(extract=extract_returned, register=register_returned, review=review_candidate,
                 materials_review=review_material_candidates, export=export_candidate)[args.operation](stem)
    else:
        assert args.family and len(args.family) == 1 and args.source
        returned(args.family[0], args.job, Path(args.source))
