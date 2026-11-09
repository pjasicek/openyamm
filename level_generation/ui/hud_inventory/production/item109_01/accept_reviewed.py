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
notes = {'item109v1': 'Brown cap, pale metal central band, curved lower rim and elongated nose guard retain native shape, perspective, opening and material identity. Fourth variant keeps its narrower taller olive-brown cap and brighter central band. Continuous painted metal and mottled cap detail replace source blocks without added ornament. Actual complete raw sheet, each full final-x2 cell, complete native/restored/overlay proof and full-size light/dark composites inspected: no conspicuous matte fringe, clipping or missing part. Footprints pass and independently measured cap apex, nose guard tip and left rim tip are within 0.5 x2 pixel.', 'item109v3': 'Brown cap, pale metal central band, curved lower rim and elongated nose guard retain native shape, perspective, opening and material identity. Fourth variant keeps its narrower taller olive-brown cap and brighter central band. Continuous painted metal and mottled cap detail replace source blocks without added ornament. Actual complete raw sheet, each full final-x2 cell, complete native/restored/overlay proof and full-size light/dark composites inspected: no conspicuous matte fringe, clipping or missing part. Footprints pass and independently measured cap apex, nose guard tip and left rim tip are within 0.5 x2 pixel.', 'item109v4': 'Brown cap, pale metal central band, curved lower rim and elongated nose guard retain native shape, perspective, opening and material identity. Fourth variant keeps its narrower taller olive-brown cap and brighter central band. Continuous painted metal and mottled cap detail replace source blocks without added ornament. Actual complete raw sheet, each full final-x2 cell, complete native/restored/overlay proof and full-size light/dark composites inspected: no conspicuous matte fringe, clipping or missing part. Footprints pass and independently measured cap apex, nose guard tip and left rim tip are within 0.5 x2 pixel.'}
deferred_reasons = {'item109v2': 'Plausible helmet and footprint pass, but independently measured left rim lower tip shifts 5 x2 pixels, exceeding 2-pixel tolerance; retain for later fitting inspection and preserve accepted siblings.'}
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
                str(OUT / 'registration-all.png'), str(OUT / 'comparison.png'), str(OUT / 'raw.png'), str(OUT / 'full-light-dark.png')])
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
