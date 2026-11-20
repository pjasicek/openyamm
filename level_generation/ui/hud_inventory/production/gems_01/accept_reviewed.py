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
notes = {'gem2': 'Cyan elongated crystal retains diagonal axis, four outer points, dark teal rim and central pale elongated reflection. Facet direction follows the long axis; restored edges and reflected planes resolve without native pixel blocks.', 'gem3': 'Amber triangular gem retains all three points, left brown face and white-gold central reflection. Internal triangular planes meet in the native central region; final x2 contour and shading remain coherent.', 'gem5': 'Blue-violet five-sided gem retains the upper oblique edge, right-facing point and pale triangular central reflection. Five principal face directions and reflection placement match visually; purple remains opaque and edges clean on light and dark.', 'gem6': 'Green hexagonal gem retains horizontal top/bottom edges and centered triangular pale reflection with dark left facets. Facet ring and internal scale match at final x2; no visible matte fringe.', 'gem7': 'Violet angular gem retains six-sided outer cut, dark rim and central triangular lilac reflection. Main internal facet spacing remains consistent with native at x2; actual purple survives cleanup without holes.'}
deferred_reasons = {'gem1': 'Rounded pale gem gained a conspicuous white specular dot and mosaic-like concentric facets rather than native softer continuous surface; inspect material fidelity later.', 'gem4': 'Red diamond gained a sharp cross/star flare and extra sparkle dots around the central reflection; inspect native highlight fidelity later.', 'gem8': 'Amber gem now has strongly segmented symmetric polygon facets, changing the native softer asymmetric surface shading. Inspect facet/material fidelity later.', 'gem9': 'Pale green oval gained coarse polygon/mosaic shading instead of the native continuous soft surface. Inspect restoration detail/material fidelity later.'}
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
