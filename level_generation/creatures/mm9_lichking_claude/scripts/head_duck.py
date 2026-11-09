#!/usr/bin/env python3
"""r11: in AttackMelee MM9's left hand sweeps over the head; our crown (the reused Lich skull plus the King's crown) stands taller than
MM9's head, so the hand passed through the crown's top (4.6 cm, 4 frames), and clearing it with the arm (arm_clear.py + arm_soft.py) failed
the jitter gate (forearm 6.3 deg/frame over MM9 in a fast swing). Here the head ducks away instead: Bip01 Head turns about a fixed axis
(through the head joint, chosen at the crossing frame so the crown top moves sideways off the hand's path), by a Gaussian in time, applied to the raw
local keys in the parent's frame. The arms are not touched, so the jitter gate does not see it.
Args: <in glb> <out glb> <clip> <centre frame at 48 fps> <peak deg> <sigma s> [staff]
2026-11-01: with 'staff' the obstacle is the staff's skull (Hit: the staff seated 2 cm deeper in the palm met the head 2.1 cm deep in two
frames, r13 1.2 cm) and the head's centre turns off it."""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

SRC, OUT, CLIP = sys.argv[1:4]; FR = float(sys.argv[4]); PEAK = np.radians(float(sys.argv[5])); SIG = float(sys.argv[6])
STAFF = len(sys.argv) > 7 and sys.argv[7] == 'staff'
g = Glb(Path(SRC)); m = Model(g); names = [n.get('name') for n in g.json['nodes']]
hi = names.index('Bip01 Head'); pi = m.parent[hi]; li = names.index('Bip01 L Finger01')
if STAFF:
    # 2026-11-01: the obstacle is the staff's skull (rigid on Bone01), not the left hand; the head centre, not the crown top, moves off it
    jn = [names[j] for j in m.joints]; bk = jn.index('Bone01'); bi_ = m.joints[bk]
    D_ = np.load(Path(__file__).resolve().parents[1] / 'work' / 'asm4.npz'); sk = D_['co'][D_['comp'] == [str(x) for x in D_['names']].index('sskull')].mean(0)
    sk = np.r_[sk[0], sk[2], -sk[1], 1.0]                                        # Blender raw -> glTF, homogeneous
    def obstacle(t): return (m.world(m.sample(CLIP, t))[bi_] @ m.inverse_binds[bk] @ sk)[:3]
else:
    def obstacle(t): return m.world(m.sample(CLIP, t))[li][:3, 3]
tc = FR / 48.0
w = m.world(m.sample(CLIP, tc))
H = w[hi][:3, 3]; P = obstacle(tc)
up = w[hi][:3, :3] @ np.linalg.lstsq(m.world({})[hi][:3, :3], np.array([0.0, 1.0, 0.0]), rcond=None)[0]   # rest world-up, carried by the head
up /= np.linalg.norm(up)
C = H + (0.08 if STAFF else 0.25) * up               # the head's centre (staff) or the crown top (left hand)
v = obstacle(tc + 2 / 48) - obstacle(tc - 2 / 48)
v -= up * (v @ up); v /= np.linalg.norm(v)  # the hand's sweep direction, across the head's axis
d = C - P; d -= up * (d @ up); d -= v * (d @ v); d /= np.linalg.norm(d)  # away from the hand's path, sideways
axis_w = np.cross(up, d); axis_w /= np.linalg.norm(axis_w)
Rp = w[pi][:3, :3]; Rp = Rp / np.linalg.norm(Rp, axis=0)
axis_l = Rp.T @ axis_w; axis_l /= np.linalg.norm(axis_l)


def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                 w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]


a = GLTF2().load(SRC); ba = bytearray(a.binary_blob())
an = next(x for x in a.animations if x.name == CLIP)
ch = next(c for c in an.channels if c.target.node == hi and c.target.path == 'rotation')
s = an.samplers[ch.sampler]
xi = a.accessors[s.input]; vi = a.bufferViews[xi.bufferView]
ts = np.frombuffer(ba, 'f4', xi.count, (vi.byteOffset or 0) + (xi.byteOffset or 0)).astype(float)
xo = a.accessors[s.output]; vo = a.bufferViews[xo.bufferView]; oo = (vo.byteOffset or 0) + (xo.byteOffset or 0)
Q = np.frombuffer(ba, 'f4', xo.count * 4, oo).reshape(-1, 4).astype(float)
th = PEAK * np.exp(-0.5 * ((ts - tc) / SIG) ** 2)
q = np.c_[axis_l[None, :] * np.sin(th / 2)[:, None], np.cos(th / 2)]
Qn = qmul(q, Q)
ba[oo:oo + Qn.size * 4] = Qn.astype('f4').tobytes()
a.set_binary_blob(bytes(ba)); a.save(OUT)
print('HEADDUCK', CLIP, 'axis world', np.round(axis_w, 2), 'away', np.round(d, 2), 'peak deg', round(float(np.degrees(th.max())), 1))
