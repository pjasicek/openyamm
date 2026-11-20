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
notes = {'6book2': 'Red-brown leather book retains pale scroll-shaped end plates, left binding and pale page block. Cover angle and page thickness match; continuous worn leather detail survives x2.', 'book1': 'Pale patterned cover retains brown corner caps and two left straps. Repeated dark marks remain a subordinate cover pattern, and page block aligns with native.', 'book4': 'Blue cover retains three vertical bars crossed by one horizontal bar, side straps and corner plates. Bar topology and placement match visually; page-block thickness and corners align.', 'book5': 'Green book retains raised oval motifs in rows, pale ornate end plates and green spine. Native cover arrangement and page thickness remain recognizable at x2.'}
deferred_reasons = {'7item190': 'Upper cover corner extremity differs by 4 x2 pixels; central gold symbol has more explicit points and needs fidelity inspection.', '7item191': 'Regional corner metrics differ by 3 to 10.5 x2 pixels; inspect semantic corner correspondence before deciding fitting repair. Retain cover lattice and stud evidence.', '7item192': 'Upper and bottom corner metrics differ by 4 and 5.5 pixels; inspect fitting and central medallion interpretation later.', '7item193': 'Central square plaque now has an explicit interlaced knot not clearly resolved in native; inspect symbol fidelity later despite passing corner measurements.', 'book3': 'Bottom page corner extremity differs by 3 x2 pixels; inspect thin page-block geometry later.'}
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
