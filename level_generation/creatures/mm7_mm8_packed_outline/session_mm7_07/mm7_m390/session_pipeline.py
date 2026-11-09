"""Local MM7 session orchestration; shared tools and prior projects remain read-only.

The shared packed preparer expects MM6 metadata and P-mode BMPs. MM7 stores descriptor
directions and Roc's indexed BMPs open in Pillow as L. This session uses those exact
index bytes and native descriptor bindings, then reuses shared extraction/registration.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import sys
import os
import fcntl
import contextlib
import io
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = Path('/home/pjasicek/github/OpenYAMM')
CREATURES = REPO / 'level_generation/creatures'
STAGE = CREATURES / 'mm7_mm8_packed_outline/session_mm7_07'
SHARED = CREATURES / 'mm6_remaining/redo_2x'
sys.path.insert(0, str(SHARED))
from prepare_packed_outline import best_grid
from whole_animation_resolution import METHOD, DEFAULT_POLICY

FAMILIES = ['m390', 'm394', 'm398', 'm402', 'm406', 'm410', 'm414', 'm418']
HEADER = ('TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration of an '
          'EXISTING Might and Magic VII (MM7) fantasy role-playing game sprite asset, using the supplied original '
          'animation bitmaps. Restore the existing fantasy-game character and its original animation; preserve its '
          'native costume, material coverage, anatomy and poses. The request is game-art restoration.')


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextmanager
def job_lock(root):
    with (root / 'redo_2x/.stage.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def native_2x(source, sources, palette):
    path = REPO / source['path']
    assert sha(path) == source['sha256']
    image = Image.open(path)
    assert image.mode in ('P', 'L') and list(image.size) == source['size']
    indices = np.array(image)
    palette_source = sources['palette_sources'][str(palette)]
    palette_path = REPO / palette_source['path']
    assert sha(palette_path) == palette_source['sha256']
    colors = np.frombuffer(palette_path.read_bytes()[:768], np.uint8).reshape(256, 3)
    pixels = np.dstack((colors[indices], (indices != source['transparency_index']).astype(np.uint8) * 255))
    pixels[indices == source['transparency_index']] = 0
    native = Image.fromarray(pixels)
    canvas = sources['logical_canvas']
    offset = [(canvas[0] - native.width) / 2, canvas[1] - native.height]
    placed = Image.new('RGBA', tuple(v * 2 for v in canvas))
    placed.paste(native.resize((native.width * 2, native.height * 2), Image.Resampling.NEAREST),
                 tuple(round(v * 2) for v in offset))
    assert np.count_nonzero(np.array(placed)[:, :, 3]) == np.count_nonzero(pixels[:, :, 3]) * 4
    return placed, offset


def scopes(manifest, sources, stem):
    jobs, seen, represented = [], {}, set()
    for descriptor, animations in manifest['descriptor_animations'].items():
        for action in ['walk', 'standing', 'attack', 'shoot', 'hit', 'fidget', 'death', 'corpse']:
            for view, steps in animations[action]['directions'].items():
                if not steps or any(step['mirror'] for step in steps):
                    continue
                names = [step['frame'] for step in steps]
                signature = tuple(names)
                binding = dict(descriptor_id=int(descriptor), action=action, view=int(view), native_frames=names)
                if signature in seen:
                    seen[signature]['bindings'].append(binding)
                    continue
                job_id = f'{action}_{view}_sheet'
                if any(job['id'] == job_id for job in jobs):
                    job_id = f'{action}_{view}_descriptor{descriptor}_sheet'
                job = dict(id=job_id, action=action, view=int(view), frames=names,
                           bindings=[binding], native_sequence=True)
                seen[signature] = job
                jobs.append(job)
                represented.update(names)
    unused = {}
    for name in sorted(set(sources['sources']) - represented):
        match = re.fullmatch(stem + r'([a-z])([a-z]+)([0-7])', name)
        assert match, name
        unused.setdefault((match[1], int(match[3])), []).append(name)
    for (code, view), names in unused.items():
        jobs.append(dict(id=f'unused_{code}_{view}_sheet', action='unused_native', view=view,
                         frames=names, bindings=[], native_sequence=False))
    assert set(name for job in jobs for name in job['frames']) == set(sources['sources'])
    return jobs


def anatomy(stem):
    chains = ('Preserve shoulder/elbow/wrist/finger and hip/knee/ankle/toe chains, joint bends, lengths, '
              'near/far ownership, foreshortening, foot lifts/contacts, head rotation, body bob and equipment grips.')
    if stem == 'm390':
        return ('Preserve both wing-root/elbow/wrist/primary-feather chains, feather fans, folds and flapping '
                'extremes, head/beak/body/tail-feather positions and two taloned legs. No human arms or new flight steps.')
    if stem == 'm394':
        return ('Preserve native head/jaw/neck/body/tail, exact fin projections and near/far ownership, segmented '
                'body curvature, head direction, mouth/teeth and swimming/recoil/disappearance steps. No new fins or limbs.')
    if stem == 'm402':
        return ('Preserve all EIGHT multi-jointed leg chains, exact projections, joint bends, near/far ownership, '
                'crossings, raised/planted hooked tips, abdomen/cephalothorax proportions, body bob, eyes and mandibles.')
    if stem == 'm418':
        chains += (' Preserve huge hood-like head, dark maw/teeth, dorsal spines, three curved hand claws, thin '
                   'curved tail and native occlusions. No invented eyes or human face.')
    return chains


def prepare(stem):
    original = CREATURES / ('mm7_' + stem)
    root = STAGE / original.name
    out = root / 'redo_2x'
    if (out / 'run.json').exists():
        run = read(out / 'run.json')
        for job in run['jobs']:
            assert all(sha(REPO / asset['path']) == asset['sha256'] for asset in job['prepared_assets'])
        print(original.name, 'resumed', len(run['jobs']))
        return
    for folder in ['references', 'prompts', 'raw', 'review', 'cleaned', 'aligned_2x', 'masks_2x']:
        (out / folder).mkdir(parents=True, exist_ok=True)
    config, sources, manifest = (read(original / name) for name in ['config.json', 'sources.json', 'manifest.json'])
    config.update(family=stem, title='MM7 ' + config['label'], mask_kind='none', matte='magenta', source_project=str(original))
    canvas = sources['logical_canvases'][0]
    sources.update(logical_canvas=canvas, logical_pivot=[canvas[0] / 2, canvas[1]], pixel_aliases={})
    save(root / 'config.json', config)
    save(root / 'sources.json', sources)
    for name in ['manifest.json', 'variants.json']:
        shutil.copy2(original / name, root / name)
    natives = {name: native_2x(source, sources, sources['base_palette'])[0]
               for name, source in sources['sources'].items()}
    jobs = scopes(manifest, sources, stem)
    for job in jobs:
        images = [natives[name] for name in job['frames']]
        bounds = [image.getbbox() for image in images]
        crop = [min(box[0] for box in bounds) - 4, min(box[1] for box in bounds) - 4,
                max(box[2] for box in bounds) + 4, max(box[3] for box in bounds) + 4]
        cell = [(crop[2] - crop[0]) // 2, (crop[3] - crop[1]) // 2]
        sampling, _, columns, rows, envelope = best_grid(len(images), *cell)
        color = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
        outline = Image.new('RGB', color.size, 'white')
        for index, image in enumerate(images):
            part = image.crop(crop)
            reconstructed = Image.new('RGBA', image.size)
            reconstructed.paste(part, tuple(crop[:2]))
            assert np.array_equal(np.array(reconstructed.convert('RGBa')), np.array(image.convert('RGBa')))
            xy = (index % columns * part.width, index // columns * part.height)
            color.paste(part, xy)
            inside = np.array(part.getchannel('A'))[::2, ::2] > 0
            edge = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[edge] = 0
            outline.paste(Image.fromarray(guide).resize(part.size, Image.Resampling.NEAREST), xy)
        paths = [out / 'references' / f'{job["id"]}_{role}.png' for role in ['native', 'outline', 'detail']]
        color.save(paths[0])
        outline.save(paths[1])
        prior = original / 'cleaned' / (job['frames'][0] + '.png')
        assert prior.exists(), prior
        detail = Image.open(prior).convert('RGBA')
        box = detail.getbbox()
        assert box
        detail = detail.crop((max(0, box[0] - 6), max(0, box[1] - 6),
                              min(detail.width, box[2] + 6), min(detail.height, box[3] + 6)))
        detail.save(paths[2])
        target = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows * cell[1] * 2.8)]
        prompt = f'''{HEADER}
Use case: style-transfer. Generate exactly ONE COMPLETE {config['label']} {job['action']} animation for stored view {job['view']}: ALL {len(images)} original bitmap steps on ONE RGBA sheet, exactly {columns} columns by {rows} rows, chronological row-major order. No extra poses or in-between steps. A one-frame action is ONE SINGLE SPRITE. Unused art remains outside playback.
Image 1: untouched correctly paletted native colour complete animation, sole authority for each pose, anatomy, proportions, camera, equipment ownership/coverage, base colours and relative placement.
Image 2: matching OUTLINE-ONLY geometry guide, thin inward alpha contours and transparent gaps, white interior/exterior. Geometry ONLY: no copied strokes, guide bands, dark grooves, flat white fill or artificial shading in the result. No internal contrast guide.
Image 3: detailed SAME-FAMILY enhanced appearance reference. Carry its fine face/material finish and coherent natural upper-left painted lighting through every step. Do not copy its pose, extra bulk or equipment absent from native art. Images 1 and 2 control all geometry.
Identity and native base material colours: {config['description']}
Anatomy: {anatomy(stem)}
Keep rich fine material texture, natural contrast and shading, crisp existing feathers/scales/bone/cloth/leather/metal details as applicable. No washed-out contrast, waxy smoothing, flat texture, blur, pixel blocks, dithering, sharpening halos or noisy pseudo-detail. Preserve native material coverage without redesign.
Layout: chronological row-major order {', '.join(job['frames'])}. Common native crop {[value / 2 for value in crop]}, padded cell {cell}, actor canvas {canvas} and pivot {sources['logical_pivot']}. Exactly {columns} columns and {rows} rows. Keep native position/scale for every step and 2 native pixels of transparent padding at all cell/sheet edges. All extremities and thin features visible. No independent centering, zoom, silhouette fit, body stretching or limb warping. Fill the grid without extra blank margins.
Palette/material separation: Generate ONLY base palette {sources['base_palette']} shown in Image 1, never alternative colours. Image 3 supplies finish only, never alternate colours or geometry.
Request a LARGE {target[0]}x{target[1]} master with reconstructed detail, aiming for >=2x actual generated sampling, preferably >=2.2x. Keeping ALL native steps together on ONE submitted and returned sheet takes priority. Do not split the animation. Export enlargement is not generated detail.
Genuine transparent background and native gaps only. No floor, cast shadow, opaque backdrop, painted checkerboard, labels, grid, text, decoration or new effects. Exactly one complete returned image.
'''
        prompt_path = out / 'prompts' / (job['id'] + '_v1.txt')
        prompt_path.write_text(prompt)
        job.update(native_crop=[value / 2 for value in crop], cell_native_size=cell, columns=columns, rows=rows,
                   observed_envelope=envelope, planned_sampling=sampling, requested_master=target,
                   references=[str(path.relative_to(REPO)) for path in paths],
                   reference_roles=['untouched_native_complete_animation', 'outline_only_geometry_no_shading',
                                    'previous_detailed_material_appearance_not_pose'],
                   appearance_source=dict(path=str(prior.relative_to(REPO)), sha256=sha(prior)),
                   prompt=str(prompt_path.relative_to(REPO)), status='pending', attempts=[],
                   prepared_assets=[dict(path=str(path.relative_to(REPO)), sha256=sha(path))
                                    for path in [*paths, prompt_path]])
        height = color.height // 2
        contact = Image.new('RGB', (color.width + max(160, detail.width // 2),
                                    max(height, detail.height // 2) + 24), (52, 52, 52))
        for index, image in enumerate([color, outline]):
            image = image.resize((color.width // 2, height), Image.Resampling.NEAREST)
            contact.paste(image, (index * color.width // 2, 24), image if image.mode == 'RGBA' else None)
        preview = detail.resize((max(1, detail.width // 2), max(1, detail.height // 2)), Image.Resampling.LANCZOS)
        contact.paste(preview, (color.width, 24), preview)
        ImageDraw.Draw(contact).text((4, 5), 'Native colour | outline ONLY | appearance: ' + job['id'], fill='white')
        contact.save(out / 'review' / (job['id'] + '_inputs.png'))
    save(out / 'run.json', dict(project=str(root.relative_to(REPO)), source_project=str(original.relative_to(REPO)),
         method=METHOD, status='in_progress', target_sampling=2.2, padding_native_px=2, reference_enlargement=2,
         source_metadata=[dict(path=str((original / name).relative_to(REPO)), sha256=sha(original / name))
                          for name in ['config.json', 'sources.json', 'manifest.json', 'variants.json']],
         native_offsets={name: [0, 0] for name in natives}, jobs=jobs))
    save(out / 'processing.json', dict(preserve_matte_hued_materials=True,
                                       whole_animation_resolution_policy=DEFAULT_POLICY))
    (root / 'native').mkdir(exist_ok=True)
    for name, image in natives.items():
        image.resize(tuple(canvas), Image.Resampling.NEAREST).save(root / 'native' / (name + '.png'))
    name = config['identity_frames'][0]
    box = natives[name].getbbox()
    crop = [box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4]
    width, height = (crop[2] - crop[0]) // 2, (crop[3] - crop[1]) // 2
    contact = Image.new('RGB', (width * len(sources['palettes']), height + 25), (45, 45, 45))
    draw = ImageDraw.Draw(contact)
    for index, palette in enumerate(sources['palettes']):
        image = native_2x(sources['sources'][name], sources, palette)[0].crop(crop)
        image = image.resize((width, height), Image.Resampling.NEAREST)
        contact.paste(image, (width * index, 25), image)
        draw.text((width * index + 3, 6), str(palette) + (' BASE' if palette == sources['base_palette'] else ''),
                  fill='white')
    contact.save(out / 'review/native_palette_comparison.png')
    print(json.dumps(dict(family=original.name, frames=len(natives), jobs=len(jobs), base=sources['base_palette'],
                          minimum_planned=round(min(job['planned_sampling'] for job in jobs), 3))))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def process(stem, selected=None):
    import extract_run
    import annotate_packed_body
    import register_packed_outline
    root = STAGE / ('mm7_' + stem)
    config, sources = read(root / 'config.json'), read(root / 'sources.json')
    config['matte'] = 'magenta'
    save(root / 'config.json', config)
    extract_run.native = lambda root, name: native_2x(sources['sources'][name], sources, sources['base_palette'])[0].resize(tuple(sources['logical_canvas']), Image.Resampling.NEAREST)
    annotate_packed_body.native_2x = native_2x
    register_packed_outline.native_2x = native_2x
    register_packed_outline.process_family.mask = lambda image, config: Image.new('L', image.size)
    project = str(root.relative_to(REPO))
    extract_run.extract(project, selected)
    annotate_packed_body.annotate(project, True, selected)
    register_packed_outline.register(project)


def extract_candidates(stem):
    import extract_run
    root = STAGE / ('mm7_' + stem)
    sources = read(root / 'sources.json')
    extract_run.native = lambda root, name: native_2x(sources['sources'][name], sources,
        sources['base_palette'])[0].resize(tuple(sources['logical_canvas']), Image.Resampling.NEAREST)
    results = []
    for job in read(root / 'redo_2x/run.json')['jobs']:
        if not job.get('selected_raw'):
            continue
        reason = None
        method = 'verified_empty_gutters'
        for choice in range(3):
            if choice:
                with job_lock(root):
                    policy = read(root / 'redo_2x/processing.json')
                    for key in ['connected_body_extraction_jobs', 'component_grid_extraction_jobs']:
                        policy[key] = [value for value in policy.get(key, []) if value != job['id']]
                    key = 'connected_body_extraction_jobs' if choice == 1 else 'component_grid_extraction_jobs'
                    policy[key].append(job['id'])
                    policy.setdefault('component_seed_alpha_threshold_by_job', {})[job['id']] = dict(
                        raw_sha256=sha(REPO / job['selected_raw']), threshold=32,
                        reason='Provisional solid-alpha seeds for full-pose review. Every remaining supplied foreground pixel is assigned exactly once. Component ownership requires visual review.')
                    save(root / 'redo_2x/processing.json', policy)
                method = key + '_pending_review'
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    extract_run.extract(str(root.relative_to(REPO)), [job['id']])
                reason = None
                break
            except Exception as error:
                reason = str(error)
        results.append(dict(job=job['id'], extracted=reason is None, method=method,
                            reason=reason, raw_sha256=sha(REPO / job['selected_raw'])))
    save(root / 'redo_2x/review/extraction_checkpoint.json', dict(results=results, accepted=False))
    print(stem, 'extracted', sum(row['extracted'] for row in results), 'of', len(results),
          'failures', [row for row in results if not row['extracted']])


def retry(stem, job_id, reason, padding):
    import repack_packed_outline
    repack_packed_outline.native_2x = native_2x
    root = STAGE / ('mm7_' + stem)
    repack_packed_outline.repack(str(root), job_id, reason, padding)
    path = root / 'redo_2x/run.json'
    with job_lock(root):
        run = read(path)
        job = next(job for job in run['jobs'] if job['id'] == job_id)
        prompt_path = REPO / job['prompt']
        prompt = prompt_path.read_text().replace('original MM6', 'original MM7')
        prompt = HEADER + '\n' + prompt
        if stem == 'm406':
            prompt = prompt.replace(
                'Only blue tabard areas recolor to green and red; white chevrons, skin, chainmail, steel and gold stay unchanged.',
                'The tabard is BLUE in this base restoration. Keep its pale silver-white chevrons, tan skin, silver chainmail and steel, and gold fittings exactly as supplied in Image 1.')
        prompt_path.write_text(prompt)
        job.pop('submission_pending', None)
        job['prepared_assets'] = [dict(path=str(REPO / asset), sha256=sha(REPO / asset))
                                  for asset in [*job['references'], job['prompt']]]
        save(path, run)


def batch_locked(stem, limit):
    root = STAGE / ('mm7_' + stem)
    run = read(root / 'redo_2x/run.json')
    jobs = []
    for job in run['jobs']:
        if job.get('selected_raw') or job.get('submission_pending') or job.get('status') == 'blocked_tool_return':
            continue
        jobs.append(dict(family=root.name, id=job['id'], prompt_text=(REPO / job['prompt']).read_text(),
                         references=[str(REPO / value) for value in job['references']],
                         contact=str(root / 'redo_2x/review' / (job['id'] + '_inputs.png'))))
        job['submission_pending'] = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                                         prompt_sha256=sha(REPO / job['prompt']))
        if len(jobs) >= limit:
            break
    save(root / 'redo_2x/run.json', run)
    print(json.dumps(jobs))


def batch(stem, limit):
    with job_lock(STAGE / ('mm7_' + stem)):
        batch_locked(stem, limit)


def failure_locked(stem, job_id, reason):
    root = STAGE / ('mm7_' + stem)
    path = root / 'redo_2x/run.json'
    run = read(path)
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    job.setdefault('failed_submissions', []).append(dict(reason=reason,
        utc=datetime.now(timezone.utc).isoformat(), prepared_assets=job['prepared_assets']))
    job.pop('submission_pending', None)
    job['status'] = 'blocked_tool_return'
    save(path, run)


def failure(stem, job_id, reason):
    with job_lock(STAGE / ('mm7_' + stem)):
        failure_locked(stem, job_id, reason)


def contacts(stem):
    import review_complete_sheets, review_detail_and_alpha
    review_complete_sheets.native_2x = native_2x
    project = str((STAGE / ('mm7_' + stem)).relative_to(REPO))
    review_complete_sheets.contacts(project)
    review_detail_and_alpha.review(project)


def export_candidate(stem):
    """Reuse the MM7 packer; expose the same native data in the existing shared reviewer contract."""
    root = STAGE / ('mm7_' + stem)
    out = root / 'redo_2x'
    sources, records = read(root / 'sources.json'), read(out / 'registration.json')
    missing = sorted(set(sources['sources']) - set(records))
    assert set(records) <= set(sources['sources'])
    for name in ['sources.json', 'config.json']:
        shutil.copy2(root / name, out / name)
    if missing:
        packing_config = read(out / 'config.json')
        packing_config['identity_frames'] = [name for name in packing_config['identity_frames'] if name in records]
        save(out / 'config.json', packing_config)
        # The packer requires complete groups. Pack available artwork without inventing
        # substitute art, then restore exact available views and retain missing native
        # sequences explicitly in the partial export metadata below.
        packing_sources = json.loads(json.dumps(sources))
        if 'null' not in packing_sources['groups']:
            # Internal empty packing group only; never exported as native metadata.
            packing_sources['groups']['null'] = dict(sprite_id=-1, animation_length_raw=0, frames=[])
        packing_sources['sources'] = {name: row for name, row in sources['sources'].items() if name in records}
        native_animations = read(root / 'manifest.json')['descriptor_animations']
        for descriptor, bindings in packing_sources['descriptor_bindings'].items():
            for action, animation in native_animations[descriptor].items():
                if any(step['frame'] not in records for steps in animation['directions'].values() for step in steps):
                    bindings[action] = 'null'
        save(out / 'sources.json', packing_sources)
    save(out / 'processing_settings.json', dict(status='candidate_visual_review_pending'))
    for name, record in records.items():
        target = out / 'cleaned' / (name + '.png')
        source = REPO / record['clean_path']
        if target.is_symlink() and target.resolve() != source.resolve():
            target.unlink()
        if not target.exists():
            target.symlink_to(os.path.relpath(source, target.parent))
    sys.path.insert(0, str(CREATURES / 'mm7_m514'))
    if stem in ['m398', 'm402'] and not read(root / 'config.json').get('session_use_generic_materials'):
        materials = module('session_' + stem + '_materials', CREATURES / ('mm7_' + stem) / 'variants.py')
        materials.HERE, materials.REPO = out, REPO
        materials.run()
    else:
        module('session_generic_materials', CREATURES / 'mm7_ambient/material_variants.py').run(out)
    module('session_mm7_pack', CREATURES / 'mm7_m514/package.py').run(out)
    manifest = read(out / 'manifest.json')
    original = read(root / 'manifest.json')
    native_offsets = read(out / 'run.json')['native_offsets']
    for name, frame in manifest['frames'].items():
        frame['native_offset'] = [(sources['logical_canvas'][0] - frame['source_canvas'][0]) / 2,
                                  sources['logical_canvas'][1] - frame['source_canvas'][1]]
        frame['registration_native_offset'] = native_offsets[name]
        assert frame['native_offset'] == frame['registration_native_offset'], name
    if not missing:
        assert manifest['descriptor_animations'] == original['descriptor_animations'], 'Changed native steps or flags'
    else:
        manifest['descriptor_animations'] = json.loads(json.dumps(original['descriptor_animations']))
        for animations in manifest['descriptor_animations'].values():
            for animation in animations.values():
                for view, steps in animation['directions'].items():
                    if any(step['frame'] not in records for step in steps):
                        animation.setdefault('unavailable_views', {})[view] = steps
                        animation['directions'][view] = []
        manifest['native_group_bindings'] = sources['descriptor_bindings']
        shutil.copy2(root / 'sources.json', out / 'sources.json')
    manifest['complete_native_descriptor_animations'] = original['descriptor_animations']
    manifest['native_variants_metadata'] = manifest['variants']
    manifest['native_material_regions'] = manifest['regions']
    manifest['regions'] = {'mask_' + 'rgb'[index]: region.get('id', region.get('name'))
                           for index, region in enumerate(manifest['native_material_regions'])}
    manifest['variants'] = {str(v['palette_id']): dict(v, exact_base_bypass=v['exact_bypass'],
                            name='Native palette ' + str(v['palette_id']))
                            for v in manifest['native_variants_metadata']}
    manifest['animations_by_palette'] = {}
    for palette, variant in manifest['variants'].items():
        descriptor = str(variant['descriptors'][0])
        animations = manifest['descriptor_animations'][descriptor]
        manifest['animations_by_palette'][palette] = {action: dict(
            native_group=data['native_group'], native_group_id=data['native_group_id'],
            animation_length_raw=data['animation_length_raw'], loop=data['loop'],
            hold_last=data['hold_last'], single_view=all(not steps for view, steps in data['directions'].items() if view != '0'),
            unavailable_views=data.get('unavailable_views', {}),
            views={view: [dict(step, mirrored=step['mirror'], native_scale=step['scale']) for step in steps]
                   for view, steps in data['directions'].items()}) for action, data in animations.items()}
    manifest['animations'] = manifest['animations_by_palette'][str(sources['base_palette'])]
    manifest['quality_status'] = 'pending_full_anatomy_placement_detail_alpha_palette_review'
    if missing:
        manifest['quality_status'] = 'partial_generation_blocked_by_imagegen_usage_limit_review_pending'
    manifest['coverage'] = dict(native_total=len(sources['sources']), exported=len(records),
        native_coverage_complete=not missing, missing_native_frames=missing,
        rejected_art_used=False, accepted=False)
    manifest['review_label'] = read(root / 'config.json')['title'] + ' — packed session 07 candidate'
    minimum = min(min(record['effective_sampling_xy']) for record in records.values())
    manifest['generated_detail'] = dict(measured_minimum=minimum,
        physical_export_tier=2, actual_generated_detail_at_least_2x=minimum >= 2,
        registration='registration.json', calibration='calibration.json',
        below_2x_frames=[name for name, record in records.items() if min(record['effective_sampling_xy']) < 2],
        reason='User prioritizes complete native cycles; physical 2x export does not add generated detail.')
    manifest['generation_method'] = METHOD
    manifest['review_record'] = 'review/acceptance.json'
    manifest['limitations'] = ['AI interpretation requires independent anatomy and placement review.',
        'Delivered real alpha was preserved except reviewed near-transparent noise at alpha 1..8.']
    if minimum < 2:
        manifest['limitations'].append(f'Actual generated sampling reaches {minimum:.4f}x; reviewed below-2x whole cycles are authorized.')
    (out / 'native_variants').mkdir(exist_ok=True)
    for palette in sources['palettes']:
        for name in records:
            source = sources['sources'][name]
            native_2x(source, sources, palette)[0].resize(tuple(sources['logical_canvas']),
                Image.Resampling.NEAREST).save(out / 'native_variants' / f'{name}_{palette}.png')
    for page_index, page in enumerate(manifest['pages']):
        page['variant_previews'] = {str(p): f'previews/palette_{p}_page_{page_index}.png' for p in sources['palettes']}
    save(out / 'manifest.json', manifest)
    validation = read(out / 'validation.json')
    validation.update(raw_cells_unclipped=not any(r['raw_clip'] for r in records.values()),
        native_coverage_complete=not missing, missing_native_frames=missing,
        exact_descriptor_metadata_preserved=True,
        minimum_actual_generated_sampling=minimum, actual_generated_detail_at_least_2x=minimum >= 2,
        visual_acceptance=False)
    save(out / 'validation.json', validation)
    print(stem, 'exported candidate', len(records), 'missing', len(missing), 'minimum', minimum)


def verify_browser(selected=None):
    """Exercise the unchanged shared reviewer against these pinned staged exports."""
    import base64
    import subprocess
    import tempfile
    import time
    import urllib.request
    import websocket
    with tempfile.TemporaryDirectory(prefix='mm7-session07-browser-', dir='/tmp') as temporary:
        temporary = Path(temporary)
        log = (temporary / 'chrome.log').open('w')
        chrome = subprocess.Popen([shutil.which('google-chrome'), '--headless', '--no-sandbox',
            '--disable-gpu', '--disable-dev-shm-usage', '--remote-debugging-port=0',
            '--remote-allow-origins=*', '--window-size=1800,1400',
            '--user-data-dir=' + str(temporary / 'profile'), 'http://127.0.0.1:8897/'],
            stdout=log, stderr=log)
        socket = None
        try:
            port_path = temporary / 'profile/DevToolsActivePort'
            deadline = time.monotonic() + 30
            while not port_path.exists():
                assert chrome.poll() is None and time.monotonic() < deadline, 'Chrome startup failed'
                time.sleep(.05)
            port = int(port_path.read_text().splitlines()[0])
            pages = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list'))
            page = next(page for page in pages if page['type'] == 'page')
            socket = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=120)
            number = 0
            def call(method, parameters=None):
                nonlocal number
                number += 1
                socket.send(json.dumps(dict(id=number, method=method, params=parameters or {})))
                while True:
                    result = json.loads(socket.recv())
                    if result.get('id') == number:
                        assert 'error' not in result, result
                        return result['result']
            def evaluate(code):
                result = call('Runtime.evaluate', dict(expression=code, awaitPromise=True, returnByValue=True))
                assert 'exceptionDetails' not in result, result
                return result['result'].get('value')
            deadline = time.monotonic() + 60
            while not evaluate('typeof state !== "undefined" && !!state.manifest && !$("play").disabled'):
                assert time.monotonic() < deadline, evaluate('document.body.innerText')
                time.sleep(.1)
            count = evaluate('state.families.length')
            checked = []
            for index in range(count):
                evaluate(f'showFamily({index})')
                deadline = time.monotonic() + 60
                while not evaluate('!!state.manifest && !$("play").disabled'):
                    assert time.monotonic() < deadline, evaluate('document.body.innerText')
                    time.sleep(.1)
                family_id = evaluate('currentFamily().id')
                selected_record = next(row for row in read(STAGE / 'mm7_m390/review_collection.json')['families']
                                       if row['creature'].replace(':', '_') == family_id)
                selected_stem = (STAGE / 'mm7_m390' / selected_record['manifest']).resolve().parent.parent.name.replace('mm7_', '')
                if selected_stem == 'm410' or (selected and selected_stem not in selected):
                    continue
                result = evaluate('''(async () => {
                    const m=state.manifest; let clips=0, frames=0;
                    for (const palette of Object.keys(m.variants)) {
                        state.palette=palette; state.images.clear(); clearColorCache();
                        for (const [action, animation] of Object.entries(m.animations_by_palette[palette])) {
                            for (const [view, sequence] of Object.entries(animation.views)) {
                                if (!sequence.length) continue;
                                state.action=action; state.view=view; state.manualStep=null;
                                configureCanvas(); await prepareClip();
                                if ($('play').disabled) throw new Error($('message').textContent);
                                for (let i=0;i<sequence.length;i++) { state.frameIndex=i; renderStage(); }
                                clips++;
                            }
                        }
                        for (const name of Object.keys(m.frames)) {
                            await getImage(`native_variants/${name}_${palette}.png`).decode();
                            await getImage(m.pages[m.frames[name].page].variant_previews[palette]).decode();
                            frames++;
                        }
                    }
                    state.palette=Object.keys(m.variants).find(p=>m.variants[p].exact_base_bypass);
                    $('palette').value=state.palette; state.action='walk'; state.view='0';
                    populateActions(); populateViews(); updateColorControls(); configureCanvas();
                    await prepareClip(); state.frameIndex=0; renderStage();
                    return {family:currentFamily().id, clips, palette_frame_images:frames,
                        manifest_sha256:currentFamily().manifest_sha256,
                        rendering_validation_passed:true, timed_playback_watched:false};
                })()''')
                checked.append(result)
                record = next(row for row in read(STAGE / 'mm7_m390/review_collection.json')['families']
                              if row['creature'].replace(':', '_') == result['family'])
                out = (STAGE / 'mm7_m390' / record['manifest']).resolve().parent
                shot = call('Page.captureScreenshot', dict(format='png'))
                (out / 'review/shared_reviewer.png').write_bytes(base64.b64decode(shot['data']))
                save(out / 'review/browser_validation.json', result)
                print(json.dumps(result), flush=True)
            save(STAGE / 'mm7_m390/shared_browser_validation.json', dict(
                families=checked, rendering_validation_passed=True,
                visual_acceptance_evaluated=False, reviewer_code_unchanged=True))
        finally:
            if socket:
                socket.close()
            chrome.terminate()
            try:
                chrome.wait(timeout=15)
            except subprocess.TimeoutExpired:
                chrome.kill()
                chrome.wait(timeout=5)
            log.close()
            chrome.wait(timeout=20)
            log.close()


def all_pose_reviews(stem):
    """Compose every native palette/pose and enhanced material mask without fitting silhouettes."""
    root = STAGE / ('mm7_' + stem)
    out = root / 'redo_2x'
    sources, records, variants = read(root / 'sources.json'), read(out / 'registration.json'), read(out / 'variants.json')
    sys.path.insert(0, str(CREATURES / 'mm7_m514'))
    from process import apply_variant, composite
    rows, detail_rows, checks = [], [], {}
    for name, record in records.items():
        base = Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBA')
        mask = Image.open(out / 'masks_2x' / (name + '.png'))
        origin = record['canvas_origin_px']
        native_images = [native_2x(sources['sources'][name], sources, v['palette_id'])[0] for v in variants['variants']]
        enhanced = [apply_variant(base, mask, v) for v in variants['variants']]
        assert all(np.array_equal(np.array(im)[:, :, 3], np.array(base)[:, :, 3]) for im in enhanced)
        exact_base = next(im for im, v in zip(enhanced, variants['variants']) if v['exact_bypass'])
        assert np.array_equal(np.array(exact_base), np.array(base))
        bounds = [native_images[0].getbbox()]
        box = base.getbbox()
        bounds.append([box[i] + origin[i % 2] for i in range(4)])
        crop = [math.floor(min(b[0] for b in bounds) / 2)-5, math.floor(min(b[1] for b in bounds) / 2)-5,
                math.ceil(max(b[2] for b in bounds) / 2)+5, math.ceil(max(b[3] for b in bounds) / 2)+5]
        width, height = crop[2]-crop[0], crop[3]-crop[1]
        row = Image.new('RGB', (7*(width+6), height+32), (37, 40, 39))
        draw = ImageDraw.Draw(row)
        images = []
        for native, im in zip(native_images, enhanced):
            images.extend([native.crop(tuple(v*2 for v in crop)), im.crop(
                (crop[0]*2-origin[0], crop[1]*2-origin[1], crop[2]*2-origin[0], crop[3]*2-origin[1]))])
        bands = mask.split() if mask.mode == 'RGB' else (mask, Image.new('L', mask.size), Image.new('L', mask.size))
        overlay = Image.merge('RGBA', (*bands, base.getchannel('A'))).crop(
            (crop[0]*2-origin[0], crop[1]*2-origin[1], crop[2]*2-origin[0], crop[3]*2-origin[1]))
        images.append(overlay)
        for col, im in enumerate(images):
            scaled = im.resize((width, height), Image.Resampling.NEAREST) if col%2 == 0 and col<6 else im.convert('RGBa').resize((width,height),Image.Resampling.LANCZOS).convert('RGBA')
            row.paste(scaled, (col*(width+6), 24), scaled)
            label = 'mask' if col==6 else str(variants['variants'][col//2]['palette_id']) + (' native' if col%2==0 else ' restored')
            draw.text((col*(width+6)+3, 3), name+' '+label, fill='white')
        rows.append((name, row))
        clean = Image.open(REPO / record['clean_path']).convert('RGBA')
        rgba = np.array(clean); alpha=rgba[:, :, 3]
        solid = alpha >= 128
        distance = ndimage.distance_transform_edt(solid)
        y, x = np.unravel_index(distance.argmax(), distance.shape)
        material = clean.crop((x-56,y-56,x+56,y+56))
        edge = (alpha>0) & ((distance<=4) | (alpha<128))
        excess = np.maximum(0, np.minimum(rgba[:,:,0].astype(float),rgba[:,:,2])-rgba[:,:,1]) * alpha/255
        excess[~edge]=0
        ey, ex = np.unravel_index(excess.argmax(), excess.shape)
        patch=clean.crop((ex-56,ey-56,ex+56,ey+56))
        detail = Image.new('RGB',(448,138),(37,40,39));dd=ImageDraw.Draw(detail)
        dd.text((3,3),name+' | 100% raw pixels: material light/dark, edge light/dark',fill='white')
        for col,(im,bg) in enumerate([(material,(235,235,235)),(material,(25,25,25)),(patch,(235,235,235)),(patch,(25,25,25))]):
            detail.paste(composite(im,bg),(col*112,24))
        detail_rows.append((name, detail))
        checks[name]=dict(base_exact_bypass=True,all_palette_alpha_identical=True,
            mask_zero_outside_alpha=not np.any(np.array(mask)[np.array(base)[:,:,3]==0]),
            maximum_candidate_spill=float(excess.max()), raw_sha256=record['raw_sha256'],
            material_patch_center=[int(x),int(y)],edge_patch_center=[int(ex),int(ey)],visual_review='pending')
    def pages_for(items, prefix, max_height, columns=1):
        paths=[]; page_items=[]; height=0
        def flush():
            if not page_items:return
            width=max(im.width for _,im in page_items)*columns
            row_heights=[max(im.height for _,im in page_items[i:i+columns]) for i in range(0,len(page_items),columns)]
            page=Image.new('RGB',(width,sum(row_heights)),(37,40,39)); y=0
            for i in range(0,len(page_items),columns):
                for col,(_,im) in enumerate(page_items[i:i+columns]):page.paste(im,(col*(width//columns),y))
                y+=row_heights[i//columns]
            path=out/'review'/f'{prefix}_{len(paths):02d}.png';page.save(path);paths.append(dict(path=str(path.relative_to(out)),sha256=sha(path),frames=[n for n,_ in page_items],status='pending_visual_review'))
        for index,item in enumerate(items):
            if index%columns==0:
                increment=max(im.height for _,im in items[index:index+columns])
                if page_items and height+increment>max_height:flush();page_items=[];height=0
                height+=increment
            page_items.append(item)
        flush();return paths
    palette_pages=pages_for(rows,'all_palette_poses',1500)
    detail_pages=pages_for(detail_rows,'all_detail_edges_100pct',1380,3)
    save(out/'review/all_pose_review.json',dict(status='pending_visual_review',frames=checks,
        palette_pages=palette_pages,detail_pages=detail_pages,accepted=False))
    print(stem,'review frames',len(checks),'palette pages',len(palette_pages),'100% detail pages',len(detail_pages),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'process', 'extract', 'export', 'browser', 'all-review', 'retry', 'batch', 'failure', 'contacts'])
    parser.add_argument('--family', choices=FAMILIES, action='append')
    parser.add_argument('--jobs', nargs='+')
    parser.add_argument('--reason')
    parser.add_argument('--padding', type=int, default=6)
    parser.add_argument('--limit', type=int, default=12)
    args = parser.parse_args()
    if args.operation == 'browser':
        verify_browser(args.family)
        sys.exit(0)
    for family in args.family or FAMILIES:
        if args.operation == 'prepare':
            prepare(family)
        elif args.operation == 'process':
            process(family, args.jobs)
        elif args.operation == 'extract':
            extract_candidates(family)
        elif args.operation == 'export':
            export_candidate(family)
        elif args.operation == 'all-review':
            all_pose_reviews(family)
        elif args.operation == 'retry':
            assert args.jobs and len(args.jobs) == 1 and args.reason
            retry(family, args.jobs[0], args.reason, args.padding)
        elif args.operation == 'batch':
            batch(family, args.limit)
        elif args.operation == 'failure':
            assert args.jobs and len(args.jobs) == 1 and args.reason
            failure(family, args.jobs[0], args.reason)
        else:
            contacts(family)
