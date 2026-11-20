#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[1] / 'references_native'
REL = '../../references_native'
clips = {
 'Standing': ('loop', 'Mixamo Zombie Idle; the severed forearm carried level and forward at the hip (authored carry, native m438sa)', ['m438sa0', 'm438sa1', 'm438sa2']),
 'Walking': ('loop', 'Mixamo Walking (5), a staggering shamble (1.2 m/s); the carry arm held from the idle with a 14 deg swing; per-frame floor pass', [f'm438w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run fitted + authored carry (spare: the tier speeds stay under the run threshold)', [f'm438w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash (2) MIRRORED to the left hand: the forearm raised overhead and chopped down and across (native m438aa..ag); planted + 20 % legs, 0.3 s ready pause, blow 0.95 s', [f'm438a{c}0' for c in 'abcdefg']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1; blends 0.2 s', [f'm438n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward: falls onto the back (native m438da..dd); travel halved, floor pass', [f'm438d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m438xa0']),
 'Fidget': ('once', 'Mixamo Zombie Scream (planted): a sideways lurch with the arms out (native m438fa..fe)', [f'm438f{c}0' for c in 'abcde']),
}
raw = (V / 'mm7_m438_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m438_claude_v1', 'model': 'mm7_m438_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm438_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m438_a', 'Rotted Corpse - A (olive trousers, palette 118)'), ('m438_b', 'Walking Dead - B (pale grey, 119)'), ('m438_c', 'Zombie - C (black, 123)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m438_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m438sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
