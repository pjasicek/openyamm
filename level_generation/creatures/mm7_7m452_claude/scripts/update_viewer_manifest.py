#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_7m452' / 'aligned_2x'
REL = '../../../mm7_7m452/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Unarmed Idle 01 (arms bowed out); the billhook carried level at the right hip, blade forward (authored carry, native walk 7m452w*); the native stands holding it with both hands', ['7m452sa0', '7m452sa1', '7m452sa2']),
 'Walking': ('loop', 'Mixamo Standard Walk, the billhook carried level (authored carry, 0.3 of the arm swing); left hand cleared of the thigh', [f'7m452w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 2: recoils back, arms out (native 7m452na..ne); blends 0.2 s; billhook cleared', [f'7m452n{c}0' for c in 'abcde']),
 'Death': ('once', 'Humanoid set Armed Death 1: staggers and falls onto the back, billhook kept at the side (review 2026-10-20: Mixamo Standing React Death Backward drove it through the left thigh)', ['7m452na0', '7m452nb0'] + [f'7m452d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m452xa0']),
 'Fidget': ('once', 'Mixamo Weight Shift with the billhook carry (the native raises the billhook upright in both hands - not reproduced)', [f'7m452f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_7m452_c2.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_7m452_claude_v1', 'model': 'mm7_7m452_c2.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': '7m452_c2', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
LOOKS = [('7m452_a1', '439 Peasant Goblin Male A/A (palette 453: brown tunic, olive trousers)'),
         ('7m452_a2', '440 A/B (454: white tunic, black trousers)'), ('7m452_a3', '441 A/C (455: ochre tunic, green trousers)'),
         ('7m452_b1', '442 B/A (393: black tunic, black trousers)'), ('7m452_b2', '443 B/B (493: white tunic, red trousers)'),
         ('7m452_b3', '444 B/C (494: purple tunic, black trousers)'), ('7m452_c1', '445 C/A (495: black tunic, brown trousers)'),
         ('7m452_c2', '446 C/B (497: red tunic, blue-grey trousers - the HD masters)'), ('7m452_c3', '447 C/C (498: olive tunic, olive trousers)')]
for vid, lab in LOOKS:
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_7m452_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['7m452sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
