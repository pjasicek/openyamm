#!/usr/bin/env python3
"""review/viewer/manifest.json for one tag (rebuild | before; the viewer checks clip durations per manifest): the three tiers' viewer GLBs.
Usage: viewer_manifest.py <tag> <revision>"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, '../mm7_m274_texpass_claude/scripts')
from glb import Glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
tag0, rev = sys.argv[1], sys.argv[2]
TIERS = {'pfem_a': 'PeasantF1 A (green)', 'pfem_b': 'PeasantF1 B (brown)', 'pfem_c': 'Peasantf1 C (blue)'}
SRC = {'Standing': 'MM9 PeasantFemale stand1', 'Walking': 'Walk', 'Walk2': 'Walk, leg swing x1.15 (game walk)', 'Running': 'run',
       'Fidget': 'Conv2 (subtle talk gesture)', 'Attack': 'Conv1 0.8-2.7 s x1.2 (restrained gesture)', 'Hit': 'Wince1', 'Death': 'Die1', 'Dead': 'Die1 end pose'}
clips = {}
for tag in (tag0,):
    g = Glb(V / f'pfem_a_{tag}.glb')
    for anim in g.doc['animations']:
        n = anim['name']; d = max(float(g.accessor(s['input']).max()) for s in anim['samplers'])
        if n in clips: continue
        clips[n] = {'label': n, 'duration': d, 'mode': 'loop' if n in ('Standing', 'Walking', 'Walk2', 'Running', 'Jog', 'Dead') else 'once',
                    'provenance': SRC.get(n, 'installed v3 only') if tag == 'rebuild' else 'installed v3', 'anchors': []}
models = []
for tag in (tag0,):
    for t, label in TIERS.items():
        f = V / f'{t}_{tag}.glb'; h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{t}_{tag}', 'label': f'{label} · {tag}', 'url': f'{f.name}?v={h[:12]}', 'sha256': h, 'revision': rev})
man = {'revision': rev, 'default_model': models[0]['id'], 'default_clip': 'Standing', 'models': models, 'clips': clips, 'issues': [],
       'feedback': 'feedback/user_feedback.json', 'model': models[0]['url'], 'model_sha256': models[0]['sha256']}
(V / 'manifest.json').write_text(json.dumps(man, indent=1) + '\n'); print('MANIFEST', len(models), list(clips))
