"""Commit the completed visual review of this retained sheet, preserving exact full canvases."""
import fcntl
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
HUD = OUT.parents[1]
sys.path.insert(0, str(HUD))
from finalize_classification import digest

spec = importlib.util.spec_from_file_location('hud_queue', HUD / 'queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
lock = (HUD / 'checkpoint/state.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX)
q = module.Queue()
manifest = json.loads((OUT / 'manifest.json').read_text())
processing = json.loads((OUT / 'processing.json').read_text())
landmarks = json.loads((OUT / 'measured-landmarks.json').read_text())
notes = {'7item118v1': 'Black plated boots retain gold studded cuff rims, silver ankle/toe highlights, native pair angles and full-canvas margins. Angled variants retain smooth dark foot plates; standing variant retains its native asymmetric shin fastening and segmented silver toes. Continuous metal shading replaces native pixel blocks without adding a different material. Raw, complete final comparisons, light/dark composites and all full overlays visually reviewed. Both footprint thresholds pass and four independent cuff/toe landmarks are within 2 x2 pixels; no conspicuous matte fringe.', '7item118v2': 'Black plated boots retain gold studded cuff rims, silver ankle/toe highlights, native pair angles and full-canvas margins. Angled variants retain smooth dark foot plates; standing variant retains its native asymmetric shin fastening and segmented silver toes. Continuous metal shading replaces native pixel blocks without adding a different material. Raw, complete final comparisons, light/dark composites and all full overlays visually reviewed. Both footprint thresholds pass and four independent cuff/toe landmarks are within 2 x2 pixels; no conspicuous matte fringe.', '7item118v4': 'Black plated boots retain gold studded cuff rims, silver ankle/toe highlights, native pair angles and full-canvas margins. Angled variants retain smooth dark foot plates; standing variant retains its native asymmetric shin fastening and segmented silver toes. Continuous metal shading replaces native pixel blocks without adding a different material. Raw, complete final comparisons, light/dark composites and all full overlays visually reviewed. Both footprint thresholds pass and four independent cuff/toe landmarks are within 2 x2 pixels; no conspicuous matte fringe.'}
deferred_reasons = {'7item118v5': 'Right toe landmark differs by 2.5 x2 pixels despite passing global footprint checks. Inspect native toe-tip shape and standing pair placement; retain raw and full comparison/overlay evidence in production/mm7boots118_01/ for repair after first pass.'}
accepted = []
for row in processing['cells']:
    cell = row['cell']
    name = Path(q.members[cell][1]['source_path']).stem
    if name in deferred_reasons:
        if not q.accepted(cell):
            q.state['cells'][cell] = dict(status='deferred', reason=deferred_reasons[name], attempt=manifest['attempt'])
            module.save(q.state_path, q.state)
        continue
    assert not row['failures'] and all(p['max_error_x2'] <= 2 for p in landmarks[name])
    artifact, record_path = Path(row['artifact']), Path(row['registration_record'])
    if not q.accepted(cell):
        record = json.loads(record_path.read_text())
        record.update(landmarks=landmarks[name], visual_fit_notes=notes[name] +
            ' Raw master, final x2/light-dark combined proof and every native/restored/overlay comparison '
            'in the unscaled registration-all.png were inspected. Smooth painted detail survives at final size; '
            'no conspicuous magenta fringe, missing component or enlarged native pixel-grid shading.')
        module.save(record_path, record)
        review = dict(identity=True, registration=True, compositing=True, detail_at_x2=True,
            state_or_animation_consistency=True, notes=record['visual_fit_notes'],
            registration_record=str(record_path), review_images=[*row['review_images'],
                str(OUT / 'registration-all.png'), str(OUT / 'comparison.png'), str(OUT / 'raw.png')])
        module.save(OUT / (name + '-acceptance.json'), review)
        q.accept(cell, artifact, review, manifest['attempt'])
    reconstructed = q.reconstruct(cell)
    assert digest(Path(reconstructed['path'])) == digest(artifact)
    review = dict(full_canvas_review=True, artifact_sha256=reconstructed['sha256'],
        notes=notes[name] + ' Full single-cell reconstruction is byte-identical to the reviewed native-x2 canvas.',
        review_images=[str(OUT / 'registration-all.png'), str(OUT / 'comparison.png')])
    module.save(OUT / (name + '-canvas-review.json'), review)
    q.stage(cell, review)
    accepted.append(cell)
module.save(OUT / 'acceptance.json', dict(attempt=manifest['attempt'], accepted_and_staged=accepted,
    generation_calls_this_review=0, runtime_review='pending', deferred=deferred_reasons))
print(json.dumps(dict(accepted_and_staged=len(accepted), attempt=manifest['attempt'])))
