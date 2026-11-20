#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm6_nobl' / 'native'
clips = {
 'Standing': ('loop', 'Relaxed native stance; solved sword grip', ['noblsta0', 'noblsta1', 'noblsta2']),
 'Walking': ('loop', 'Armed walk', [f'noblwa{c}0' for c in 'abcdef']),
 'Running': ('loop', 'Selected Run B: upright jog, fitted ground contact and cloak', [f'noblwa{c}0' for c in 'abcdef']),
 'Attack': ('once', 'One-handed sword attack R1: raise behind the right shoulder, overhead, diagonal cut, recovery', [f'noblat{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Selected Hit A: short standing recoil', [f'noblwi{c}0' for c in 'bcdef']),
 'Death': ('once', 'Shield death 1: knees forward, prone; cloth settling', [f'noblde{c}0' for c in 'abcdef']),
 'Dead': ('loop', 'Last Death pose held', ['nobldef0']),
 'Fidget': ('once', 'Subtle native idle / blink', [f'noblfi{c}0' for c in 'bcdef']),
}
raw = (V / 'mm6_nobl_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm6_nobl_codex_feedback_v6', 'model': 'mm6_nobl_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'nobl_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('nobl_a', 'Swordsman — olive / burgundy'), ('nobl_b', 'Expert Swordsman — blue / violet'), ('nobl_c', 'Master Swordsman — magenta / brown')):
    h = _h.sha256((V / f'mm6_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm6_nobl_codex_feedback_v6', 'url': f'mm6_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['noblsta0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'../../../mm6_nobl/native/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
