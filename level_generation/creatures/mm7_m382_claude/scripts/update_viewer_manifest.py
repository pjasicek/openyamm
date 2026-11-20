#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m382' / 'trimmed_2x'
REL = '../../../mm7_m382/trimmed_2x'
clips = {
 'Standing': ('loop', 'Breathing, sniffing head, tail sway on the floor', ['m382sa0', 'm382sa1', 'm382sa2']),
 'Walking': ('loop', 'Trot on IK footholds (diagonal pairs), native 1.0 s cycle', [f'm382w{c}2' for c in 'abcdefgh']),
 'Running': ('loop', 'Faster trot, 0.6 s cycle', [f'm382w{c}2' for c in 'abcdefgh']),
 'Attack': ('once', 'Crouch, lunging bite (impact 0.5 s), rears up clawing with both forepaws', [f'm382a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Flinch back, head recoil, tail whips up', [f'm382n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Rears with the forepaws up, twists and falls onto its side', ['m382da0', 'm382db0', 'm382dc0', 'm382dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m382xa0']),
 'Fidget': ('once', 'Sniffing: quick head turns and nods, tail sway', [f'm382f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_m382_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m382_claude_v1', 'model': 'mm7_m382_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm382_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m382_a', 'Giant Rat - A (mint)'), ('m382_b', 'Lightning Rat - B (pale blue)'), ('m382_c', 'Fire Rat - C (pink)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m382_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m382sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
