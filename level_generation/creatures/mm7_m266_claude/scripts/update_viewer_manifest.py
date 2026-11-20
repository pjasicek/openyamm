#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m266' / 'trimmed_2x'
REL = '../../../mm7_m266/trimmed_2x'
clips = {
 'Standing': ('loop', 'Breathing; the five necks sway on their own phases, heads look about', ['m266sa0', 'm266sa1', 'm266sa2']),
 'Walking': ('loop', 'Lateral-sequence walk on IK footholds, native 1.0 s cycle, stride 1.3 m; necks bob in turn', [f'm266w{c}2' for c in 'abcdefgh']),
 'Running': ('loop', 'Trot, 0.6 s cycle, stride 1.9 m, necks stretched forward', [f'm266w{c}2' for c in 'abcdefgh']),
 'Attack': ('once', 'Necks rear back and up, the middle three lash forward and down (bend travels base to head), impact 0.62 s', [f'm266a{c}2' for c in 'abcdefgh']),
 'Hit': ('once', 'Necks recoil, body flinches, heads shake', [f'm266n{c}2' for c in 'abcdef']),
 'Death': ('once', 'Rears, collapses onto its belly with legs sprawled, necks fall forward in a fan', ['m266fa0', 'm266fb0', 'm266da0', 'm266db0', 'm266dc0', 'm266dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m266xa0']),
 'Fidget': ('once', 'Heads look round on their own beats, outer heads outward', ['m266fa0', 'm266fb0', 'm266fc0', 'm266fd0']),
}
raw = (V / 'mm7_m266_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m266_claude_v1', 'model': 'mm7_m266_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm266_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m266_a', 'Fire Hydra - A (olive)'), ('m266_b', 'Air Hydra - B (blue-grey)'), ('m266_c', 'Chaos Hydra - C (red)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m266_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m266sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
