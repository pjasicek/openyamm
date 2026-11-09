#!/usr/bin/env python3
"""review/viewer/manifest.json for the reduction review: the creature viewer's clips (../mm9_skeleton_claude/review/viewer)
with this project's models, installed and reduced per tier. Usage: viewer_manifest_skel.py <revision> <id>=<label> ..."""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review' / 'viewer'
m = json.load(open(HERE.parent / 'mm9_skeleton_claude' / 'review' / 'viewer' / 'manifest.json'))
rev = sys.argv[1]; models = []
for spec in sys.argv[2:]:
    mid, label = spec.split('=', 1)
    sha = hashlib.sha256((V / f'{mid}.glb').read_bytes()).hexdigest()
    models.append({'id': mid, 'label': label, 'revision': rev, 'url': f'{mid}.glb?v={sha[:12]}', 'sha256': sha})
m['models'] = models; m['revision'] = rev; m['model'] = models[0]['url'].split('?')[0]; m['default_model'] = models[0]['id']
txt = json.dumps(m, indent=1).replace('../../references_hd/', '../../../mm9_skeleton_claude/references_hd/')
(V / 'manifest.json').write_text(txt + '\n'); print('MANIFEST', [x['id'] for x in models])
