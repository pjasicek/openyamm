#!/usr/bin/env python3
"""MM9's sockets as nodes on our model (raw ABC space, L at -x; mirrored with the model): LHand1 (RangeAttack is on it in LICHKING.abc) on
the left palm under Bip01 L Finger0 (MM9: L Finger01), RHand1 on the right palm under Bip01 R Hand (MM9: R Finger01), u1 (MM9's staff socket on
Bone01) at the centre of the staff's skull. Palms: the finger bases' mean, 3/4 of the way from the wrist. Args: <in> <out>"""
import json, subprocess, sys
import numpy as np
IN, OUT = sys.argv[1:3]
R = json.load(open('work/rig.json')); F = R['fingers']; J = R['joints']
base = np.mean([F[f][0] for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
wr = np.array(J['Bip01 R Hand']); palm = wr + (base - wr) * 0.75
D = np.load('work/asm4.npz'); sk = D['co'][D['comp'] == [str(x) for x in D['names']].index('sskull')].mean(0)
def gl(p): return [float(p[0]), float(p[2]), float(-p[1])]
py = sys.executable; t1, t2 = 'work/_sock1.glb', 'work/_sock2.glb'
subprocess.check_call([py, '-W', 'ignore', 'scripts/add_socket.py', IN, t1, 'RHand1', 'Bip01 R Hand'] + [str(x) for x in gl(palm)])
subprocess.check_call([py, '-W', 'ignore', 'scripts/add_socket.py', t1, t2, 'LHand1', 'Bip01 L Finger0'] + [str(x) for x in gl(palm * [-1, 1, 1])])
subprocess.check_call([py, '-W', 'ignore', 'scripts/add_socket.py', t2, OUT, 'u1', 'Bone01'] + [str(x) for x in gl(sk)])
print('SOCKETS', gl(palm), gl(sk))
