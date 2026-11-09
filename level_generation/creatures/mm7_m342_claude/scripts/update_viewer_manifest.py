#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m342 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m342' / 'aligned_2x'
REL = '../../../mm7_m342/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; skirt simulated (robe chains); loose fists (60 % source curl)', ['m342sa0', 'm342sa1', 'm342sa2']),
 'Walking': ('loop', 'Humanoid set Relax Walk Forward (batch J m312 dress walk): legs and shoes under the skirt, feet flattened, walk bob evened; also the run and the attack (native: walk frames)', [f'm342w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Mixamo Standing React Large From Front, planted, eased from/to Standing: arms flung out (native m342n)', [f'm342n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Humanoid set Unarmed Death 1, legs damped to 40 % under the skirt: falls onto her back, skirt laid flat (native m342d)', ['m342na0', 'm342nb0'] + [f'm342d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m342dd0']),
 'Fidget': ('once', 'Mixamo Standing Idle 03 Examine, planted: looks at her hand (native m342f)', [f'm342f{c}0' for c in 'abcd']),
}
first = sorted(V.glob('mm7_m342_aa.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m342_claude_v1', 'model': 'mm7_m342_aa.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm342_aa', 'models': [], 'clips': {}}
for vid, lab in (('m342_aa', 'FemaleOutfit A tier A (palette 343)'), ('m342_ab', 'FemaleOutfit A tier B (palette 344)'), ('m342_ac', 'FemaleOutfit A tier C (palette 345)'), ('m342_ba', 'FemaleOutfit B tier A (palette 346)'), ('m342_bb', 'FemaleOutfit B tier B (palette 347)'), ('m342_bc', 'FemaleOutfit B tier C (palette 348)'), ('m342_ca', 'FemaleOutfit C tier A (palette 349)'), ('m342_cb', 'FemaleOutfit C tier B (palette 350)'), ('m342_cc', 'FemaleOutfit C tier C (palette 351)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m342_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m342sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
