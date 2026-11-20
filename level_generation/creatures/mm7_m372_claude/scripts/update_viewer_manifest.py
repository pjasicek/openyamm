#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m372 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m372' / 'aligned_2x'
REL = '../../../mm7_m372/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle; loose hands (60 % of the source finger curl); skirt on simulated robe chains', ['m372sa0', 'm372sa1', 'm372sa2']),
 'Walking': ('loop', 'Humanoid set Relax Walk Forward (batch J m312 dress walk): legs and shoes under the robe, feet flattened, walk bob evened; also the run and the attack (native: walk frames)', [f'm372w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Mixamo Standing React Large From Front, planted, eased from/to Standing: arms flung out (native m372n)', [f'm372n{c}0' for c in 'abcdefg']),
 'Death': ('once', 'Humanoid set Unarmed Death 1, legs damped to 40 % under the robe: falls onto her back; skirt and bell sleeves simulated and laid on the floor (native m372d)', ['m372na0'] + [f'm372d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m372dd0']),
 'Fidget': ('once', 'Mixamo Standing Idle 03 Examine, planted: looks at her hand (native m372f)', [f'm372f{c}0' for c in 'abc']),
}
first = sorted(V.glob('mm7_m372_aa.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m372_claude_v1', 'model': 'mm7_m372_aa.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm372_aa', 'models': [], 'clips': {}}
for vid, lab in (('m372_aa', 'FemaleA A (palette 373): green gown, sage veil, auburn hair'), ('m372_ab', 'FemaleA B (palette 374): blue gown, blonde hair'), ('m372_ac', 'FemaleA C (palette 375): red gown, rose veil'), ('m372_ba', 'FemaleB A + FemaleC A (palette 376)'), ('m372_bb', 'FemaleB B + FemaleC B (palette 377)'), ('m372_bc', 'FemaleB C + FemaleC C (palette 378)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m372_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m372sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
