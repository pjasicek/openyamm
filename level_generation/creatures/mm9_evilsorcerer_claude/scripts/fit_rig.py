"""Joints on the assembled A-pose mesh (Blender frame: faces -Y, z up): limb axes by plane sections per part, fingers by geodesic merge levels on the left hand part. Spine, neck and head heights are MM9's.
Writes work/rig.json {joints, fingers, across, palm} and work/finger_labels.npy (per vertex 0 none, 1..5). Args: <asm npz> <mm9 true glb> <out json>"""
import sys, json
import numpy as np
from pathlib import Path
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from meshlib import section, nearest_loop
from glb_pose import Glb, Model
npz, mm9, out = sys.argv[1:4]
D = np.load(npz); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
pid = {n: i for i, n in enumerate(names)}
tp = comp[tri[:, 0]]
def T(*ns): return tri[np.isin(tp, [pid[n] for n in ns])]
X, Y, Z = np.eye(3)
m = Model(Glb(mm9)); nn = [n.get('name') for n in m.glb.json['nodes']]; w0 = m.world({})
MJ = {n: np.array([w0[i][0, 3], -w0[i][2, 3], w0[i][1, 3]]) for i, n in enumerate(nn)}     # glTF -> Blender
J = {}
# crotch from the leg part
tl = T('legs'); crotch = None
for z in np.arange(1.15, 0.6, -0.005):
    L = [l for l in section(co, tl, np.array([0, 0, z]), Z) if l['per'] > 0.1]
    if len(L) == 2: crotch = z; break
print('crotch', crotch)
# spine: MM9's heights, centred on the torso section
tt = T('torso'); pel_y = None
for k in ('Pelvis', 'Spine', 'Spine1', 'Spine2', 'Spine3', 'Neck', 'Head'):
    z = MJ['Bip01 ' + k][2]
    secs = section(co, T('legs') if k == 'Pelvis' else tt, np.array([0, 0, z]), Z)
    l = nearest_loop(secs, np.array([0, 0, z]))
    y = float(l['c'][1]) if l is not None and abs(l['c'][0]) < 0.04 and l['per'] < 1.3 else None
    J['Bip01 ' + k] = [0.0, y, float(z)]
    print(k, z, y, None if l is None else round(l['per'], 3))
last = None
for k in ('Pelvis', 'Spine', 'Spine1', 'Spine2', 'Spine3', 'Neck', 'Head'):
    if J['Bip01 ' + k][1] is None: J['Bip01 ' + k][1] = last
    last = J['Bip01 ' + k][1]
# torso sections are unreliable through the belt and shoulders: the centre line by hand, from the sections above
for k, y in dict(Pelvis=-0.011, Spine=-0.011, Spine1=-0.012, Spine2=-0.012, Spine3=0.006, Neck=0.012, Head=0.012).items(): J['Bip01 ' + k][1] = y
J['Bip01 Neck'][2] = 1.555; J['Bip01 Head'][2] = 1.668        # our head sits on a neck higher than MM9's: the skull's base
hip_z = J['Bip01 Pelvis'][2]
pel = np.array(J['Bip01 Pelvis'])
# left leg
pts = []
for z in np.arange(crotch - 0.02, 0.40, -0.02):
    l = nearest_loop([q for q in section(co, tl, np.array([0, 0, z]), Z) if q['c'][0] > 0], np.array([0.1 + (crotch - z) * .25, 0, z]))
    if l is not None: pts.append(l['c'])
for z in np.arange(0.40, 0.16, -0.02):
    l = nearest_loop(section(co, T('boots'), np.array([0, 0, z]), Z), np.array([0.27, 0, z]))
    if l is not None and l['c'][0] > 0: pts.append(l['c'])
pts = np.array(pts); print('leg pts', pts[::4].round(3).tolist())
hip = np.array([abs(MJ['Bip01 L Thigh'][0]) + 0.0, pel[1], hip_z])
fit = np.polyfit(pts[-6:, 2], pts[-6:, :2], 1); ank_z = float(MJ['Bip01 L Foot'][2]) + 0.01
ank = np.array([*(fit[0] * ank_z + fit[1]), ank_z])
poly = np.vstack([hip, pts, ank]); seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
rk = 0.558                                  # MM9: thigh 0.515 / (0.515+0.387) of the leg... our knee from the mesh below
knee_z = float(MJ['Bip01 L Calf'][2])
ki = np.interp(-knee_z, -poly[:, 2], s)
knee = np.array([np.interp(ki, s, poly[:, i]) for i in range(3)])
fv = co[comp == pid['shoes']]; fv = fv[fv[:, 0] > 0]
tip_y, heel_y = fv[:, 1].min(), fv[:, 1].max(); ball_y = heel_y + (tip_y - heel_y) * 0.70
bv = fv[np.abs(fv[:, 1] - ball_y) < 0.02]; toe = np.array([bv[:, 0].mean(), ball_y, 0.02])
print('leg hip', hip.round(3), 'knee', knee.round(3), 'ankle', ank.round(3), 'toe', toe.round(3), 'len', s[-1].round(3))
leg = dict(Thigh=hip, Calf=knee, Foot=ank, Toe0=toe)
# left arm: march from the shoulder to the wrist on the sleeve
wrist_ring = co[comp == pid['hands']]; wrist_ring = wrist_ring[wrist_ring[:, 0] > 0]
tb = T('torso')
d = np.array([0.72, 0.0, -0.70]); d /= np.linalg.norm(d)
p = np.array([0.27, 0.01, 1.42]); arm = []
for i in range(60):
    l = nearest_loop(section(co, tb, p, d), p)
    if l is None or np.linalg.norm(l['c'] - p) > 0.06: print('arm stop', i, p.round(3)); break
    arm.append((*l['c'], l['per']))
    if len(arm) > 3:
        nd = np.array(arm[-1][:3]) - np.array(arm[-4][:3]); nd /= np.linalg.norm(nd); d = 0.7 * d + 0.3 * nd; d /= np.linalg.norm(d)
    p = l['c'] + d * 0.012
arm = np.array(arm); print('arm line', arm[::3].round(3).tolist())
# hand ring: the open end of the left hand part
ht = T('hands'); ht = ht[co[ht[:, 0], 0] > 0]
e = np.sort(np.vstack([ht[:, [0, 1]], ht[:, [1, 2]], ht[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True); bd = u[c == 1]
wrist = co[np.unique(bd)].mean(0); print('wrist ring', wrist.round(3), len(bd))
shdir = arm[0, :3] - arm[5, :3]; shdir /= np.linalg.norm(shdir)
sh = arm[0, :3] + shdir * ((arm[0, 0] - abs(MJ['Bip01 L UpperArm'][0])) / max(abs(shdir[0]), .1))
poly = np.vstack([sh, arm[:, :3], wrist]); seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
ua, fa = np.linalg.norm(MJ['Bip01 L Forearm'] - MJ['Bip01 L UpperArm']), np.linalg.norm(MJ['Bip01 L Hand'] - MJ['Bip01 L Forearm'])
ek = s[-1] * ua / (ua + fa)
el = np.array([np.interp(ek, s, poly[:, i]) for i in range(3)])
print('shoulder', sh.round(3), 'elbow', el.round(3), 'wrist', wrist.round(3), 'arm', s[-1].round(3), 'MM9', round(ua + fa, 3))
cl = MJ['Bip01 L Clavicle']; nk = np.array(J['Bip01 Neck'])
arms = dict(Clavicle=np.array([abs(cl[0]), nk[1], cl[2]]), UpperArm=sh, Forearm=el, Hand=wrist)
for k, v in {**leg, **arms}.items():
    J[f'Bip01 R {k}'] = v.tolist(); J[f'Bip01 L {k}'] = [-float(v[0]), float(v[1]), float(v[2])]    # raw ABC space: L at -x; mirror_glb.py makes it true-handed last
# fingers, left hand: geodesic from the wrist ring
axis = (wrist - el) / np.linalg.norm(wrist - el)
hand = (comp == pid['hands']) & (co[:, 0] > 0)
hv = np.where(hand)[0]; rem = -np.ones(len(co), int); rem[hv] = np.arange(len(hv))
tt = tri[hand[tri].all(1)]
e = np.vstack([tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]]); w = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[rem[e[:, 0]], rem[e[:, 1]]], np.r_[rem[e[:, 1]], rem[e[:, 0]]])), shape=(len(hv), len(hv))).tocsr()
seeds = rem[np.unique(bd)]; dd = dijkstra(G, indices=seeds, min_only=True)
order = np.argsort(-dd); parent = {}; birth = {}; comps = {}; tips = {}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
adj = [[] for _ in hv]
for a, b in zip(rem[e[:, 0]], rem[e[:, 1]]): adj[a].append(b); adj[b].append(a)
done = np.zeros(len(hv), bool); fingers = []
LONG = 0.03
for i in order:
    if not np.isfinite(dd[i]): continue
    parent[i] = i; birth[i] = dd[i]; comps[i] = [i]; done[i] = True
    for j in adj[i]:
        if done[j] and j in parent:
            ri, rj = find(i), find(j)
            if ri == rj: continue
            li = birth[ri] - dd[i] > LONG; lj = birth[rj] - dd[i] > LONG
            if li and lj:
                for r in (ri, rj):
                    if tips.get(r, 1) == 1: fingers.append((birth[r], dd[i], [hv[q] for q in comps[r]]))
            nt = tips.get(ri, 1) + tips.get(rj, 1) if (li and lj) else max(tips.get(ri, 1), tips.get(rj, 1)) if (li or lj) else 1
            if len(comps[ri]) < len(comps[rj]): ri, rj = rj, ri
            parent[rj] = ri; comps[ri] += comps[rj]; birth[ri] = max(birth[ri], birth[rj]); tips[ri] = nt
fingers.sort(key=lambda f: -len(f[2]))
keep = []
for f in fingers:
    s_ = set(f[2])
    if any(len(s_ & set(k[2])) > 0.5 * len(s_) for k in keep): continue
    keep.append(f)
print('finger candidates', [(round(f[0], 3), round(f[1], 3), len(f[2])) for f in keep[:8]])
keep = keep[:5]
info = []
for tipd, based, vs in keep:
    vs = np.array(vs); q = co[vs]; dv = dd[rem[vs]]
    info.append(dict(tip=q[dv.argmax()], base=q[np.abs(dv - dv.min()) < 0.006].mean(0), vs=vs, dv=dv, based=based, length=tipd - based))
thumb = min(info, key=lambda f: f['based']); rest = [f for f in info if f is not thumb]
ctr = np.mean([f['base'] for f in rest], axis=0)
ac = ctr - thumb['base']; ac -= axis * (ac @ axis); ac /= np.linalg.norm(ac)
rest.sort(key=lambda f: f['base'] @ ac)
FN = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']; labels = np.zeros(len(co), int); F = {}
for fi, (nm, f) in enumerate(zip(FN, [thumb] + rest), 1):
    vs, dv = f['vs'], f['dv']; labels[vs] = fi
    a, b = dv.min(), dv.max(); L = b - a
    def ring(t):
        m_ = np.abs(dv - (a + L * t)) < max(0.004, L * 0.06)
        return co[vs[m_]].mean(0)
    p1, p2, p3, tip = ring(0.02), ring(0.42), ring(0.74), f['tip']
    dirn = (p2 - p1) / np.linalg.norm(p2 - p1); p0 = p1 - dirn * (0.012 if nm != 'Thumb' else 0.02)
    F[nm] = [p0.tolist(), p2.tolist(), p3.tolist(), tip.tolist()]
    print(nm, 'len', round(float(L), 3), 'verts', len(vs), 'base', p0.round(3).tolist(), 'tip', tip.round(3).tolist())
d_, m_ = cKDTree(co * [-1, 1, 1]).query(co)
print('mirror residual max', d_[comp == pid['hands']].max())
labels = np.maximum(labels, labels[m_])
np.save(HERE / 'work/finger_labels.npy', labels)
palm = np.cross(thumb['base'] - wrist, ctr - wrist); palm /= np.linalg.norm(palm)
pfz, pbz = co[comp == pid['panelF']], co[comp == pid['panelB']]
print('panel y', pfz[:, 1].mean(), pbz[:, 1].mean())
json.dump(dict(joints=J, panel_y=dict(F=float(pfz[:, 1].mean()), B=float(pbz[:, 1].mean())), fingers=F, palm_axis=axis.tolist(), across=ac.tolist(), palm=palm.tolist(), hip_z=hip_z, crotch=crotch, mm9={k: v.tolist() for k, v in MJ.items()}), open(out, 'w'), indent=0)
