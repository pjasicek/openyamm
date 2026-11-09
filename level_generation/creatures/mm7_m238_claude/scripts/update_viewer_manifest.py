#!/usr/bin/env python3
"""Review viewer manifest from the tier GLBs (viewer_tiers.py): clip durations read from the GLB, native reference
frames per clip (the validated m238 restorations), cache-busting hash on the model URLs."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m238' / 'aligned_2x'
REL = '../../../mm7_m238/aligned_2x'
CL = json.load(open(Path(__file__).resolve().parents[1] / 'work' / 'clips.json'))
clips = {
 'Standing': ('loop', 'Humanoid set Unarmed Idle upper body, arms folded by IK, hover and vortex sway', [f'm238w{c}0' for c in 'abcdeg']),
 'Walking': ('loop', 'Standing + forward lean, the vortex trailing (the native walk is the same folded float)', [f'm238w{c}0' for c in 'abcdeg']),
 'Attack': ('once', f"Humanoid set Unarmed Cast Dual Summon 1, hover kept, a hold with the hands overhead; release at {CL['impact']:.3f} s (attack, ranged and cast)", [f'm238a{c}0' for c in 'abcdefg']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit B1, hover kept, eased from/to Standing', [f'm238n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Authored: arms up, rise, spin, the body shrinks away into the vortex; the lamp appears and drops', ['m238na0'] + [f'm238d{c}0' for c in 'abcdef']),
 'Dead': ('loop', 'The lamp alone on the floor (body hidden)', ['m238xa0']),
 'Fidget': ('once', 'Authored over Standing: head turns and a shrug, arms folded', [f'm238f{c}0' for c in 'abcde']),
}
first = sorted(V.glob('mm7_m238_a.glb'))[0]
raw = first.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m = {'revision': 'mm7_m238_claude_v1', 'model': 'mm7_m238_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm238_a', 'models': [], 'clips': {}}
for vid, lab in (('m238_a', 'Djinni - A (green)'), ('m238_b', 'Genie - B (violet)'), ('m238_c', 'Efreet - C (red)')):
    h = hashlib.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m238_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m238wa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
