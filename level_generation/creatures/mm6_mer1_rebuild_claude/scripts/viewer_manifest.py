#!/usr/bin/env python3
"""review/viewer/manifest.json for the given tag (rebuild | before): the three tiers' viewer GLBs, clips and durations from the first.
Usage: viewer_manifest.py <tag> <revision>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm7_m274_texpass_claude/scripts'))
from glb import Glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
tag, rev = sys.argv[1], sys.argv[2]
TIERS = {'mer1_a': 'Merchant A', 'mer1_b': 'Merchant B', 'mer1_c': 'Merchant C'}
SRC = {'Standing': 'MM9 NOBLEMAN stand', 'Walking': 'NOBLEMAN walk', 'Running': 'NOBLEMAN run (sprint)', 'Fidget': 'NOBLEMAN fidget1',
       'Attack': 'FIGHTERBASE Hattack2 (club blow)', 'Hit': 'NOBLEMAN wince1', 'Death': 'NOBLEMAN die1', 'Dead': 'die1 end pose',
       'Walk2': 'NOBLEMAN walk, legs gained', 'Jog': 'NOBLEMAN run, legs gained'}
g = Glb(V / f'mer1_a_{tag}.glb'); clips = {}
for anim in g.doc['animations']:
    n = anim['name']; d = max(float(g.accessor(s['input']).max()) for s in anim['samplers'])
    clips[n] = {'label': n, 'duration': d, 'mode': 'loop' if n in ('Standing', 'Walking', 'Running', 'Walk2', 'Jog', 'Sprint', 'Dead') else 'once',
                'provenance': SRC.get(n, 'installed before the rebuild') if tag == 'rebuild' else 'installed before the rebuild', 'anchors': []}
models = []
for tg in [tag] + [x for x in ('rebuild', 'before') if x != tag]:       # both tags listed: identical-camera before/after shots
    for t, label in TIERS.items():
        f = V / f'{t}_{tg}.glb'
        if not f.exists(): continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{t}_{tg}', 'label': f'{label} · {tg}', 'url': f'{f.name}?v={h[:12]}', 'sha256': h, 'revision': rev})
man = {'revision': rev, 'default_model': models[0]['id'], 'default_clip': 'Standing', 'models': models, 'clips': clips, 'issues': [],
       'feedback': 'feedback/user_feedback.json', 'model': models[0]['url'], 'model_sha256': models[0]['sha256']}
(V / 'manifest.json').write_text(json.dumps(man, indent=1) + '\n'); print('MANIFEST', tag, len(models), list(clips))
