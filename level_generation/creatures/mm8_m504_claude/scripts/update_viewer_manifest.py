#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m198' / 'aligned_2x'
REL = '../../../mm7_m198/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle, arms turned out 14 deg (native m198sa holds the fists out)', ['m198sa0', 'm198sa1', 'm198sa2']),
 'Walking': ('loop', 'Mixamo Orc Walk (heavy stomp), arms out 10 deg, floor pass for the boulder feet', [f'm198w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Zombie Attack (two-handed overhead) planted (20 % legs) at 1.4x, arms out and forward over the raise, fists kept apart and clear of the head; blow 0.583 s; also the cast (shoot = attack natively)', [f'm198a{c}0' for c in 'abcdefg']),
 'Hit': ('once', 'Unarmed get-hit front 1 (humanoid set), arms out 6 deg', [f'm198n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Backward react (Mixamo) until 0.4 s, then the body breaks into 14 rigid stone pieces that fall apart (native m198d)', [f'm198d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Rubble pieces at rest (native corpse m198xa)', ['m198xa0']),
 'Fidget': ('once', 'Mixamo Mutant Flexing Muscles planted, arms out 10 deg (native m198f flexes the arms)', [f'm198f{c}0' for c in 'abcde']),
}
raw = (V / 'mm8_m504_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm8_m504_claude_v1', 'model': 'mm8_m504_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm504_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m504_a', 'A - palette 504 brown (MM8 Lesser; all MM7 tiers)'), ('m504_b', 'B - MM8 palette 506 blue-slate'), ('m504_c', 'C - MM8 palette 507 red')):
    h = _h.sha256((V / f'mm8_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm8_m504_claude_v1', 'url': f'mm8_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m198sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
