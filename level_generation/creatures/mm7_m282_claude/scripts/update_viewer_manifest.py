#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m282' / 'trimmed_2x'
REL = '../../../mm7_m282/trimmed_2x'
clips = {
 'Standing': ('loop', 'Native idle (bow upright in the left fist, right hand on the belly): breathing, column sway, writhing hair snakes', ['m282sa0', 'm282sa1', 'm282sa2']),
 'Walking': ('loop', 'Serpentine travelling wave down the floor tail, native 0.875 s cycle, stride 1.6 m', [f'm282w{c}2' for c in 'abcdefg']),
 'Running': ('loop', 'Faster, deeper wave with a forward lean, 0.7 s cycle, stride 2.1 m (B/C move above the run threshold)', [f'm282w{c}2' for c in 'abcdefg']),
 'Attack': ('once', 'Reach over the right shoulder to the quiver, raise the bow, nock, draw to the cheek, hold, release at 1.0 s', [f'm282a{c}1' for c in 'abcdefgh']),
 'Hit': ('once', 'Recoil back and aside, head thrown back, arms flinch', [f'm282n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Recoils, twists and topples to her left; the bow slips from the fist', ['m282da0', 'm282db0', 'm282dc0', 'm282dd0', 'm282de0']),
 'Dead': ('loop', 'Last Death pose held', ['m282xa0']),
 'Fidget': ('once', 'Looks left and right, lifts the bow to check it', ['m282fa0', 'm282fb0', 'm282fc0', 'm282fd0']),
}
raw = (V / 'mm7_m282_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m282_claude_v1', 'model': 'mm7_m282_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm282_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m282_a', 'Medusa - A (charcoal mail)'), ('m282_b', 'Queen Medusa - B (silver mail)'), ('m282_c', 'Empress Medusa - C (gold mail)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m282_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m282sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
