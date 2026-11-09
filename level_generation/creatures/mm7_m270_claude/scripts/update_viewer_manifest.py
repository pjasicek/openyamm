#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m270' / 'aligned_2x'
REL = '../../../mm7_m270/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; staff carried upright in the left hand (authored carry)', ['m270sa0', 'm270sa1', 'm270sa2']),
 'Walking': ('loop', 'Mixamo Walk under the chain skirt (pelvis -> 85 % legs at the hem); staff carry', [f'm270w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run fit + carry (never reached at the tiers speeds)', [f'm270w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Spell: Mixamo 1H magic attack body (free hand casts forward, 1.75x) + authored staff: tipped at the target, raised beside the head for the release at 0.78 s', [f'm270a{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Unarmed get-hit front 1 + staff carry', [f'm270n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved); skirt bones fold the hem around the legs', ['m270na0', 'm270nb0', 'm270da0', 'm270db0', 'm270dc0', 'm270dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m270xa0']),
 'Fidget': ('once', 'Mixamo Annoyed Head Shake planted + staff carry', ['m270fa0', 'm270fb0', 'm270fc0', 'm270fd0']),
}
raw = (V / 'mm7_m270_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m270_claude_v1', 'model': 'mm7_m270_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm270_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m270_a', 'Lich - A (palette 271, blue-violet chain)'), ('m270_b', 'Power Lich - B (272, silver)'), ('m270_c', 'Lich King - C (273, rose-gold)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m270_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m270sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
