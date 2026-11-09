#!/usr/bin/env python3
"""Viewer manifest for the 2026-10-30 rework: copies v2/export/mm9_<prefix>.glb into review/viewer/ and writes
manifest.json with per-clip provenance. Usage: make_viewer_v2.py <revision> <prefix> <label> <provenance json>"""
import hashlib, json, shutil, struct, sys
from pathlib import Path
P = Path(__file__).resolve().parents[2]
VIEWER = P / 'review' / 'viewer'
MODES = {'Standing': 'loop', 'Walking': 'loop', 'Running': 'loop', 'Dead': 'loop'}
revision, prefix, label, prov = sys.argv[1:5]
prov = json.load(open(prov))
(VIEWER / 'feedback').mkdir(parents=True, exist_ok=True)
fb = VIEWER / 'feedback' / 'user_feedback.json'
if not fb.exists():
    fb.write_text('{"findings": []}\n')
dst = VIEWER / f'{prefix}.glb'
shutil.copyfile(P / 'v2' / 'export' / f'mm9_{prefix}.glb', dst)
data = dst.read_bytes()
doc = json.loads(data[20:20 + struct.unpack_from('<I', data, 12)[0]])
clips = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(data).hexdigest()
manifest = {'revision': revision, 'model': dst.name, 'default_clip': 'Standing', 'default_model': prefix,
            'feedback': 'feedback/user_feedback.json',
            'models': [{'id': prefix, 'label': label, 'revision': revision, 'url': f'{dst.name}?v={sha[:12]}', 'sha256': sha}],
            'clips': {n: {'label': f"{n} ({prov['clips'].get(n, '')})", 'duration': d, 'mode': MODES.get(n, 'once'),
                          'provenance': prov['provenance'],
                          'anchors': [{'time': 0, 'label': n, 'phase': 'Start',
                                       'source_images': ['../../references_hd/01_front.png']}]}
                      for n, d in clips.items()}}
(VIEWER / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('manifest', revision, {k: round(v, 3) for k, v in clips.items()})
