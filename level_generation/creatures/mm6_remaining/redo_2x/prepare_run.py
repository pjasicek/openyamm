"""Prepare measured, overlapping native reference batches; never calls an image API."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parents[1]))
from sheet_checks import choose_layout


def read(path):
    return json.loads(path.read_text())


def native(root, name):
    sources = read(root / 'sources.json')
    manifest = read(root / 'manifest.json')
    source = sources['sources'][name]
    index = np.array(Image.open(REPO / source['path']))
    palette = str(source['fixed_palette'] if 'fixed_palette' in source else
                  sources['base_palette'] if 'base_palette' in sources else manifest['frames'][name]['source_palette'])
    path = sources['palette_sources'][palette]['path']
    colors = np.frombuffer((REPO / path).read_bytes()[:768], np.uint8).reshape(256, 3)
    image = Image.fromarray(np.dstack([colors[index], (index != 0).astype(np.uint8) * 255]))
    canvas = Image.new('RGBA', manifest['logical_canvas'])
    offset = manifest['frames'][name]['native_offset']
    assert all(value == int(value) for value in offset), 'Half-pixel native placement requires a 2x reference canvas'
    canvas.paste(image, tuple(int(value) for value in offset))
    assert np.count_nonzero(np.array(canvas)[:, :, 3]) == np.count_nonzero(index)
    return canvas


def layout(count, width, height):
    return choose_layout(count, width, height)


def prepare(project):
    root = REPO / project
    family = next(f for f in read(HERE / 'inventory.json')['families'] if f['project'] == project)
    out = root / 'redo_2x'
    run_path = out / 'run.json'
    if run_path.exists():
        run = read(run_path)
        signatures = {scope['id']: scope['input_signature'] for scope in family['jobs']}
        for job in run['jobs']:
            assert job['source_signature'] == signatures[job['scope']], 'Native inputs changed; version the run explicitly'
            reference = out / 'references' / (job['id'] + '.png')
            assert hashlib.sha256(reference.read_bytes()).hexdigest() == job['reference_sha256'], reference
            assert (REPO / job['prompt']).is_file(), job['prompt']
            assert all((REPO / path).is_file() for path in job['references'])
        print(json.dumps(dict(project=project, batches=len(run['jobs']), reused_existing_run=True)))
        return
    for folder in ['references', 'prompts', 'raw', 'review']:
        (out / folder).mkdir(parents=True, exist_ok=True)
    config = read(root / 'config.json')
    identity = out / 'raw/standing_01_v1.png' if project.endswith('mm6_arc1') else root / 'raw/standing.png'
    if config.get('identity_reference'):
        identity = REPO / config['identity_reference']
    jobs = []
    for scope in family['jobs']:
        names = scope['sequence_context_frames']
        if project.endswith('mm6_arc1') and scope['batch'] == 'standing':
            names = names[2:]  # Existing front/profile checkpoint; profile is the overlap.
        crop = scope['native_crop_xyxy_with_6px_padding']
        width, height = scope['native_crop_size']
        start = 0
        sequence = 1
        while start < len(names):
            for count in range(len(names) - start, 0, -1):
                chosen = layout(count, width, height)
                if chosen:
                    break
            if not chosen:
                raise ValueError('Even one pose exceeds observed budget; choose another output envelope: ' + scope['id'])
            budget, _, columns, rows, envelope = chosen
            selected = names[start:start + count]
            key = scope['batch'].replace('/', '_') + '_redo_%02d' % sequence
            bg = (255, 0, 255) if config['matte'] == 'magenta' else (0, 255, 255)
            sheet = Image.new('RGB', (columns * width, rows * height), bg)
            for i, name in enumerate(selected):
                source = native(root, name)
                cell = source.crop(crop)
                restored = Image.new('RGBA', source.size)
                restored.paste(cell, (crop[0], crop[1]))
                assert np.array_equal(np.array(source.convert('RGBa')), np.array(restored.convert('RGBa'))), name
                sheet.paste(cell, (i % columns * width, i // columns * height), cell)
            reference = out / 'references' / (key + '.png')
            sheet.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST).save(reference)
            views = (scope.get('previous_layout') or {}).get('view', scope['batch'])
            if scope['batch'] == 'standing' and all(n[-1] in '01234' for n in selected):
                labels = ['front', 'front-oblique', 'profile', 'rear-oblique', 'back']
                views = ', '.join(labels[int(n[-1])] for n in selected)
            prompt = f'''Use case: style-transfer. Restore these native Might and Magic VI game sprites into crisp, richly resolved painted game artwork, preserving the original design and restrained tonal weight.
Image 1 is native POSE, SILHOUETTE and LAYOUT authority: {columns} columns by {rows} rows, {count} occupied cells in row-major order, remaining cells empty. Action {scope['batch']}, views {views}. Each cell has identical logical crop and scale. Keep every native limb, equipment orientation, gesture, foot contact and motion difference. Do not recenter or fit individual characters to cells.
Image 2 is accepted enhanced IDENTITY and MATERIAL reference only; its poses and layout do not control this request. Character: {config['description']}
Match native proportions, age, colors and dark tonal weight. Refine contours, face, fabric, hair and existing materials with restrained detail. Preserve all existing native clothing and accessories, adding none. No glossy plastic, fashion redesign, chibi proportions or photorealistic scene lighting. Keep full bodies and accessories inside their corresponding cells, with clean empty gutters.
Reconstruct fine shading and continuous contours. No enlarged pixel blocks, pixel-art imitation, dithering, blurry interpolation, smeared faces, sharpening halos or crunchy invented texture.
Palette regions: {config['regions']}. Protect other materials. Preserve common anatomical scale even in crouched or prone poses; never enlarge a collapsed body to fill a cell. Falling/resting poses are non-graphic, with no added blood or injuries.
Return a large {'landscape' if sheet.width > sheet.height else 'portrait'} sheet with the SAME aspect and grid as Image 1, ideally at least {envelope[0]} by {envelope[1]} pixels or larger. Actual per-character detail must exceed twice native size; do not shrink figures within cells. Preserve all thin native features.
Return true RGBA transparency outside the creature silhouettes, including empty gutters. Do not paint a checkerboard, black backdrop, grid lines, text, labels, ground shadows, gradients, colored reflections or fringe halos. Image 1 uses a colored matte only to show the original silhouette; do not reproduce that matte. Exactly the requested native poses, no extras.
'''
            prompt_path = out / 'prompts' / (key + '_v1.txt')
            prompt_path.write_text(prompt)
            jobs.append(dict(id=key, scope=scope['id'], frames=selected, start=start,
                             overlap_frames=selected[:1] if start else [],
                             native_crop=crop, cell_native_size=[width, height], columns=columns, rows=rows,
                             observed_envelope=list(envelope), planned_sampling=budget,
                             references=[str(reference.relative_to(REPO)), str(identity.relative_to(REPO))],
                             prompt=str(prompt_path.relative_to(REPO)), status='pending', attempts=[],
                             source_signature=scope['input_signature'],
                             reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest()))
            if start + count >= len(names):
                break
            start += max(1, count - 1)
            sequence += 1
    run_path = out / 'run.json'
    previous = {j['id']: j for j in read(run_path)['jobs']} if run_path.exists() else {}
    for job in jobs:
        old = previous.get(job['id'])
        if old and old['reference_sha256'] == job['reference_sha256'] and old['source_signature'] == job['source_signature']:
            for key in ['status', 'attempts', 'selected_raw', 'review', 'blocker']:
                if key in old:
                    job[key] = old[key]
    run_path.write_text(json.dumps(dict(project=project, minimum_sampling_exclusive=2,
                                      target_sampling=2.2, status='in_progress', jobs=jobs), indent=2) + '\n')
    print(json.dumps(dict(project=project, batches=len(jobs), frames_with_overlap=sum(len(j['frames']) for j in jobs))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    prepare(parser.parse_args().project)
