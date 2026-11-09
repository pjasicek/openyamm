"""Explicitly adopt the historical sheet and reviewed cells; never submit or pretend to rerun imagegen."""
import fcntl
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
HUD = OUT.parents[1]
sys.path.insert(0, str(HUD))
from finalize_classification import ROOT, digest

spec = importlib.util.spec_from_file_location('hud_queue', HUD / 'queue.py')
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)
lock = (HUD / 'checkpoint/state.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX)
q = queue_module.Queue()
manifest = json.loads((OUT / 'manifest.json').read_text())
processing = json.loads((OUT / 'processing.json').read_text())
landmarks = json.loads((OUT / 'measured-landmarks.json').read_text())
assert digest(OUT / 'raw.png') == manifest['raw_sha256'] == processing['raw_sha256']
assert digest(OUT / 'reference.png') == manifest['reference_sha256']
jobs = sorted({r['job'] for r in manifest['rows']})
dependencies = {j: {c: q.state['cells'][c]['sha256'] for c in q.dependency_cells(q.jobs[j])} for j in jobs}
assert all(not q.blockers(q.jobs[j]) for j in jobs)
assert all(d == dependencies[jobs[0]] for d in dependencies.values())
for row in manifest['rows']:
    member = row['member']
    assert q.members[member['id']] == (row['job'], member)
    assert digest(ROOT / member['source_path']) == member['source_sha256']
attempts = [a for a in q.state['attempts'] if a['sha256'] == manifest['raw_sha256']]
assert len(attempts) <= 1, 'Do not duplicate a retained generation call'
if attempts:
    attempt = attempts[0]['id']
else:
    batch_id = 'batch-retained-eight-items-v1'
    directory = q.payload_root / batch_id
    directory.mkdir(parents=True, exist_ok=False)
    prompt = (OUT / 'prompt.txt').read_text().rstrip('\n')
    payload = dict(job=jobs[0], jobs=jobs, batch_id=batch_id,
        selected_cells=[r['member']['id'] for r in manifest['rows']], prompt=prompt,
        dependency_cells=dependencies[jobs[0]], layout_sha256=q.state.get('layout_revision', {}).get('sha256'),
        source_hashes={r['member']['id']: r['member']['source_sha256'] for r in manifest['rows']},
        reference_hashes={str(OUT / 'reference.png'): manifest['reference_sha256']},
        execution_layout=dict(canvas_size=manifest['reference_size'],
            cell_rects={r['member']['id']: r['reference_rect'] for r in manifest['rows']},
            slot_rects={r['member']['id']: r['cell_rect'] for r in manifest['rows']}),
        retrospective_import=dict(manifest=str(OUT / 'manifest.json'), sha256=digest(OUT / 'manifest.json'),
            note='Historical built-in 4x2 experiment; original prompt/reference/raw retained. No new call. '
                 'Only accepted treatment-pilot dependencies apply; no page or identity-seed art was supplied.'),
        tool_args=dict(prompt=prompt, referenced_image_paths=[str(OUT / 'reference.png')]))
    assert all(d['kind'] == 'accepted_treatment_pilot' for j in jobs for d in q.jobs[j]['dependencies'])
    queue_module.save(directory / 'payload.json', payload)
    attempt = q.record(batch_id, OUT / 'raw.png')['attempt']

notes = {'6hat2': 'Blue wide-brim hat, pale band and feather ornament retain native proportions and offsets. Continuous cloth shading and fine feather detail replace pixel blocks; light/dark contours are clean.', '6hat3': 'Dark pointed hat retains its apex, brim and pale central emblem relative to the band. Smooth purple-black cloth and folded pale band preserve the original identity; no conspicuous matte fringe.', '6helm1': 'Bronze dome retains its top knob, central strip, hanging tab and rim. Metal detail is smooth, with the same highlight side and full native canvas occupancy.', '6helm2': 'Dark mottled helmet retains spike, T-shaped face opening and both cheek guards. Fine metal texture preserves the original dark-light balance; openings and contours are clean.'}

deferred_reasons = {'6crown1': 'Gold leaf circlet central ornament/leaf arrangement interpreted too freely; requires focused fidelity repair.', '6crown2': 'Blue gem placement needs internal registration review before acceptance; outer footprint alone does not prove center ornament alignment.', '6crown3': 'Gold crown materially brighter than native; match native subdued gold before acceptance.', '6hat1': 'Green cap right feather extremity differs by 5 x2 pixels in landmark measurement; repair the feather while retaining cap silhouette.'}
accepted = []
for row in processing['cells']:
    cell = row['cell']
    name = Path(q.members[cell][1]['source_path']).stem
    if name not in notes:
        if not q.accepted(cell):
            q.state['cells'][cell] = dict(status='deferred', attempt=attempt,
                reason=deferred_reasons[name])
            queue_module.save(q.state_path, q.state)
        continue
    assert not row['failures']
    artifact = Path(row['artifact'])
    record_path = Path(row['registration_record'])
    if not q.accepted(cell):
        record = json.loads(record_path.read_text())
        record['landmarks'] = landmarks[name]
        record['visual_fit_notes'] = notes[name] + ' Actual raw sheet, all registration comparisons composed '
        record['visual_fit_notes'] += 'without scaling in registration-all.png, and light/dark final proof reviewed.'
        queue_module.save(record_path, record)
        review = dict(identity=True, registration=True, compositing=True, detail_at_x2=True,
            state_or_animation_consistency=True, notes=record['visual_fit_notes'],
            registration_record=str(record_path), review_images=[*row['review_images'],
                str(OUT / 'registration-all.png'), str(OUT / 'comparison.png'), str(OUT / 'comparison-enlarged.png'),
                str(OUT / 'raw.png')])
        queue_module.save(OUT / (name + '-acceptance.json'), review)
        q.accept(cell, artifact, review, attempt)
    accepted.append(cell)
    # These are full-canvas single-cell items. Reconstructed pixels must exactly match the reviewed candidate.
    result = q.reconstruct(cell)
    reconstructed = q.state['reconstructed_targets'][cell]
    canvas = Path(reconstructed['path'])
    assert digest(canvas) == digest(artifact), 'Single-cell reconstruction must preserve the reviewed bytes'
    canvas_review = dict(full_canvas_review=True, artifact_sha256=digest(canvas),
        notes=notes[name] + ' Full single-cell reconstruction is pixel-identical to the inspected exact-x2 canvas.',
        review_images=[str(OUT / 'comparison.png'), str(OUT / 'registration-all.png')])
    queue_module.save(OUT / (name + '-canvas-review.json'), canvas_review)
    q.stage(cell, canvas_review)
queue_module.save(OUT / 'adoption.json', dict(attempt=attempt, accepted_and_staged=accepted,
    deferred=['engine--icons--'+n+'.bmp' for n in deferred_reasons], generation_calls_this_adoption=0))
print(json.dumps(dict(attempt=attempt, accepted_and_staged=len(accepted), deferred=len(deferred_reasons))))
