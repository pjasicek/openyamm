"""Size-aware sheet preparation and intake. All commands are offline; none calls imagegen."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil

import numpy as np
from PIL import Image

from readiness import HERE, REPO, digest, read
from policy import QUALITY

PIXEL_BUDGET = 1_572_000  # Observed local built-in returns, NOT an API size guarantee.
PLANNED_SCALE = 2.2
PADDING = 4  # Native pixels on every side; full native canvases retain all internal margins.
MAX_TARGETS = 64


def save(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def job_state(job):
    path = HERE / 'state' / (job['id'] + '.json')
    return read(path) if path.exists() else dict(status=job['status'], attempts=[])


def pack(cells):
    """Deterministic shelf search. Never rotate, shrink or alpha-trim an individual canvas."""
    if not cells or len(cells) > MAX_TARGETS:
        return None
    ordered = sorted(cells, key=lambda c: (-c['native_size'][1], -c['native_size'][0], c['asset']))
    max_area = PIXEL_BUDGET / PLANNED_SCALE ** 2
    minimum_width = max(c['native_size'][0] + 2 * PADDING for c in ordered)
    best = None
    for width in range(minimum_width, int(math.sqrt(2 * max_area)) + 1, 4):
        x, y, row_height = 0, 0, 0
        placed = []
        for cell in ordered:
            w, h = [n + 2 * PADDING for n in cell['native_size']]
            if x + w > width:
                y += row_height
                x, row_height = 0, 0
            placed.append(dict(cell, cell=[x, y, x + w, y + h],
                               native_rectangle=[x + PADDING, y + PADDING,
                                                 x + w - PADDING, y + h - PADDING]))
            x += w
            row_height = max(row_height, h)
        height = max(y + row_height, math.ceil(width / 2))
        if height > width * 2 or width * height > max_area:
            continue
        score = (width * height, abs(width - height))
        if best is None or score < best[0]:
            best = (score, dict(sheet_size=[width * 2, height * 2],
                               predicted_master_scale=math.sqrt(PIXEL_BUDGET / (width * height)),
                               cells=[dict(c, cell=[v * 2 for v in c['cell']],
                                           native_rectangle=[v * 2 for v in c['native_rectangle']]) for c in placed]))
    return best[1] if best else None


def validate_asset_reviews(keys, review):
    observations = review.get('assets', {})
    if set(observations) != set(keys):
        raise ValueError('Batch review must cover every asset exactly; no sheet-wide automatic acceptance')
    for key in keys:
        for field in ('master_detail', 'layout', 'placement'):
            if len(observations[key].get(field, '').strip()) < 20:
                raise ValueError(f'{key}: record specific {field} observations')


def validate_sheet(sheet):
    width, height = sheet['sheet_size']
    cells = sheet['cells']
    if width <= 0 or height <= 0 or not .5 <= width / height <= 2:
        raise ValueError('Sheet aspect must be between 1:2 and 2:1')
    if not 1 <= len(cells) <= MAX_TARGETS or len({c['asset'] for c in cells}) != len(cells):
        raise ValueError('Duplicate assets or invalid cell count')
    for i, cell in enumerate(cells):
        box, rect, native = cell['cell'], cell['native_rectangle'], cell['native_size']
        if (not all(isinstance(v, int) for v in box + rect + native)
                or not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)
                or any(n <= 0 for n in native)
                or any(rect[a + 2] - rect[a] != 2 * native[a] for a in range(2))
                or any(rect[a] - box[a] < 2 * PADDING or box[a + 2] - rect[a + 2] < 2 * PADDING
                       for a in range(2))):
            raise ValueError('Invalid full native canvas/padding: ' + cell['asset'])
        for other in cells[:i]:
            b = other['cell']
            if max(box[0], b[0]) < min(box[2], b[2]) and max(box[1], b[1]) < min(box[3], b[3]):
                raise ValueError('Overlapping cells')


def make_prompt(sheet, jobs):
    labels = '; '.join(f'{i + 1}: {jobs[c["job"]]["label"]} ({c["asset"]})'
                       for i, c in enumerate(sheet['cells']))
    effect_rules = ''
    if sheet['profile'] == 'soft_fx':
        effect_rules = ('Preserve native effect phase progression, hue, luminous core, detached particles and quiet frames. '
                        'Keep soft opacity and glow falloff; do not make smoke or dark energy falsely additive. '
                        'Do not fill transparent space between rays or particles with an opaque haze.\n')
    return f'''{QUALITY}
{effect_rules}
Use case: high-resolution reconstruction; faithful restoration of native MM6-MM8 game sprite artwork.
Input image is the edit target: one sheet containing {len(sheet['cells'])} separate native sprite canvases.
Any additional references are accepted identity seeds only; do not copy their sheet layout or add their cells.
Return one sheet with exactly the SAME dimensions/aspect, slot layout and sprite order as the reference.
Reconstruct continuous contours AND fine material detail and shading, not enlarged pixel blocks or blurred
nearest-neighbor artwork. Match the original subdued palette, forms, pose, lighting and tonal weight.
Do not add, remove, duplicate, rotate or mix objects. No text, labels, borders, grid lines or decorative background.
Preserve each full native canvas, original empty margins, proportions, internal landmarks and placement.
Do NOT fit each visible silhouette to its cell, independently centre it, or move its bottom/contact point.
Grounded rocks/bases/roots keep their native contact; suspended/water objects keep their native anchors.
Animation/view/state families retain fixed supports and shared material identity with native pose differences.
Gutters stay empty. No cast shadows, ground planes or props absent from the source.
Return genuine transparent RGBA: empty areas and true holes have alpha 0, no painted checkerboard or matte.
Keep solid dark materials opaque; preserve genuine soft flame/water transitions and fine foliage.
Slot identities (for instructions only; never draw these labels): {labels}
The reference is prepared at 2x native coordinates. Preserve its exact layout; reconstruct detail throughout.
'''


def prepare(output, requested=(), reason='', native_only=False):
    if native_only and (not requested or len(reason.strip()) < 20):
        raise ValueError('Native-only repair requires explicit jobs and an observed layout-copying defect')
    ledger = read(HERE / 'readiness.json')
    sources = read(HERE / 'sources.json')
    jobs = {j['id']: read(HERE / 'jobs' / (j['id'] + '.json')) for j in read(HERE / 'index.json')}
    if set(requested) - jobs.keys():
        raise ValueError('Unknown jobs: ' + ', '.join(sorted(set(requested) - jobs.keys())))
    selected, excluded, snapshots = [], [], {}
    for job in jobs.values():
        if requested and job['id'] not in requested:
            continue
        static_item = (job['category'] == 'world_items' and job['profile'] == 'solid'
                       and len(job['assets']) == 1 and job['timeline_frames'] == 1
                       and not job['depends_on'])
        explicit_effect = (bool(requested) and job['category'] == 'effects_projectiles_other'
                           and job['profile'] in ('solid', 'soft_fx'))
        if job['category'] != 'decorations' and not static_item and not explicit_effect:
            if requested:
                excluded.append(dict(job=job['id'], reason='specialized_art; use its own profile workflow'))
            continue
        state = job_state(job)
        issues = {v for key in job['assets'] for v in ledger['assets'][key]['reasons']}
        why = None
        if state.get('user_excluded'):
            why = 'user_excluded; preserve native and history'
        elif state.get('batch_claim') or state['status'] == 'in_flight':
            why = 'already_in_flight'
        elif all(ledger['assets'][key]['ready'] for key in job['assets']) and not requested:
            why = 'already_verified; reuse'
        elif any(not all(ledger['assets'][key]['ready'] for key in jobs[d]['assets']) for d in job['depends_on']):
            why = 'identity_seed_needs_verification_first'
        elif state.get('attempts') and 'master_below_2x' not in issues and not requested:
            why = 'inspect_existing_master_first; no automatic regeneration'
        elif state.get('attempts') and requested and len(reason.strip()) < 20:
            why = 'existing_art_needs_concrete_generation_reason'
        if why:
            excluded.append(dict(job=job['id'], reason=why))
            continue
        cells = [dict(asset=k, job=job['id'], native_size=sources[k]['native_size']) for k in job['assets']]
        if pack(cells) is None:
            excluded.append(dict(job=job['id'], reason='oversize_group; explicitly split with identity seeds '
                                 'or obtain measured larger output; never shrink native canvases'))
            continue
        selected.append((job, cells))
        snapshots[job['id']] = dict(state_sha256=fingerprint(state),
                                    job_sha256=digest(HERE / 'jobs' / (job['id'] + '.json')))
    # Independent static props may share a sheet. Animations, view/state families and soft effects
    # stay together and separate from unrelated jobs; processing keeps the original profile.
    bins = []
    for job, cells in sorted(selected, key=lambda pair: -sum(math.prod(c['native_size']) for c in pair[1])):
        compatible = (len(cells) == 1 and job['timeline_frames'] == 1 and not job['depends_on']
                      and job['profile'] in ('solid', 'foliage'))
        candidate = None
        if compatible:
            options = [(i, pack(b['cells'] + cells)) for i, b in enumerate(bins)
                       if b['compatible'] and b['profile'] == job['profile']]
            options = [(i, layout) for i, layout in options if layout is not None]
            if options:
                candidate = min(options, key=lambda pair: math.prod(pair[1]['sheet_size']))[0]
        if candidate is None:
            bins.append(dict(cells=list(cells), profile=job['profile'], compatible=compatible))
        else:
            bins[candidate]['cells'].extend(cells)
    output = output.resolve()
    if not output.is_relative_to(HERE):
        raise ValueError('Keep prepared batches inside restoration_jobs for portable provenance')
    output.mkdir(parents=True, exist_ok=False)
    sheets = []
    for number, batch in enumerate(bins, 1):
        sheet = pack(batch['cells'])
        sheet.update(id=f'S{number:03d}', profile=batch['profile'], jobs=sorted({c['job'] for c in sheet['cells']}))
        validate_sheet(sheet)
        sheet['seeds'] = []
        dependencies = sorted({d for job_id in sheet['jobs'] for d in jobs[job_id]['depends_on']})
        for number_seed, dependency in enumerate(dependencies, 1):
            seed_state = job_state(jobs[dependency])
            seed_raw = HERE / seed_state['attempts'][-1]['raw']
            seed_path = output / f'{sheet["id"]}.seed{number_seed}.png'
            from identity_reference import write_identity_reference
            write_identity_reference(seed_raw, seed_path, tuple(jobs[dependency]['matte_rgb']))
            sheet['seeds'].append(dict(job=dependency, file=seed_path.name, sha256=digest(seed_path),
                                       review_only=native_only,
                                       state_sha256=fingerprint(seed_state)))
        reference = Image.new('RGBA', tuple(sheet['sheet_size']))
        for cell in sheet['cells']:
            source = sources[cell['asset']]
            path = HERE / source['native']
            with Image.open(path) as native:
                if list(native.size) != cell['native_size'] or not native.getchannel('A').getbbox():
                    raise ValueError('Native canvas mismatch/empty art: ' + cell['asset'])
                reference.paste(native.resize(tuple(n * 2 for n in native.size), Image.Resampling.NEAREST),
                                tuple(cell['native_rectangle'][:2]))
            cell['source_sha256'] = digest(path)
        reference_path = output / (sheet['id'] + '.png')
        reference.save(reference_path)
        prompt_path = output / (sheet['id'] + '.txt')
        prompt = make_prompt(sheet, jobs)
        if native_only:
            prompt += ('\nOnly the native target sheet is supplied for this targeted repair. '
                       'Earlier candidates copied other animation phases or seed layouts. '
                       'Restore exactly these cells; accepted family masters remain local review references.\n')
        prompt_path.write_text(prompt)
        sheet.update(reference=reference_path.name, reference_sha256=digest(reference_path),
                     prompt=prompt_path.name, prompt_sha256=digest(prompt_path))
        sheets.append(sheet)
    manifest = dict(schema_version=1, observed_output_pixels=PIXEL_BUDGET, planned_scale=PLANNED_SCALE,
                    max_targets=MAX_TARGETS, native_padding=PADDING, reason=reason,
                    preparation_only=True, jobs=snapshots, sheets=sheets, excluded=excluded,
                    ledger_sha256=digest(HERE / 'readiness.json'),
                    calibration='First sheet must pass per-asset layout/detail/anchor review before bulk submission.')
    save(output / 'manifest.json', manifest)
    return dict(manifest=str(output / 'manifest.json'), jobs=len(selected), sheets=len(sheets),
                assets=sum(len(s['cells']) for s in sheets),
                targets_per_sheet=dict(Counter(len(s['cells']) for s in sheets)),
                excluded=dict(Counter(x['reason'] for x in excluded)))


def load_sheet(path, sheet_id):
    manifest = read(path)
    return manifest, next(s for s in manifest['sheets'] if s['id'] == sheet_id)


def preflight(path, sheet_id, claimed=False):
    manifest, sheet = load_sheet(path, sheet_id)
    validate_sheet(sheet)
    if digest(path.parent / sheet['reference']) != sheet['reference_sha256']:
        raise ValueError('Reference changed')
    if digest(path.parent / sheet['prompt']) != sheet['prompt_sha256']:
        raise ValueError('Prompt changed; prepare a new immutable batch')
    if not claimed and QUALITY not in (path.parent / sheet['prompt']).read_text():
        raise ValueError('Stale quality policy; prepare a new immutable batch before submission')
    if manifest['observed_output_pixels'] != PIXEL_BUDGET or manifest['planned_scale'] < PLANNED_SCALE:
        raise ValueError('Unsupported/stale pixel budget')
    if math.sqrt(PIXEL_BUDGET / (math.prod(sheet['sheet_size']) / 4)) < PLANNED_SCALE:
        raise ValueError('Predicted resolution below planning margin')
    sources = read(HERE / 'sources.json')
    for cell in sheet['cells']:
        if cell['native_size'] != sources[cell['asset']]['native_size']:
            raise ValueError('Native size changed')
        if digest(HERE / sources[cell['asset']]['native']) != cell['source_sha256']:
            raise ValueError('Native reference changed: ' + cell['asset'])
        for alias in sources[cell['asset']].get('aliases', []):
            if digest(REPO / alias['path']) != alias['sha256']:
                raise ValueError('Original source changed; reconcile inventory first: ' + alias['path'])
    for seed in sheet.get('seeds', []):
        seed_job = read(HERE / 'jobs' / (seed['job'] + '.json'))
        if (digest(path.parent / seed['file']) != seed['sha256']
                or fingerprint(job_state(seed_job)) != seed['state_sha256']):
            raise ValueError('Identity seed changed; replan')
    for job_id in sheet['jobs']:
        job_path = HERE / 'jobs' / (job_id + '.json')
        if digest(job_path) != manifest['jobs'][job_id]['job_sha256']:
            raise ValueError('Frozen job changed: ' + job_id)
        job = read(job_path)
        if set(job['assets']) != {c['asset'] for c in sheet['cells'] if c['job'] == job_id}:
            raise ValueError('Sheet does not contain the complete job')
        state = job_state(job)
        claim = state.pop('batch_claim', None)
        if claimed:
            if claim != dict(manifest=str(path.relative_to(HERE)), sheet=sheet_id):
                raise ValueError('Missing or different batch claim: ' + job_id)
        elif claim:
            raise ValueError('Already claimed: ' + job_id)
        if fingerprint(state) != manifest['jobs'][job_id]['state_sha256']:
            raise ValueError('Job progressed since planning; prepare again: ' + job_id)
    return manifest, sheet


def inspect_return(sheet, raw):
    """Cheap guards before any cleanup/resampling; semantic layout/detail still needs visual review."""
    validate_sheet(sheet)
    with Image.open(raw) as image:
        if image.mode != 'RGBA' or image.getchannel('A').getextrema()[0] != 0:
            raise ValueError('Expected genuine transparent RGBA, including alpha-zero empty areas')
        factors = [image.size[i] / sheet['sheet_size'][i] for i in range(2)]
        if abs(factors[0] / factors[1] - 1) > .01:
            raise ValueError('Returned aspect/layout changed by >1%; retain master for layout review')
        frames = {}
        alpha = np.asarray(image.getchannel('A'))
        for cell in sheet['cells']:
            rectangle = cell['native_rectangle']
            scale = [(rectangle[i + 2] - rectangle[i]) * factors[i] / cell['native_size'][i] for i in range(2)]
            if min(scale) < 2:
                raise ValueError('Returned master below strict 2x: ' + cell['asset'])
            box = [round(cell['cell'][i] * factors[i % 2]) for i in range(4)]
            crop = alpha[box[1]:box[3], box[0]:box[2]]
            if crop.size == 0 or not np.any(crop):
                raise ValueError('Empty/missing cell: ' + cell['asset'])
            # Thin outer strip of padding must stay empty: catches merged sprites/painted backgrounds.
            edge = np.concatenate((crop[:2].ravel(), crop[-2:].ravel(), crop[:, :2].ravel(), crop[:, -2:].ravel()))
            if np.any(edge > 16):
                raise ValueError('Art crosses cell gutter: ' + cell['asset'])
            frames[cell['asset']] = dict(master_scale=scale, nonzero_alpha_pixels=int(np.count_nonzero(crop)))
        return dict(raw_size=list(image.size), frames=frames,
                    visual_review_required='Inspect actual cell layout/scale, master detail, native anchors and holes.')


def claim_sheet(path, sheet_id):
    _, sheet = preflight(path, sheet_id)
    claim = dict(manifest=str(path.relative_to(HERE)), sheet=sheet_id)
    receipt = path.parent / (sheet_id + '.state.json')
    if receipt.exists():
        raise ValueError('Sheet already claimed/returned; reconcile it, do not resubmit')
    save(receipt, dict(status='in_flight', manifest_sha256=digest(path)))
    for job_id in sheet['jobs']:
        job = read(HERE / 'jobs' / (job_id + '.json'))
        state = job_state(job)
        state['batch_claim'] = claim
        save(HERE / 'state' / (job_id + '.json'), state)
    return dict(status='in_flight', sheet=sheet_id)


def record_sheet(path, sheet_id, raw):
    _, sheet = load_sheet(path, sheet_id)
    receipt = path.parent / (sheet_id + '.state.json')
    state = read(receipt)
    if state['status'] != 'in_flight' or state['manifest_sha256'] != digest(path):
        raise ValueError('Sheet is not an unchanged in-flight request')
    directory = path.parent / 'returns' / sheet_id
    directory.mkdir(parents=True, exist_ok=False)
    shutil.copy2(raw, directory / 'raw.png')
    shutil.copy2(path.parent / sheet['prompt'], directory / 'prompt.txt')
    state.update(status='returned', raw_sha256=digest(directory / 'raw.png'))
    save(receipt, state)  # Retain even failed returns; never lose the expensive result.
    try:
        preflight(path, sheet_id, claimed=True)
        checks = inspect_return(sheet, directory / 'raw.png')
    except ValueError as error:
        state.update(status='return_needs_review', error=str(error))
        save(receipt, state)
        raise
    save(directory / 'preflight.json', checks)
    return dict(status='returned', directory=str(directory), next='import; process and visually review each job')


def import_sheet(path, sheet_id):
    manifest, sheet = load_sheet(path, sheet_id)
    receipt = read(path.parent / (sheet_id + '.state.json'))
    if receipt['status'] not in ('returned', 'imported') or receipt['manifest_sha256'] != digest(path):
        raise ValueError('Record and pass static return checks first')
    raw = path.parent / 'returns' / sheet_id / 'raw.png'
    if digest(raw) != receipt['raw_sha256']:
        raise ValueError('Retained raw changed')
    inspect_return(sheet, raw)
    imported = []
    for job_id in sheet['jobs']:
        job = read(HERE / 'jobs' / (job_id + '.json'))
        current = job_state(job)
        if any(a.get('batch_manifest') == str(path.relative_to(HERE)) and a.get('batch_sheet') == sheet_id
               for a in current.get('attempts', [])):
            continue  # Resume a partially imported sheet without duplicate attempts.
        previous = dict(current)
        expected_claim = dict(manifest=str(path.relative_to(HERE)), sheet=sheet_id)
        if current.pop('batch_claim', None) != expected_claim:
            raise ValueError('Missing matching claim: ' + job_id)
        if fingerprint(current) != manifest['jobs'][job_id]['state_sha256']:
            raise ValueError('Job changed since preparation: ' + job_id)
        directory = HERE / 'results' / job_id / f'attempt_{len(current.get("attempts", [])) + 1:02d}'
        directory.mkdir(parents=True, exist_ok=False)
        save(directory / 'previous_state.json', previous)
        mapping = dict(job, sheet_size=sheet['sheet_size'],
                       cells=[c for c in sheet['cells'] if c['job'] == job_id])
        save(directory / 'sampling_job.json', mapping)
        shutil.copy2(path.parent / sheet['prompt'], directory / 'prompt.txt')
        attempt = dict(raw=str(raw.relative_to(HERE)), raw_sha256=receipt['raw_sha256'],
                       batch_manifest=str(path.relative_to(HERE)), batch_sheet=sheet_id,
                       sampling_job=str((directory / 'sampling_job.json').relative_to(HERE)),
                       sampling_job_sha256=digest(directory / 'sampling_job.json'))
        current.setdefault('attempts', []).append(attempt)
        current.update(status='generated', output_dir=str(directory.relative_to(HERE)))
        for key in ('accepted_hashes', 'accepted_checks_sha256', 'acceptance_review', 'visual_review_note',
                    'reviewed_warnings', 'mask', 'mask_sha256'):
            current.pop(key, None)
        save(HERE / 'state' / (job_id + '.json'), current)
        imported.append(job_id)
    receipt['status'] = 'imported'
    save(path.parent / (sheet_id + '.state.json'), receipt)
    return dict(imported=imported, next='queue.py process JOB; inspect raw/proofs; accept with per-asset evidence')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    plan = sub.add_parser('plan')
    plan.add_argument('--output', type=Path, required=True)
    plan.add_argument('--jobs', nargs='*', default=[])
    plan.add_argument('--reason', default='')
    plan.add_argument('--native-only', action='store_true',
                      help='Keep verified identity seeds for local review, omit them from targeted layout repairs')
    for name in ('preflight', 'payload', 'claim', 'record', 'import', 'release'):
        command = sub.add_parser(name)
        command.add_argument('manifest', type=Path)
        command.add_argument('sheet')
        if name == 'record':
            command.add_argument('raw', type=Path)
        if name == 'release':
            command.add_argument('--reason', required=True)
    args = parser.parse_args()
    if args.command == 'plan':
        return prepare(args.output, args.jobs, args.reason, args.native_only)
    path = args.manifest.resolve()
    if args.command == 'claim':
        return claim_sheet(path, args.sheet)
    if args.command == 'record':
        return record_sheet(path, args.sheet, args.raw)
    if args.command == 'import':
        return import_sheet(path, args.sheet)
    if args.command == 'release':
        if len(args.reason.strip()) < 20:
            raise ValueError('Record terminal call/cancellation evidence before releasing ownership')
        _, sheet = load_sheet(path, args.sheet)
        receipt_path = path.parent / (args.sheet + '.state.json')
        receipt = read(receipt_path)
        if receipt['status'] == 'imported':
            raise ValueError('Already imported; continue through job review')
        claim = dict(manifest=str(path.relative_to(HERE)), sheet=args.sheet)
        for job_id in sheet['jobs']:
            state_path = HERE / 'state' / (job_id + '.json')
            if not state_path.exists():
                continue
            state = read(state_path)
            if state.get('batch_claim') == claim:
                state.pop('batch_claim')
                save(state_path, state)
        receipt.update(status='released', reason=args.reason)
        save(receipt_path, receipt)
        return receipt
    _, sheet = preflight(path, args.sheet)
    if args.command == 'payload':
        return dict(tool_args=dict(prompt=(path.parent / sheet['prompt']).read_text(),
                                   referenced_image_paths=[str(path.parent / sheet['reference'])]
                                   + [str(path.parent / seed['file']) for seed in sheet.get('seeds', [])
                                      if not seed.get('review_only')]),
                    next='Inspect reference, then claim immediately before ONE built-in imagegen call for the sheet')
    return dict(valid=True, sheet=args.sheet, cells=len(sheet['cells']),
                predicted_scale=sheet['predicted_master_scale'])


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
