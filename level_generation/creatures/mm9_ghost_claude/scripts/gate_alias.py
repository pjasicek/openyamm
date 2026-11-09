#!/usr/bin/env python3
"""A copy of a GLB with the Ghost's arm joints under Bip01 names, for the shared arm and jitter gates (they find joints by side token and name). --no-head drops the floating head's primitive: MM9's hands reach for it on purpose (fidget2 holds it). --reverse restores the MM9 names. Usage: gate_alias.py in out [--no-head|--reverse]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
g = Glb(sys.argv[1])
M = {}
for tag, s in (('01', 'R'), ('', 'L')):
    M.update({f'Zarmbase{tag}': f'Bip01 {s} Clavicle', f'Zarmpiv{tag}': f'Bip01 {s} UpperArm', f'Zarm{tag}': f'Bip01 {s} Forearm', f'Zhand{tag}': f'Bip01 {s} Hand', f'Zfingbase{tag}': f'Bip01 {s} Finger0'})
M['Xspine2'] = 'Bip01 Spine2'
R = {v: k for k, v in M.items()}
for n in g.json['nodes']:
    k = n.get('name', '')
    if '--reverse' in sys.argv:
        if k in R:
            n['name'] = R[k]
        elif k.startswith('Bip01 '):
            n['name'] = 'Finger ' + k[6:]
    elif k in M:
        n['name'] = M[k]
    elif k.startswith('Finger '):
        n['name'] = 'Bip01 ' + k[7:]
if '--no-head' in sys.argv:
    for m_ in g.json['meshes']:
        m_['primitives'] = [p for p in m_['primitives'] if not g.json['materials'][p['material']]['name'].startswith('GhostHead')]
g.write(sys.argv[2])
