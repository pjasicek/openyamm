#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m394' / 'trimmed_2x'
REL = '../../../mm7_m394/trimmed_2x'
clips = {
 'Standing': ('loop', 'Hovering in place: slow tail beat and sway, jaw breathing (native m395f, also the fidget)', ['m394sa0', 'm394sa1', 'm394sa2'] + [f'm394f{c}0' for c in 'abcdefg']),
 'Walking': ('loop', 'Swimming: lateral travelling wave, 1.25 s cycle (native m394w)', [f'm394w{c}2' for c in 'abcdefghij']),
 'Attack': ('once', 'Rears nose-up with the jaws wide, lunges and snaps shut (impact 0.6 s), dives and levels out (native m394a)', [f'm394a{c}0' for c in 'abcdefghij']),
 'Hit': ('once', 'Twists onto its side and curls, recovers (native m394n)', [f'm394n{c}0' for c in 'abcdefgh']),
 'Death': ('once', 'Rolls belly-up with the jaws agape, curls, sinks to the floor and settles on its back and flank', ['m394na0', 'm394nb0', 'm394da0', 'm394db0', 'm394dc0', 'm394dd0', 'm394de0']),
 'Dead': ('loop', 'Last Death pose held (native corpse m394xa)', ['m394xa0']),
}
raw = (V / 'mm7_m394_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m394_claude_v1', 'model': 'mm7_m394_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm394_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m394_a', 'Giant Shark - A (palette 395, teal-blue)'), ('m394_b', 'Piranha Shark - B (396, lavender)'), ('m394_c', 'Dragon Shark - C (397, red)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m394_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m394sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
