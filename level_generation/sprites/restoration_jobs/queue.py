"""Small resumable worker interface. All commands are offline; imagegen is called by the agent."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import re

from policy import REPAIRS, ALPHA_MASK, PLACEMENT, QUALITY, BACKGROUND, LEGACY_MAGENTA_BACKGROUND
from identity_reference import write_identity_reference
from weather import validate_native_field

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state(job):
    path = HERE / 'state' / (job['id'] + '.json')
    return read(path) if path.exists() else dict(status=job['status'], attempts=[])


def save_state(job, value):
    value['updated_utc'] = datetime.now(timezone.utc).isoformat()
    save(HERE / 'state' / (job['id'] + '.json'), value)


def dependencies_ready(job, index):
    return all(state(index[d])['status'] == 'accepted' for d in job['depends_on'])


def validate():
    sources = read(HERE / 'sources.json')
    index = read(HERE / 'index.json')
    coverage = read(HERE / 'coverage.json')
    provenance = read(HERE / 'provenance.json')
    for path, expected in provenance.items():
        assert digest(REPO / path) == expected, f'Stale plan input: {path}'
    seen = set()
    for job in index:
        assert all(d in seen for d in job['depends_on']), ('Dependency is not earlier', job['id'])
        seen.add(job['id'])
        full = read(HERE / 'jobs' / (job['id'] + '.json'))
        assert (REPO / full['reference']).is_file()
        assert digest(REPO / full['reference']) == full['reference_sha256']
        assert (HERE / full['prompt_file']).stat().st_size > 300
        assert digest(HERE / full['prompt_file']) == full['prompt_sha256']
        assert full['assets'] == job['assets']
        for key in job['assets']:
            assert sources[key]['job'] == job['id']
    checked_files = set()
    for key, source in sources.items():
        assert (HERE / source['native']).is_file()
        assert sum(k in source for k in ('reuse', 'keep_native', 'job')) == 1, key
        for alias in source['aliases']:
            if alias['path'] not in checked_files:
                assert digest(REPO / alias['path']) == alias['sha256'], alias['path']
                checked_files.add(alias['path'])
            for palette in alias['palettes']:
                if palette['path'] not in checked_files:
                    assert digest(REPO / palette['path']) == palette['sha256'], palette['path']
                    checked_files.add(palette['path'])
        if 'reuse' in source:
            assert digest(REPO / source['reuse']['path']) == source['reuse']['sha256']
    assert all(f['assets'] and set(f['assets']) <= sources.keys() for f in coverage['referenced'])
    assert len(coverage['referenced']) == 2571
    assert len(read(HERE / 'triage.json')) == 152
    return dict(valid=True, jobs=len(index), referenced_files=len(coverage['referenced']),
                rendered_assets=len(sources), triage_files=152)


def export(index, sources):
    """Gather accepted outputs without installing them; incomplete coverage stays explicit."""
    from readiness import build_ledger
    readiness = build_ledger()
    frames, pending = {}, []
    excluded = []
    for key, source in sources.items():
        if readiness['assets'][key].get('disposition') == 'user_excluded_keep_native':
            excluded.append(key)
            continue
        if not readiness['assets'][key]['ready'] and 'keep_native' not in source:
            pending.append(key)
            continue
        if 'reuse' in source:
            path = REPO / source['reuse']['path']
        elif 'keep_native' in source:
            frames[key] = dict(keep_native=source['keep_native'], aliases=source['aliases'])
            continue
        else:
            current = state(index[source['job']])
            if current['status'] != 'accepted':
                pending.append(key)
                continue
            directory = HERE / current['output_dir']
            if not current.get('accepted_checks_sha256'):
                pending.append(key)
                continue
            assert digest(directory / 'checks.json') == current['accepted_checks_sha256'], 'Checks changed'
            from placement import validate_review
            full = read(HERE / 'jobs' / (source['job'] + '.json'))
            validate_review(read(directory / 'checks.json'), current['acceptance_review'], full['timeline_frames'] > 1)
            path = directory / (key + '.png')
            assert digest(path) == current['accepted_hashes'][key], f'Accepted output changed: {path}'
        frames[key] = dict(file=str(path.relative_to(REPO)), sha256=digest(path),
                           logical_size=source['native_size'],
                           physical_size=[n * 2 for n in source['native_size']],
                           aliases=source['aliases'])
    triage = []
    for job in read(HERE / 'triage.json'):
        path = HERE / 'state' / (job['id'] + '.json')
        triage.append(read(path) if path.exists() else dict(id=job['id'], status='unresolved'))
    result = dict(status='complete' if not pending and not readiness['summary'].get('restoration_pending', 0)
                  and all(t['status'] == 'resolved' for t in triage)
                  else 'incomplete', pixels_per_logical_pixel=2, frames=frames, pending_assets=pending,
                  user_excluded_assets=excluded,
                  animation_and_flags='groups.json', missing_references='coverage.json', triage=triage,
                  readiness_policy=readiness['policy'],
                  installation='not installed; no runtime blend mode or global override inferred')
    save(HERE / 'export.json', result)
    return dict(status=result['status'], available_assets=len(frames), pending_assets=len(pending),
                unresolved_triage=sum(t['status'] != 'resolved' for t in triage),
                manifest=str(HERE / 'export.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('status', 'validate', 'export'):
        sub.add_parser(name)
    p = sub.add_parser('next')
    p.add_argument('--limit', type=int, default=3)
    p.add_argument('--profile')
    p.add_argument('--deferred', action='store_true')
    for name in ('show', 'payload', 'claim', 'record', 'record-mask', 'process', 'accept', 'defer', 'import-draft', 'revise', 'check'):
        p = sub.add_parser(name)
        p.add_argument('job')
        if name == 'payload':
            p.add_argument('--repair', choices=[*REPAIRS, 'alpha_mask'])
            p.add_argument('--repair-note', help='Concrete observed defect and requested correction for this attempt')
            p.add_argument('--native-only', action='store_true',
                           help='For an explicit repair, omit candidates/seeds that caused layout or pixel copying')
            p.add_argument('--full-frame-weather', action='store_true',
                           help='Use the entire native opaque weather field without square-sheet padding')
        elif name == 'record':
            p.add_argument('raw', type=Path)
            p.add_argument('--prompt', type=Path)
        elif name == 'record-mask':
            p.add_argument('mask', type=Path)
        elif name == 'check':
            p.add_argument('--landmarks', type=Path)
        elif name == 'process':
            p.add_argument('--landmarks', type=Path)
            p.add_argument('--layout', type=Path)
            p.add_argument('--adjust', nargs=3, type=float, default=[1., 0., 0.], metavar=('SCALE', 'DX', 'DY'))
        elif name in ('accept', 'defer', 'revise'):
            p.add_argument('--note', required=True)
            if name == 'accept':
                p.add_argument('--review', type=Path, required=True)
    p = sub.add_parser('triage')
    p.add_argument('--limit', type=int, default=5)
    p = sub.add_parser('resolve-triage')
    p.add_argument('job')
    p.add_argument('--disposition', required=True,
                   choices=['alias', 'restored', 'utility_keep_native', 'unused_keep_native', 'unresolved'])
    p.add_argument('--evidence', required=True)
    p.add_argument('--artifact', type=Path)
    args = parser.parse_args()
    index = {j['id']: j for j in read(HERE / 'index.json')}
    if args.command == 'validate':
        return validate()
    if args.command == 'status':
        snapshot = read(HERE / 'readiness.json') if (HERE / 'readiness.json').exists() else None
        return dict(counts=dict(Counter(state(j)['status'] for j in index.values())),
                    counts_meaning='Historical job states, NOT verified-ready assets. Refresh readiness.py for readiness.',
                    readiness_snapshot=dict(updated_utc=snapshot['updated_utc'], summary=snapshot['summary'])
                    if snapshot else None,
                    ready_without_dependencies=sum(not state(j).get('user_excluded') and
                                                   state(j)['status'] in ('ready', 'review_existing') and
                                                   dependencies_ready(j, index) for j in index.values()),
                    summary=read(HERE / 'summary.json'))
    if args.command == 'next':
        eligible = ('needs_repair', 'deferred') if args.deferred else ('ready', 'review_existing')
        return [dict(id=j['id'], label=j['label'], profile=j['profile'], action=state(j)['status'])
                for j in index.values() if not state(j).get('user_excluded')
                and state(j)['status'] in eligible and dependencies_ready(j, index)
                and (not args.profile or args.profile == j['profile'])][:args.limit]
    if args.command == 'triage':
        return [j for j in read(HERE / 'triage.json') if not (HERE / 'state' / (j['id'] + '.json')).exists()][:args.limit]
    if args.command == 'resolve-triage':
        entry = next(j for j in read(HERE / 'triage.json') if j['id'] == args.job)
        assert len(args.evidence) >= 20, 'Record concrete source/usage/palette evidence'
        if args.disposition in ('alias', 'restored'):
            assert args.artifact and args.artifact.is_file(), 'Provide accepted output/manifest for restored or alias art'
        result = dict(id=entry['id'], source=entry['path'], source_sha256=entry['sha256'],
                      status='unresolved' if args.disposition == 'unresolved' else 'resolved',
                      disposition=args.disposition, evidence=args.evidence,
                      artifact=str(args.artifact.resolve()) if args.artifact else None,
                      artifact_sha256=digest(args.artifact) if args.artifact else None)
        save(HERE / 'state' / (entry['id'] + '.json'), result)
        return result
    sources = read(HERE / 'sources.json')
    if args.command == 'export':
        return export(index, sources)
    job = read(HERE / 'jobs' / (args.job + '.json'))
    current = state(job)
    if current.get('user_excluded') and args.command in ('payload', 'claim', 'process', 'accept'):
        raise ValueError('User excluded this job from restoration: ' + current['user_excluded']['reason'])
    if args.command != 'show' and current.get('batch_claim'):
        raise ValueError('Job belongs to an active batch; record/release that batch before another submission')
    if args.command in ('process', 'check') and current.get('attempts'):
        sampling = current['attempts'][-1].get('sampling_job')
        if sampling:
            path = HERE / sampling
            assert digest(path) == current['attempts'][-1]['sampling_job_sha256'], 'Sampling job changed'
            mapped = read(path)
            assert mapped['assets'] == job['assets'] and mapped['id'] == job['id'], 'Wrong sampling identity'
            job = mapped
    if current.get('attempts') and current['attempts'][-1].get('matte_rgb'):
        job = dict(job, matte_rgb=current['attempts'][-1]['matte_rgb'])
        import numpy as np
        from PIL import Image
        conflicting, total = 0, 0
        for key in job['assets']:
            pixels = np.array(Image.open(HERE / sources[key]['native']).convert('RGBA'), dtype=np.int16)
            rgb = pixels[:, :, :3][pixels[:, :, 3] > 0]
            conflicting += int(np.sum(np.minimum(rgb[:, 0], rgb[:, 2]) - rgb[:, 1] > 8))
            total += len(rgb)
        job['matte_collision_fraction'] = conflicting / max(total, 1)
    if args.command == 'show':
        return dict(job=job, state=current,
                    assets={k: sources[k] for k in job['assets']},
                    prompt=(HERE / job['prompt_file']).read_text())
    if args.command == 'payload':
        if args.repair_note and (not args.repair or len(args.repair_note.strip()) < 20):
            raise ValueError('--repair-note requires --repair and a concrete observation of at least 20 characters')
        if args.native_only and (not args.repair or args.repair == 'alpha_mask' or not args.repair_note):
            raise ValueError('--native-only requires an explicit artwork repair and concrete --repair-note')
        assert dependencies_ready(job, index), 'Accept the shared identity seed first'
        if job['category'] == 'decorations' and args.repair != 'alpha_mask':
            from batching import PIXEL_BUDGET, PLANNED_SCALE
            import math
            predicted = math.sqrt(PIXEL_BUDGET / math.prod(job['sheet_size']))
            scales = [(c['native_rectangle'][i + 2] - c['native_rectangle'][i])
                      * predicted / c['native_size'][i] for c in job['cells'] for i in range(2)]
            if min(scales) < PLANNED_SCALE:
                raise ValueError('Frozen sheet lacks 2.2x planning margin; use size-aware batching/reviewed splitting')
        references = [str(REPO / job['reference'])]
        prompt = re.sub(r'^Background:.*$', '', (HERE / job['prompt_file']).read_text(), flags=re.MULTILINE)
        prompt += '\n' + PLACEMENT + '\n' + BACKGROUND + '\n' + QUALITY
        if args.full_frame_weather:
            from PIL import Image
            if job['profile'] != 'weather' or len(job['assets']) != 1 or args.repair == 'alpha_mask':
                raise ValueError('Full-frame weather requires one weather asset and no alpha-mask repair')
            source = sources[job['assets'][0]]
            with Image.open(HERE / source['native']) as native:
                native = native.convert('RGBA')
                validate_native_field(native)
                size = tuple(n * 2 for n in native.size)
                reference = HERE / 'state' / 'weather_references' / (job['id'] + '.png')
                reference.parent.mkdir(exist_ok=True)
                native.resize(size, Image.Resampling.NEAREST).save(reference)
            references[0] = str(reference)
            prompt = re.sub(r'^Layout:.*$',
                            f'Layout: ONE full-frame field, aspect {size[0]}:{size[1]}. '
                            f'Return at least {size[0]} by {size[1]} pixels. '
                            'The entire canvas is the native image: no inset, frame, margin or padding.',
                            prompt, flags=re.MULTILINE)
            prompt = prompt.replace('Keep empty areas genuinely transparent (alpha 0).',
                                    'Preserve the fully opaque native weather field.')
            prompt = prompt.replace(BACKGROUND,
                                    'Background contract: the native BLACK field is opaque artwork. '
                                    'Keep it opaque black across the entire returned canvas, including edges. '
                                    'Do not convert black to transparency or introduce a colored matte.\n')
        if args.repair:
            assert current['attempts'], 'Record the candidate first'
            if not args.native_only:
                references.append(str(HERE / current['attempts'][-1]['raw']))
            if args.repair == 'alpha_mask':
                references.reverse()
                prompt = ALPHA_MASK + f'\nAsset: {job["label"]}. Backdrop RGB{tuple(job["matte_rgb"])}.\n'
            elif args.native_only:
                prompt += '\nRestore only the native target reference. ' + REPAIRS[args.repair] + '\n'
            else:
                prompt += ('\nThe SECOND reference is the candidate to correct; it is NOT an accepted identity. '
                           + REPAIRS[args.repair] + '\n')
        for dependency in job['depends_on'] if args.repair != 'alpha_mask' and not args.full_frame_weather and not args.native_only else []:
            previous = state(index[dependency])
            raw = HERE / previous['attempts'][-1]['raw']
            assert digest(raw) == previous['attempts'][-1]['raw_sha256'], 'Identity master changed'
            matte = tuple(job['matte_rgb'])
            directory = HERE / 'state' / 'identity_references'
            directory.mkdir(exist_ok=True)
            seed = directory / (dependency + '-' + digest(raw)[:16] + '-' + '-'.join(map(str, matte)) + '.png')
            write_identity_reference(raw, seed, matte)
            references.append(str(seed))
        if job['depends_on'] and args.repair != 'alpha_mask' and not args.full_frame_weather and not args.native_only:
            prompt += ('\nAdditional identity seeds are composited over a flat reference matte to show accepted '
                       'opacity faithfully. That matte is not artwork. Copy only their foreground materials; '
                       'use the FIRST native reference for every requested phase and cell. Output transparent RGBA.\n')
        if args.full_frame_weather:
            prompt += ('\nWEATHER OVERRIDE: output one fully opaque black particle field, edge to edge. '
                       'The entire returned canvas maps to the entire native canvas. '
                       'No transparent margins, inset particle panel, scenery or large decorative flakes. '
                       'Restore the exact FIRST reference particle positions. Do not invent or randomize their layout. '
                       'No other animation frame is supplied because it must not replace this frame.\n')
            if job['label'].lower() == 'rain':
                prompt += ('\nRAIN DETAIL: redraw each streak as a slender continuous shaded stroke with smoothly '
                           'tapered ends. Preserve particle centers and length distribution, NOT native rectangular '
                           'hooks, flat square caps or abrupt pixel-width steps. Separate overlapping streaks into '
                           'fine lines. Softening the edges of block-shaped strokes is not reconstruction.\n')
        if args.repair_note:
            prompt += '\nSPECIFIC OBSERVED DEFECT TO CORRECT: ' + args.repair_note.strip() + '\n'
        prompt_path = HERE / 'state' / (job['id'] + '.submitted.txt')
        prompt_path.parent.mkdir(exist_ok=True)
        prompt_path.write_text(prompt)
        return dict(tool_args=dict(prompt=prompt, referenced_image_paths=references),
                    record_prompt=str(prompt_path),
                    next='Inspect ALL references with view_image before the built-in imagegen call')
    if args.command == 'revise':
        assert current['attempts'], 'Record a candidate before making a revision'
        assert len(args.note.strip()) >= 20, 'Record the concrete reason for revision'
        number = len(current['attempts']) + 1
        directory = HERE / 'results' / job['id'] / f'attempt_{number:02d}'
        directory.mkdir(parents=True, exist_ok=False)
        save(directory / 'previous_state.json', current)
        previous = HERE / current['output_dir']
        raw = HERE / current['attempts'][-1]['raw']
        assert digest(raw) == current['attempts'][-1]['raw_sha256'], 'Raw master changed'
        shutil.copy2(raw, directory / 'raw.png')
        shutil.copy2(previous / 'prompt.txt', directory / 'prompt.txt')
        for key in job['assets']:
            if (previous / (key + '.png')).exists():
                shutil.copy2(previous / (key + '.png'), directory / (key + '.png'))
        if (previous / 'checks.json').exists():
            shutil.copy2(previous / 'checks.json', directory / 'checks.json')
        if current.get('mask'):
            shutil.copy2(HERE / current['mask'], directory / 'mask.png')
            current['mask'] = str((directory / 'mask.png').relative_to(HERE))
        sampling_fields = {}
        for name in ('sampling_job', 'batch_manifest', 'batch_sheet'):
            if name in current['attempts'][-1]:
                sampling_fields[name] = current['attempts'][-1][name]
        if 'sampling_job' in sampling_fields:
            sampling_fields['sampling_job_sha256'] = current['attempts'][-1]['sampling_job_sha256']
        current['attempts'].append(dict(raw=str((directory / 'raw.png').relative_to(HERE)),
                                        raw_sha256=digest(raw), reused_master=True, reason=args.note,
                                        **sampling_fields,
                                        **({'matte_rgb': current['attempts'][-1]['matte_rgb']}
                                           if current['attempts'][-1].get('matte_rgb') else {})))
        current.update(status='generated', output_dir=str(directory.relative_to(HERE)))
        for key in ('accepted_hashes', 'visual_review_note', 'reviewed_warnings', 'acceptance_review',
                    'accepted_checks_sha256'):
            current.pop(key, None)
        save_state(job, current)
        return dict(job=job['id'], **current)
    assert current['status'] != 'accepted', 'Accepted jobs are immutable; make an explicit revision instead'
    if args.command == 'claim':
        assert dependencies_ready(job, index), 'Accept the shared identity seed first'
        assert current['status'] != 'in_flight', 'Job already claimed; inspect pending call before resubmitting'
        current.update(status='in_flight', submitted_utc=datetime.now(timezone.utc).isoformat())
    elif args.command in ('record', 'import-draft'):
        assert dependencies_ready(job, index), 'Accept the shared identity seed first'
        number = len(current['attempts']) + 1
        output_dir = Path('results') / job['id'] / f'attempt_{number:02d}'
        directory = HERE / output_dir
        directory.mkdir(parents=True, exist_ok=False)
        if args.command == 'record':
            from PIL import Image
            with Image.open(args.raw) as image:
                image.verify()
            raw = args.raw
            submitted = args.prompt or HERE / job['prompt_file']
            shutil.copy2(submitted, directory / 'prompt.txt')
        else:
            from finish import review
            assert len(job['assets']) == 1 and 'draft' in sources[job['assets'][0]]
            key = job['assets'][0]
            draft = sources[key]['draft']
            raw = REPO / draft['raw']
            old_prompt = raw.parent.parent / 'prompts' / (raw.stem + '.txt')
            shutil.copy2(old_prompt, directory / 'prompt.txt')
            shutil.copy2(REPO / draft['enhanced'], directory / (key + '.png'))
            report = dict(imported_benchmark_draft=True,
                          warnings=[draft['repair']] if draft['repair'] else [],
                          frames={key: {'native_size': sources[key]['native_size']}})
            save(directory / 'checks.json', report)
            review(job, sources, directory)
        shutil.copy2(raw, directory / 'raw.png')
        current['attempts'].append(dict(raw=str(output_dir / 'raw.png'), raw_sha256=digest(directory / 'raw.png'),
                                        imported_draft=args.command == 'import-draft',
                                        **({'matte_rgb': [255, 0, 255]}
                                           if LEGACY_MAGENTA_BACKGROUND in (directory / 'prompt.txt').read_text() else {})))
        current.update(status='review' if args.command == 'import-draft' else 'generated',
                       output_dir=str(output_dir))
        current.pop('mask', None)
        current.pop('mask_sha256', None)
    elif args.command == 'record-mask':
        from PIL import Image
        assert current['attempts'], 'Record RGB candidate first'
        with Image.open(args.mask) as image:
            image.verify()
        path = HERE / current['output_dir'] / 'mask.png'
        assert not path.exists(), 'Keep existing mask; make an explicit new candidate/revision'
        shutil.copy2(args.mask, path)
        current['mask'] = str(path.relative_to(HERE))
        current['mask_sha256'] = digest(path)
        submitted = HERE / 'state' / (job['id'] + '.submitted.txt')
        if submitted.exists():
            shutil.copy2(submitted, path.parent / 'mask_prompt.txt')
    elif args.command == 'check':
        from finish import check_existing
        check_existing(job, sources, HERE / current['output_dir'],
                       read(args.landmarks) if args.landmarks else None)
        current['status'] = 'review'
    elif args.command == 'process':
        from finish import process
        assert current['attempts'], 'Record raw output first'
        if args.layout:
            from placement import apply_layout_override
            job = apply_layout_override(job, read(args.layout), digest(HERE / current['attempts'][-1]['raw']))
        process(job, sources, HERE / current['attempts'][-1]['raw'], HERE / current['output_dir'], args.adjust,
                HERE / current['mask'] if current.get('mask') else None,
                read(args.landmarks) if args.landmarks else None)
        current['status'] = 'review'
    elif args.command == 'accept':
        from PIL import Image
        assert current['status'] == 'review', 'Run processing / draft import and view proofs first'
        directory = HERE / current['output_dir']
        checks = read(directory / 'checks.json')
        from placement import validate_review
        acceptance_review = read(args.review)
        if len(str(acceptance_review.get('master_detail', '')).strip()) < 20:
            raise ValueError('Inspect the full-resolution raw master and record specific master_detail observations')
        validate_review(checks, acceptance_review, job['timeline_frames'] > 1)
        from readiness import require_resolution
        raw_attempt = current['attempts'][-1]
        assert digest(HERE / raw_attempt['raw']) == raw_attempt['raw_sha256'], 'Raw master changed'
        require_resolution(job, current)
        if current['attempts'][-1].get('batch_manifest'):
            from batching import validate_asset_reviews
            validate_asset_reviews(job['assets'], acceptance_review)
        hashes = {}
        for key in job['assets']:
            path = directory / (key + '.png')
            with Image.open(path) as image:
                assert image.mode == 'RGBA' and list(image.size) == [n * 2 for n in sources[key]['native_size']]
                assert image.getchannel('A').getbbox(), 'Empty generated art cannot be accepted'
            hashes[key] = digest(path)
        current.update(status='accepted', accepted_hashes=hashes, visual_review_note=args.note,
                       reviewed_warnings=checks.get('warnings', []), acceptance_review=acceptance_review,
                       accepted_checks_sha256=digest(directory / 'checks.json'))
    elif args.command == 'defer':
        current.update(status='deferred', reason=args.note)
    save_state(job, current)
    return dict(job=job['id'], **current)


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
