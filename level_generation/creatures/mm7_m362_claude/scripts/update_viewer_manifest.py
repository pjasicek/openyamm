#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m362 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m362' / 'aligned_2x'
REL = '../../../mm7_m362/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle, feet levelled; loose fists (60 % of the source finger curl); rapier rigid on the pelvis', ['m362sa0', 'm362sa1', 'm362sa2']),
 'Walking': ('loop', 'Mixamo Standard Walk; feet levelled (constant tilt), floor lift; also the run and the attack (native: walk frames)', [f'm362w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Mixamo Standing React Large From Front, planted, eased from/to Standing: one arm flung up, head back (native m362n)', [f'm362n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Falling Back Death (travel halved): falls backward, legs up (native m362d)', ['m362na0', 'm362nb0'] + [f'm362d{c}0' for c in 'abc']),
 'Dead': ('loop', 'Last Death pose held', ['m362dc0']),
 'Fidget': ('once', 'Mixamo Standing Idle 03 Examine, planted: looks at his hand (native m362f: hands at the belt)', [f'm362f{c}0' for c in 'abcd']),
}
first = sorted(V.glob('mm7_m362_aa.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m362_claude_v1', 'model': 'mm7_m362_aa.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm362_aa', 'models': [], 'clips': {}}
for vid, lab in (('m362_aa', 'MaleOutfit A tier A (palette 363)'), ('m362_ab', 'MaleOutfit A tier B (palette 364)'), ('m362_ac', 'MaleOutfit A tier C (palette 365)'), ('m362_ba', 'MaleOutfit B tier A (palette 366)'), ('m362_bb', 'MaleOutfit B tier B (palette 367)'), ('m362_bc', 'MaleOutfit B tier C (palette 368)'), ('m362_ca', 'MaleOutfit C tier A (palette 369)'), ('m362_cb', 'MaleOutfit C tier B (palette 370)'), ('m362_cc', 'MaleOutfit C tier C (palette 371)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m362_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m362sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
