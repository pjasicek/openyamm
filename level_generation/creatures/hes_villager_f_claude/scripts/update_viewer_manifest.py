#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, the approved concept
and HD masters as the reference images (no native sprite), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
REF = ['../../references_hd/concept.png', '../../references_hd/01_front.png', '../../references_hd/04_right.png']
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle, thighs turned in 4 deg (narrow_stance.py); coat simulated (robe chains); loose fists (60 % source curl)'),
 'Walking': ('loop', 'Humanoid set Relax Walk Forward: feet flattened, walk bob evened; legs on the leg bones under the open coat'),
 'Hit': ('once', 'Mixamo Standing React Large From Front, planted, eased from/to Standing: arms flung out'),
 'Death': ('once', 'Humanoid set Unarmed Death 1, legs kept at 70 %: falls onto her back, coat laid flat'),
 'Dead': ('loop', 'Last Death pose held'),
 'Fidget': ('once', 'Mixamo Standing Idle 03 Examine, planted: looks at her hand'),
}
first = V / 'hes_vf_a.glb'
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'hes_villager_f_claude_v1', 'model': 'hes_vf_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'vf_a', 'models': [], 'clips': {}}
for vid, lab in (('vf_a', 'Outfit A: slate blue coat, off-white, red sash, dark brown hair'),
                 ('vf_b', 'Outfit B: grey-green coat, cream, ochre sash, black hair'),
                 ('vf_c', 'Outfit C: plum grey coat, pale grey, teal sash, auburn hair')):
    h = hashlib.sha256((V / f'hes_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'hes_villager_f_claude_v1', 'url': f'hes_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov) in clips.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': REF}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
