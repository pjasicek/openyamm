"""Extract measured opaque Dense64 cells and register retained masters for local review.

This does not generate, accept or stage artwork. Cutouts and ambiguous grids require
their own reviewed extraction. Never infer acceptance from successful extraction.
"""
import argparse
import fcntl
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from finalize_classification import HERE, ROOT, digest
import registration

spec = importlib.util.spec_from_file_location('hud_queue', HERE / 'queue.py')
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)
BATCH = HERE / 'chat_bundles/dense64_20260916'


def read(path):
    return json.loads(path.read_text())


def runs(mask):
    changes = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    return list(zip(np.flatnonzero(changes == 1).tolist(), np.flatnonzero(changes == -1).tolist()))


def opaque_rectangles(image, columns, rows):
    """Locate actual continuous magenta gutters, not the nominal scaled input grid."""
    pixels = np.asarray(image.convert('RGB')).astype(np.int16)
    matte = ((pixels[:, :, 0] > 200) & (pixels[:, :, 1] < 75) & (pixels[:, :, 2] > 200))
    vertical = runs(matte.mean(axis=0) > 0.95)
    horizontal = runs(matte.mean(axis=1) > 0.95)
    assert len(vertical) == columns + 1, 'Ambiguous column boundaries: supply a reviewed extraction separately'
    assert len(horizontal) == rows + 1, 'Ambiguous row boundaries: supply a reviewed extraction separately'
    rectangles = []
    for row in range(rows):
        for col in range(columns):
            x0, x1 = vertical[col][1], vertical[col + 1][0]
            y0, y1 = horizontal[row][1], horizontal[row + 1][0]
            assert x1 > x0 and y1 > y0
            rectangles.append([x0, y0, x1 - x0, y1 - y0])
    return rectangles


def sampling(rect, native_size):
    ratios = [rect[2] / native_size[0], rect[3] / native_size[1]]
    assert min(ratios) >= 2, f'Insufficient original-master sampling: {ratios}'
    assert max(ratios) / min(ratios) < 1.04, f'Distorted returned rectangle: {ratios}'
    return ratios


def trim_gutter(image, rect):
    """Remove only residual straight matte borders inside the measured opaque cell."""
    x, y, w, h = rect
    pixels = np.asarray(image.convert('RGB')).astype(np.int16)
    red, green, blue = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
    matte = (red - green > 65) & (blue - green > 65) & (red > 140) & (blue > 140)
    bounds = [x, y, x + w, y + h]
    for side in range(4):
        for distance in range(5):
            left, top, right, bottom = bounds
            edge = [matte[top:bottom, left], matte[top, left:right],
                    matte[top:bottom, right - 1], matte[bottom - 1, left:right]][side]
            if edge.mean() <= 0.05:
                break
            assert distance < 4, 'Matte extends into artwork; manual boundary review required'
            bounds[side] += 1 if side < 2 else -1
    left, top, right, bottom = bounds
    return [left, top, right - left, bottom - top]


def process(bundle, sid):
    folder = BATCH / bundle
    issued = next(b for b in read(BATCH / 'catalogue.json')['bundles'] if b['bundle_id'] == bundle)
    assert digest(folder / 'manifest.json') == issued['manifest_sha256']
    manifest = read(folder / 'manifest.json')
    sheet = next(s for s in manifest['sheets'] if s['id'] == sid)
    for key in ('reference', 'layout', 'prompt'):
        assert digest(folder / sheet[key]) == sheet[key + '_sha256']
    layout = read(folder / sheet['layout'])
    assert all(c['member']['cleanup'] == 'opaque_canvas' for c in layout['cells']), 'Opaque extraction only'
    receipt = read(folder / 'outputs/progress.json')['sheets'][sid]
    raw = folder / receipt['raw_path']
    prompt = folder / receipt['submitted_prompt_path']
    assert digest(raw) == receipt['raw_sha256'] and digest(prompt) == receipt['submitted_prompt_sha256']
    assert receipt.get('restoration_detail_review') == 'pass', 'Review raw detail before extracting candidates'
    assessment_path = BATCH / 'runs/finish_159_20260921/assessments.json'
    if assessment_path.exists():
        for assessment in read(assessment_path)['sheets']:
            if assessment['bundle'] == bundle and assessment['sheet'] == sid:
                assert assessment['raw_sha256'] == receipt['raw_sha256'], 'Stale sheet assessment'
                assert not assessment['block_generic_extraction'], assessment['notes']
    output = folder / 'outputs/local_review_edges_v2' / sid
    output.mkdir(parents=True, exist_ok=True)
    q = queue_module.Queue()
    cells = sheet['cells']
    jobs = sorted({q.members[c][0] for c in cells})
    references = {str(folder / sheet['reference']): sheet['reference_sha256']}
    native_identity = {}
    for ref in sheet['identity_references']:
        path = folder / ref['path']
        assert digest(path) == ref['sha256']
        references[str(path)] = ref['sha256']
        for member in read(path.parent / 'sources.json'):
            assert member == q.members[member['id']][1], 'Identity source contract changed'
            original = path.parent / member['id']
            assert digest(original) == member['source_sha256']
            native_identity[member['id']] = member['source_sha256']
    for cell in layout['cells']:
        assert q.members[cell['id']][1] == cell['member'], 'Native member contract changed'
        assert q.jobs[cell['original_job']] == cell['job_contract'], 'Frozen job changed'
        assert digest(ROOT / cell['member']['source_path']) == cell['source_sha256']
        assignment = q.state['external_assignments'][cell['id']]
        assert assignment['bundle'] == bundle and assignment['dense_sheet'] == sid
        assert assignment['manifest_sha256'] == issued['manifest_sha256']
    execution_id = 'dense-' + bundle + '-' + sid + '-' + receipt['raw_sha256'][:12]
    payload = dict(job=jobs[0], jobs=jobs, selected_cells=cells, prompt=prompt.read_text(),
        source_hashes={c['id']: c['source_sha256'] for c in layout['cells']},
        reference_hashes=references, dependency_cells={},
        external_return=dict(bundle=bundle, sheet=sid, manifest_sha256=issued['manifest_sha256']),
        execution_layout=dict(canvas_size=layout['reference_size'],
                              cell_rects={c['id']: c['reference_rect'] for c in layout['cells']}))
    if all(q.jobs[j]['treatment'] == 'player_portrait_frames' for j in jobs):
        payload.update(dependency_policy='external_portrait_native_identity_first_pass',
                       native_identity_sources=native_identity)
    elif all(q.jobs[j]['treatment'] == 'npc_portrait_family' for j in jobs):
        payload['dependency_policy'] = 'independent_external_portrait_first_pass'
    else:
        dependencies = {c for j in jobs for c in q.generation_dependencies(q.jobs[j], payload)}
        assert all(q.accepted(c) for c in dependencies), 'Review and accept required seeds first'
        payload['dependency_cells'] = {c: q.state['cells'][c]['sha256'] for c in dependencies}
    for job in jobs:
        q.generation_dependencies(q.jobs[job], payload)
    attempts = [a for a in q.state['attempts'] if read(Path(a['payload'])).get('external_return')
                == payload['external_return'] and a['sha256'] == receipt['raw_sha256']]
    assert len(attempts) <= 1
    if attempts:
        attempt = attempts[0]
    else:
        queue_module.save(q.payload_root / execution_id / 'payload.json', payload)
        result = q.record(execution_id, raw)
        attempt = next(a for a in q.state['attempts'] if a['id'] == result['attempt'])
    report = dict(bundle=bundle, sheet=sid, raw_sha256=digest(raw), attempt=attempt['id'],
                  status='per_cell_visual_review_pending', accepted=0, staged=0, cells=[])
    with Image.open(raw) as image:
        rectangles = opaque_rectangles(image, sheet['columns'], sheet['rows'])
        pages = []
        for i, cell in enumerate(layout['cells']):
            rect = rectangles[cell['slot'] - 1]
            try:
                rect = trim_gutter(image, rect)
                ratios = sampling(rect, cell['native_size'])
            except AssertionError as error:
                report['cells'].append(dict(id=cell['id'], raw_rect=rect,
                    status='deferred_extraction', reason=str(error)))
                if cell['id'] not in q.state['cells']:
                    q.state['cells'][cell['id']] = dict(status='deferred', attempt=attempt['id'],
                        reason=str(error), external_return=str(output / 'review.json'))
                q.state['external_assignments'][cell['id']].update(status='returned', attempt=attempt['id'])
                continue
            x, y, w, h = rect
            candidate = image.crop((x, y, x + w, y + h)).convert('RGB').resize(
                tuple(cell['x2_size']), Image.Resampling.LANCZOS)
            artifact = output / (cell['id'] + '.png')
            if artifact.exists():
                with Image.open(artifact) as previous:
                    assert np.array_equal(np.asarray(previous), np.asarray(candidate)), 'Existing candidate changed'
            else:
                candidate.save(artifact)
            evidence_path = output / 'registration' / (cell['id'] + '-registration.json')
            if not evidence_path.exists():
                registration.evidence(cell['member'], q.targets[cell['id']], artifact, output / 'registration')
            evidence = read(evidence_path)
            report['cells'].append(dict(id=cell['id'], raw_rect=rect, sampling=ratios,
                artifact=str(artifact), artifact_sha256=digest(artifact), registration_record=str(evidence_path),
                status=q.state['cells'].get(cell['id'], {}).get('status', 'review_pending')))
            while len(pages) <= i // 16:
                pages.append(Image.new('RGB', (4 * 252, 4 * 190), '#292929'))
            page = pages[i // 16]
            col, row = i % 4, (i % 16) // 4
            px, py = col * 252, row * 190
            with Image.open(folder / cell['native_png']) as source:
                native = source.convert('RGB').resize(tuple(cell['x2_size']), Image.Resampling.NEAREST)
            assert max(native.size) <= 158, 'Use a larger review page for this artwork'
            page.paste(native, (px, py + 24))
            page.paste(candidate, (px + 126, py + 24))
            ImageDraw.Draw(page).text((px + 2, py + 3), f"{cell['slot']}: {Path(cell['member']['source_path']).name}",
                                      fill='white')
            if cell['id'] not in q.state['cells']:
                q.state['cells'][cell['id']] = dict(status='review_pending', attempt=attempt['id'],
                    reason='Dense master retained; exact x2 candidate extracted. Visual fidelity and seed review pending.',
                    artifact=str(artifact), external_return=str(output / 'review.json'))
            elif (q.state['cells'][cell['id']].get('status') == 'review_pending'
                  and q.state['cells'][cell['id']].get('attempt') == attempt['id']):
                q.state['cells'][cell['id']].update(artifact=str(artifact),
                    external_return=str(output / 'review.json'))
            q.state['external_assignments'][cell['id']].update(status='returned', attempt=attempt['id'])
        for index, page in enumerate(pages):
            page.save(output / f'comparison-{index + 1:02d}.png')
    queue_module.save(q.state_path, q.state)
    queue_module.save(output / 'review.json', report)
    return dict(bundle=bundle, sheet=sid, candidates=sum('artifact' in c for c in report['cells']),
                deferred_extraction=sum(c['status'] == 'deferred_extraction' for c in report['cells']),
                review=str(output / 'review.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle')
    parser.add_argument('sheets', nargs='+')
    args = parser.parse_args()
    with (HERE / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for sid in args.sheets:
            print(json.dumps(process(args.bundle, sid)), flush=True)
