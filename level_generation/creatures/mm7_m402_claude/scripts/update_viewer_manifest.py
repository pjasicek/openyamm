#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m402' / 'trimmed_2x'
REL = '../../../mm7_m402/trimmed_2x'
clips = {
 'Standing': ('loop', 'Abdomen breathing, small sway, fang twitch', ['m402sa0', 'm402sa1', 'm402sa2']),
 'Walking': ('loop', 'Alternating tetrapod gait on IK footholds, native 1.0 s cycle', [f'm402w{c}2' for c in 'abcdefgh']),
 'Running': ('loop', 'Same gait, 0.6 s cycle, longer stride', [f'm402w{c}2' for c in 'abcdefgh']),
 'Attack': ('once', 'Rears up with the front legs raised and fangs spread, lunges and bites (impact 0.55 s)', [f'm402a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Jolt back and down, legs splay', [f'm402n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Rears with the front legs flailing, collapses flat with the legs splayed', ['m402da0', 'm402db0', 'm402dc0', 'm402dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m402xa0']),
 'Fidget': ('once', 'Front legs tap, fangs work', [f'm402f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_m402_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m402_claude_v1', 'model': 'mm7_m402_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm402_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m402_a', 'Giant Spider - A (green)'), ('m402_b', 'Venomous Spider - B (blue)'), ('m402_c', 'Widowmaker - C (red)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m402_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m402sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
