#!/usr/bin/env python3
"""review/viewer/manifest.json for the given tag (rebuild | before): the three tiers' viewer GLBs, clips and durations from the first.
Usage: viewer_manifest.py <tag> <revision>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, '../mm7_m274_texpass_claude/scripts')
from glb import Glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
tag, rev = sys.argv[1], sys.argv[2]
TIERS = {'gua_a': 'Guard A (blue sleeves, teal trousers)', 'gua_b': 'Lieutenant B (green)', 'gua_c': 'Captain C (red)'}
SRC = {'Standing': 'MM9 GUARD stand', 'Walking': 'walk', 'Running': 'run', 'Fidget': 'fidget1', 'Attack': 'Hattack1 (impact 0.456 s)',
       'Attack2': 'Hattack2', 'Hit': 'wince1', 'Death': 'die1', 'Dead': 'die1 end pose'}
g = Glb(V / f'gua_a_{tag}.glb'); clips = {}
for anim in g.doc['animations']:
    n = anim['name']; d = max(float(g.accessor(s['input']).max()) for s in anim['samplers'])
    clips[n] = {'label': n, 'duration': d, 'mode': 'loop' if n in ('Standing', 'Walking', 'Running', 'Jog', 'Sprint', 'Dead') else 'once',
                'provenance': SRC.get(n, 'installed before the rebuild') if tag == 'rebuild' else 'installed before the rebuild', 'anchors': []}
models = []
for t, label in TIERS.items():
    f = V / f'{t}_{tag}.glb'; h = hashlib.sha256(f.read_bytes()).hexdigest()
    models.append({'id': f'{t}_{tag}', 'label': f'{label} · {tag}', 'url': f'{f.name}?v={h[:12]}', 'sha256': h, 'revision': rev})
man = {'revision': rev, 'default_model': models[0]['id'], 'default_clip': 'Standing', 'models': models, 'clips': clips, 'issues': [],
       'feedback': 'feedback/user_feedback.json', 'model': models[0]['url'], 'model_sha256': models[0]['sha256']}
(V / 'manifest.json').write_text(json.dumps(man, indent=1) + '\n'); print('MANIFEST', tag, len(models), list(clips))
