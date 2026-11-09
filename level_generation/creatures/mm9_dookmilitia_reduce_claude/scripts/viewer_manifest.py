#!/usr/bin/env python3
"""review/viewer/manifest.json: installed (12,906) and reduced candidate for tiers A/B/C (GLBs from viewer_tiers.py); clips
copied from the creature project's viewer manifest (read only), anchor images pointed there.
Usage: viewer_manifest.py <tag> <reduced count label>"""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
tag, cnt = sys.argv[1], sys.argv[2]
o = json.load(open(ROOT.parent / 'mm9_dookmilitia_claude' / 'review' / 'viewer' / 'manifest.json'))
for c in o['clips'].values():
    for a in c.get('anchors', []):
        a['source_images'] = [x.replace('../../', '../../../mm9_dookmilitia_claude/', 1) for x in a.get('source_images', [])]
names = {'a': 'A: Half Orc Recruit', 'b': 'B: Half Orc Soldier', 'c': 'C: Half Orc Captain'}
labs = {'before': 'installed r19 · 12,906', tag: f'reduced {tag} · {cnt}'}
models = []
for t in 'abc':
    for lab in labs:
        f = f'dook_{t}_{lab}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1', 'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'model': f'dook_a_{tag}.glb', 'default_clip': 'Standing', 'default_model': f'a_{tag}',
           'feedback': 'feedback/user_feedback.json', 'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models), 'models', len(o['clips']), 'clips')
