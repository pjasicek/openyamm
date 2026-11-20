#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[1] / 'source' / 'aligned_2x'
REL = '../../source/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; authored spear carry (low, level, tip forward, native natmsta)', ['natmsta0', 'natmsta1', 'natmsta2']),
 'Walking': ('loop', 'Mixamo Walk (1.69 m stride); authored spear carry', [f'natmwa{c}0' for c in 'abcdef']),
 'Running': ('loop', 'Mixamo Standard Run, high pelvis fit, 1.5 m stride; spear carry tip raised', [f'natmwa{c}0' for c in 'abcdef']),
 'Attack': ('once', 'Underhand lunge thrust authored over mocap (Mixamo Stabbing 2 trunk/shield arm): draw-back with shield up, step and drive, spear aimed at chest height; blow at contact', [f'natmat{c}0' for c in 'abcdef']),
 'Cast': ('once', 'Ready ease + left-palm cast (humanoid set), spear held upright; Fire Bolt release from the left palm', [f'natmat{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Unarmed get-hit front 1 + spear carry', [f'natmwi{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved): falls onto the back like natmde', [f'natmde{c}0' for c in 'abcdef']),
 'Dead': ('loop', 'Last Death pose held', ['natmdef0']),
 'Fidget': ('once', 'Mixamo Sword And Shield Power Up (planted): spear raised overhead, chest out', [f'natmfi{c}0' for c in 'abcdef']),
}
raw = (V / 'mm6_natm_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm6_natm_claude_v1', 'model': 'mm6_natm_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'natm_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('natm_a', 'Cannibal - A (grey)'), ('natm_b', 'Head Hunter - B (olive)'), ('natm_c', 'Witch Doctor - C (red)')):
    h = _h.sha256((V / f'mm6_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm6_natm_claude_v1', 'url': f'mm6_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['natmsta0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
