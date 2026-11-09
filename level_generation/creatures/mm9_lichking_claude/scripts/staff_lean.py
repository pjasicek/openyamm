#!/usr/bin/env python3
"""r9: the staff's lean in Standing. Our shoulders are 5 cm narrower than MM9's, so with MM9's hand rotations the staff crossed the body
(skull at mid-chest; MM9's stands at the right side, skull by the shoulder). One constant extra rotation D of the R Hand (right-multiplied on
its local keys in every clip, like arm_out.py) turns our shaft onto MM9's shaft direction in Standing (mean over the clip's keys). Fist and
staff turn together (both ride R Hand / Bone01), so the grip is unchanged. Args: <in glb> <out glb> [fraction 1.0]"""
import sys, numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model, matrix_quaternion, quaternion_matrix
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]; FRAC = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
mm = Model(Glb('source/lk2/lichking.glb')); mo = Model(Glb(IN))
nm = [n['name'] for n in mm.glb.json['nodes']]; no = [n['name'] for n in mo.glb.json['nodes']]; jo = [no[j] for j in mo.joints]
si = [i for i, p in enumerate(mm.primitives) if mm.glb.json['nodes'][p['node']]['name'] == 'staff2.mesh'][0]
mats = [mo.glb.json['materials'][p['material']]['name'] for p in mo.glb.json['meshes'][0]['primitives']]
oi = [i for i, n in enumerate(mats) if n.startswith('LichKingStaff') and 'Skull' not in n][0]; pj = mo.primitives[oi]
shaft = np.where((pj['joints'][:, 0] == jo.index('Bone01')) & (pj['weights'][:, 0] > 0.99))[0]
def axis(P):
    c = P.mean(0); u = np.linalg.svd(P - c)[2][0]; return u if u[1] > 0 else -u
Rs = []
for t in np.linspace(0, 2.6, 9):
    wm = mm.world(mm.sample('stand', float(t))); wo = mo.world(mo.sample('Standing', float(t)))
    um = axis(mm.skinned_positions(wm)[si][0]); uo = axis(mo.skinned_positions(wo)[oi][0][shaft])
    v = np.cross(uo, um); s = np.linalg.norm(v); c = uo @ um
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    R = np.eye(3) + K + K @ K * ((1 - c) / max(s * s, 1e-12))
    Wr = wo[no.index('Bip01 R Hand')][:3, :3]; Wr = Wr / np.linalg.norm(Wr, axis=0)
    Rs.append(Wr.T @ R @ Wr)
    if t == 0: print('Standing: MM9 shaft', um.round(3), 'ours', uo.round(3), 'angle', round(float(np.degrees(np.arccos(np.clip(c, -1, 1)))), 1))
D = np.mean(Rs, 0); U, _, Vt = np.linalg.svd(D); D = U @ Vt                    # mean rotation in the hand's frame
ang = np.arccos(np.clip((np.trace(D) - 1) / 2, -1, 1)) * FRAC
ax = np.array([D[2, 1] - D[1, 2], D[0, 2] - D[2, 0], D[1, 0] - D[0, 1]]); ax /= np.linalg.norm(ax)
d = np.r_[ax * np.sin(ang / 2), np.cos(ang / 2)]
print('STAFF_LEAN R Hand local turn', round(float(np.degrees(ang)), 1), 'deg about', ax.round(3))
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); idx = [n.name for n in g.nodes].index('Bip01 R Hand'); k = 0
for an in g.animations:
    for c in an.channels:
        if c.target.node == idx and c.target.path == 'rotation':
            x = g.accessors[an.samplers[c.sampler].output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
            Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).astype(float)
            Qn = qmul(Q, np.tile(d, (len(Q), 1))); blob[o:o + Qn.size * 4] = Qn.astype('f4').tobytes(); k += 1
g.set_binary_blob(bytes(blob)); g.save(OUT); print('channels', k)
