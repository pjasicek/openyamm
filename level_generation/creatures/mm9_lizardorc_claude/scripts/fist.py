"""Right fist round the cutlass grip, left hand keeps MM9's curl. Fingers solved round the grip axis per finger (rotation of each segment about the axis), thumb over them; the grip centre is searched near MM9's Bone07 so that the palm stays clear. Output work/hand_poses.json: bone-local quaternions (node rotation keys), grip centre G, and writes nothing else.
Frame: bind (glTF). L_n = R(BIND_p)^T R(Dp)^T R(Dn) R(BIND_n), where Dn is the bone's delta rotation in bind space."""
import sys, json, numpy as np
sys.path.insert(0, 'scripts')
from pathlib import Path
import rig_bones as RB, mm9_joints
from scipy.spatial import cKDTree
J = np.load('work/joined.npz'); co, part = J['co'].astype(float), J['part']
labels = np.zeros(len(co), int); lb = np.load('work/finger_labels.npy'); labels[:len(lb)] = lb
P, tips = RB.joints(); W, par, _ = mm9_joints.rest(); X = np.array([-1, 1, 1.])
F = np.load('work/cut_frame.npz'); AX = F['a'] / np.linalg.norm(F['a'])
G0 = W['Bone07'][:3, 3].copy()
S = 'R'; pre = 'Bip01 R '
R_GRIP = .024
def rot(ax, a):
    ax = np.asarray(ax) / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
FN = ['Finger1', 'Finger2', 'Finger3']
ch = {}
for f in FN + ['Finger0']:
    ch[f] = np.array([P[pre + RB.fk(f, k)] for k in range(3)] + [tips[f] * X])
hand = (co[:, 0] < -.45) & (part == 0)
half = {}
for i, f in enumerate(FN + ['Finger0'], 1):
    q = co[(labels == i) & (co[:, 0] < 0)]; pts = ch[f]
    d = np.min([np.linalg.norm(np.cross(q - a, (b - a) / np.linalg.norm(b - a)), axis=1) for a, b in zip(pts[:-1], pts[1:])], axis=0); half[f] = float(np.median(d))
palm = co[(labels == 0) & (co[:, 0] < -.58) & (co[:, 1] < .16) & (part == 0)]
# constant wrist turn: the knuckle line onto the grip axis (the hand turns, the blade stays where MM9 has it)
wr = P[pre + 'Hand']; kn = (ch['Finger3'][0] - ch['Finger1'][0]); kn /= np.linalg.norm(kn)
if kn @ AX < 0: AXk = -AX
else: AXk = AX
TURN = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
v_ = np.cross(kn, AXk); sn_ = np.linalg.norm(v_); th_ = np.arctan2(sn_, kn @ AXk) * TURN
RD = rot(v_ / sn_, th_) if sn_ > 1e-6 else np.eye(3)
print('wrist turn deg', round(np.degrees(th_), 1))
for f in ch: ch[f] = wr + (ch[f] - wr) @ RD.T
palm = wr + (palm - wr) @ RD.T
print('half', {k: round(v, 3) for k, v in half.items()}, 'palm verts', len(palm), 'R grip', R_GRIP)
A1 = np.radians(np.arange(-30, 100, 5)); A2 = np.radians(np.arange(0, 121, 6)); A3 = np.radians(np.arange(-20, 91, 6))
g1, g2, g3 = np.meshgrid(A1, A2, A3, indexing='ij'); g1, g2, g3 = g1.ravel(), g2.ravel(), g3.ravel()
def rotv(v, angs):
    """v (3) rotated about AX by each angle (n) -> n,3"""
    c, s = np.cos(angs)[:, None], np.sin(angs)[:, None]; return v * c + np.cross(AX, v) * s + np.outer(angs * 0 + (v @ AX), AX) * (1 - c)
def fk(j, sg):
    t1 = sg * g1; t2 = t1 + sg * g2; t3 = t2 + sg * g3
    p1 = j[0] + rotv(j[1] - j[0], t1); p2 = p1 + rotv(j[2] - j[1], t2); p3 = p2 + rotv(j[3] - j[2], t3)
    return p1, p2, p3
def radial(p, G):
    v = p - G; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
def seg_samples(ps):
    s = []
    for a, b in zip(ps[:-1], ps[1:]):
        for t in (.34, .67, 1.): s.append(a + (b - a) * t)
    return s
def solve_finger(f, G, sg):
    j = ch[f]; want = R_GRIP + half[f] + .002
    p1, p2, p3 = fk(j, sg); s = seg_samples([np.repeat(j[0][None], len(p1), 0), p1, p2, p3])
    r = np.stack([radial(x, G) for x in s], 1)                # n, samples
    # first samples may stay away from the grip (the knuckle): count the last 2/3
    tail = r[:, 2:]
    c = ((tail - want) ** 2).sum(1) + 300 * (np.minimum(r - (want - .002), 0) ** 2).sum(1) + .00015 * ((g1 - g2) ** 2 + (g2 - 1.3 * g3) ** 2)
    i = int(c.argmin()); return c[i], (g1[i], g2[i], g3[i]), np.array([j[0], p1[i], p2[i], p3[i]])
b = np.array([np.cross(AX, [1, 0, 0]), np.cross(AX, np.cross(AX, [1, 0, 0]))]); b = b / np.linalg.norm(b, axis=1, keepdims=True)
# sign of the curl: tip toward the palm side
mcp = np.mean([ch[f][0] for f in FN], 0); inward = G0 - mcp; inward -= AX * (inward @ AX)
sg = 1.0 if ((rot(AX, .3) @ (ch['Finger2'][3] - ch['Finger2'][0]) - (ch['Finger2'][3] - ch['Finger2'][0])) @ inward) > 0 else -1.0
best = None
for du in np.arange(-.10, .101, .0125):
    for dv in np.arange(-.10, .101, .0125):
        G = G0 + b[0] * du + b[1] * dv
        rp = radial(palm, G)
        pen = np.minimum(rp - (R_GRIP + .006), 0)
        tb_ = ch['Finger0'][0]; tl_ = np.linalg.norm(np.diff(ch['Finger0'], axis=0), axis=1).sum()
        cost = 40 * (pen ** 2).sum() + .05 * (du ** 2 + dv ** 2) + 12 * (rp.min() - (R_GRIP + .007)) ** 2 + 3 * max(radial(tb_[None], G)[0] - (tl_ * .85 + R_GRIP), 0) ** 2
        for f in FN: cost += solve_finger(f, G, sg)[0]
        if best is None or cost < best[0]: best = (cost, G, du, dv)
_, G, du, dv = best
print('G', G.round(3), 'moved from Bone07', round(float(np.hypot(du, dv)), 3), 'cost', round(best[0], 5), 'palm clear', round(float(radial(palm, G).min()), 3), 'sign', sg)
BIND = {}
sys.argv = ['x']
# bind rotations: as build_glb
def unit(v): return v / np.linalg.norm(v)
def least(a, b):
    a, b = unit(a), unit(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
Rw = lambda n: W[n][:3, :3]
a0 = W[pre + 'Finger11'][:3, 3] - W[pre + 'Finger1'][:3, 3]
b0 = P[pre + 'Finger21'] - P[pre + 'Finger2']; b1 = P[pre + 'Finger22'] - P[pre + 'Finger21']
D0, D1 = least(a0, b0), least(a0, b1)
th0 = W[pre + 'Finger01'][:3, 3] - W[pre + 'Finger0'][:3, 3]
Dt0 = least(th0, P[pre + 'Finger01'] - P[pre + 'Finger0']); Dt1 = least(th0, P[pre + 'Finger02'] - P[pre + 'Finger01'])
Bf = lambda k: (D0 if k == 0 else D1) @ Rw(pre + ('Finger1' if k == 0 else 'Finger11'))
Bt = lambda k: (Dt0 @ Rw(pre + 'Finger0') if k == 0 else Dt1 @ Rw(pre + 'Finger01'))
def m2q(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
        q = [0, 0, 0, 0]; q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s; q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return (q / np.linalg.norm(q)).tolist()
RH = W[pre + 'Hand'][:3, :3]
poses = {}; posed = {}
for f in FN:
    c, a, p = solve_finger(f, G, sg); posed[f] = p
    print('FIST', f, np.round(np.degrees(a), 0), 'r', np.round(radial(p, G), 3), 'want', round(R_GRIP + half[f] + .004, 3), 'cost', round(c, 5))
    Ds = [rot(AX, sg * a[0]) @ RD, rot(AX, sg * (a[0] + a[1])) @ RD, rot(AX, sg * (a[0] + a[1] + a[2])) @ RD]
    prev, Bp = RD, RH
    for k in range(3):
        B = Bf(k); L = Bp.T @ prev.T @ Ds[k] @ B; poses[pre + RB.fk(f, k)] = m2q(L); prev, Bp = Ds[k], B
# thumb: over the fingers
t = ch['Finger0']; target = posed['Finger2'][2] + unit(posed['Finger2'][2] - G) * (half['Finger2'] + half['Finger0']) * .9
want = R_GRIP + half['Finger0'] + .004; bestt = None
f0 = unit(np.cross(AX, unit(mcp - G)))
for th in np.radians(np.arange(-70, 101, 6)):
    R1 = rot(f0, th)
    for ph in np.radians(np.arange(-120, 121, 6)):
        R2 = rot(AX, ph) @ R1
        for ps in np.radians(np.arange(-20, 91, 6)):
            R3 = rot(AX, ps) @ R2
            p1 = t[0] + R2 @ (t[1] - t[0]); p2 = p1 + R3 @ (t[2] - t[1]); p3 = p2 + R3 @ (t[3] - t[2])
            s = np.array(seg_samples([t[0], p1, p2, p3])); r = radial(s, G)
            ax_ = (p3 - G) @ AX; c = abs(r[-1] - want) + .6 * abs(r[-3] - want) + 3 * max(abs(ax_) - .05, 0) + 60 * np.maximum(want - r, 0).sum() + .06 * np.linalg.norm(p3 - target)
            if bestt is None or c < bestt[0]: bestt = (c, R2, R3, (th, ph, ps), p3)
print('THUMB', np.round(np.degrees(bestt[3]), 0), 'tip radial', round(float(radial(bestt[4][None], G)[0]), 3), 'want', round(want, 3))
Ds = [bestt[1] @ RD, bestt[2] @ RD, bestt[2] @ RD]; prev, Bp = RD, RH
for k in range(3):
    B = Bt(k); L = Bp.T @ prev.T @ Ds[k] @ B; poses[pre + RB.fk('Finger0', k)] = m2q(L); prev, Bp = Ds[k], B
# the hand's key offset and the weapon bone's constant local transform
qoff = RH.T @ RD @ RH
L07 = RH.T @ Rw('Bone07'); Lw = qoff.T @ L07; tw = qoff.T @ (RH.T @ (G - wr))
json.dump({'grip': poses, 'hand_offset': {pre + 'Hand': m2q(qoff)}, 'weapon': {'q': m2q(Lw), 't': tw.tolist()}, 'G': G.tolist(), 'AX': AX.tolist(), 'R': R_GRIP, 'RD': RD.tolist()}, open('work/hand_poses.json', 'w'), indent=0)
