#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm6_goblin' / 'stage1_20261006' / 'source' / 'frames'
REL = '../../../mm6_goblin/stage1_20261006/source/frames'
clips = {
 'Standing': ('loop', 'Armed idle (humanoid set), world-rotation copy; solved scimitar fist', ['gobsta0', 'gobsta1', 'gobsta2']),
 'Walking': ('loop', 'Armed walk, arms abducted 7 deg (goblin proportions)', [f'gobwa{c}0' for c in 'abcdef']),
 'Running': ('loop', 'Armed run forward, arms abducted 7 deg', [f'gobwa{c}0' for c in 'abcdef']),
 'Attack': ('once', 'Ready pause 0.4 s + one-handed sword attack R6 (raise over the shoulder, wide diagonal slash); blow at 0.683 s', [f'gobat{c}0' for c in 'abcdef']),
 'Cast': ('once', 'Ready pause 0.4 s + left-hand cast attack 1 with an authored open hand (straight wrist, open fingers); release at 0.650 s', [f'gobat{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Armed get-hit front 1', [f'gobwi{c}0' for c in 'abcdef']),
 'Death': ('once', 'Armed death 1 (falls forward)', [f'gobdy{c}0' for c in 'abcde']),
 'Dead': ('loop', 'Last Death pose held', ['gobdye0']),
 'Fidget': ('once', 'Authored from native gobfi: chest/shoulder rise and release', [f'gobfi{c}0' for c in 'abcdef']),
}
raw = (V / 'mm6_gob2_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm6_gob2_claude_v1', 'model': 'mm6_gob2_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'gob2_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('gob2_a', 'Goblin - A (olive)'), ('gob2_b', 'Goblin Shaman - B (blue)'), ('gob2_c', 'Goblin King - C (red)')):
    h = _h.sha256((V / f'mm6_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm6_gob2_claude_v1', 'url': f'mm6_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['gobsta0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
