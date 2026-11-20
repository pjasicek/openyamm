#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m332' / 'aligned_2x'
REL = '../../../mm7_m332/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Unarmed Idle 01: arms bowed out, wide stance (native m332sa)', ['m332sa0', 'm332sa1', 'm332sa2']),
 'Walking': ('loop', 'Mixamo Standard Walk; floor pass (native walk; attack/shoot alias it)', [f'm332w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed Get Hit F2, planted: recoils back with the arms flung out (native m332na..ne)', [f'm332n{c}0' for c in 'abcde']),
 'Death': ('once', 'Mixamo Standing React Death Backward: steps back and falls onto the back, spread (native m332da..dd)', ['m332na0', 'm332nb0'] + [f'm332d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m332xa0']),
 'Fidget': ('once', 'Mixamo Weight Shift (the native fidget barely moves)', [f'm332f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_m332_a3.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m332_claude_v1', 'model': 'mm7_m332_a3.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm332_a3', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
LOOKS = [('m332_a1', '340 Peasant Elf MaleA A (palette 333: green tights, black hair)'),
         ('m332_a2', '341 A/B (334: blue tights, ginger hair)'), ('m332_a3', '342 A/C (59: burgundy tights, blonde - the HD masters)'),
         ('m332_b1', '343 B/A (60: brown tights, grey hair)'), ('m332_b2', '344 B/B (61: grey tights, brown hair)'),
         ('m332_b3', '345 B/C (62: mustard tights, white hair)'), ('m332_c1', '346 C/A (339: charcoal tights, blonde)'),
         ('m332_c2', '347 C/B (340: cream tights, light brown hair)'), ('m332_c3', '348 C/C (341: white tights, dark grey hair)')]
for vid, lab in LOOKS:
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m332_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m332sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
