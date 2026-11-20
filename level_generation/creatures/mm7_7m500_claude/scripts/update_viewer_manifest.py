#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_7m500' / 'trimmed_2x'
REL = '../../../mm7_7m500/trimmed_2x'
clips = {
 'Standing': ('loop', 'Breathing, head turns, tail sway (native 7m500sa; the native fidget and hit are this frame)', ['7m500sa0', '7m500sa1', '7m500sa2']),
 'Walking': ('loop', 'Walk (lateral sequence) on IK footholds at the native 0.875 s cycle, ~0.6 m per cycle', [f'7m500w{c}2' for c in 'abcdefgh']),
 'Attack': ('once', 'Crouch, pounce-swipe (impact 0.5 s), recover; the native shows the walk', [f'7m500w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Flinch back, head recoil, tail up (no native frames)', ['7m500sa0']),
 'Death': ('once', 'Rears up twisting, falls onto its side (native 7m500da-de)', ['7m500da0', '7m500db0', '7m500dc0', '7m500dd0']),
 'Dead': ('loop', 'Last Death pose held (native corpse 7m500xa)', ['7m500xa0']),
 'Fidget': ('once', 'Head turns and nods, tail sway (no native frames)', ['7m500sa0']),
}
raw = (V / 'mm7_7m500_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_7m500_claude_v1', 'model': 'mm7_7m500_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': '7m500_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('7m500_a', 'All three descriptors (palette 545: zcat a / b / c)'),):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_7m500_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['7m500sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
