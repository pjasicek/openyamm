#!/usr/bin/env python3
"""Scratch viewer review/vtest/ for A/B checks: copies the given viewer GLBs and writes its manifest (first = default).
Usage: vtest.py <glb> [<glb> ...]"""
import hashlib, json, shutil, struct, sys
from pathlib import Path


def durations(g):
    """Clip lengths of a GLB (the viewer rejects a model whose clips differ from the manifest)."""
    b = g.read_bytes(); n = struct.unpack_from('<I', b, 12)[0]; j = json.loads(b[20:20 + n])
    return {a['name']: max(j['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in j['animations']}
V = Path('review/vtest'); base = json.loads(Path('review/viewer/manifest.json').read_text())
models = []
for g in map(Path, sys.argv[1:]):
    shutil.copy(g, V / g.name); h = hashlib.sha256(g.read_bytes()).hexdigest()
    models.append({'id': g.stem, 'label': g.stem, 'url': f'{g.name}?v={h[:12]}', 'revision': 't', 'sha256': h})
for name, t in durations(Path(sys.argv[1])).items():
    if name in base['clips']:
        base['clips'][name]['duration'] = round(t, 6)
base.update(models=models, default_model=models[0]['id'], feedback='../feedback/user_feedback.json')
(V / 'manifest.json').write_text(json.dumps(base, indent=1)); print('VTEST', [m['id'] for m in models])
