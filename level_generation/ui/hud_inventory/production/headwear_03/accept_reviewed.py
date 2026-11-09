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
notes = {'item109': 'Brown conical cap retains silver cross strap and projecting nose guard. Strap width, guard length and brown panel proportions visually align at x2; smooth metal contours and leather shading, complete clean edges.', 'item114': 'Brown soft cap retains red crown patch, blue band, small blue front button and side flaps. Band height and patch extent visually match native; soft folded brim preserved with clean matte extraction.', 'item115': 'Dark blue drooping cap retains left red feather, gold base band and small right gold fold. Feather root, cloth bend and band height match visually at final x2; feather barbs and cloth shading resolve without enlarged source pixels.', 'item258': 'Tall black and gold crown retains five separated dark points, taller center spike and green-red-green front stones. Spike roots, spacing and central gold panel checked against native at final x2; holes remain open and rim/canvas placement complete.'}
deferred_reasons = {'item110': 'Chainmail acquired very bright densely outlined rings versus native dark mesh; inspect mail tone and fang/face opening details later.', 'item111': 'Left/right contour extrema differ9/2.5 x2 pixels; inspect corresponding rim points and added gold studs/eye-slot framing before acceptance.', 'item112': 'Upper/lower contour metrics differ3.85/2.35 x2 pixels; inspect horn-tip/rim correspondence and explicit gold flame/diamond ornament interpretation.', 'item113': 'Wing edge differs2.16 x2 pixels; inspect feather correspondence, brighter gold wings and explicit red tied ribbon versus native details.', 'item256': 'Left horn/rim metrics differ3/2.17 x2 pixels; inspect horn tip correspondence and eye/faceplate shape before acceptance.'}
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
