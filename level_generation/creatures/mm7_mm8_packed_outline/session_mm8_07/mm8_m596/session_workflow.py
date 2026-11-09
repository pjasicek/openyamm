"""Local MM8 native-schema preparation using shared packing and source decoding.

The shared packed preparer requires MM6 config/manifest files. Seven assigned MM8
projects have only descriptor-backed sources, so this bridge prepares their whole
cycles without changing shared tools or historical packages. It generates no art.
"""
import argparse
import fcntl
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import yaml

REPO = Path('/home/pjasicek/github/OpenYAMM')
CREATURES = REPO / 'level_generation/creatures'
STAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CREATURES))
sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
from prepare_packed_outline import best_grid
from whole_animation_resolution import DEFAULT_POLICY, METHOD
import mm8_restore_queue as native_queue

HEADER = ('TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration of an '
          'EXISTING Might and Magic VIII (MM8) fantasy role-playing game sprite asset, using the supplied original '
          'animation bitmaps. Restore the existing fantasy-game character and its original animation; preserve its '
          'native costume, material coverage, anatomy and poses. The request is game-art restoration.')
FAMILIES = [f'm{number}' for number in range(596, 628, 4)]
ANATOMY = {
    'm596': 'Rose-purple crystalline humanoid with angular crystal crown, slim faceted torso, long segmented arms, '
            'three-pronged claw hands, long legs and angular feet. Preserve crystalline refraction and fine chips; '
            'no skin, clothing, extra horns or bulk.',
    'm600': 'Native green organic Nightmare with several eyestalks, two tall toothed mouth stalks, eyes and another '
            'toothed maw in the body and irregular stump base. Preserve every visible mouth/eye, stalk attachment, '
            'bend and overlap in each pose. It is NOT a horse, quadruped or humanoid; do not invent arms or legs.',
    'm604': 'Slim gaunt undead Ether Knight, greenish grey head and limbs, green shoulder mantle and hanging panel, '
            'dark torso, gold fasteners/knee fittings, red/gold belt and native dark weapon. Preserve the same '
            'weapon hand/grip, mantle coverage and skeletal proportions; no fuller muscles or new armor.',
    'm608': 'Native grey rocky Juggernaut with cragged head, pale luminous eyes, huge rough stone torso/arms, '
            'green studded waist band and THREE separate suspended rock chunks below it. Preserve the empty gaps '
            'and each fragment motion. Never invent connected human legs or merge the detached chunks.',
    'm612': 'Native green scaled Gog with original curved horns/crest, pointed ears, shoulder protrusions, '
            'clawed hands/feet and long slender tail. Preserve each native joint, claw ownership and tail curl. '
            'Keep fine scales and natural dark green tonal weight; no clothes, new horns or larger muscle bulk.',
    'm616': 'Native skeletal Bone Dragon with long skull/neck, exposed rib cage, paired articulated wings and '
            'their long jointed spars, torn dark membranes, bony taloned legs and tail. Preserve each wing fold, '
            'rib opening, bone chain and near/far occlusion in every flap. Finish follows native weathered bone '
            'and membrane; do not turn the bones into glossy polished metal or add flesh.',
    'm620': 'Native slim bedraggled human peasant with short dark hair, ragged OPEN green vest, native exposed '
            'torso/arms, torn grey trousers and worn brown footwear. Preserve original material coverage, slender '
            'limb chains, foot contacts and tired posture. Fine woven cloth, seams, worn leather and natural skin.',
    'm624': 'Native Naga with long brown hair, green original top, gold neck/arm jewelry, SIX arm chains each '
            'holding its own native blade, and a long tan scaled snake lower body with belly scutes and coiled '
            'tail. Preserve all six shoulder/elbow/wrist/hand/weapon ownership chains, each blade shape/angle, '
            'native costume coverage and exact coil undulation. No human legs, extra arms or missing swords.'
}


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scopes(sources, stem):
    jobs, seen, represented = [], {}, set()
    aliases = sources['pixel_aliases']
    for descriptor, actor in sources['bindings'].items():
        for action, animation in actor['actions'].items():
            for view, steps in animation['views'].items():
                if not steps or any(step['mirrored'] for step in steps):
                    continue
                # No-image timelines remain in sources, with no generated replacement.
                if all(step['frame'] is None for step in steps):
                    continue
                assert all(step['frame'] is not None for step in steps), 'Mixed empty cycle needs shared support'
                names = [aliases.get(step['frame'], step['frame']) for step in steps]
                signature = tuple(names)
                binding = dict(descriptor_id=int(descriptor), action=action, view=int(view),
                               native_frames=[step['frame'] for step in steps])
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
    for name in sorted(set(sources['sources']) - represented - set(aliases)):
        match = re.fullmatch(stem + r'([a-z])([a-z]+)([0-7])', name)
        assert match, name
        unused.setdefault((match[1], int(match[3])), []).append(name)
    for (code, view), names in unused.items():
        jobs.append(dict(id=f'unused_{code}_{view}_sheet', action='unused_native', view=view,
                         frames=names, bindings=[], native_sequence=False))
    assert set(name for job in jobs for name in job['frames']) == set(sources['sources']) - set(aliases)
    return jobs


def validate_native(sources, row):
    descriptors_path = REPO / sources['descriptor_table']['path']
    descriptors = {int(fields[0]): fields for line in descriptors_path.read_text().splitlines()
                   if (fields := line.split('\t'))[0].isdigit()}
    assert [int(key) for key in sources['bindings']] == [entry['id'] for entry in row['descriptors']]
    assert set(sources['sources']) == set(row['all_native_family_images'])
    files = {REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml'}
    for key, actor in sources['bindings'].items():
        assert actor['native_descriptor'] == descriptors[int(key)], key
        for animation in actor['actions'].values():
            name = animation['native_group'].lower()
            files.add(REPO / 'assets_dev/engine/rendering/sprite_frames/monsters' / (name[:-1] + '.yml'))
    groups = {}
    hashes = []
    for path in sorted(files):
        if not path.exists():
            continue
        hashes.append(dict(path=str(path.relative_to(REPO)), sha256=sha(path)))
        for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            groups[group['sprite_name'].lower()] = group
    for actor in sources['bindings'].values():
        for animation in actor['actions'].values():
            group = groups[animation['native_group'].lower()]
            assert animation['native_group_record'] == group
            for view, steps in animation['views'].items():
                assert len(steps) == len(group['frames'])
                for step, frame in zip(steps, group['frames']):
                    name, mirror = native_queue.resolve(frame, int(view))
                    assert step['native_texture'] == name and step['mirrored'] == mirror
                    assert step['duration_raw'] == frame['frame_length_raw']
                    assert step['duration_ticks'] == frame['frame_length_raw'] * 8
                    assert step['duration_ms'] == frame['frame_length_raw'] * 62.5
                    assert step['flags'] == frame.get('flags', [])
                    assert step['palette'] == frame.get('palette_id', 0)
                    assert step['scale'] == frame.get('scale', 1)
    hashes.append(dict(path=str(descriptors_path.relative_to(REPO)), sha256=sha(descriptors_path)))
    for asset in [*sources['sources'].values(), *sources['palette_sources'].values()]:
        assert sha(REPO / asset['path']) == asset['sha256'], asset['path']
    return hashes


def prepare(stem):
    original = CREATURES / ('mm8_' + stem)
    root = STAGE / original.name
    out = root / 'redo_2x'
    if (out / 'run.json').exists():
        run = read(out / 'run.json')
        for job in run['jobs']:
            assert all(sha(REPO / asset['path']) == asset['sha256'] for asset in job['prepared_assets'])
        print(json.dumps(dict(family=stem, jobs=len(run['jobs']), resumed=True)))
        return
    sources = read(original / 'sources.json')
    row = next(row for row in read(CREATURES / 'remaining_inventory.json')['families']
               if row['world'] == 'mm8' and row['label'] == sources['label'])
    tables = validate_native(sources, row)
    canvas = [max(source['size'][axis] for source in sources['sources'].values()) for axis in (0, 1)]
    assert {tuple(source['size']) for source in sources['sources'].values()} == {tuple(canvas)}
    sources.update(logical_canvas=canvas, logical_pivot=[canvas[0] / 2, canvas[1]])
    save(root / 'sources.json', sources)
    for folder in ['references', 'prompts', 'raw', 'review']:
        (out / folder).mkdir(parents=True, exist_ok=True)
    natives = {}
    for name in sources['sources']:
        image = native_queue.native(root, name, sources['base_palette'])
        pixels = np.array(image)
        pixels[pixels[:, :, 3] == 0] = 0
        image = Image.fromarray(pixels)
        natives[name] = image.resize((canvas[0] * 2, canvas[1] * 2), Image.Resampling.NEAREST)
    # Every source is 256 square: center flags are preserved in bindings; no
    # inter-frame anchor displacement is introduced by the shared preparation canvas.
    palette_names = list(sources['palette_sources'])
    preview = Image.new('RGB', (len(palette_names) * 256, 280), (48, 48, 48))
    first = next(job for job in scopes(sources, stem) if job['action'] == 'standing')['frames'][0]
    for index, palette in enumerate(palette_names):
        image = native_queue.native(root, first, int(palette))
        preview.paste(image, (index * 256, 24), image)
        ImageDraw.Draw(preview).text((index * 256 + 4, 5), f'{sources["label"]} palette {palette}', fill='white')
    preview.save(out / 'review/native_palettes.png')
    jobs = scopes(sources, stem)
    for job in jobs:
        images = [natives[name] for name in job['frames']]
        bounds = [image.getbbox() for image in images]
        assert all(bounds), 'Empty native bitmap needs shared support'
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
            assert np.array_equal(np.asarray(reconstructed.convert('RGBa')), np.asarray(image.convert('RGBa')))
            xy = (index % columns * part.width, index // columns * part.height)
            color.paste(part, xy)
            inside = np.array(part.getchannel('A'))[::2, ::2] > 0
            edge = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[edge] = 0
            outline.paste(Image.fromarray(guide).resize(part.size, Image.Resampling.NEAREST), xy)
        paths = [out / 'references' / f'{job["id"]}_{role}.png' for role in ['native', 'outline']]
        color.save(paths[0])
        outline.save(paths[1])
        prior = original / 'redo_2x/cleaned' / (job['frames'][0] + '.png')
        if not prior.exists():
            prior = original / 'cleaned' / (job['frames'][0] + '.png')
        appearance = None
        if prior.exists():
            detail = Image.open(prior).convert('RGBA')
            box = detail.getbbox()
            assert box
            target_path = out / 'references' / (job['id'] + '_detail.png')
            detail.crop((max(0, box[0] - 6), max(0, box[1] - 6),
                         min(detail.width, box[2] + 6), min(detail.height, box[3] + 6))).save(target_path)
            paths.append(target_path)
            appearance = dict(path=str(prior.relative_to(REPO)), sha256=sha(prior))
        target = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows * cell[1] * 2.8)]
        appearance_text = ('Image 3 is detailed SAME-FAMILY enhanced appearance art: material detail and natural '
                           'shading ONLY. Never copy its pose, altered bulk or absent equipment.') if appearance else (
                           'No prior enhanced appearance exists. Restore the native identity in fine detail on this '
                           'first useful complete sheet; its reviewed result will become the appearance reference '
                           'for subsequent jobs. Do not redesign the character.')
        prompt = f'''{HEADER}

Generate exactly ONE COMPLETE {sources['label']} {job['action']} animation for stored rotation {job['view']}: ALL {len(images)} native bitmap steps on ONE RGBA sheet, {columns} columns by {rows} rows, chronological row-major order. A single-bitmap animation is ONE SINGLE SPRITE, never an invented cycle. Unused art remains outside playback.
Image 1 is untouched correctly paletted native colour: sole authority for each step's anatomy, proportions, pose, equipment, costume/material coverage, camera, base colours and native position.
Image 2 is the matching separate OUTLINE-ONLY sheet. Thin inward silhouette boundaries and transparent gaps guide GEOMETRY ONLY. White interior/exterior and black lines convey no texture, light or shading. No copied guide strokes/bands, dark grooves or internal contrast guides in the result.
{appearance_text}
Respect every step's actual native limb chains, joint lengths/widths/bends, near/far ownership, crossings, foreshortening, grips, raised/planted extremities, head angle, body bob, wing/tail structures and effects. Preserve the visible costume, material coverage, proportions and equipment. No fused/swapped/extra limbs, invented joints, altered bulk, duplicated steps or new motion. Do not substitute humanoid chains for a quadruped, skeletal wing or snake tail.
Preserve rich reconstructed fine material detail and natural contrast/shading, coherent native baked lighting, face planes, wrinkles, crystal facets, bone porosity, scales, cloth/leather grain, seams, rivets and metal wear only where present. No washed-out contrast, waxy/plastic smoothing, blur, pixel blocks, dithering, flat surfaces, sharpening halos, pseudo-detail or artificial blotchy shading bands.
Generate ONLY native base palette {sources['base_palette']} from Image 1. Any appearance input supplies finish only, never alternate colours or geometry.
Layout: {', '.join(job['frames'])}. Common native-coordinate crop {[v / 2 for v in crop]}, padded cell {cell}, canvas {canvas}, bottom-center preparation pivot {sources['logical_pivot']}; native anchor flags remain in exact playback metadata. Keep common position and uniform scale, 2 native px transparent safety padding, full tips and limb gaps. No independent pose centering, zoom or silhouette fitting; preserve native foot lifts, body bob and motion extremes. Leave unused grid cells transparent, with no oversized exterior margins.
Request a LARGE {target[0]}x{target[1]} master, aiming for >=2x actual generated detail, preferably >=2.2x. ALL native steps on ONE submitted and returned sheet take priority over that target; never split or enlarge a previous return to claim more generated detail.
Exactly one genuinely transparent RGBA complete-animation image. No floor, cast shadows, opaque/painted checkerboard, labels, grid, text or new effects.
'''
        if not job['native_sequence']:
            prompt += 'These unreferenced native bitmaps are preserved art, with no invented playback or timing.\n'
        if job['action'] in ['death', 'corpse']:
            prompt += ('Preserve the original non-graphic falling/resting/dissipating sequence, including detached '
                       'particles or residue. Never replace effect cells with an invented complete body.\n')
        prompt_path = out / 'prompts' / (job['id'] + '_v1.txt')
        prompt_path.write_text(prompt)
        job.update(native_crop=[v / 2 for v in crop], cell_native_size=cell, columns=columns, rows=rows,
                   observed_envelope=list(envelope), planned_sampling=sampling, requested_master=target,
                   references=[str(path.relative_to(REPO)) for path in paths],
                   reference_roles=['untouched_native_complete_animation', 'outline_only_geometry_no_shading'] +
                   (['previous_detailed_material_appearance_not_pose'] if appearance else []),
                   appearance_source=appearance, prompt=str(prompt_path.relative_to(REPO)), status='pending', attempts=[],
                   prepared_assets=[dict(path=str(path.relative_to(REPO)), sha256=sha(path))
                                    for path in [*paths, prompt_path]])
    save(out / 'run.json', dict(project=str(root.relative_to(REPO)), source_project=str(original.relative_to(REPO)),
         method=METHOD, status='prepared', target_sampling=2.2, padding_native_px=2, reference_enlargement=2,
         source_metadata=[dict(path=str((original / 'sources.json').relative_to(REPO)),
                               sha256=sha(original / 'sources.json'))], current_native_tables=tables,
         source_validation=dict(current_descriptors_and_groups_match=True, all_source_palette_hashes_match=True,
                                exact_foreground_reconstruction=True, exact_anchor_offsets=True),
         native_offsets={name: [0, 0] for name in natives}, jobs=jobs))
    save(out / 'processing.json', dict(preserve_matte_hued_materials=True, supplied_alpha_noise_floor=0,
                                       whole_animation_resolution_policy=DEFAULT_POLICY))
    print(json.dumps(dict(family=stem, label=sources['label'], native_images=len(sources['sources']),
                          unused_images=len(sources['orphan_images']), jobs=len(jobs))))


def refine_prompts():
    for stem in FAMILIES:
        out = STAGE / ('mm8_' + stem) / 'redo_2x'
        run = read(out / 'run.json')
        for job in run['jobs']:
            if job['attempts'] or job['prompt'].endswith('_v2.txt'):
                continue
            prior = REPO / job['prompt']
            prompt = prior.read_text().replace('Respect every step', 'Native identity and anatomy: ' +
                                               ANATOMY[stem] + '\nRespect every step', 1)
            path = out / 'prompts' / (job['id'] + '_v2.txt')
            path.write_text(prompt)
            job['prompt'] = str(path.relative_to(REPO))
            job['prepared_assets'].append(dict(path=job['prompt'], sha256=sha(path)))
        save(out / 'run.json', run)


def submit(stem, job_id):
    out = STAGE / ('mm8_' + stem) / 'redo_2x'
    run = read(out / 'run.json')
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    assert job['status'] == 'pending', 'Submission requires an unclaimed pending job'
    paths = [REPO / path for path in job['references']]
    roles = list(job['reference_roles'])
    assert roles[:2] == ['untouched_native_complete_animation', 'outline_only_geometry_no_shading']
    assert paths[0].name == job_id + '_native.png' and paths[1].name == job_id + '_outline.png'
    assert Image.open(paths[0]).size == Image.open(paths[1]).size
    for path in paths:
        asset = next(asset for asset in job['prepared_assets'] if asset['path'] == str(path.relative_to(REPO)))
        assert sha(path) == asset['sha256']
    prompt = (REPO / job['prompt']).read_text()
    bootstrap = out / 'bootstrap.json'
    exception = None
    if len(paths) == 2 and bootstrap.exists():
        selected = read(bootstrap)
        appearance = REPO / selected['path']
        assert sha(appearance) == selected['sha256']
        assert selected['material_appearance_reviewed']
        paths.append(appearance)
        roles.append('selected_detailed_same_family_appearance_not_pose')
        if 'No prior enhanced appearance exists.' in prompt:
            start = prompt.index('No prior enhanced appearance exists.')
            end = prompt.index('\n', start)
            prompt = prompt[:start] + ('Image 3 is the selected detailed SAME-FAMILY restoration: carry its fine '
                  'material finish and native colors through every step. It controls APPEARANCE ONLY; never copy '
                  'its pose, anatomy, broader bulk or equipment. Images 1 and 2 control native geometry.') + prompt[end:]
        version = out / 'prompts' / (job_id + f'_appearance_attempt{len(job["attempts"]) + 1}_v3.txt')
        version.write_text(prompt)
        job['prompt'] = str(version.relative_to(REPO))
        job['prepared_assets'].append(dict(path=job['prompt'], sha256=sha(version)))
    elif len(paths) == 2:
        assert job_id == run['jobs'][0]['id'], 'Only first complete sheet may bootstrap missing appearance'
        exception = 'No adequate enhanced same-family art; first complete sheet establishes appearance.'
    if not job['attempts']:
        prompt += ('View fidelity: show ONLY facial features visible in each native step. Rear-facing heads show '
                   'their backs, never a frontal face pasted onto the back. Preserve original occlusions, body '
                   'bob and the native last-to-first transition.\n')
        repeated = sorted({name for name in job['frames'] if job['frames'].count(name) > 1})
        if repeated:
            prompt += ('Native held/repeated source steps: ' + ', '.join(repeated) +
                       '. These occurrences MUST have identical pose and appearance; preserve the original '
                       'holds without inventing movement. The prohibition on duplicates means added steps only.\n')
        if job['action'] in ['death', 'corpse', 'unused_native']:
            prompt += ('The living identity applies ONLY where that body remains visible in Image 1. Keep '
                       'the original fragment/effect/residue geometry, material and alpha gaps; never replace '
                       'a native residue or dissipating effect with a complete living character.\n')
        version = out / 'prompts' / (job_id + '_submitted_v4.txt')
        version.write_text(prompt)
        job['prompt'] = str(version.relative_to(REPO))
        job['prepared_assets'].append(dict(path=job['prompt'], sha256=sha(version)))
    assert prompt.startswith(HEADER)
    attempt = dict(submitted_utc=datetime.now(timezone.utc).isoformat(), tool='built-in imagegen',
                   prompt_path=str((REPO / job['prompt']).resolve()),
                   prompt_sha256=sha(REPO / job['prompt']), transparent_background=True,
                   referenced_image_paths=[str(path.resolve()) for path in paths],
                   submitted_inputs=[dict(path=str(path.resolve()), role=role, sha256=sha(path))
                                     for path, role in zip(paths, roles)],
                   matching_outline_attached=True, bootstrap_exception=exception, status='submitted')
    attempt['submitted_layout'] = {key: job[key] for key in
                                  ['native_crop', 'cell_native_size', 'columns', 'rows', 'requested_master']}
    job['attempts'].append(attempt)
    job['status'] = 'submitted'
    run['status'] = 'in_progress'
    save(out / 'run.json', run)
    print(json.dumps(dict(prompt=prompt, referenced_image_paths=attempt['referenced_image_paths'],
                          transparent_background=True, family=stem, job_id=job_id)))


def record(stem, job_id, raw):
    from sheet_checks import screen
    out = STAGE / ('mm8_' + stem) / 'redo_2x'
    run = read(out / 'run.json')
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    attempt = job['attempts'][-1]
    assert attempt['status'] == 'submitted'
    destination = out / 'raw' / (job_id + f'_v{len(job["attempts"])}.png')
    if destination.exists():
        assert sha(destination) == sha(Path(raw))
    else:
        shutil.copy2(raw, destination)
    checks = screen(destination, job['cell_native_size'], [job['columns'], job['rows']], len(job['frames']))
    sampling_flags = [flag for flag in checks['failures'] if 'below 2x' in flag]
    checks['failures'] = [flag for flag in checks['failures'] if flag not in sampling_flags]
    checks['warnings'].extend(sampling_flags)
    attempt.update(raw=str(destination.relative_to(REPO)), sha256=sha(destination),
                   original_output=raw, actual_size=checks['delivered_size'], static_screen=checks,
                   status='returned_review_pending')
    job['selected_raw'] = attempt['raw']
    job['status'] = 'returned_review_pending'
    save(out / 'run.json', run)
    print(json.dumps(dict(family=stem, job=job_id, size=checks['delivered_size'],
                          failures=checks['failures'], warnings=checks['warnings'])))


def process(stem):
    import extract_run
    import register_packed_outline
    import annotate_packed_body
    root = STAGE / ('mm8_' + stem)
    sources = read(root / 'sources.json')
    save(root / 'config.json', dict(family=stem, title=sources['label'], label=sources['label'],
                                    description=ANATOMY[stem], mask_kind='none', matte='magenta'))
    extract_run.native = lambda project, name: native_queue.native(project, name, sources['base_palette'])
    register_packed_outline.process_family.mask = lambda image, config: Image.new('L', image.size)
    project = str(root.relative_to(REPO))
    out = root / 'redo_2x'
    policy = read(out / 'processing.json')
    for job in read(out / 'run.json')['jobs']:
        if not job.get('selected_raw') or len(job['frames']) == 1:
            continue
        policy.setdefault('component_grid_extraction_jobs', [])
        if job['id'] not in policy['component_grid_extraction_jobs']:
            policy['component_grid_extraction_jobs'].append(job['id'])
        policy.setdefault('component_seed_alpha_threshold_by_job', {})[job['id']] = dict(
            raw_sha256=sha(REPO / job['selected_raw']), threshold=32,
            reason='Candidate solid-alpha component seeds avoid near-transparent scatter joining cells. '
                   'All supplied foreground pixels remain assigned once; ownership requires every-pose review.')
    save(out / 'processing.json', policy)
    extract_run.extract(project)
    # Candidate measurements are marked pending correspondence review, not acceptance.
    reviewed_translations = {name: item for name, item in policy.get('frame_translation_calibration', {}).items()
                             if item.get('reviewed_native_contact_placement')}
    annotate_packed_body.annotate(project, False)
    current = read(out / 'processing.json')
    for name, item in reviewed_translations.items():
        clean = REPO / item['clean_path']
        raw = REPO / item['raw_path']
        if clean.exists() and raw.exists() and sha(clean) == item['clean_sha256'] and sha(raw) == item['raw_sha256']:
            current.setdefault('frame_translation_calibration', {})[name] = item
    save(out / 'processing.json', current)
    register_packed_outline.register(project)


def correct_reviewed_grounded_rows(stem, job_ids):
    """Repair demonstrated returned-cell offsets, retaining one common scale and native articulation."""
    import annotate_packed_body
    import register_packed_outline
    register_packed_outline.process_family.mask = lambda image, config: Image.new('L', image.size)
    root = STAGE / ('mm8_' + stem)
    out = root / 'redo_2x'
    source = read(root / 'sources.json')
    run = read(out / 'run.json')
    records = read(out / 'registration.json')
    policy = read(out / 'processing.json')
    changed = []
    for job in run['jobs']:
        if job['id'] not in job_ids:
            continue
        assert job['action'] in ['attack', 'hit', 'fidget'] or (stem in ['m596', 'm600'] and (job['action'] == 'death' or (stem == 'm600' and job['id'].startswith('unused_d_')))) or (stem == 'm608' and job['id'] in ['unused_d_1_sheet', 'unused_d_2_sheet', 'unused_d_3_sheet', 'unused_d_4_sheet', 'unused_a_4_sheet']) or (stem == 'm624' and job['id'] in ['death_0_sheet', 'unused_d_1_sheet', 'unused_d_2_sheet', 'unused_d_3_sheet', 'unused_d_4_sheet', 'unused_a_1_sheet', 'unused_a_2_sheet', 'unused_a_3_sheet']), 'Only explicitly reviewed poses with corresponding native support contacts'
        rows = {}
        for i, name in enumerate(job['frames']):
            r = records.get(name)
            if not r or r['batch'] != job['id'] or name in job['frames'][:i]:
                continue
            clean_path = REPO / r['clean_path']
            clean = Image.open(clean_path).convert('RGBA')
            native = native_queue.native(root, name, source['base_palette'])
            npnt = [v / 2 for v in annotate_packed_body.points(native.resize((native.width * 2, native.height * 2),
                                                       Image.Resampling.NEAREST), 2)['contact_plane']]
            cpnt = annotate_packed_body.points(clean, 2 / r['scale'])['contact_plane']
            effective = np.array([2 / v for v in r['effective_sampling_xy']])
            placed_y = (cpnt[1] * effective[1] + r['translate'][1]) / 2
            rows.setdefault(i // job['columns'], []).append((name, r, npnt, cpnt, npnt[1] - placed_y))
        for row, items in rows.items():
            if len(items) < 2 or max(p[2][1] for p in items) - min(p[2][1] for p in items) > 1:
                continue
            offsets = [p[4] for p in items]
            if abs(float(np.median(offsets))) < 4 or max(offsets) - min(offsets) > 5:
                continue
            for name, r, npnt, cpnt, offset in items:
                policy.setdefault('frame_translation_calibration', {})[name] = dict(
                    raw_sha256=r['raw_sha256'], clean_sha256=r['clean_sha256'],
                    raw_path=r['raw_path'], clean_path=r['clean_path'], axes=[1],
                    landmark='corresponding_native_visible_support_contact', native=npnt, clean=cpnt,
                    reviewed_native_contact_placement=True, reviewed_returned_row=row,
                    observed_logical_offset_before_correction=offset,
                    method='Native/restored sequence review found a shifted returned grid row. Translate each complete '
                           'grounded pose from its corresponding visible support contact to the actual native '
                           'contact coordinate; retain the ONE shared animation scale, every joint and native body bob. '
                           'No resizing or silhouette fitting. Head, waist, knees, wrists and weapon grips require '
                           'independent visual review after correction.')
                changed.append(name)
    save(out / 'processing.json', policy)
    register_packed_outline.register(str(root.relative_to(REPO)))
    print(json.dumps(dict(family=stem, grounded_contact_translations=changed, independent_review_pending=True)))


def fail(stem, job_id, reason):
    path = STAGE / ('mm8_' + stem) / 'redo_2x/run.json'
    run = read(path)
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    job['attempts'][-1].update(status='failed_tool', reason=reason)
    job['status'] = 'failed_tool'
    save(path, run)


def next_job(stem):
    run = read(STAGE / ('mm8_' + stem) / 'redo_2x/run.json')
    pending = next((job['id'] for job in run['jobs'] if job['status'] == 'pending'), None)
    print(json.dumps(dict(job=pending)))


def review_candidates(stem):
    """Bridge shared MM8 material generation and shared packed visual contacts."""
    import review_complete_sheets
    import review_detail_and_alpha
    sys.path.insert(0, str(CREATURES / 'mm8_remaining'))
    import native_materials
    root = STAGE / ('mm8_' + stem)
    out = root / 'redo_2x'
    source = read(root / 'sources.json')
    records = read(out / 'registration.json')
    definitions = {
        'm596': ([], ['All crystal; native family has one palette.']),
        'm600': (['Native organic skin and variant eye colours'], ['Unchanged teeth and highlights']),
        'm604': (['Green mantle and hanging cloth'], ['Undead skin, dark torso, gold fittings, red belt, weapon']),
        'm608': (['Green studded waist band'], ['Grey rock body and detached fragments, eyes']),
        'm612': (['Native scaled body and tail'], ['Unchanged eyes, teeth, horn details']),
        'm616': ([], ['All bone and membranes; native family has one palette.']),
        'm620': (['Green vest'], ['Skin, hair, grey trousers and brown footwear']),
        'm624': (['Green original costume'], ['Skin, hair, gold jewelry, blades, tan snake scales'])
    }
    regions, protected = definitions[stem]
    policy_path = out / 'processing.json'
    policy = read(policy_path)
    materials = dict(regions=regions, protected=protected)
    if stem in ['m604', 'm608', 'm620', 'm624']:
        materials['support'] = dict(green_excess=[0, 6])
    policy['materials'] = materials
    save(policy_path, policy)
    # Shared native_materials expects the source and policy beside the masters.
    save(out / 'sources.json', source)
    native_materials.ROOT = out
    config = native_materials.settings()
    save(out / 'material_settings.json', config)
    for folder in ['toned_2x', 'previews', 'native_variants', 'native_palettes']:
        (out / folder).mkdir(exist_ok=True)
    for palette, item in source['palette_sources'].items():
        destination = out / 'native_palettes' / (str(palette) + '.bin')
        shutil.copy2(REPO / item['path'], destination)
        assert sha(destination) == item['sha256']
    for name, record in records.items():
        path = out / 'aligned_2x' / (name + '.png')
        image = Image.open(path).convert('RGBA')
        shutil.copy2(path, out / 'toned_2x' / path.name)
        mask = native_materials.masks(image, config)
        mask_image = Image.fromarray(mask)
        mask_image.save(out / 'masks_2x' / path.name)
        record['aligned_size_px'] = list(image.size)
        for palette in config['palette_deltas']:
            variant = native_materials.recolor(image, mask_image, int(palette), config)
            assert np.array_equal(np.array(image)[:, :, 3], np.array(variant)[:, :, 3])
            if int(palette) == source['base_palette']:
                assert np.array_equal(image, variant)
            variant.save(out / 'previews' / f'{name}_{palette}.png')
            native_queue.native(root, name, int(palette)).save(out / 'native_variants' / f'{name}_{palette}.png')
    save(out / 'registration.json', records)
    review_complete_sheets.contacts(str(root.relative_to(REPO)))
    review_detail_and_alpha.review(str(root.relative_to(REPO)))
    # The compact palette/mask contact includes every registered bitmap, grouped
    # in small pages at native logical size; no visual acceptance is inferred.
    palettes = list(config['palette_deltas'])
    page_paths = []
    names = sorted(records)
    for start in range(0, len(names), 4):
        selected = names[start:start + 4]
        panel = Image.new('RGB', ((len(palettes) + 1) * 256, len(selected) * 278), '#292d2b')
        draw = ImageDraw.Draw(panel)
        for row, name in enumerate(selected):
            record = records[name]
            origin = record['canvas_origin_px']
            for column, palette in enumerate(palettes + ['mask']):
                original = Image.open(out / ('masks_2x' if palette == 'mask' else 'previews') /
                                      (name + '.png' if palette == 'mask' else f'{name}_{palette}.png'))
                if palette == 'mask':
                    rgba = np.array(Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBA'))
                    coverage = np.array(original) / 255 * .7
                    rgba[:, :, :3] = np.round(rgba[:, :, :3] * (1 - coverage[:, :, None]) +
                                             np.array([255, 100, 0]) * coverage[:, :, None]).astype(np.uint8)
                    original = Image.fromarray(rgba)
                original = original.convert('RGBa').resize((round(original.width / 2), round(original.height / 2)),
                                                            Image.Resampling.LANCZOS).convert('RGBA')
                x, y = column * 256, row * 278
                panel.paste(original, (x + round(origin[0] / 2), y + 22 + round(origin[1] / 2)), original)
                draw.text((x + 3, y + 4), f'{name} {palette}', fill='white')
        path = out / 'review' / f'palette_mask_poses_{start // 4:02d}.png'
        panel.save(path)
        page_paths.append(dict(path=str(path.relative_to(REPO)), sha256=sha(path), frames=selected))
    save(out / 'review/material_checks.json', dict(status='visual_review_pending', frames=len(records),
         all_native_palettes=palettes, base_exact_bypass=True, variant_alpha_unchanged=True,
         masks_from_enhanced_rgb=True, palettes_copied_with_verified_hashes=True, pages=page_paths))
    expanded = []
    for job in read(out / 'run.json')['jobs']:
        names = [name for name in dict.fromkeys(job['frames']) if name in records]
        if not names:
            continue
        bounds = [0, 0, *source['logical_canvas']]
        for name in names:
            rec = records[name]
            origin = np.asarray(rec['canvas_origin_px']) / 2
            dims = np.asarray(Image.open(out / 'aligned_2x' / (name + '.png')).size) / 2
            bounds = [min(bounds[0], math.floor(origin[0])), min(bounds[1], math.floor(origin[1])),
                      max(bounds[2], math.ceil(origin[0] + dims[0])), max(bounds[3], math.ceil(origin[1] + dims[1]))]
        if bounds == [0, 0, *source['logical_canvas']]:
            continue
        tile = [bounds[2] - bounds[0], bounds[3] - bounds[1]]
        cols = min(4, len(names)); rows = math.ceil(len(names) / cols)
        contact = Image.new('RGB', (tile[0] * cols, (tile[1] * 2 + 32) * rows), (42, 45, 42))
        draw = ImageDraw.Draw(contact)
        for i, name in enumerate(names):
            x = i % cols * tile[0]; y = i // cols * (tile[1] * 2 + 32)
            draw.text((x + 3, y + 3), name + ' native / restored; common coordinates', fill='white')
            native = native_queue.native(root, name, source['base_palette'])
            contact.paste(native, (x - bounds[0], y + 22 - bounds[1]), native)
            image = Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBa')
            image = image.resize((image.width // 2, image.height // 2), Image.Resampling.LANCZOS).convert('RGBA')
            origin = records[name]['canvas_origin_px']
            contact.paste(image, (x + round(origin[0] / 2) - bounds[0], y + 22 + tile[1] + round(origin[1] / 2) - bounds[1]), image)
        path = out / 'review' / (job['id'] + '_expanded_registered.png')
        contact.save(path)
        expanded.append(dict(path=str(path.relative_to(out)), sha256=sha(path), frames=names, logical_union=bounds))
    save(out / 'review/expanded_contact_checks.json', dict(status='visual_review_pending', pages=expanded,
         reason='Common-coordinate contacts retain every master pixel beyond the original logical source canvas.'))
    print(json.dumps(dict(family=stem, candidate_material_frames=len(records), palette_review_pages=len(page_paths))))


def export_candidates(stem):
    """Use the existing MM8 exporter, preserving explicit fractional anchors."""
    sys.path.insert(0, str(CREATURES / 'mm8_remaining'))
    import native_package
    root = STAGE / ('mm8_' + stem)
    out = root / 'redo_2x'
    source = read(root / 'sources.json')
    records = read(out / 'registration.json')
    missing = sorted(set(source['sources']) - set(records))
    # The MM8 shared exporter has no partial-unused-art schema. Preserve all native
    # playback bindings and explicitly archive only generation-blocked unused art.
    missing_art = {}
    full_source = read(out / 'sources.json')
    if missing:
        assert all(not source['sources'][name]['referenced'] for name in missing), 'Playback art is missing'
        run = read(out / 'run.json')
        for name in missing:
            job = next(job for job in run['jobs'] if name in job['frames'])
            assert job['status'] == 'failed_tool' and not job.get('selected_raw'), 'Pending work is not final partial coverage'
            asset = source['sources'][name]
            path = out / 'unrestored_native_art' / (name + '.bmp')
            path.parent.mkdir(exist_ok=True)
            shutil.copy2(REPO / asset['path'], path)
            assert sha(path) == asset['sha256']
            native_previews = {}
            for palette in source['palette_sources']:
                preview = out / 'unrestored_native_art' / (name + '_' + palette + '_native_1x.png')
                native_queue.native(root, name, int(palette)).save(preview)
                native_previews[palette] = dict(path=str(preview.relative_to(out)), sha256=sha(preview), pixels_per_logical_pixel=1)
            missing_art[name] = dict(source_path=asset['path'], path=str(path.relative_to(out)), sha256=asset['sha256'],
                native_palette_previews=native_previews, referenced=False, restored=False, job_id=job['id'],
                reason=job['attempts'][-1].get('reason', 'No valid generated return'))
    aliases = {name: canonical for name, canonical in source['pixel_aliases'].items()
               if name in records and canonical in records}
    subset = dict(full_source, sources={name: asset for name, asset in full_source['sources'].items() if name in records},
                  pixel_aliases=aliases, orphan_images=[name for name in full_source['orphan_images'] if name in records])
    save(out / 'sources.json', subset)
    save(out / 'registration.json', {name: record for name, record in records.items() if name not in aliases})
    try:
        native_package.ROOT = out
        native_package.run()
    finally:
        save(out / 'registration.json', records)
        save(out / 'sources.json', full_source)
    path = out / 'draft_manifest.json'
    manifest = read(path)
    manifest.update(label=source['label'], logical_canvas=source['logical_canvas'],
                    logical_pivot=source['logical_pivot'], method=METHOD,
                    actual_generated_sampling=dict(minimum=min(min(r['effective_sampling_xy']) for r in records.values()),
                       below_2x_frames=[name for name, r in records.items() if min(r['effective_sampling_xy']) < 2]),
                    native_palettes={key: dict(path='native_palettes/' + key + '.bin', sha256=value['sha256'])
                                     for key, value in source['palette_sources'].items()},
                    viewer=None, source_run='run.json', installed=False, missing_frames=missing,
                    native_source_frames=len(source['sources']), enhanced_frames=len(records),
                    unrestored_native_art=missing_art, all_playback_art_restored=True,
                    native_anchor_flag_mapping=dict(Center='center', default='bottom_center'))
    for name, frame in manifest['frames'].items():
        origin = np.asarray(frame['aligned_canvas_origin_px'])
        crop = np.asarray(frame['crop_in_aligned_px'][:2])
        size = frame['atlas_xywh'][2:]
        logical_origin = (origin + crop) / 2
        anchors = dict(bottom_center=source['logical_pivot'],
                       center=[source['logical_canvas'][0] / 2, source['logical_canvas'][1] / 2])
        frame.update(native_offset=[0, 0], registration_native_offset=[0, 0],
                     crop_origin_px=(origin + crop).tolist(),
                     logical_crop_origin=logical_origin.tolist(), logical_size=[v / 2 for v in size],
                     native_anchor_mapping={key: (np.asarray(value) - logical_origin).tolist()
                                            for key, value in anchors.items()},
                     mirrored_anchor_mapping={key: [size[0] / 2 - (value[0] - logical_origin[0]),
                                                     value[1] - logical_origin[1]] for key, value in anchors.items()},
                     effective_generated_sampling_xy=records[name]['effective_sampling_xy'],
                     physical_master='aligned_2x/' + name + '.png')
        for key, anchor in frame['native_anchor_mapping'].items():
            assert np.array_equal(np.asarray(anchor) + logical_origin, anchors[key])
        assert np.all(np.equal(logical_origin * 2, np.round(logical_origin * 2)))
    assert manifest['animations'] == source['bindings']
    assert {name for name, f in manifest['frames'].items() if not f['referenced']} == set(source['orphan_images']) - set(missing)
    from exact_placement import validate_manifest
    errors = validate_manifest(manifest, records)
    assert not errors, errors
    if missing:
        manifest['status'] = 'partial_generation_blocked_review_pending'
    save(path, manifest)
    checks_path = out / 'review/export_checks.json'
    checks = read(checks_path)
    checks.update(full_coverage=not missing, native_source_frames=len(source['sources']),
                  enhanced_frames=len(records), missing_frames=missing, all_playback_art_restored=True,
                  unrestored_native_art_archived=bool(missing_art), exact_placement_shared_validator_passed=True,
                  exact_fractional_anchor_mapping=True, exact_mirrored_anchor_mapping=True,
                  exact_native_animation_bindings=True, unused_art_excluded_from_playback=True,
                  generated_sampling_separate_from_physical_tier=True)
    save(checks_path, checks)


def pad_retry(stem, job_id):
    """Enlarge only a demonstrated clipped complete-sheet reference; preserve all old inputs."""
    root = STAGE / ('mm8_' + stem)
    out = root / 'redo_2x'
    run = read(out / 'run.json')
    source = read(root / 'sources.json')
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    assert job.get('selected_raw') and job['status'] == 'returned_review_pending'
    old = {key: job[key] for key in ['native_crop', 'cell_native_size', 'columns', 'rows', 'requested_master']}
    job['attempts'][-1].update(status='rejected_visual_clipping',
        reason='Reviewed native feature contour is cut by the outer returned canvas; enlarge the common native union safety padding.',
        submitted_layout=old)
    crop = [old['native_crop'][0] - 4, old['native_crop'][1] - 4,
            old['native_crop'][2] + 4, old['native_crop'][3] + 4]
    cell = [round(crop[2] - crop[0]), round(crop[3] - crop[1])]
    sampling, _, columns, rows, envelope = best_grid(len(job['frames']), *cell)
    color = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
    outline = Image.new('RGB', color.size, 'white')
    for index, name in enumerate(job['frames']):
        native = native_queue.native(root, name, source['base_palette'])
        array = np.array(native)
        array[array[:, :, 3] == 0] = 0
        native = Image.fromarray(array).resize(tuple(v * 2 for v in source['logical_canvas']), Image.Resampling.NEAREST)
        part = native.crop(tuple(round(v * 2) for v in crop))
        rebuilt = Image.new('RGBA', native.size)
        rebuilt.paste(part, tuple(round(v * 2) for v in crop[:2]))
        assert np.array_equal(np.asarray(rebuilt.convert('RGBa')), np.asarray(native.convert('RGBa')))
        xy = (index % columns * part.width, index // columns * part.height)
        color.paste(part, xy)
        inside = np.asarray(part.getchannel('A'))[::2, ::2] > 0
        edge = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
        guide = np.full((*inside.shape, 3), 255, np.uint8)
        guide[edge] = 0
        outline.paste(Image.fromarray(guide).resize(part.size, Image.Resampling.NEAREST), xy)
    old_padding = job.get('padding_native_px', 2)
    padding = old_padding + 4
    folder = out / 'references' / (job_id + f'_padding{padding}')
    assert not folder.exists(), 'Retain previous submitted inputs unchanged'
    folder.mkdir(exist_ok=True)
    paths = [folder / (job_id + '_native.png'), folder / (job_id + '_outline.png')]
    appearance_path = Path(job['attempts'][-1]['referenced_image_paths'][2])
    paths.append(appearance_path)
    color.save(paths[0])
    outline.save(paths[1])
    prompt = (REPO / job['prompt']).read_text()
    prompt = prompt.replace(str(old['native_crop']), str(crop)).replace(str(old['cell_native_size']), str(cell))
    prompt = prompt.replace(f'{old_padding} native px transparent safety padding', f'{padding} native px transparent safety padding')
    target = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows * cell[1] * 2.8)]
    prompt = prompt.replace(f"{old['columns']} columns by {old['rows']} rows", f'{columns} columns by {rows} rows')
    prompt = prompt.replace(f"{old['requested_master'][0]}x{old['requested_master'][1]}", f'{target[0]}x{target[1]}')
    prompt += ('\nCLIPPING CORRECTION: Preserve the exact native poses and complete original anatomy, costume, '
               'equipment, thin features, effects and extremity tips in EVERY cell. Use the newly enlarged '
               'matching native-colour and outline inputs. Keep every complete silhouette inside the transparent '
               f'canvas with {padding} native pixels of clearance; no outer-edge contact or truncated contour. Preserve '
               'native foot lifts, body bob and original placement, with ONE shared scale for the whole animation.\n')
    path = out / 'prompts' / (job_id + f'_padding{padding}_retry.txt')
    path.write_text(prompt)
    # The selected appearance will be reattached by submit exactly as on other jobs.
    job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=rows, planned_sampling=sampling,
               observed_envelope=list(envelope), references=[str(p.relative_to(REPO)) for p in paths],
               reference_roles=['untouched_native_complete_animation', 'outline_only_geometry_no_shading',
                                'selected_detailed_same_family_appearance_not_pose'],
               requested_master=target, prompt=str(path.relative_to(REPO)), padding_native_px=padding, status='pending')
    job['prepared_assets'].extend(dict(path=str(p.relative_to(REPO)), sha256=sha(p)) for p in [*paths, path])
    job.pop('selected_raw')
    save(out / 'run.json', run)
    print(json.dumps(dict(family=stem, job=job_id, retry_pending=True, padding_native_px=padding)))


def retry_failed_return(stem, job_id):
    root = STAGE / ('mm8_' + stem)
    out = root / 'redo_2x'
    run = read(out / 'run.json')
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    assert job['status'] == 'failed_tool' and len(job['attempts']) == 1
    prompt = (REPO / job['prompt']).read_text()
    prompt += ('\nRESTORATION COVERAGE CHECK: Preserve the native green costume intact in every view. '
               'Do not remove clothing, expose additional anatomy or sexualize the character. '
               'Keep the supplied existing fantasy-game sprite appearance and covered materials exactly.\n')
    assert prompt.startswith(HEADER)
    path = out / 'prompts' / (job_id + '_costume_preservation_retry.txt')
    path.write_text(prompt)
    job['prepared_assets'].append(dict(path=str(path.relative_to(REPO)), sha256=sha(path)))
    job.update(prompt=str(path.relative_to(REPO)), status='pending')
    save(out / 'run.json', run)
    print(json.dumps(dict(family=stem, job=job_id, retry_pending=True, retained_failed_attempt=True)))


def correct_nightmare_rears():
    out = STAGE / 'mm8_m600/redo_2x'
    run = read(out / 'run.json')
    correction = ('\nREAR MULTI-HEAD ANATOMY CORRECTION: This view shows the BACKS of the two tall mouth '
                  'stalk heads in the native colour and outline inputs. Their rear bulbs are CLOSED ORGANIC '
                  'SURFACES, with no tooth opening, lips, smile, frontal eye or face pasted onto those backs. '
                  'Do not rotate a front-facing mouth from Image 3 into this rear view. Reconstruct the native '
                  'closed rear scalp surfaces with skin grain and native shading. Only the small eyeballs whose '
                  'pupils are ACTUALLY visible in each native bitmap may show a pupil; all other stalk ends show '
                  'their native backs. Preserve stalk bends, stump body, posture and every original step.\n')
    for job in run['jobs']:
        if job['view'] not in [3, 4] or job['status'] == 'submitted':
            continue
        if job['id'] in ['walk_3_sheet', 'walk_4_sheet'] and job.get('selected_raw'):
            job['attempts'][-1].update(status='rejected_visual_rear_anatomy',
                reason='Every-pose native comparison found frontal tooth openings added to the closed backs of mouth stalks.')
            job.pop('selected_raw')
            job['status'] = 'pending'
        if job['status'] != 'pending':
            continue
        prompt = (REPO / job['prompt']).read_text()
        if 'REAR MULTI-HEAD ANATOMY CORRECTION' in prompt:
            continue
        path = out / 'prompts' / (job['id'] + '_rear_closed_stalks_retry.txt')
        path.write_text(prompt + correction)
        job.update(prompt=str(path.relative_to(REPO)))
        job['prepared_assets'].append(dict(path=str(path.relative_to(REPO)), sha256=sha(path)))
    save(out / 'run.json', run)
    print(json.dumps(dict(family='m600', rejected_rear_walk_views=[3, 4], corrected_pending_rear_prompts=True)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family', choices=FAMILIES + ['all', 'refine'])
    parser.add_argument('--submit')
    parser.add_argument('--record', nargs=2, metavar=('JOB', 'RAW'))
    parser.add_argument('--process', action='store_true')
    parser.add_argument('--fail', nargs=2, metavar=('JOB', 'REASON'))
    parser.add_argument('--next', action='store_true')
    parser.add_argument('--review', action='store_true')
    parser.add_argument('--export', action='store_true')
    parser.add_argument('--pad-retry')
    parser.add_argument('--retry-failed')
    parser.add_argument('--correct-nightmare-rears', action='store_true')
    parser.add_argument('--correct-grounded-rows', nargs='+')
    args = parser.parse_args()
    if args.family in FAMILIES:
        lock_path = STAGE / ('mm8_' + args.family) / '.session_workflow.lock'
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        session_lock = lock_path.open('a')
        fcntl.flock(session_lock, fcntl.LOCK_EX)
    if args.family == 'refine':
        refine_prompts()
    elif args.submit:
        submit(args.family, args.submit)
    elif args.record:
        record(args.family, *args.record)
    elif args.process:
        process(args.family)
    elif args.fail:
        fail(args.family, *args.fail)
    elif args.next:
        next_job(args.family)
    elif args.review:
        review_candidates(args.family)
    elif args.export:
        export_candidates(args.family)
    elif args.pad_retry:
        pad_retry(args.family, args.pad_retry)
    elif args.retry_failed:
        retry_failed_return(args.family, args.retry_failed)
    elif args.correct_grounded_rows:
        correct_reviewed_grounded_rows(args.family, args.correct_grounded_rows)
    elif args.correct_nightmare_rears:
        assert args.family == 'm600'
        correct_nightmare_rears()
    else:
        for stem in FAMILIES if args.family == 'all' else [args.family]:
            prepare(stem)
