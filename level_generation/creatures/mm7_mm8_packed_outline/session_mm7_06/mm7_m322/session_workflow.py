"""Session-local MM7 schema bridge; reuse shared packing, extraction and atlas operations.

The existing packed preparer accepts only MM6 metadata. This bridge keeps the MM7
descriptor schema and whole cycles without changing shared scripts or prior projects.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = Path(__file__).resolve().parents[5]
SESSION = Path(__file__).resolve().parent.parent
SHARED = REPO / 'level_generation/creatures/mm6_remaining/redo_2x'
sys.path.insert(0, str(SHARED))
from prepare_packed_outline import best_grid, native_2x

FAMILIES = [322, 332, 342, 352, 362, 372, 382, 386]
CONTEXT = ('TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration '
           'of an EXISTING Might and Magic VII (MM7) fantasy role-playing game sprite asset, using the supplied '
           'original animation bitmaps. Restore the existing fantasy-game character and its original animation; '
           'preserve its native costume, material coverage, anatomy and poses. The request is game-art restoration.')


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(REPO))


def prepare():
    inventory = read(REPO / 'level_generation/creatures/remaining_inventory.json')['families']
    descriptor_path = REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt'
    rows = {row.split('\t')[0]: row.split('\t') for row in descriptor_path.read_text().splitlines()}
    for number in FAMILIES:
        family = f'mm7_m{number}'
        old, root = REPO / 'level_generation/creatures' / family, SESSION / family
        if (root / 'run.json').exists():
            run = read(root / 'run.json')
            for job in run['jobs']:
                assert all(sha(REPO / a['path']) == a['sha256'] for a in job['prepared_assets'])
            print(f'{family}: resume {len(run["jobs"])} whole sheets')
            continue
        sources, config, manifest = (read(old / name) for name in ('sources.json', 'config.json', 'manifest.json'))
        inv = next(f for f in inventory if f['world'] == 'mm7' and f'm{number}sa0' in f['standing_images'])
        assert set(sources['sources']) == set(inv['all_native_family_images'])
        assert set(map(int, sources['descriptor_bindings'])) == {d['id'] for d in inv['descriptors']}
        assert sources['palettes'] == inv['palettes']
        for row in sources['descriptor_rows']:
            assert rows[row[0]] == row, f'{family}: current descriptor differs'
        for a in list(sources['sources'].values()) + sources['group_sources'] + list(sources['palette_sources'].values()):
            assert sha(REPO / a['path']) == a['sha256'], a['path']
        sources['logical_canvas'] = sources['logical_canvases'][0]
        for directory in ('references', 'prompts', 'raw', 'review', 'native', 'cleaned', 'aligned_2x', 'masks_2x'):
            (root / directory).mkdir(parents=True, exist_ok=True)
        write(root / 'sources.json', sources)
        # Historical, raw-specific repairs must not be applied to these fresh sheets.
        clean_config = {k: config[k] for k in ('label', 'creature', 'base_palette', 'description', 'materials') if k in config}
        clean_config.update(preserve_delivered_rgb=True, matte='magenta', true_alpha=True)
        write(root / 'config.json', clean_config)
        write(root / 'inventory.json', inv)
        shutil.copy2(old / 'variants.json', root / 'variants.json')
        write(root / 'review/prior_artifact_hashes.json', {rel(p): sha(p) for p in old.rglob('*') if p.is_file()})
        native = {}
        for name, source in sources['sources'].items():
            image, offset = native_2x(source, sources, sources['base_palette'])
            assert offset == [0, 0]
            native[name] = image
            image.resize(tuple(source['size']), Image.Resampling.NEAREST).save(root / f'native/{name}.png')
        jobs, signatures, represented = [], {}, set()
        # Native descriptor truth owns action names; Image1 cycles deduplicate their identical stored view.
        for action in ('walk', 'standing', 'attack', 'shoot', 'hit', 'fidget', 'death', 'corpse'):
            animation = manifest['animations'][action]
            for view, steps in animation['directions'].items():
                if not steps or any(step['mirror'] for step in steps):
                    continue
                names = [step['frame'] for step in steps]
                binding = dict(action=action, view=int(view), native_frames=names,
                               native_group=animation['native_group'])
                signature = tuple(names)
                if signature in signatures:
                    signatures[signature]['bindings'].append(binding)
                    continue
                job = dict(id=f'{action}_{view}_sheet', action=action, view=int(view), frames=names,
                           bindings=[binding], native_sequence=True)
                signatures[signature] = job
                jobs.append(job)
                represented.update(names)
        unused = set(sources['sources']) - represented
        assert unused == set(inv['unreferenced_family_images'])
        groups = {}
        for name in sorted(unused):
            match = re.fullmatch(r'(m\d+)([a-z])([a-z])(\d)', name)
            assert match, name
            groups.setdefault((match[2], int(match[4])), []).append(name)
        for (action, view), names in groups.items():
            jobs.append(dict(id=f'unused_{action}_{view}_sheet', action='unused_native', native_art_action=action,
                             view=view, frames=names, bindings=[], native_sequence=False))
        for job in jobs:
            images = [native[n] for n in job['frames']]
            boxes = [im.getbbox() for im in images]
            assert all(boxes)
            crop2 = [min(b[0] for b in boxes)-4, min(b[1] for b in boxes)-4,
                     max(b[2] for b in boxes)+4, max(b[3] for b in boxes)+4]
            cell = [(crop2[2]-crop2[0])//2, (crop2[3]-crop2[1])//2]
            sampling, _, cols, rows_count, envelope = best_grid(len(images), *cell)
            colour = Image.new('RGBA', (cols*cell[0]*2, rows_count*cell[1]*2))
            outline = Image.new('RGB', colour.size, 'white')
            for index, image in enumerate(images):
                piece = image.crop(crop2)
                reconstruction = Image.new('RGBA', image.size)
                reconstruction.paste(piece, crop2[:2])
                assert np.array_equal(np.array(image), np.array(reconstruction))
                xy = (index % cols * piece.width, index // cols * piece.height)
                colour.paste(piece, xy)
                inside = np.asarray(piece)[:, :, 3][::2, ::2] > 0
                boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
                guide = np.full((*inside.shape, 3), 255, np.uint8)
                guide[boundary] = 0
                outline.paste(Image.fromarray(guide).resize(piece.size, Image.Resampling.NEAREST), xy)
            npth = root / f'references/{job["id"]}_native.png'
            opth = root / f'references/{job["id"]}_outline.png'
            dpth = root / f'references/{job["id"]}_detail.png'
            colour.save(npth)
            outline.save(opth)
            # Adequate accepted same-family art, retaining its generated detail without an extra identity call.
            candidates = list(dict.fromkeys([f'm{number}sa{min(job["view"],4)}', job['frames'][0],
                                              job['frames'][len(job['frames'])//2]]))
            details = []
            for name in candidates:
                im = Image.open(old / f'cleaned/{name}.png').convert('RGBA')
                b = im.getbbox()
                details.append(im.crop((b[0]-6, b[1]-6, b[2]+6, b[3]+6)))
            detail = Image.new('RGBA', (sum(im.width for im in details)+16*(len(details)-1),
                                      max(im.height for im in details)))
            x = 0
            for im in details:
                detail.paste(im, (x, detail.height-im.height))
                x += im.width+16
            detail.save(dpth)
            refs = [npth, opth, dpth]
            view_name = ['front', 'front-oblique', 'profile', 'rear-oblique', 'back'][min(job['view'],4)]
            prompt = (CONTEXT + '\n\nRestore exactly ONE complete packed original ' + job['action'] +
                      f' animation at its {view_name} stored rotation ({job["view"]}) for {config["label"]}. '
                      f'Return ONE transparent RGBA sheet with EXACTLY {len(images)} distinct sprite cells in '
                      f'{cols} columns and {rows_count} rows, chronological ROW-MAJOR order; trailing unused grid '
                      f'cells stay entirely transparent. Native step order: {", ".join(job["frames"])}. '
                      f'Request approximately {envelope[0]} x {envelope[1]} pixels, retaining the submitted grid aspect. '
                      'Every native frame must be present on this single returned sheet. No combined poses, skipped '
                      'endpoints, extra sprites, labels, backdrop, floor, cast shadow or opaque checkerboard.\n\n'
                      'INPUT ROLES: Image 1 is UNTOUCHED native base-palette colour and alpha, the authority for each '
                      'step\'s silhouette, limb anatomy, costume coverage and colours. Image 2 is the matching separate '
                      'OUTLINE-ONLY guide: thin native alpha contours and transparent gaps on white, white interiors, '
                      'with no shading. It guides GEOMETRY ONLY; never reproduce black outlines, edge bands, artificial '
                      'shading stripes or dark carved grooves in the restored art. Image 3 is detailed accepted '
                      'appearance of this exact family: borrow material finish and facial detail only, never its '
                      'pose, changed bulk or placement.\n\n' + config['description'] + '\n\n'
                      'Trace each original limb chain and its joints, near/far ownership, crossings, foreshortening, '
                      'hands and grips, planted versus lifted feet, torso bob, head angle and native accessories. '
                      'Preserve native proportions and motion at every step; retain thin tips and all open gaps. '
                      'Use the SAME native-coordinate union crop, common scale, registration and equal cell dimensions '
                      'for all steps. Do not independently center, size-fit or straighten poses. Transparent safety '
                      'padding is initially 2 native pixels; keep every feature away from the outer sheet boundaries. '
                      'Maintain rich fine material texture, seams, wrinkles, grain and restrained natural directional '
                      'shading, native tonal weight and clear contrast. No washed-out detail, blur, waxy smoothing, '
                      'noisy pseudo-detail or costume redesign. Aim for at least 2x actual new detail, preferably '
                      '2.2x, while completeness of this original whole cycle takes priority. True transparent alpha '
                      'with clean unoutlined antialiasing and no pale or coloured fringe.')
            if not job['native_sequence']:
                prompt += ('\nThese are UNUSED original native bitmaps at this one stored rotation. Preserve exactly '
                           'these original poses; they are retained as artwork and will not be added to playback.')
            pp = root / f'prompts/{job["id"]}_v1.txt'
            pp.write_text(prompt + '\n')
            job.update(columns=cols, rows=rows_count, cell_native_px=cell, native_union_crop=[v/2 for v in crop2],
                       padding_native_px=2, reference_scale=2, requested_output_px=list(envelope),
                       estimated_sampling_native=sampling, prompt=rel(pp), references=[rel(p) for p in refs],
                       prepared_assets=[dict(path=rel(p), sha256=sha(p), role=role)
                                        for p, role in zip(refs, ('untouched_native_colour', 'outline_only_geometry',
                                                                 'detailed_same_family_appearance'))], attempts=[])
        write(root / 'run.json', dict(source_project=rel(old), family=family, source_game='MM7',
              method='packed_complete_animation_outline_only_detailed_appearance', jobs=jobs,
              native_bitmap_count=len(sources['sources']), unused_native_count=len(unused),
              source_descriptor_sha256=sha(descriptor_path), physical_export_tier=2,
              resolution_policy='Whole-cycle priority; measure and review below-2x sheets normally.'))
        print(f'{family}: verified {len(sources["sources"])} native bitmaps, {len(jobs)} whole sheets, {len(sources["palettes"])} palettes')


def ingest(family, job_id, result_path, failure=None):
    with (SESSION / family / '.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _ingest(family, job_id, result_path, failure)


def _ingest(family, job_id, result_path, failure=None):
    root = SESSION / family
    run = read(root / 'run.json')
    job = next(j for j in run['jobs'] if j['id'] == job_id)
    version = len(job['attempts']) + 1
    attempt = dict(version=version, prompt=job['prompt'], prompt_sha256=sha(REPO/job['prompt']),
                   references=job['prepared_assets'])
    if failure:
        attempt.update(status='failed', reason=failure)
    else:
        source = Path(result_path)
        target = root / f'raw/{job_id}_v{version}.png'
        shutil.copy2(source, target)
        im = Image.open(target)
        attempt.update(status='returned_unreviewed', path=rel(target), sha256=sha(target),
                       delivered_px=list(im.size), alpha_extrema=list(im.convert('RGBA').getchannel('A').getextrema()))
        job['selected_raw'] = rel(target)
    job['attempts'].append(attempt)
    write(root / 'run.json', run)
    print(json.dumps(dict(family=family, job=job_id, status=attempt['status'],
                         delivered_px=attempt.get('delivered_px'), alpha_extrema=attempt.get('alpha_extrema'))))


def inputs(index):
    selected = []
    cards = []
    for number in FAMILIES:
        root = SESSION / f'mm7_m{number}'
        run = read(root / 'run.json')
        if index >= len(run['jobs']):
            continue
        job = run['jobs'][index]
        if job.get('selected_raw'):
            continue
        card = Image.new('RGB', (960, 470), (46, 46, 46))
        draw = ImageDraw.Draw(card)
        draw.text((3, 3), f'{root.name}: {job["id"]} ({len(job["frames"])} steps)', fill='white')
        for k, ref in enumerate(job['references']):
            im = Image.open(REPO / ref).convert('RGBA')
            im.thumbnail((312, 435), Image.Resampling.LANCZOS)
            bg = Image.new('RGBA', im.size, (229, 229, 229, 255))
            bg.alpha_composite(im)
            card.paste(bg.convert('RGB'), (k*320, 28))
        cards.append(card)
        selected.append(dict(family=root.name, id=job['id'], prompt=(REPO/job['prompt']).read_text(),
                             references=[str(REPO/p) for p in job['references']]))
    if cards:
        contact = Image.new('RGB', (1920, ((len(cards)+1)//2)*470), (46, 46, 46))
        for i, card in enumerate(cards):
            contact.paste(card, (i % 2 * 960, i // 2 * 470))
        contact.save(SESSION / f'mm7_m322/review/inputs_round_{index:02d}.png')
    print(json.dumps(selected))


def repack(family, job_id, reason):
    """Prepare a complete-sheet retry with larger native-coordinate safety margins."""
    root = SESSION / family
    with (root / '.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        run, sources = read(root / 'run.json'), read(root / 'sources.json')
        job = next(j for j in run['jobs'] if j['id'] == job_id)
        version = len(job['attempts'])+1
        images = [native_2x(sources['sources'][n], sources, sources['base_palette'])[0]
                  for n in job['frames']]
        boxes = [im.getbbox() for im in images]
        pad = max(6, job['padding_native_px']+4)
        crop2 = [min(b[0] for b in boxes)-pad*2, min(b[1] for b in boxes)-pad*2,
                 max(b[2] for b in boxes)+pad*2, max(b[3] for b in boxes)+pad*2]
        cell = [(crop2[2]-crop2[0])//2, (crop2[3]-crop2[1])//2]
        sampling, _, cols, rows_count, envelope = best_grid(len(images), *cell)
        colour = Image.new('RGBA', (cols*cell[0]*2, rows_count*cell[1]*2))
        outline = Image.new('RGB', colour.size, 'white')
        for i, im in enumerate(images):
            piece = im.crop(crop2)
            rebuilt = Image.new('RGBA', im.size)
            rebuilt.paste(piece, crop2[:2])
            assert np.array_equal(np.array(im), np.array(rebuilt))
            xy = (i%cols*piece.width, i//cols*piece.height)
            colour.paste(piece, xy)
            inside = np.asarray(piece)[::2, ::2, 3] > 0
            boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3,3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[boundary] = 0
            outline.paste(Image.fromarray(guide).resize(piece.size, Image.Resampling.NEAREST), xy)
        paths = [root / f'references/{job_id}_v{version}_{role}.png' for role in ('native', 'outline')]
        colour.save(paths[0])
        outline.save(paths[1])
        paths.append(REPO / job['references'][2])
        prompt = (REPO / job['prompt']).read_text()
        prompt = re.sub(r'\d+ columns and \d+ rows', f'{cols} columns and {rows_count} rows', prompt)
        prompt = re.sub(r'Request approximately \d+ x \d+ pixels',
                        f'Request approximately {envelope[0]} x {envelope[1]} pixels', prompt)
        prompt = re.sub(r'padding is initially \d+ native pixels', f'padding is now {pad} native pixels', prompt)
        prompt += ('\nCOMPLETE-SHEET CORRECTION: ' + reason +
                   f' Keep the full {pad}-native-pixel safety margin around EVERY cell and all outer edges. '
                   'Retain the complete native cycle, all poses and rich surface detail.\n')
        prompt_path = root / f'prompts/{job_id}_v{version}.txt'
        prompt_path.write_text(prompt)
        if job.get('selected_raw'):
            selected = next(a for a in job['attempts'] if a.get('path') == job['selected_raw'])
            selected.update(status='rejected', review_reason=reason)
        job.update(columns=cols, rows=rows_count, cell_native_px=cell, native_union_crop=[v/2 for v in crop2],
                   padding_native_px=pad, requested_output_px=list(envelope), estimated_sampling_native=sampling,
                   prompt=rel(prompt_path), references=[rel(p) for p in paths],
                   prepared_assets=[dict(path=rel(p), sha256=sha(p), role=role) for p, role in zip(paths,
                     ('untouched_native_colour', 'outline_only_geometry', 'detailed_same_family_appearance'))])
        job.pop('selected_raw', None)
        job.pop('processing_status', None)
        write(root / 'run.json', run)
        print(json.dumps(dict(family=family, id=job_id, prompt=prompt,
                             references=[str(p) for p in paths])))


def process(family):
    with (SESSION / family / '.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _process(family)


def _process(family):
    from extract_run import connected_cells
    from annotate_packed_body import points
    import process_family as extraction
    root = SESSION / family
    run, sources = read(root / 'run.json'), read(root / 'sources.json')
    policy = read(root / 'processing.json') if (root / 'processing.json').exists() else {}
    registration = {}
    failures = []
    for job in run['jobs']:
        if not job.get('selected_raw'):
            continue
        raw_path = REPO / job['selected_raw']
        raw = Image.open(raw_path).convert('RGBA')
        pixels = np.array(raw)
        alpha = pixels[:, :, 3]
        # Retain genuine delivered edge/whisker pixels; exclude only faint distant background noise.
        distance = ndimage.distance_transform_edt(alpha < 64)
        noise = (alpha <= 8) & (distance > 6)
        pixels[noise] = 0
        pixels[pixels[:, :, 3] == 0] = 0
        cleaned_sheet = Image.fromarray(pixels)
        try:
            mode = policy.get('extraction_mode_by_job', {}).get(job['id'])
            if mode:
                assert mode['raw_sha256'] == sha(raw_path) and mode['reason']
                assert mode['mode'] in ('verified_alpha_gutters', 'ordered_components')
            if mode and mode['mode'] == 'ordered_components':
                cells = connected_cells(cleaned_sheet, job, grid_groups=False, seed_alpha_threshold=64)
            elif mode:
                foreground = pixels[:, :, 3] > 0
                ycuts = extraction.gutters(foreground.any(axis=1), job['rows'])
                cells = []
                retained = 0
                for i in range(len(job['frames'])):
                    row, col = divmod(i, job['columns'])
                    xcuts = extraction.gutters(foreground[ycuts[row]:ycuts[row+1]].any(axis=0), job['columns'])
                    rect = [xcuts[col], ycuts[row], xcuts[col+1], ycuts[row+1]]
                    clean = cleaned_sheet.crop(rect)
                    retained += int((np.asarray(clean)[:, :, 3] > 0).sum())
                    cells.append((rect, clean))
                assert retained == int(foreground.sum()), 'Gutters must preserve every foreground pixel once'
            else:
                cells = connected_cells(cleaned_sheet, job, grid_groups=True, seed_alpha_threshold=64)
            nominal = min(raw.width/(job['columns']*job['cell_native_px'][0]),
                          raw.height/(job['rows']*job['cell_native_px'][1]))
            first_native = native_2x(sources['sources'][job['frames'][0]], sources, sources['base_palette'])[0]
            npoints = points(first_native, 2)
            cpoints = points(cells[0][1], nominal)
            overrides = policy.get('anatomical_point_overrides', {}).get(job['id'], {})
            if overrides:
                assert policy['override_raw_sha256'][job['id']] == sha(raw_path)
                for label, pair in overrides.items():
                    npoints[label] = [v*2 for v in pair['native']]
                    cpoints[label] = pair['clean']
            if policy.get('sampling_basis_by_job', {}).get(job['id']) == 'paired_distance':
                assert overrides, 'Paired-distance sampling needs reviewed corresponding anatomy points.'
                sampling = (np.linalg.norm(np.array(cpoints['contact_plane'])-cpoints['body_cap']) /
                            (np.linalg.norm(np.array(npoints['contact_plane'])-npoints['body_cap'])/2))
            else:
                sampling = ((cpoints['contact_plane'][1]-cpoints['body_cap'][1]) /
                            ((npoints['contact_plane'][1]-npoints['body_cap'][1])/2))
            assert sampling > 0
            factor = 2/sampling
            job_dir = root / 'review' / job['id']
            job_dir.mkdir(exist_ok=True)
            records = []
            pose_images = []
            shared_grid = policy.get('shared_sheet_registration', {}).get(job['id'])
            if shared_grid:
                assert shared_grid['raw_sha256'] == sha(raw_path) and shared_grid['reason']
            first_translation = None
            for i, (name, (rect, clean)) in enumerate(zip(job['frames'], cells)):
                clean_path = job_dir / f'{name}__step_{i}.png'
                clean.save(clean_path)
                native = native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
                npnts, cpnts = points(native, 2), points(clean, sampling)
                manual = policy.get('pose_point_overrides', {}).get(job['id'], {}).get(name)
                if manual:
                    assert policy['override_raw_sha256'][job['id']] == sha(raw_path)
                    npnts['body_cap'] = [v*2 for v in manual['native']]
                    cpnts['body_cap'] = manual['clean']
                elif i == 0 and overrides:
                    npnts, cpnts = npoints, cpoints
                size = [max(1, round(v*factor)) for v in clean.size]
                effective = np.array(size)/clean.size
                translation = np.round(np.array(npnts['body_cap'])-np.array(cpnts['body_cap'])*effective).astype(int)
                if shared_grid:
                    if first_translation is None:
                        first_translation = translation.copy()
                    row_index, column_index = divmod(i, job['columns'])
                    cell_origin = np.array([column_index*raw.width/job['columns'], row_index*raw.height/job['rows']])
                    translation = np.round(first_translation+(np.array(rect[:2])-cell_origin-
                                           np.array(cells[0][0][:2]))*factor).astype(int)
                scaled = clean.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
                bounds = scaled.getbbox()
                origin = np.minimum([0, 0], translation+np.array(bounds[:2])-4)
                end = np.maximum(np.array(sources['logical_canvas'])*2, translation+np.array(bounds[2:])+4)
                aligned = Image.new('RGBA', tuple(end-origin))
                aligned.paste(scaled, tuple(translation-origin))
                a = np.array(clean)[:, :, 3]
                clip = bool((rect[0] == 0 and (a[:, 0]>64).any()) or
                            (rect[1] == 0 and (a[0]>64).any()) or
                            (rect[2] == raw.width and (a[:, -1]>64).any()) or
                            (rect[3] == raw.height and (a[-1]>64).any()))
                row = dict(batch=job['id'], raw_size=list(raw.size), raw_sha256=sha(raw_path), raw_rect=rect,
                           scale=factor, actual_generated_sampling=sampling, translate=translation.tolist(),
                           canvas_origin_px=origin.tolist(), raw_clip=clip, clean_path=rel(clean_path),
                           clean_sha256=sha(clean_path), native_landmarks=npnts, clean_landmarks=cpnts,
                           method='Shared first-pose body-cap/contact-plane scale; whole-pose body-cap translation. '
                                  'Independent torso, limb and contact features require visual review.')
                if shared_grid:
                    row['method'] = ('One reviewed first-pose joint-to-foot scale and corresponding joint anchor; '
                                     'shared returned-cell coordinate transform preserves within-sheet motion. '
                                     'Other automatically detected cap/torso points are diagnostic only.')
                if policy.get('sampling_basis_by_job', {}).get(job['id']) == 'paired_distance':
                    row['method'] = ('Uniform scale from reviewed corresponding left/right wrists; '
                                     'left wrist translation. Independent hips, soles and body depth require visual review.')
                records.append(dict(frame=name, **row))
                pose_images.append((native, aligned, origin, npnts, cpnts, effective, translation))
                if name not in registration:
                    registration[name] = row
                    aligned.save(root / f'aligned_2x/{name}.png')
                    clean.save(root / f'cleaned/{name}.png')
                else:
                    registration[name].setdefault('reused_in_jobs', []).append(dict(job=job['id'], step=i))
            # Review uses one shared union that also contains all delivered detail outside the native contour.
            crop = [round(v*2) for v in job['native_union_crop']]
            for native, aligned, origin, *_ in pose_images:
                b = aligned.getbbox()
                crop = [min(crop[0], b[0]+origin[0]-4), min(crop[1], b[1]+origin[1]-4),
                        max(crop[2], b[2]+origin[0]+4), max(crop[3], b[3]+origin[1]+4)]
            tile_w, tile_h = crop[2]-crop[0], crop[3]-crop[1]
            contact = Image.new('RGB', (tile_w*len(cells), tile_h*2+60), (42, 42, 42))
            draw = ImageDraw.Draw(contact)
            for i, (native, aligned, origin, npnts, cpnts, effective, translation) in enumerate(pose_images):
                for kind, im, offset in [('native', native, [0, 0]), ('enhanced', aligned, origin)]:
                    box = [crop[k]-int(offset[k%2]) for k in range(4)]
                    piece = im.crop(box)
                    bg = Image.new('RGBA', piece.size, (229,229,229,255) if kind == 'enhanced' else (42,42,42,255))
                    bg.alpha_composite(piece)
                    dy = 26 if kind == 'native' else 38+tile_h
                    contact.paste(bg.convert('RGB'), (i*tile_w, dy))
                    marker = ImageDraw.Draw(contact)
                    for label, color in [('body_cap', '#00dddd'), ('contact_plane', '#ddcc00'),
                                         ('torso_left', '#ff6666'), ('torso_right', '#ff6666')]:
                        pt = npnts[label] if kind == 'native' else np.array(cpnts[label])*effective+translation
                        x, y = i*tile_w+pt[0]-crop[0], dy+pt[1]-crop[1]
                        marker.ellipse((x-2,y-2,x+2,y+2), fill=color)
                draw.text((i*tile_w+3, 4), job['frames'][i], fill='white')
            contact.save(root / f'review/{job["id"]}_poses.png')
            write(job_dir / 'registration_candidates.json', dict(raw=job['selected_raw'], sampling=sampling,
                  faint_distant_noise_excluded=int(noise.sum()), frames=records,
                  status='pending_pose_placement_detail_alpha_palette_review'))
            job['processing_status'] = 'registered_pending_review'
            job['generated_sampling'] = sampling
            if any(r['raw_clip'] for r in records):
                failures.append(dict(job=job['id'], reason='Visible alpha reaches outer raw boundary; inspect/retry complete sheet.'))
        except (AssertionError, ValueError) as error:
            job['processing_status'] = 'extraction_failed'
            failures.append(dict(job=job['id'], reason=str(error)))
    write(root / 'registration.json', registration)
    write(root / 'review/processing_failures.json', failures)
    write(root / 'run.json', run)
    print(json.dumps(dict(family=family, registered=len(registration), expected=run['native_bitmap_count'], failures=failures)))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def landmarks(family, action):
    """Expose native and delivered coordinates for a demonstrated registration correction."""
    root = SESSION / family
    run, sources = read(root / 'run.json'), read(root / 'sources.json')
    selected = [j for j in run['jobs'] if j['action'] == action and j.get('selected_raw')]
    sheet = Image.new('RGB', (1100, len(selected)*410), (235,235,235))
    draw = ImageDraw.Draw(sheet)
    rows = []
    for row, job in enumerate(selected):
        report = read(root / f'review/{job["id"]}/registration_candidates.json')
        frame = report['frames'][0]
        native = native_2x(sources['sources'][frame['frame']], sources, sources['base_palette'])[0]
        nb = native.getbbox()
        crop = [max(0,nb[0]-8),max(0,nb[1]-8),min(native.width,nb[2]+8),min(native.height,nb[3]+8)]
        native = native.crop(crop)
        clean = Image.open(REPO/frame['clean_path']).convert('RGBA')
        display_scale = min(1,520/clean.width,365/clean.height)
        for image, x, origin, scale in [(native,0,crop[:2],2),(clean,530,[0,0],display_scale)]:
            if x:
                image = image.resize((round(image.width*scale),round(image.height*scale)), Image.Resampling.LANCZOS)
            bg = Image.new('RGBA', image.size, (235,235,235,255))
            bg.alpha_composite(image)
            sheet.paste(bg.convert('RGB'), (x,row*410+30))
            for axis in range(2):
                start, end = origin[axis]/scale, (origin[axis]+image.size[axis])/scale
                step = 20 if scale >= .75 else 100
                for v in range(int(start//step)*step, int(end)+1,step):
                    p = int(v*scale-origin[axis])
                    if axis == 0:
                        draw.line((x+p,row*410+30,x+p,row*410+30+image.height),fill='#bbbbbb')
                        draw.text((x+p+1,row*410+18),str(v),fill='black')
                    else:
                        draw.line((x,row*410+30+p,x+image.width,row*410+30+p),fill='#bbbbbb')
                        draw.text((x,row*410+30+p+1),str(v),fill='black')
        draw.text((3,row*410+2),job['id']+' NATIVE logical pixels / CLEAN delivered pixels',fill='black')
        rows.append(dict(job=job['id'],raw_sha256=frame['raw_sha256'],native_crop_2x=crop,
                         clean_size=list(clean.size),raw_rect=frame['raw_rect']))
    sheet.save(root / f'review/{action}_landmark_coordinates.png')
    print(json.dumps(rows))


def protect_fixed_warm_materials(root, sources, config, selected):
    """Keep enhanced recolor coverage off native-located fixed skin/leather details.

    Native colors locate small material boxes, rather than supplying resized masks.
    Enhanced RGB remains the material coverage and generated alpha is unchanged.
    """
    palettes = [np.frombuffer((REPO / item['path']).read_bytes()[:768], np.uint8).reshape(256,3)
                for item in sources['palette_sources'].values()]
    base = np.frombuffer((REPO / sources['palette_sources'][str(sources['base_palette'])]['path']).read_bytes()[:768],
                         np.uint8).reshape(256,3).astype(float)
    fixed = np.logical_and.reduce([np.all(p == base,axis=1) for p in palettes])
    r,g,b = base.T
    warm = fixed & (r>80) & (g/r.clip(1)>.40) & (g/r.clip(1)<.85) & (b/g.clip(1)>.35) & (b/g.clip(1)<.92)
    if root.name == 'mm7_m332':
        # Native deeply shaded hands and neutral dagger sheath are fixed too.
        warm = fixed & (r>15) & (((g/r.clip(1)>.40)&(g/r.clip(1)<.85)&
                (b/g.clip(1)>.35)&(b/g.clip(1)<.92)) | ((base.max(axis=1)-base.min(axis=1))<18))
    warm[0] = False
    annotations = {}
    registration = read(root/'registration.json')
    for name in selected:
        indices = np.asarray(Image.open(REPO/sources['sources'][name]['path']))
        mask = np.asarray(Image.open(root/f'masks_2x/{name}.png')).copy()
        enhanced = np.asarray(Image.open(root/f'aligned_2x/{name}.png').convert('RGBA'))
        er,eg,eb = enhanced[:,:,:3].astype(float).transpose(2,0,1)
        origin = registration[name]['canvas_origin_px']
        yy,xx = np.indices(mask.shape[:2]);xx=(xx+origin[0])/2;yy=(yy+origin[1])/2
        records = []
        for channel,region in enumerate(config['materials']['regions']):
            if not region.get('protect_fixed_warm_materials'):
                continue
            ys,xs = np.where(np.isin(indices,region['palette_indices']))
            if not len(xs):
                continue
            native_y,native_x = np.indices(indices.shape)
            vicinity = 15 if root.name == 'mm7_m332' else 6
            nearby = ((native_x>=xs.min()-vicinity)&(native_x<=xs.max()+vicinity)&
                      (native_y>=ys.min()-vicinity)&(native_y<=ys.max()+vicinity))
            skin = np.isin(indices,np.flatnonzero(warm)) & nearby
            labels,count = ndimage.label(ndimage.binary_closing(skin,iterations=1))
            protected = np.zeros(mask.shape[:2],float)
            for component in range(1,count+1):
                cy,cx=np.where(labels==component)
                if len(cx)<3:
                    continue
                box=[int(cx.min()),int(cy.min()),int(cx.max()),int(cy.max())]
                if root.name == 'mm7_m332':
                    box = [box[0]-12,box[1]-12,box[2]+12,box[3]+12]
                # A small soft box protects refined skin a little beyond native seeds.
                guard=4.5 if root.name == 'mm7_m352' else 2.5
                support=(np.clip((xx-box[0]+guard)/guard,0,1)*np.clip((box[2]+guard-xx)/guard,0,1)*
                         np.clip((yy-box[1]+guard)/guard,0,1)*np.clip((box[3]+guard-yy)/guard,0,1))
                if root.name == 'mm7_m332':
                    # Native seeds locate the vicinity; delivered tan skin defines
                    # full hand coverage, including refined fingers beyond tiny seeds.
                    support *= ((er>10)&(eg/er.clip(1)>.40)&(eg/er.clip(1)<1.16)&
                                (eb/eg.clip(1)>.40)&(eb/eg.clip(1)<1.12))
                if root.name == 'mm7_m342':
                    # A broad skin component includes the face, neck and shoulders.
                    # Its coarse ellipse protects those anatomical locations while
                    # clearing the rectangle's corners that contain long side hair.
                    cx0,cy0=(box[0]+box[2])/2,(box[1]+box[3])/2
                    rx,ry=max((box[2]-box[0])/2+2,3),max((box[3]-box[1])/2+2,3)
                    ellipse=np.clip((1.20-np.sqrt(((xx-cx0)/rx)**2+((yy-cy0)/ry)**2))/.15,0,1)
                    bright_skin=((er>90)&(eg/er.clip(1)>.66)&(eb/eg.clip(1)>.74))
                    support *= np.maximum(ellipse,bright_skin)
                if root.name == 'mm7_m352':
                    # Fixed face seeds locate skin, but their rectangular bounds also
                    # cross restored dark beard strands. Protect delivered skin tones,
                    # rather than suppressing all hair coverage within those bounds.
                    # Hair coverage must never recolor the skin-located face box.
                    # The separately located beard channel retains dark strands.
                    if region['name'] == 'beard':
                        support *= np.clip((er-45)/10,0,1)
                protected=np.maximum(protected,support)
                records.append(dict(material=region['name'],fixed_colour_seed_box=box,soft_guard_native_px=guard))
            mask[:,:,channel] = np.round(mask[:,:,channel]*(1-protected)).astype(np.uint8)
        Image.fromarray(mask).save(root/f'masks_2x/{name}.png')
        annotations[name]=dict(raw_sha256=registration[name]['raw_sha256'],protected_material_locations=records)
    write(root/'review/material_protection.json',dict(policy='Fixed warm native colors locate soft protected material boxes; '
          'enhanced RGB defines recolorable coverage. No native alpha stencil, art RGB or alpha changes.',frames=annotations))


def export(family, partial=False):
    root = SESSION / family
    sources, config, run = (read(root / p) for p in ('sources.json', 'config.json', 'run.json'))
    registration = read(root / 'registration.json')
    failures = read(root / 'review/processing_failures.json')
    if not partial:
        assert set(registration) == set(sources['sources']), 'Partial family: use explicit partial export.'
        assert all(j.get('selected_raw') and j.get('processing_status') == 'registered_pending_review' for j in run['jobs'])
        assert not failures, 'Resolve recorded clipping/extraction failures first.'
    rejected = {f['job'] for f in failures}
    active_jobs = {j['id'] for j in run['jobs'] if j.get('selected_raw') and
                   j.get('processing_status') == 'registered_pending_review' and j['id'] not in rejected}
    selected = {n:r for n,r in registration.items() if r['batch'] in active_jobs}
    assert selected
    number = int(family[-3:])
    if number in (322, 332, 342, 352):
        prior = read(REPO / f'level_generation/creatures/{family}/variants.json')
        names = {322: ['trousers', 'hair'], 332: ['trousers', 'hair'],
                 342: ['green_cloth', 'hair'], 352: ['tunic', 'hair', 'beard']}[number]
        selectors = {322: ['green', 'burgundy'], 332: ['purple', 'cream'],
                     342: ['green', 'burgundy'], 352: ['green', 'warm_body', 'warm_body']}[number]
        regions = []
        for index, (name, selector) in enumerate(zip(names, selectors)):
            indices = prior['variants'][0]['regions'][index]['native_indices']
            region = dict(name=name, selector=selector, thresholds=[.025, .13], palette_indices=indices,
                          mask_sigma=.7, native_palette_spatial_support=indices, support_padding=4)
            if number == 332 and name == 'trousers':
                region.update(thresholds=[-.30,-.12], brightness_ceiling=[160,220],protect_fixed_warm_materials=True)
            if name in ('hair', 'beard'):
                region.update(exclude_channels=list(range(index)), support_padding=5)
                if selector == 'burgundy':
                    region.update(thresholds=[.30,.50], brightness_ceiling=[180,230],
                                  minimum_warm_chroma=[.50,.70], minimum_green_over_blue=[.25,.40])
                elif selector == 'cream':
                    region.update(red_penalty=.65, thresholds=[-.025,.08], minimum_warm_chroma=[.10,.24])
                else:
                    region.update(brightness_ceiling=[50,95] if name == 'hair' else [45,85])
                if number in (342,352):
                    region.update(selector='warm_body',thresholds=[.12,.25],brightness_ceiling=[190,240],
                                  protect_fixed_warm_materials=True)
                    region.pop('minimum_warm_chroma',None)
                    region.pop('minimum_green_over_blue',None)
                if number == 352 and name == 'beard':
                    region.update(exclude_channels=[0],support_padding=3,
                                  brightness_ceiling=[50,75])
            regions.append(region)
        config['materials'] = dict(regions=regions, limitation='Native palette ramp fits; enhanced RGB coverage with '
                                   'native material locations as seeds. Inspect hair, facial hair and protected skin.')
    if config.get('materials'):
        # Recompute coverage on fresh enhanced pixels; preserve native ramp parameters, never old pose repairs.
        for region in config['materials']['regions']:
            region.pop('frame_exclude_polygons', None)
        config['identity_frames'] = [n for n in sources['sources'] if 'sa' in n][:5]
        write(root / 'config.json', config)
        shared_process = load_module('process', REPO / 'level_generation/creatures/mm7_m514/process.py')
        materials = load_module('session_mm7_materials', REPO / 'level_generation/creatures/mm7_ambient/material_variants.py')
        materials.run(root)
        if number in (332,342,352):
            protect_fixed_warm_materials(root,sources,config,selected)
        if number == 352:
            # This native base has almost-zero monochrome hair ramps. Applying their gain
            # directly to newly restored brown highlights clips them to flat yellow/white.
            # Match the ramp's shade range to delivered material luminance before tinting.
            variants = read(root / 'variants.json')
            palette = np.frombuffer((REPO / sources['palette_sources'][str(sources['base_palette'])]['path']).read_bytes()[:768],
                                    np.uint8).reshape(256,3)
            luma = np.array([.2126,.7152,.0722])
            calibrations = {}
            for channel in (1,2):
                spec = config['materials']['regions'][channel]
                samples = []
                for name in selected:
                    rgba = np.asarray(Image.open(root / f'aligned_2x/{name}.png').convert('RGBA'))
                    mask = np.asarray(Image.open(root / f'masks_2x/{name}.png'))[:,:,channel]
                    values = rgba[:,:,:3][(mask>160)&(rgba[:,:,3]>240)] @ luma
                    if len(values):
                        samples.extend(values[::max(1,len(values)//128)].tolist())
                native_high = float((palette[spec['palette_indices']] @ luma).max())
                enhanced_high = float(np.percentile(samples,90)) if samples else max(native_high,1)
                ratio = min(1,native_high/max(enhanced_high,1))
                calibrations[spec['name']] = dict(native_ramp_max_luminance=native_high,
                    delivered_material_luminance_90th=enhanced_high, gain_normalization=ratio,
                    limitation='A near-zero native ramp cannot encode restored strand shading exactly. Base bypass stays exact.')
                for variant in variants['variants']:
                    if not variant['exact_bypass']:
                        matrix = np.array(variant['regions'][channel]['rgb_matrix'])*ratio
                        region = variant['regions'][channel]
                        region['native_unscaled_fit_mean_channel_error'] = region['native_fit_mean_channel_error']
                        region['rgb_matrix'] = matrix.tolist()
                        target_palette = np.frombuffer((REPO / sources['palette_sources'][str(variant['palette_id'])]['path']).read_bytes()[:768],
                                                       np.uint8).reshape(256,3)
                        region['native_fit_mean_channel_error'] = float(abs(palette[spec['palette_indices']] @ matrix-
                            target_palette[spec['palette_indices']]).mean())
            variants['restored_shade_calibration'] = calibrations
            write(root / 'variants.json',variants)
    else:
        for name in registration:
            im = Image.open(root / f'aligned_2x/{name}.png')
            Image.new('L', im.size).save(root / f'masks_2x/{name}.png')
        shared_process = load_module('process', REPO / 'level_generation/creatures/mm7_m514/process.py')
    package = load_module('session_mm7_package', REPO / 'level_generation/creatures/mm7_m514/package.py')
    if partial:
        # The shared packager requires complete supplied bindings. A temporary, explicitly reduced
        # input exports available art; authoritative full native metadata remains in sources.json.
        work = root / '.partial_package_work'
        work.mkdir(exist_ok=False)
        subset = dict(sources)
        subset['sources'] = {n:sources['sources'][n] for n in selected}
        subset['descriptor_bindings'] = {}
        full_native = read(REPO / f'level_generation/creatures/{family}/manifest.json')['descriptor_animations']
        omitted = {}
        for descriptor, animations in full_native.items():
            included = {}
            omitted[descriptor] = []
            for action, animation in animations.items():
                names = {s['frame'] for steps in animation['directions'].values() for s in steps}
                if names <= set(selected):
                    included[action] = sources['descriptor_bindings'][descriptor][action]
                else:
                    omitted[descriptor].append(action)
            subset['descriptor_bindings'][descriptor] = included
        write(work / 'sources.json', subset)
        write(work / 'registration.json', selected)
        for name in ('config.json', 'variants.json'):
            shutil.copy2(root / name, work / name)
        for directory in ('aligned_2x', 'masks_2x', 'cleaned'):
            (work / directory).symlink_to(root / directory, target_is_directory=True)
        (work / 'review').mkdir()
        try:
            package.run(work)
            for directory in ('atlas', 'trimmed_2x', 'trimmed_masks_2x', 'previews'):
                shutil.copytree(work / directory, root / directory, dirs_exist_ok=True)
            for name in ('manifest.json', 'validation.json', 'review/edge_audit.json', 'review/edge_closeups.png'):
                shutil.copy2(work / name, root / name)
        finally:
            shutil.rmtree(work)
    else:
        package.run(root)
    manifest = read(root / 'manifest.json')
    for name, frame in manifest['frames'].items():
        frame['native_offset'] = [(sources['logical_canvas'][0]-frame['source_canvas'][0])/2,
                                  sources['logical_canvas'][1]-frame['source_canvas'][1]]
        frame['registration_native_offset'] = frame['native_offset']
    manifest['generated_detail'] = dict(measured_minimum=min(r['actual_generated_sampling'] for r in selected.values()),
        physical_export_tier=2, sampling_by_complete_sheet={j['id']:j['generated_sampling'] for j in run['jobs'] if j['id'] in active_jobs},
        resolution_policy=run['resolution_policy'])
    if partial:
        manifest['schema_status'] = 'PARTIAL offline candidate export; incomplete family; not accepted or installed'
        manifest['native_descriptor_animations'] = full_native
        manifest['native_group_bindings_full'] = sources['descriptor_bindings']
        manifest['source_coverage'] = dict(expected=len(sources['sources']), exported=len(selected),
            missing=sorted(set(sources['sources'])-set(selected)), omitted_playback_actions=omitted,
            rule='Only complete available native actions enter candidate playback. Full original bindings are retained separately.')
    manifest['limitations'] = ['AI material detail is an interpretation of native artwork. Static pose review; '
                               'not installed into gameplay. Palette ramp fits retain shading with the documented approximation.']
    write(root / 'manifest.json', manifest)
    sys.path.insert(0, str(REPO / 'level_generation/creatures'))
    from exact_placement import validate_manifest
    assert not validate_manifest(manifest, registration)
    # The shared MM7 exporter reconstructs every native descriptor sequence directly from saved native groups.
    for descriptor, animations in manifest['descriptor_animations'].items():
        for action, animation in animations.items():
            group = sources['groups'][sources['descriptor_bindings'][descriptor][action]]
            assert animation['animation_length_raw'] == group['animation_length_raw']
            for view, sequence in animation['directions'].items():
                assert len(sequence) == len(group['frames'])
                for step, native in zip(sequence, group['frames']):
                    single = 'Image1' in native['flags']
                    mirror = not single and f'Mirror{view}' in native['flags']
                    stored = 8-int(view) if mirror else int(view)
                    expected = native['texture_name'].lower()+('' if single else str(stored))
                    assert step['frame'] == expected and step['mirror'] == mirror
                    assert step['duration_raw'] == native['frame_length_raw'] and step['flags'] == native['flags']
                    assert step['scale'] == native.get('scale',1) and step['palette_id'] == native['palette_id']
    viewer = load_module('session_mm7_viewer', REPO / 'level_generation/creatures/mm7_m514/build_viewer.py')
    viewer.run(root)
    if 'walk' not in manifest['animations']:
        path = root / 'viewer.html'
        path.write_text(path.read_text().replace("if(!q.has('action'))$('action').value='walk';",
                                                "if(!q.has('action'))$('action').value='standing';"))
    validation = read(root / 'validation.json')
    validation.update(exact_native_anchors=True, native_descriptor_bindings_verified=True,
                      whole_animation_jobs=len(active_jobs), unused_art_retained_without_playback=True,
                      family_complete=set(selected)==set(sources['sources']),
                      visual_acceptance_frozen=False)
    write(root / 'validation.json', validation)


def review_pages(family):
    """Expose every exported pose, delivered 100% detail, palette and mask for offline inspection."""
    root = SESSION / family
    manifest, registration = read(root / 'manifest.json'), read(root / 'registration.json')
    shared = load_module('session_review_process', REPO / 'level_generation/creatures/mm7_m514/process.py')
    names = list(manifest['frames'])
    variants = read(root / 'variants.json')['variants']
    evidence = dict(base_pose_pages=[], delivered_detail_pages=[], palette_mask_pages=[], frames=names,
                    rendered_all_exported_palettes=True, generated_detail_crop_scale=1,
                    status='Prepared evidence; visual review must be recorded separately.')
    standing = [n for n in names if 'sa' in n][:5]
    identity = Image.new('RGB',(len(standing)*240,len(variants)*280),(45,45,45));draw=ImageDraw.Draw(identity)
    for col,name in enumerate(standing):
        im=Image.open(root/f'aligned_2x/{name}.png').convert('RGBA');mask=Image.open(root/f'masks_2x/{name}.png')
        for row,variant in enumerate(variants):
            piece=shared.apply_variant(im,mask,variant).convert('RGBa').resize((240,240),Image.Resampling.LANCZOS).convert('RGBA')
            bg=Image.new('RGBA',piece.size,(45,45,45,255));bg.alpha_composite(piece)
            identity.paste(bg.convert('RGB'),(col*240,row*280+22));draw.text((col*240+2,row*280+2),name+' '+str(variant['palette_id']),fill='white')
    identity.save(root/'review/identity_variants.png')
    # Shared logical bounds include all native and enhanced pixels. Never size-fit individual frames.
    bounds = [512, 512, 0, 0]
    for name in names:
        im = Image.open(root / f'aligned_2x/{name}.png').convert('RGBA')
        b = im.getbbox(); origin = registration[name]['canvas_origin_px']
        native = Image.open(root / f'native/{name}.png').convert('RGBA')
        n = native.getbbox()
        bounds = [min(bounds[0], b[0]+origin[0], n[0]*2), min(bounds[1], b[1]+origin[1], n[1]*2),
                  max(bounds[2], b[2]+origin[0], n[2]*2), max(bounds[3], b[3]+origin[1], n[3]*2)]
    bounds = [bounds[0]-6, bounds[1]-6, bounds[2]+6, bounds[3]+6]
    def render(im, origin, scale, bg):
        crop = im.crop([bounds[k]-origin[k%2] for k in range(4)])
        crop = crop.convert('RGBa').resize((round(crop.width*scale),round(crop.height*scale)),
                                          Image.Resampling.LANCZOS).convert('RGBA')
        result = Image.new('RGBA', crop.size, (*bg,255)); result.alpha_composite(crop)
        return result.convert('RGB')
    for page, start in enumerate(range(0,len(names),40)):
        subset = names[start:start+40]
        tile = [round((bounds[2]-bounds[0])*.5),round((bounds[3]-bounds[1])*.5)]
        cell = [tile[0]*2+8,tile[1]+22]
        out = Image.new('RGB',(cell[0]*5,cell[1]*((len(subset)+4)//5)),(45,45,45));d=ImageDraw.Draw(out)
        for i,name in enumerate(subset):
            x,y=i%5*cell[0],i//5*cell[1]
            native=Image.open(root/f'native/{name}.png').convert('RGBA').resize((512,512),Image.Resampling.NEAREST)
            enhanced=Image.open(root/f'aligned_2x/{name}.png').convert('RGBA')
            out.paste(render(native,[0,0],.5,(45,45,45)),(x,y+20))
            out.paste(render(enhanced,registration[name]['canvas_origin_px'],.5,(229,229,229)),(x+tile[0]+8,y+20))
            d.text((x+2,y+2),name+' native / restored',fill='white')
        path=root/f'review/base_pose_page_{page}.png';out.save(path);evidence['base_pose_pages'].append(rel(path))
    for page,start in enumerate(range(0,len(names),40)):
        subset=names[start:start+40];out=Image.new('RGB',(1280,((len(subset)+9)//10)*150),(225,225,225));d=ImageDraw.Draw(out)
        for i,name in enumerate(subset):
            clean=Image.open(root/f'cleaned/{name}.png').convert('RGBA');b=clean.getbbox()
            solid = ndimage.binary_erosion(np.asarray(clean)[:,:,3]>180,iterations=5)
            sy,sx = np.where(solid)
            # Two unresized 64px patches: upper material/face and torso/primary surface.
            for patch,fy in enumerate((.15,.45)):
                cx=(b[0]+b[2])//2;cy=round(b[1]+(b[3]-b[1])*fy)
                if int(family[-3:]) >= 380 and len(sx):
                    closest = np.argmin((sx-cx)**2+(sy-cy)**2)
                    cx,cy = int(sx[closest]),int(sy[closest])
                crop=clean.crop((cx-32,cy-32,cx+32,cy+32))
                bg=Image.new('RGBA',crop.size,(225,225,225,255));bg.alpha_composite(crop)
                out.paste(bg.convert('RGB'),(i%10*128+patch*64,i//10*150+22))
            d.text((i%10*128+1,i//10*150+2),name,fill='black')
        path=root/f'review/detail_100_page_{page}.png';out.save(path);evidence['delivered_detail_pages'].append(rel(path))
    # Every palette and mask for every pose; whole-viewer masters remain available at 100%.
    items=[]
    for name in names:
        im=Image.open(root/f'aligned_2x/{name}.png').convert('RGBA');mask=Image.open(root/f'masks_2x/{name}.png')
        for variant in variants:
            altered=shared.apply_variant(im,mask,variant)
            assert np.array_equal(np.asarray(altered)[:,:,3],np.asarray(im)[:,:,3])
            items.append((name,str(variant['palette_id']),render(altered,registration[name]['canvas_origin_px'],.35,(50,50,50))))
        channels=mask.split() if mask.mode=='RGB' else (mask,Image.new('L',mask.size),Image.new('L',mask.size))
        overlay=Image.merge('RGBA',(*channels,im.getchannel('A')))
        items.append((name,'MASK',render(overlay,registration[name]['canvas_origin_px'],.35,(50,50,50))))
    tile=items[0][2].size;cw,ch=tile[0]+8,tile[1]+22;columns=max(1,1900//cw)
    per_page=columns*max(1,1800//ch)
    for page,start in enumerate(range(0,len(items),per_page)):
        subset=items[start:start+per_page]
        out=Image.new('RGB',(columns*cw,((len(subset)+columns-1)//columns)*ch),(50,50,50));d=ImageDraw.Draw(out)
        for i,(name,label,im) in enumerate(subset):
            x,y=i%columns*cw,i//columns*ch;out.paste(im,(x,y+20));d.text((x+1,y+2),name+' '+label,fill='white')
        path=root/f'review/palette_mask_page_{page}.png';out.save(path);evidence['palette_mask_pages'].append(rel(path))
    shutil.copy2(REPO/evidence['base_pose_pages'][0],root/'review/all_comparison.png')
    write(root/'review/evidence_pages.json',evidence)
    print(json.dumps(dict(family=family,frames=len(names),palettes=len(variants),
                         pages={k:len(v) for k,v in evidence.items() if k.endswith('_pages')})))


def remaining_inputs():
    queue = []
    for number in FAMILIES:
        root = SESSION / f'mm7_m{number}'
        jobs = read(root / 'run.json')['jobs'][5:]
        for page_index, start in enumerate(range(0, len(jobs), 15)):
            page = Image.new('RGB', (1920, 2000), (48,48,48))
            draw = ImageDraw.Draw(page)
            for i, job in enumerate(jobs[start:start+15]):
                x, y = i%3*640, i//3*400
                im = Image.open(REPO/job['references'][0]).convert('RGBA')
                im = im.resize((im.width//2, im.height//2), Image.Resampling.NEAREST)
                im.thumbnail((632,375), Image.Resampling.NEAREST)
                bg = Image.new('RGBA', im.size, (230,230,230,255)); bg.alpha_composite(im)
                page.paste(bg.convert('RGB'), (x,y+23))
                draw.text((x+3,y+3), root.name+' '+job['id'], fill='white')
            page.save(root / f'review/native_remaining_{page_index}.png')
        for job in jobs:
            if not job.get('selected_raw'):
                queue.append(dict(family=root.name, id=job['id'], prompt=(REPO/job['prompt']).read_text(),
                                  references=[str(REPO/p) for p in job['references']]))
    Path('/tmp/mm7_remaining_queue.json').write_text(json.dumps(queue))
    print(json.dumps(dict(jobs=len(queue), input_pages=[str(p) for p in SESSION.glob('*/review/native_remaining_*.png')])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'ingest', 'inputs', 'process', 'export', 'remaining_inputs', 'repack', 'landmarks', 'review_pages'])
    parser.add_argument('--family')
    parser.add_argument('--job')
    parser.add_argument('--source')
    parser.add_argument('--failure')
    parser.add_argument('--reason')
    parser.add_argument('--action', default='walk')
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('--index', type=int, default=0)
    args = parser.parse_args()
    if args.operation == 'prepare':
        prepare()
    elif args.operation == 'ingest':
        ingest(args.family, args.job, args.source, args.failure)
    elif args.operation == 'inputs':
        inputs(args.index)
    elif args.operation == 'process':
        process(args.family)
    elif args.operation == 'review_pages':
        review_pages(args.family)
    elif args.operation == 'export':
        export(args.family, args.partial)
    elif args.operation == 'repack':
        repack(args.family, args.job, args.reason)
    elif args.operation == 'landmarks':
        landmarks(args.family, args.action)
    else:
        remaining_inputs()
