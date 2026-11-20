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
    batch_id = 'batch-retained-nine-items-v1'
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
            note='Historical built-in 3x3 experiment; original prompt/reference/raw retained. No new call. '
                 'Only accepted treatment-pilot dependencies apply; no page or identity-seed art was supplied.'),
        tool_args=dict(prompt=prompt, referenced_image_paths=[str(OUT / 'reference.png')]))
    assert all(d['kind'] == 'accepted_treatment_pilot' for j in jobs for d in q.jobs[j]['dependencies'])
    queue_module.save(directory / 'payload.json', payload)
    attempt = q.record(batch_id, OUT / 'raw.png')['attempt']

notes = {
    '6helm3': 'Silver feathered wings, spike, T-shaped opening and cheek spacing preserved. '
              'Smooth feather ridges and mottled metal resolve beyond source pixels; no conspicuous matte fringe.',
    '6helm4': 'Two curved horns, brow band, open face and cheek guards retain native scale. '
              'Gold highlights and rivets are clearer but retain the original materials and single brow ornament.',
    '6helm5': 'Gold swept projections, central ridge, blue brow gem, open face and neck guard retain layout. '
              'Dense gold neck texture and engravings are interpreted more crisply; native identity is preserved.',
    '7item090': 'Dark small domed cap retains its tiny apex, rim position and full canvas occupancy. '
                'Restrained textured dome and clearer gold rim remain readable at native logical size.',
    '7item091': 'Silver dome and pale riveted bands remain aligned above asymmetric dark chainmail flaps. '
                'Fine mail replaces block shading without changing the neck silhouette.',
    '7item092': 'Reddish metal, two short ivory horns, dark face and unequal long cheek guards retained. '
                'Rivets sharpen while the opening and crown-to-guard proportions match.',
    '7item093': 'Green engraved dome, two red oval ornaments, gold apex and ivory horns preserve orientation. '
                'More distinct engraving remains subordinate to the original red/green identity and proportions.',
    '7item094': 'Brown folded hat, gold rope band and long striped feather retain placement and relative scale. '
                'Continuous folds and braided detail replace native blocks; no missing brim or feather tip.',
}
accepted = []
for row in processing['cells']:
    cell = row['cell']
    name = Path(q.members[cell][1]['source_path']).stem
    if name not in notes:
        if not q.accepted(cell):
            q.state['cells'][cell] = dict(status='deferred', attempt=attempt,
                reason='3x3 retained candidate: alpha-16 footprint/margins exceed tolerance; inspect horn/spike edge.')
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
    deferred=['engine--icons--7item089.bmp'], generation_calls_this_adoption=0))
print(json.dumps(dict(attempt=attempt, accepted_and_staged=len(accepted), deferred=1)))
