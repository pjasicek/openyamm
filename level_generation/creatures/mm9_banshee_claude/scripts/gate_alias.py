#!/usr/bin/env python3
"""A copy of a GLB with the Banshee's arm joints under Bip01 names, for the shared arm and jitter gates (they find joints by side token and name). Finger chains: 04-07 are the +x (R) hand, none-03 the -x (L) hand.
--no-head drops the head and hair primitives. --reverse restores the MM9 names. Usage: gate_alias.py in out [--no-head|--reverse]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
g = Glb(sys.argv[1])
M = {}
for tag, s in (('01', 'R'), ('', 'L')):
    M.update({f'Zarmbase{tag}': f'Bip01 {s} Clavicle', f'Zarmpiv{tag}': f'Bip01 {s} UpperArm', f'Zarm{tag}': f'Bip01 {s} Forearm', f'Zhand{tag}': f'Bip01 {s} Hand'})
fing = {'Index': 0, 'Middle': 1, 'Ring': 2, 'Thumb': 3}
for s, base in (('L', 0), ('R', 4)):
    for fname, k in fing.items():
        tag = '' if base + k == 0 else f'{base + k:02d}'
        for p, seg in (('Zfingbase', 0), ('ZfingA', 1), ('ZfingB', 2), ('ZfingC', 3)):
            M[p + tag] = f'Bip01 {s} {fname}{seg}'
M['Xspine2'] = 'Bip01 Spine2'
R = {v: k for k, v in M.items()}
for n in g.json['nodes']:
    k = n.get('name', '')
    if '--reverse' in sys.argv:
        if k in R:
            n['name'] = R[k]
    elif k in M:
        n['name'] = M[k]
if '--no-head' in sys.argv:
    for m_ in g.json['meshes']:
        m_['primitives'] = [p for p in m_['primitives'] if not g.json['materials'][p['material']]['name'].startswith(('BansheeHead', 'BansheeHair'))]
g.write(sys.argv[2])
