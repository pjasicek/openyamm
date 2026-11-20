#!/usr/bin/env python3
"""review/viewer/manifest.json for a texture pass: every review/viewer/<variant>_<tag>.glb of the given tags, in tag
order per tier; clips (name, duration) from the before GLB; camera focuses from the LOD0 bind pose (body, head from the
head faces, arms/hands, feet). Usage: tp_viewer_manifest.py <default model id> <tag>[=label] ..."""
import hashlib
import json
import sys

import numpy as np

import tp_common as C

cfg = C.config()
V = C.PROJECT / 'review/viewer'
default = sys.argv[1]
tags = [a.split('=', 1) if '=' in a else (a, a) for a in sys.argv[2:]]
g = C.Glb(C.before_glb(cfg))
doc = g.doc
variants = []
for path in [C.before_glb(cfg)] + sorted(set((C.PROJECT / 'work' / 'before_texpass').glob('*.glb')) - {C.before_glb(cfg)}):
    other = C.Glb(path).doc
    variants += [v['name'] for v in other.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])
                 if v['name'] not in variants]
variants = variants or ['base']
models = []
for tier in variants:
    for tag, label in tags:
        f = V / f'{tier}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{tier}_{tag}', 'label': f'{tier} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': 'texpass-20261111'})
ONCE = ('Attack', 'Hit', 'Death', 'Cast', 'Shoot', 'Dead')
clips = {}
for anim in doc.get('animations', []):
    duration = max(float(g.accessor(s['input']).max()) for s in anim['samplers'])
    clips[anim['name']] = {'label': anim['name'], 'duration': duration,
                           'mode': 'once' if anim['name'].startswith(ONCE) else 'loop', 'anchors': []}
d = np.load(C.lod0_path())
pos = d['pos']
lo, hi = pos.min(0), pos.max(0)
size = float((hi - lo).max())
centre = (lo + hi) / 2
hv = np.unique(d['tri'][d['head_face']])
head = pos[hv].mean(0) if len(hv) else np.array([centre[0], hi[1] - 0.1 * size, centre[2]])
hand = d['g_Hands'] > 0.5 if 'g_Hands' in d.files else None
hands = pos[hand].mean(0) if hand is not None and hand.any() else centre
focuses = {'body': [float(centre[0]), float(centre[1]), float(centre[2]), 2.2 * size],
           'head': [float(head[0]), float(head[1]), float(head[2]), 0.45 * size],
           'arms': [float(hands[0]), float(hands[1]), float(hands[2]), 0.9 * size],
           'shoulders': [float(centre[0]), float(lo[1] + 0.8 * (hi[1] - lo[1])), float(centre[2]), 1.0 * size],
           'skirt': [float(centre[0]), float(lo[1] + 0.45 * (hi[1] - lo[1])), float(centre[2]), 1.0 * size],
           'feet': [float(centre[0]), float(lo[1] + 0.1 * (hi[1] - lo[1])), float(centre[2]), 0.8 * size]}
pick = next(m for m in models if m['id'] == default)
manifest = {'revision': 'texpass-20261111', 'creature': f"{cfg['world']}:{cfg['stem']}", 'default_model': default,
            'default_clip': 'Standing' if 'Standing' in clips else next(iter(clips)), 'models': models,
            'clips': clips, 'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'],
            'model_sha256': pick['sha256'], 'focuses': focuses}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('MANIFEST', len(models), 'models', 'focuses', json.dumps(focuses))
