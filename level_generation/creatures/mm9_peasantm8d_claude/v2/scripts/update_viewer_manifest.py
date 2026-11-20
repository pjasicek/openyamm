#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, the approved concept
and HD masters as the reference images (there are no native frames), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
REL = '../../references_hd'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle, feet levelled; loose hands (60 % of the source finger curl)', ['01_front', '00_three_quarter']),
 'Walking': ('loop', 'Mixamo Standard Walk; upper arms out 6 deg, constant foot tilt, even pelvis bob', ['03_left', '04_right']),
 'Hit': ('once', 'Mixamo Standing React Large From Front, planted, eased from/to Standing: arms flung out, head back', ['01_front']),
 'Death': ('once', 'Mixamo Dying Backwards (travel halved): sinks to a sit, lies back', ['01_front']),
 'Dead': ('loop', 'Last Death pose held', ['01_front']),
 'Fidget': ('once', 'Mixamo Standing Idle 03 Examine, planted: looks at his raised hand', ['01_front']),
}
first = V / 'hes_vm_a.glb'
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'hes_villager_m_claude_v1', 'model': 'hes_vm_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'vm_a', 'models': [], 'clips': {}}
for vid, lab in (('vm_a', 'Outfit A: slate blue / off-white / red collar / dark-brown hair'),
                 ('vm_b', 'Outfit B: dark slate grey-green / cream / ochre collar / black hair'),
                 ('vm_c', 'Outfit C: warm grey / pale blue-grey / teal collar / auburn hair')):
    h = hashlib.sha256((V / f'hes_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'hes_villager_m_claude_v1', 'url': f'hes_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
