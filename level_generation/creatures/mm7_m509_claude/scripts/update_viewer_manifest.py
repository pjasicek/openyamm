#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m509' / 'trimmed_2x'
REL = '../../../mm7_m509/trimmed_2x'
clips = {
 'Standing': ('loop', 'Breathing, head turns, tail sway (native m509sa; the native fidget and hit are this frame)', ['m509sa0', 'm509sa1', 'm509sa2']),
 'Walking': ('loop', 'Trot (diagonal pairs) on IK footholds at the native 0.875 s cycle, ~1.0 m per cycle', [f'm509w{c}2' for c in 'abcdefgh']),
 'Attack': ('once', 'Crouch, lunging snap (impact 0.5 s), recover; the native shows the walk', [f'm509w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Flinch back, head recoil, tail tucked (no native frames)', ['m509sa0']),
 'Death': ('once', 'Rears up with the forelegs off the ground, twists and falls onto its side (native m509da-dd)', ['m509da0', 'm509db0', 'm509dc0', 'm509dd0']),
 'Dead': ('loop', 'Last Death pose held (native corpse m509xa)', ['m509xa0']),
 'Fidget': ('once', 'Sniffing: head turns and nods, tail sway (no native frames)', ['m509sa0']),
}
raw = (V / 'mm7_m509_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m509_claude_v1', 'model': 'mm7_m509_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm509_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m509_a', 'All three descriptors (palette 545: zdog a / b / c)'),):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m509_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m509sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
