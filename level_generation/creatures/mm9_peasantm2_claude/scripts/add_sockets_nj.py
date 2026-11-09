#!/usr/bin/env python3
"""MM9's hand sockets LHand1 / RHand1 (PEASANTMALE.abc's; RangeAttack releases there) as nodes on our palms: 3/4 of the way from
the wrist to the mean of the finger bases, in the GLB's rest (glTF space). Args: <in glb> <out glb>"""
import subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]
m = Model(Glb(IN)); names = [n.get('name') for n in m.glb.json['nodes']]; w = m.world({})
tmp = IN + '.s1.glb'; src = IN
for k, (S, nm) in enumerate((('R', 'RHand1'), ('L', 'LHand1'))):
    wr = w[names.index(f'Bip01 {S} Hand')][:3, 3]
    base = np.mean([w[names.index(f'Bip01 {S} {f}1')][:3, 3] for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
    palm = wr + (base - wr) * 0.75
    dst = tmp if k == 0 else OUT
    subprocess.check_call([sys.executable, '-W', 'ignore', str(Path(__file__).parent / 'add_socket.py'), src, dst, nm, f'Bip01 {S} Hand'] + [str(float(x)) for x in palm])
    src = dst
Path(tmp).unlink()
print('SOCKETS done')
