#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m442 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m442' / 'native'      # m442: only the standing frames were restored
REL = '../../../mm7_m442/native'
clips = {
 'Standing': ('loop', 'Mixamo Standard Idle, arms abducted 8 deg (wide sleeves clear the thighs); sickle in the right fist', ['m442sa0', 'm442sa1', 'm442sa2']),
 'Walking': ('loop', 'Mixamo Female Walk, arms abducted 8 deg; also the attack (native: walk frames)', [f'm442w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Mixamo Standing React Large From Front, planted, eased from/to Standing (native m442n: staggers, sickle raised)', [f'm442n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Mixamo Falling Back Death (travel halved): falls backward, legs up (native m442d; the native throws the sickle, ours keeps it)', ['m442na0', 'm442nb0'] + [f'm442d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m442xa0']),
 'Fidget': ('once', 'Mixamo Look Around, planted, arms abducted 14 deg: turns and looks round (native m442f)', [f'm442f{c}0' for c in 'abcd']),
}
first = sorted(V.glob('mm7_m442_aa.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m442_claude_v1', 'model': 'mm7_m442_aa.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm442_aa', 'models': [], 'clips': {}}
for vid, lab in (('m442_aa', 'Goblin female A A (palette 139)'), ('m442_ab', 'Goblin female A B (palette 141)'), ('m442_ac', 'Goblin female A C (palette 145)'), ('m442_ba', 'Goblin female B A (palette 146)'), ('m442_bb', 'Goblin female B B (palette 147)'), ('m442_bc', 'Goblin female B C (palette 148)'), ('m442_ca', 'Goblin female C A (palette 149)'), ('m442_cb', 'Goblin female C B (palette 390)'), ('m442_cc', 'Goblin female C C (palette 391)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m442_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m442sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
