"""Right-hand grip set-up: the staff axis in our fist and the roll of the R Hand bind frame that carries MM9's staff (rigid on Bone01 under R Hand)
onto it. Writes rig.json['grip'] = {point, axis (staff top direction), finger_dir, mm9_axis, mm9_dir}. Blender frame. Args: <asm npz> <rig json>"""
import sys, json, numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
D = np.load(sys.argv[1]); R = json.load(open(sys.argv[2]))
F = R['fingers']; J = R['joints']; wr = np.array(J['Bip01 R Hand'])
base = np.mean([np.array(F[f][0]) for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
tips = np.mean([np.array(F[f][3]) for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
fd = base - wr; fd /= np.linalg.norm(fd)
ac = np.array(F['Pinky'][0]) - np.array(F['Index'][0]); ac -= fd * (ac @ fd); ac /= np.linalg.norm(ac)
a = -ac                                                       # staff top on the thumb and index side
curl = tips - base; curl -= fd * (curl @ fd); curl -= a * (curl @ a); n = curl / np.linalg.norm(curl)      # palm side
# grip point: the staff's skin cylinder touches the palm (palm vertices of the +x hand at RS + 3 mm), finger first joints stay outside the
# finger wrap radius; grid over the palm-side and finger-direction offsets (2026-10-31: a fixed 2.4 cm offset ran the staff through the fingers)
RS, RW = 0.0165, 0.025
lab = np.load('work/finger_labels.npy'); co = D['co']; comp = D['comp']; pn = [str(x) for x in D['names']]
palm_v = co[(comp == pn.index('hands')) & (co[:, 0] > 0) & (lab == 0)]
fj = np.array([F[f_][k] for f_ in ('Index', 'Middle', 'Ring', 'Pinky') for k in (0,)])
def adist(P_, G_): d_ = P_ - G_; return np.linalg.norm(d_ - np.outer(d_ @ a, a), axis=1)
best = None
for dn in np.arange(0.0, 0.05, 0.002):
    for df in np.arange(-0.02, 0.04, 0.002):
        G_ = base + n * dn + fd * df
        pm = adist(palm_v, G_).min(); fm = adist(fj, G_).min()
        sc_ = abs(pm - (RS + 0.003)) + 4 * max(0, RW - 0.004 - fm) + 0.1 * abs(df - 0.01)
        if best is None or sc_ < best[0]: best = (sc_, dn, df, pm, fm)
print('grip search: palm side', round(best[1], 3), 'along fingers', round(best[2], 3), 'palm dist', round(best[3], 4), 'finger base dist', round(best[4], 4))
G = base + n * best[1] + fd * best[2]
m = Model(Glb('source/lk/lichking.glb')); w = m.world({}); nn = [x['name'] for x in m.glb.json['nodes']]
def bl(p): return np.array([p[0], -p[2], p[1]])
P = np.load('work/mm9_staff_pts.npy') - [0, 0, 0.968]               # back to raw (Blender frame, MM9 origin)
c = P.mean(0); u = np.linalg.svd(P - c)[2][0]; u = u if u[2] > 0 else -u
md = bl(w[nn.index('Bip01 R Finger0')][:3, 3] - w[nn.index('Bip01 R Hand')][:3, 3]); md /= np.linalg.norm(md)
hand = bl(w[nn.index('Bip01 R Hand')][:3, 3]); s = (hand - c) @ u
R['grip'] = dict(point=G.tolist(), axis=a.tolist(), finger_dir=fd.tolist(), palm_side=n.tolist(), mm9_axis=u.tolist(), mm9_dir=md.tolist(),
                 mm9_hand_s=float(s), mm9_s=[float(((P - c) @ u).min()), float(((P - c) @ u).max())])
print('grip point', G.round(3), 'axis', a.round(3), 'palm side', n.round(3), 'MM9 axis', u.round(3), 'MM9 finger dir', md.round(3),
      'MM9 angle staff/finger', np.degrees(np.arccos(u @ md)).round(1), 'ours', np.degrees(np.arccos(a @ fd)).round(1), 'hand s', round(s, 3))
json.dump(R, open(sys.argv[2], 'w'), indent=0)
