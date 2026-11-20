"""Prepare resumable MM8 restorations and below-2x replacements without changing accepted packages."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
CREATURES = HERE.parent
REPO = CREATURES.parents[1]
sys.path.insert(0, str(CREATURES))
import mm8_restore_queue as native_queue
from sheet_checks import plan


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sampling(record):
    if 'sampling' in record:
        return record['sampling']
    if 'generated_pixels_per_native_pixel' in record:
        return record['generated_pixels_per_native_pixel']
    return 2 / (record['scale_to_2x'] * record.get('uniform_layout_scale', 1)
                * record.get('calibration', {}).get('scale', 1))


def inventory():
    progress = read(HERE / 'progress.json')
    families = {}
    for key, family in progress['families'].items():
        root = CREATURES / family['project']
        completed = family.get('completed_package')
        manifest_path = REPO / completed if completed else root / 'manifest.json'
        manifest = read(manifest_path) if manifest_path.exists() else {}
        registration_path = manifest_path.parent / manifest.get('placement_registration', 'registration.json')
        if not registration_path.exists():
            continue
        registration = read(registration_path)
        values = {name: sampling(record) for name, record in registration.items()}
        below = [name for name, value in values.items() if value < 2 - 1e-6]
        if not below:
            continue
        sources = read(root / 'sources.json')
        families[key] = dict(project=family['project'], label=family['label'],
                             existing_status=family['status'], measured_frames=len(values),
                             minimum_sampling=min(values.values()), below_2x_frames=below,
                             missing_frames=sorted(set(sources['sources']) - set(registration)
                                                   - set(sources.get('pixel_aliases', {}))),
                             pixel_aliases=sources.get('pixel_aliases', {}),
                             registration=str(registration_path.relative_to(REPO)),
                             registration_sha256=sha(registration_path),
                             source_manifest_sha256=sha(root / 'sources.json'))
    return families


def prepare_family(key, family, initial=False):
    root = CREATURES / family['project']
    out = root / 'redo_2x'
    for folder in ['raw', 'review']:
        (out / folder).mkdir(parents=True, exist_ok=True)
    run_path = out / 'run.json'
    if run_path.exists():
        run = read(run_path)
        assert run['source_manifest_sha256'] == family['source_manifest_sha256']
        assert run.get('initial_restoration', False) == initial
        assert run['previous_registration_sha256'] == family.get('registration_sha256')
        for job in run['jobs']:
            assert sha(REPO / job['references'][0]) == job['reference_sha256']
        return run
    sources = read(root / 'sources.json')
    batches = read(root / 'batches.json')
    registration = {} if initial else read(REPO / family['registration'])
    identity = None
    if not initial:
        identity_record = next(record for record in registration.values() if record['batch'] == 'identity')
        identity = root / identity_record['raw']
        if not identity.exists():
            identity = root / 'raw' / identity_record['raw']
        assert identity.is_file(), identity
    aliases = sources.get('pixel_aliases', {})
    needed = {aliases.get(name, name) for name in family['below_2x_frames'] + family['missing_frames']}
    jobs = []
    for batch, record in batches.items():
        names = record['frames']
        if not needed.intersection(names):
            continue
        images = {name: native_queue.native(root, name) for name in names}
        # Reference placement uses exact half-native-pixel offsets on a 2x canvas.
        canvas = [max(s['size'][axis] for s in sources['sources'].values()) for axis in (0, 1)]
        placed = {}
        for name, image in images.items():
            anchors = sources['sources'][name].get('anchors', [])
            if anchors and anchors != ['bottom-center'] and list(image.size) != canvas:
                raise ValueError(f'{key}/{name}: verify native actor anchoring before preparation: {anchors}')
            offset = [canvas[0] - image.width, 2 * (canvas[1] - image.height)]
            target = Image.new('RGBA', (canvas[0] * 2, canvas[1] * 2))
            target.paste(image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST), offset)
            placed[name] = target
        bounds = [image.getbbox() for image in placed.values()]
        crop = [min(b[0] for b in bounds) // 2 - 6, min(b[1] for b in bounds) // 2 - 6,
                (max(b[2] for b in bounds) + 1) // 2 + 6, (max(b[3] for b in bounds) + 1) // 2 + 6]
        width, height = crop[2] - crop[0], crop[3] - crop[1]
        start = 0
        sequence = 1
        while start < len(names):
            layout = plan(len(names) - start, width, height)
            count = layout['poses']
            selected = names[start:start + count]
            if needed.intersection(selected):
                columns, rows = layout['columns'], layout['rows']
                job_id = f'{batch}_redo_{sequence:02}'
                sheet = Image.new('RGBA', (columns * width * 2, rows * height * 2), (45, 45, 45, 255))
                for index, name in enumerate(selected):
                    cell = placed[name].crop(tuple(v * 2 for v in crop))
                    reconstructed = Image.new('RGBA', placed[name].size)
                    reconstructed.paste(cell, (crop[0] * 2, crop[1] * 2))
                    assert np.array_equal(np.array(reconstructed.convert('RGBa')),
                                          np.array(placed[name].convert('RGBa'))), name
                    sheet.alpha_composite(cell, (index % columns * width * 2, index // columns * height * 2))
                reference = out / 'references' / (job_id + '.png')
                reference.parent.mkdir(parents=True, exist_ok=True)
                sheet.convert('RGB').save(reference)
                prompt = f'''Restore native Might and Magic VIII {family['label']} sprites into faithful high-detail painted 2D game artwork.
Image 1 is the exact native POSE, SILHOUETTE, COLOR and LAYOUT authority: {columns} columns by {rows} rows, {count} occupied cells, row-major {', '.join(selected)}. Remaining cells stay transparent. Action: {record['action']}; stored view: {record['view']}. Native reference is enlarged nearest-neighbor for inspection only; reconstruct smooth fine detail, never imitate its pixel blocks.
Image 2 is existing enhanced IDENTITY and MATERIAL reference only. Preserve that creature design and native tonal weight; its poses and layout do not control this request. Keep original face, anatomy, clothing, equipment, handedness, limb angles, raised/planted feet, foreshortening, small features and expression. Clarify existing materials; invent no accessories, injuries or action. Falling/resting poses are non-graphic.
View-dependent anatomy is mandatory: copy only the facial features actually visible in each native pose. A rear-facing head shows its back, never eyes, a face or a mouth pasted onto the back of the head. Do not transfer frontal facial features from the identity reference into rear views. Preserve native occlusion and head direction in every cell.
Preserve equal cells, common anatomical scale and exact source-relative placement. No per-frame recentering, stretching, silhouette fitting or enlargement of crouched/prone poses. Keep all thin features and complete silhouettes within their assigned cells. Exactly the ordered native poses, no duplicates or extras.
Reconstruct continuous contours and fine coherent shading: no enlarged pixel blocks, dithering, blur, smeared faces, sharpening halos, glossy toy materials or crunchy invented texture. Match native colors and restrained lighting throughout.
Each padded cell represents {width} by {height} native pixels. Preserve sheet aspect {columns * width}:{rows * height}, and deliver at least {layout['observed_envelope'][0]} by {layout['observed_envelope'][1]} actual generated pixels if possible. Actual generated detail must reach at least twice native resolution in both axes; no broad added margins or shrunken subjects.
Return true transparent PNG alpha outside silhouettes and in empty cells. The gray native reference background is guidance only: do not reproduce it. No painted checkerboard, opaque background, shadows, gradients, colored reflections, fringe halos, text or grid lines.
'''
                if initial:
                    prompt = '\n'.join(line for line in prompt.splitlines()
                                       if not line.startswith('Image 2 is existing enhanced')) + '\n'
                    prompt += ('Preserve the native anatomy, costume coverage, equipment, handedness, limb angles, '
                               'foreshortening and expression. Use the original base palette, not a redesign.\n')
                prompt_path = out / 'prompts' / (job_id + '_v1.txt')
                prompt_path.parent.mkdir(parents=True, exist_ok=True)
                prompt_path.write_text(prompt)
                jobs.append(dict(id=job_id, scope=batch, frames=selected,
                                 replace_frames=[n for n in selected if n in needed],
                                 overlap_frames=selected[:1] if start else [], native_crop=crop,
                                 cell_native_size=[width, height], columns=columns, rows=rows,
                                 logical_canvas=canvas, reference_scale=2, exact_native_placement=True,
                                 planned_sampling=layout['planned_sampling'],
                                 observed_envelope=layout['observed_envelope'],
                                 references=[str(reference.relative_to(REPO))] +
                                            ([str(identity.relative_to(REPO))] if identity else []),
                                 reference_sha256=sha(reference), identity_sha256=sha(identity) if identity else None,
                                 prompt=str(prompt_path.relative_to(REPO)), status='pending', attempts=[]))
            if start + count >= len(names):
                break
            start += max(1, count - 1)
            sequence += 1
    covered = {name for job in jobs for name in job['replace_frames']}
    assert covered == needed, (key, sorted(needed - covered))
    run = dict(project=family['project'], status='in_progress', minimum_sampling=2, target_sampling=2.2,
               source_manifest_sha256=family['source_manifest_sha256'],
               initial_restoration=initial, previous_registration_sha256=family.get('registration_sha256'),
               retained_frames=sorted(set(registration) - needed - set(aliases)), pixel_aliases=aliases, jobs=jobs)
    save(run_path, run)
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', action='append', help='Prepare only these inventoried below-2x families')
    parser.add_argument('--initial', action='store_true', help='Prepare explicitly selected families with no restored masters')
    args = parser.parse_args()
    if args.initial:
        assert args.family, 'Select the initially unrestored families explicitly'
        progress = read(HERE / 'progress.json')
        for key in args.family:
            family = dict(progress['families'][key])
            root = CREATURES / family['project']
            assert not family.get('completed_package') and not (root / 'registration.json').exists()
            sources = read(root / 'sources.json')
            family.update(source_manifest_sha256=sha(root / 'sources.json'), below_2x_frames=[],
                          missing_frames=sorted(set(sources['sources']) - set(sources.get('pixel_aliases', {}))))
            run = prepare_family(key, family, initial=True)
            print(key, len(family['missing_frames']), 'unique native poses;', len(run['jobs']), 'jobs')
        return
    families = inventory()
    ledger_path = HERE / 'detail_progress.json'
    ledger = read(ledger_path) if ledger_path.exists() else {}
    previous = ledger.get('families', {})
    for key in args.family or families:
        if key not in families and previous.get(key, {}).get('replacement_status') == 'validated':
            print(key, 'already validated; retaining accepted replacement')
            continue
        family = families[key]
        run = prepare_family(key, family)
        print(key, family['label'], len(family['below_2x_frames']), 'below 2x;', len(run['jobs']), 'jobs')
    # Preserve the original replacement scope and accepted checkpoints across resumes.
    for key, family in families.items():
        previous.setdefault(key, family)
    save(ledger_path, dict(updated_utc=datetime.now(timezone.utc).isoformat(),
         scope='Existing MM8 families with registered generated masters below 2x; include their missing native poses. '
               'Unstarted families without masters are outside this replacement scope.',
         measurement='2 / full raw-to-2x scale, including layout scaling; active manifest registration takes precedence.',
         families=previous))


if __name__ == '__main__':
    main()
