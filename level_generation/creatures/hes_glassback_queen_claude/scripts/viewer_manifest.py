#!/usr/bin/env python3
"""review/viewer/manifest.json for the review viewer (tools/run_creature_review.py): the models given as
<file>:<label> and every clip of the first model with its GLB length (the viewer check requires equal durations).
Usage: viewer_manifest.py <revision> <concept image path relative to review/viewer> <file:label> ..."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402

V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
revision, concept, specs = sys.argv[1], sys.argv[2], sys.argv[3:]
NOTES = json.loads((V / 'clip_notes.json').read_text()) if (V / 'clip_notes.json').exists() else {}
models = []
for spec in specs:
    f, label = spec.split(':', 1)
    h = hashlib.sha256((V / f).read_bytes()).hexdigest()
    models.append({'id': Path(f).stem, 'label': label, 'revision': revision, 'url': f'{f}?v={h[:12]}', 'sha256': h})
doc, b = read_glb(V / specs[0].split(':', 1)[0])
clips = {}
for an in doc['animations']:
    t = max(float(np.frombuffer(accessor_bytes(doc, b, s['input']), np.float32).max()) for s in an['samplers'])
    note = NOTES.get(an['name'], an['name'])
    loop = an['name'] in ('Standing', 'Walking', 'Running')
    clips[an['name']] = {'label': an['name'], 'duration': round(t, 6), 'mode': 'loop' if loop else 'once',
                         'provenance': note, 'anchors': [{'time': 0.0, 'label': an['name'], 'phase': note,
                                                          'source_images': [concept]}]}
default = 'Standing' if 'Standing' in clips else next(iter(clips))
json.dump({'revision': revision, 'model': models[0]['url'].split('?')[0], 'model_sha256': models[0]['sha256'],
           'default_clip': default, 'default_model': models[0]['id'], 'feedback': 'feedback/user_feedback.json',
           'models': models, 'clips': clips}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models), 'models', len(clips), 'clips', {k: v['duration'] for k, v in clips.items()})
