#!/usr/bin/env python3
"""MM9's hand sockets LHand1 / RHand1 (RangeAttack is on LHand1), as nodes on our palms: the mean of the finger bases, 3 cm towards the palm side. Raw ABC space (L at -x), mirrored with the model. Args: <in> <out>"""
import json, subprocess, sys
import numpy as np
IN, OUT = sys.argv[1:3]
R = json.load(open('work/rig.json')); F = R['fingers']; J = R['joints']
base = np.mean([F[f][0] for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)    # right-side numbers (+x in the raw space of the R hand)
wr = np.array(J['Bip01 R Hand']); palm = wr + (base - wr) * 0.75 + np.array(R['palm']) * 0.0
import struct as _st
_raw = open(IN, 'rb').read(); _n = _st.unpack_from('<I', _raw, 12)[0]; _doc = json.loads(_raw[20:20 + _n])
LIFT = next(nd.get('translation', [0, 0, 0])[1] for nd in _doc['nodes'] if nd.get('name') == 'Scene Root')   # clips_mm9 lift_to_floor
def gl(p): return [float(p[0]), float(p[2]) + LIFT, float(-p[1])]
tmp = IN + '.s1.glb'
py = sys.executable
subprocess.check_call([py, '-W', 'ignore', 'scripts/add_socket.py', IN, tmp, 'RHand1', 'Bip01 R Hand'] + [str(x) for x in gl(palm)])
subprocess.check_call([py, '-W', 'ignore', 'scripts/add_socket.py', tmp, OUT, 'LHand1', 'Bip01 L Hand'] + [str(x) for x in gl(palm * [-1, 1, 1])])
print('SOCKETS', gl(palm))
