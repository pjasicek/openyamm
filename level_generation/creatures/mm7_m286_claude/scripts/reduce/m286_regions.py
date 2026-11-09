#!/usr/bin/env python3
"""Regions of the v2b abs/shoulder fix (scripts/smooth_fix.py) on the rest mesh (work/mesh_in.npz), for keeping them
in the ladder: abs = body skin in front of the torso between the pec line and the belt (rest z 1.00-1.34, y < 0.02,
|x| < 0.33, arm weight < 0.3, the fix's own selection without its 4 cm easing margin unless M286_ABS_PAD), shoulders =
body skin within M286_SH_R (default 0.16 m: the fix's full-strength radius) of each upper-arm joint (bind positions from
the source GLB's inverse bind matrices), jaw/neck excluded. Writes work/abs.npy, work/shoulders.npy (bool per face)."""
import json, os, struct
import numpy as np
E = lambda k, x: float(os.environ.get(k, x))
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
gv = np.load('work/garment_v.npy'); skin = gv == 0
b = open('work/mm7_m286_source_pre_reduce.glb', 'rb').read(); n = struct.unpack('<I', b[12:16])[0]
doc = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = doc['skins'][0]; acc = doc['accessors'][sk['inverseBindMatrices']]; bv = doc['bufferViews'][acc['bufferView']]
ibm = np.frombuffer(b, np.float32, acc['count'] * 16, bin0 + bv.get('byteOffset', 0) + acc.get('byteOffset', 0)).reshape(-1, 4, 4)
jn = [doc['nodes'][j]['name'] for j in sk['joints']]
def joint(nm):
    m = np.linalg.inv(ibm[jn.index(nm)].T); p = m[:3, 3]
    return np.array([p[0], -p[2], p[1]])          # glTF y-up -> Blender z-up
arm = W[:, [i for i, nm in enumerate(names) if any(k in nm for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]].sum(1)
x, y, z = v[:, 0], v[:, 1], v[:, 2]; pad = E('M286_ABS_PAD', '0')
absv = skin & (z > 1.00 - pad) & (z < 1.34 + pad) & (y < 0.02 + pad) & (np.abs(x) < 0.33 + pad) & (arm < 0.3)
headneck = W[:, names.index('B_Head')] + W[:, names.index('B_Neck')]
sh = np.zeros(len(v), bool)
for s in 'LR':
    j = joint(f'B_{s}_UpperArm'); print('JOINT', s, np.round(j, 3))
    sh |= skin & (np.linalg.norm(v - j, axis=1) < E('M286_SH_R', '0.16')) & (headneck < 0.5)
fa, fs = absv[f].all(1), sh[f].all(1)
np.save('work/abs.npy', fa); np.save('work/shoulders.npy', fs)
print('REGIONS abs faces', int(fa.sum()), 'shoulder faces', int(fs.sum()))
