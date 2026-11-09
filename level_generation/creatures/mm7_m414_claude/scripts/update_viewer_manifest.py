#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m414' / 'aligned_2x'
REL = '../../../mm7_m414/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle + authored carry: the sword in front of the right hip, blade forward-up across the thighs (native m414sa)', ['m414sa0', 'm414sa1', 'm414sa2']),
 'Walking': ('loop', 'Mixamo Walk; floor pass', [f'm414w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run fitted + authored carry: the sword held up and forward at the side; loop seam blended', [f'm414w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Sword And Shield Slash (2): overhead raise and diagonal downward slash (native m414aa..af); planted + 20 % legs, 0.1 s ready pause, blow 0.783 s (native action 0.75 s)', [f'm414a{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1; blends 0.2 s; sword cleared', [f'm414n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved): falls onto the back (native m414da..db; the native crumbles to rubble, not modelled)', ['m414na0', 'm414nb0'] + [f'm414d{c}0' for c in 'abcde']),
 'Dead': ('loop', 'Last Death pose held (native corpse: a rubble pile)', ['m414xa0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted): the sword swept up, chest out (native m414fa..fe)', [f'm414f{c}0' for c in 'abcde']),
}
raw = (V / 'mm7_m414_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m414_claude_v1', 'model': 'mm7_m414_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm414_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m414_a', 'Titan - A (blue, white crest)'), ('m414_b', 'Storm Titan - B (olive, orange crest)'), ('m414_c', 'Blood Titan - C (red, pink crest)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m414_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m414sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
