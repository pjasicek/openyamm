#!/usr/bin/env python3
"""MM9's hand sockets LHand1 / RHand1 (RangeAttack is on LHand1), as nodes on our palms: the mean of the finger bases, 3 cm towards the palm side. True handed (L at +x). Args: <in> <out>"""
import json, subprocess, sys
import numpy as np
IN, OUT = sys.argv[1:3]
R = json.load(open('work/rig.json')); F = R['fingers']; J = R['joints']
base = np.mean([F[f][0] for f in ('1', '2', '3', '4')], 0)    # left-side numbers (+x)
wr = np.array(J['Bip01 L Hand']); palm = wr + (base - wr) * 0.75
def gl(p): return [float(p[0]), float(p[2]), float(-p[1])]
tmp = IN + '.s1.glb'
py = sys.executable
subprocess.check_call([py, '-W', 'ignore', 'scripts/add_socket.py', IN, tmp, 'LHand1', 'Bip01 L Hand'] + [str(x) for x in gl(palm)])
subprocess.check_call([py, '-W', 'ignore', 'scripts/add_socket.py', tmp, OUT, 'RHand1', 'Bip01 R Hand'] + [str(x) for x in gl(palm * [-1, 1, 1])])
print('SOCKETS', gl(palm))
