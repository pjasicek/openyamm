#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m302' / 'aligned_2x'
REL = '../../../mm7_m302/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Dwarf Idle (3): wide burly stance; the club hangs diagonally down to the knee from a cocked wrist (native m302sa)', ['m302sa0', 'm302sa1', 'm302sa2']),
 'Walking': ('loop', 'Mixamo Dwarf Walk (short heavy steps), club swinging with the arm; floor pass (native walk; attack/shoot alias it)', [f'm302w{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1: thrown back, arms out (native m302na..ne); blends 0.2 s', [f'm302n{c}0' for c in 'abcde']),
 'Death': ('once', 'Mixamo Standing React Death Backward: steps back and falls onto the back (native m302da..dd); the club kept in hand, cleared of the floor', ['m302na0', 'm302nb0'] + [f'm302d{c}0' for c in 'abcd']),
 'Dead': ('loop', 'Last Death pose held', ['m302xa0']),
 'Fidget': ('once', 'Mixamo Dwarf Idle (2): the left hand rises and strokes the beard (native m302fa..fd)', [f'm302f{c}0' for c in 'abcd']),
}
raw = (V / 'mm7_m302_b1.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m302_claude_v1', 'model': 'mm7_m302_b1.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm302_b1', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
LOOKS = [('m302_a1', '322 Peasant Dwarf Male A/A (palette 303: purple, black beard)'),
         ('m302_a2', '323 A/B (304: blue, yellow beard)'), ('m302_a3', '324 A/C (305: pale blue, ginger beard)'),
         ('m302_b1', '325 B/A (58: green, brown beard - the HD masters)'), ('m302_b2', '326 B/B (307: wine, white beard)'),
         ('m302_b3', '327 B/C (308: brown, grey beard)'), ('m302_c1', '328 C/A (309: cream, black beard)'),
         ('m302_c2', '329 C/B (310: white, tan beard)'), ('m302_c3', '330 C/C (311: charcoal, yellow beard)')]
for vid, lab in LOOKS:
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m302_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m302sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
