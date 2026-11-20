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
notes = {'item177': 'Blue potion retains brass-green cage, middle band, narrow color-coded neck and tiny stopper loop. Band height, body contour and light patches align visually. Family checked together: colors stay distinct and smooth material shading survives x2.', 'item178': 'Red potion retains brass-green cage, middle band, narrow color-coded neck and tiny stopper loop. Band height, body contour and light patches align visually. Family checked together: colors stay distinct and smooth material shading survives x2.', 'item180': 'White potion retains brass-green cage, middle band, narrow color-coded neck and tiny stopper loop. Band height, body contour and light patches align visually. Family checked together: colors stay distinct and smooth material shading survives x2.', 'item181': 'Gray potion retains brass-green cage, middle band, narrow color-coded neck and tiny stopper loop. Band height, body contour and light patches align visually. Family checked together: colors stay distinct and smooth material shading survives x2.', 'item182': 'Black potion retains brass-green cage, middle band, narrow color-coded neck and tiny stopper loop. Band height, body contour and light patches align visually. Family checked together: colors stay distinct and smooth material shading survives x2.', 'item183': 'Purple potion retains brass-green cage, middle band, narrow color-coded neck and tiny stopper loop. Band height, body contour and light patches align visually. Family checked together: colors stay distinct and smooth material shading survives x2. Real purple remains opaque after magenta cleanup.', 'item184': 'Green potion retains brass-green cage, middle band, narrow color-coded neck and tiny stopper loop. Band height, body contour and light patches align visually. Family checked together: colors stay distinct and smooth material shading survives x2.', 'item185': 'Amber potion retains brass-green cage, middle band, narrow color-coded neck and tiny stopper loop. Band height, body contour and light patches align visually. Family checked together: colors stay distinct and smooth material shading survives x2.'}
deferred_reasons = {'item179': 'Yellow potion fails alpha16 footprint/margin tolerance despite passing selected landmarks. Inspect thin stopper loop and low-alpha outer extent later; preserve passing siblings.'}
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
                str(OUT / 'registration-all.png'), str(OUT / 'comparison-enlarged.png'), str(OUT / 'raw.png')])
        module.save(OUT / (name + '-acceptance.json'), review)
        q.accept(cell, artifact, review, manifest['attempt'])
    reconstructed = q.reconstruct(cell)
    assert digest(Path(reconstructed['path'])) == digest(artifact)
    review = dict(full_canvas_review=True, artifact_sha256=reconstructed['sha256'],
        notes=notes[name] + ' Full single-cell reconstruction is byte-identical to the reviewed native-x2 canvas.',
        review_images=[str(OUT / 'registration-all.png'), str(OUT / 'comparison-enlarged.png')])
    module.save(OUT / (name + '-canvas-review.json'), review)
    q.stage(cell, review)
    accepted.append(cell)
module.save(OUT / 'acceptance.json', dict(attempt=manifest['attempt'], accepted_and_staged=accepted,
    generation_calls_this_review=0, runtime_review='pending', deferred=deferred_reasons))
print(json.dumps(dict(accepted_and_staged=len(accepted), attempt=manifest['attempt'])))
