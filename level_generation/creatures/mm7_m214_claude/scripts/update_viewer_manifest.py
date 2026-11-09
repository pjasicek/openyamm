#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m214' / 'aligned_2x'
REL = '../../../mm7_m214/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo longbow-pack unarmed idle 01; authored left-hand bow carry (grip at the hip, bow forward-down along the side, native m214sa)', ['m214sa0', 'm214sa1', 'm214sa2']),
 'Walking': ('loop', 'Mixamo Female Walk; bow carry; floor pass', [f'm214w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run, high pelvis fit, 1.8 m stride; bow carry held forward and out', [f'm214w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Standing Draw Arrow + Standing Aim Recoil: reach over the right shoulder into the quiver, nock, raise and draw to the face, release (1.10 s), lower; stance narrowed to 40 % and raised; string follows the drawing hand, arrow hidden at release', [f'm214a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1 + bow carry; blends 0.12/0.20 s', [f'm214n{c}0' for c in 'abcde']),
 'Death': ('once', 'Mixamo longbow-pack standing death backward 01 (travel halved): falls onto the back like m214da..dd', ['m214na0', 'm214nb0'] + [f'm214d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m214xa0']),
 'Fidget': ('once', 'Authored over Standing: the bow raised across the front, upper tip toward the chest, lower tip down and out, then lowered (native m214fa..fe)', [f'm214f{c}0' for c in 'abcde']),
}
raw = (V / 'mm7_m214_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m214_claude_v1', 'model': 'mm7_m214_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm214_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m214_a', 'Elven Archer - A (olive, blond)'), ('m214_b', 'Elven Scout - B (green, silver)'), ('m214_c', 'Elven Ranger - C (red, brown)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m214_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m214sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
