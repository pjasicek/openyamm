#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m218' / 'aligned_2x'
REL = '../../../mm7_m218/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; authored left-hand spear carry (tip forward-down, native m218sa)', ['m218sa0', 'm218sa1', 'm218sa2']),
 'Walking': ('loop', 'Mixamo Walk (1.86 m stride) + carry; floor pass', [f'm218w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run fitted (1.8 m stride) + carry held out', [f'm218w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Humanoid set 2Hand-Spear Attack9: both fists on the shaft, raised to the shoulder, horizontal two-handed thrust (native m218ab..ag); stance narrowed, wind-up retimed (blow 0.86 s, native action 0.875 s)', [f'm218a{c}0' for c in 'abcdefg']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1 + carry; blends 0.12/0.20 s', [f'm218n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved): falls onto the back; the spear drops free and lies beside the body (native m218da..dd)', ['m218na0', 'm218nb0'] + [f'm218d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m218xa0']),
 'Fidget': ('once', 'Authored over Standing: the spear lifted upright beside the body and lowered (native m218fa..fd)', [f'm218f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_m218_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m218_claude_v1', 'model': 'mm7_m218_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm218_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m218_a', 'Elven Warrior - A (green)'), ('m218_b', 'Elven Defender - B (blue-violet)'), ('m218_c', 'Elven Lancer - C (red)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m218_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m218sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
