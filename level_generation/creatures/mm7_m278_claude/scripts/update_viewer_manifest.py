#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m278' / 'trimmed_2x'
REL = '../../../mm7_m278/trimmed_2x'
clips = {
 'Standing': ('loop', 'Breathing, head and tail sway', ['m278sa0', 'm278sa1', 'm278sa2']),
 'Walking': ('loop', 'Lion walk on IK footholds (lateral sequence), native 1.0 s cycle, stride 1.6 m', [f'm278w{c}2' for c in 'abcdefgh']),
 'Running': ('loop', 'Bounding trot, 0.6 s cycle, stride 2.2 m', [f'm278w{c}2' for c in 'abcdefgh']),
 'Attack': ('once', 'Rears up with both forepaws raised, drops forward while the scorpion tail lashes over the head (impact 0.62 s)', [f'm278a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Flinch back, head recoil, tail jerks', [f'm278n{c}0' for c in 'abcde']),
 'Death': ('once', 'Rears, twists and falls onto its side', ['m278da0', 'm278db0', 'm278dc0', 'm278dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m278xa0']),
 'Fidget': ('once', 'Roar: head up, mane shake, tail sway', [f'm278f{c}0' for c in 'abcde']),
}
raw = (V / 'mm7_m278_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m278_claude_v1', 'model': 'mm7_m278_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm278_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m278_a', 'Minicore - A (sage mane)'), ('m278_b', 'Manticore - B (black mane)'), ('m278_c', 'Scorpicore - C (crimson mane)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m278_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m278sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
