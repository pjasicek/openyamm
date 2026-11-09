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
notes = {'item212': 'Pink pointed gem retains high apex, left dark face and pale diagonal lower-right band. Internal central planes and pale band endpoints align visually at final x2. Genuine pink stays opaque after matte extraction; continuous angled edges replace source pixel steps.', 'item213': 'Yellow irregular gem retains dark olive-brown upper-right plane and broad pale left/lower faces. Outer corners and division between dark and pale planes match visually; clean bright edge on dark and light previews.', 'item214': 'Orange gem retains raised pale pink-white upper face, warm orange body and bright lower-right edge. Main facet divisions, cap extent and oblique top remain consistent at final x2, with resolved reflective planes rather than enlarged source pixels.', 'item215': 'Low orange oval retains dark central amber face, pale upper rim and broad white lower highlight. Relative height, center and reflection placement remain consistent; smooth contour and distinct facets survive final size.', 'item217': 'Blue tilted oval retains diagonal axis, dark blue middle and large icy lower-left reflection with pale top edge. Reflection regions and rim spacing align visually; no visible magenta fringe or missing material.', 'item220': 'Violet rounded angular gem retains dark diagonal central face and pale upper-left and lower-right border reflections. Internal dark face occupies the native area and direction; purple remains opaque and complete at final x2.'}
deferred_reasons = {'item216': 'Pale round gem gained a conspicuous straight horizontal equator dividing its surface, absent from native cloudy shading. Inspect retained material fidelity before later repair.', 'item218': 'Paired violet lobes retain outline but bright upper highlights become broad faceted caps and lower reflections shift; inspect native internal highlight correspondence later.', 'item219': 'Green oval now has busy high-contrast triangular facets instead of softer native pale-green reflection regions. Inspect internal surface fidelity later.'}
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
