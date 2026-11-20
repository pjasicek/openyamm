"""Joints on the assembled A-pose mesh (Blender frame: faces -Y, z up, figure's L at +x, true handed). Trunk and legs take MM9's bone lengths exactly (so MM9's root translations keep the feet where MM9 has them);
arm joints from the sleeve and hand; fingers by geodesic merge levels on the left hand. Writes work/rig.json and work/finger_labels.npy. Args: <asm npz> <mm9 glb> <out json>"""
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
MJ = {n: np.array([w0[i][0, 3], -w0[i][2, 3], w0[i][1, 3]]) for i, n in enumerate(nn) if n}     # glTF -> Blender
L = lambda a, b: float(np.linalg.norm(MJ['Bip01 ' + a] - MJ['Bip01 ' + b]))
J = {}
leg = L('L Thigh', 'L Calf') + L('L Calf', 'L Foot')
foot_h = MJ['Bip01 L Foot'][2] - MJ['Bip01 L Toe0'][2]
hip_z = leg + foot_h
print('hip z', hip_z, 'foot h', foot_h)
Y0 = -0.02
z = hip_z
J['Bip01'] = [0.0, Y0, z]; J['Bip01 Pelvis'] = [0.0, Y0, z]
for a, b in (('Pelvis', 'Spine'), ('Spine', 'Spine1'), ('Spine1', 'Spine2'), ('Spine2', 'Neck'), ('Neck', 'Head')):
    z += L(a, b); J['Bip01 ' + b] = [0.0, Y0, z]
print({k: round(v[2], 3) for k, v in J.items()})
# head ring: the neck centre of the head mesh at the head joint's height
hl = [l for l in section(co, T('head'), np.array([0, 0, J['Bip01 Head'][2]]), Z) if l['per'] > 0.1]
print('neck loops', [(np.round(l['c'], 3).tolist(), round(l['per'], 3)) for l in hl])
if hl:
    c_ = min(hl, key=lambda l: abs(l['c'][0]))['c']; J['Bip01 Head'][1] = float(c_[1]); J['Bip01 Neck'][1] = float(0.5 * (c_[1] + Y0))
# legs, left: straight down, MM9's lengths; the ankle over the mesh's foot
fv = co[comp == pid['feet']]; fv = fv[fv[:, 0] > 0]
top = fv[fv[:, 2] > fv[:, 2].max() - 0.03]
ax, ay = top[:, 0].mean(), top[:, 1].mean()
print('shin top centre', ax, ay, 'foot y', fv[:, 1].min(), fv[:, 1].max(), 'z', fv[:, 2].min())
hx = float(np.linalg.norm((MJ['Bip01 L Thigh'] - MJ['Bip01 R Thigh'])[:2])) / 2
hipL = np.array([hx, Y0, hip_z]); ank = np.array([ax, ay, foot_h]); kn = hipL + (ank - hipL) * L('L Thigh', 'L Calf') / leg
toe = np.array([ax, ay - np.hypot(*(MJ['Bip01 L Toe0'] - MJ['Bip01 L Foot'])[:2]), 0.005])
legs = dict(Thigh=hipL, Calf=kn, Foot=ank, Toe0=toe)
# left arm
hv = (comp == pid['hands']) & (co[:, 0] > 0)
ht = tri[hv[tri].all(1)]
e = np.sort(np.vstack([ht[:, [0, 1]], ht[:, [1, 2]], ht[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True); bd = u[c == 1]
wrist = co[np.unique(bd)].mean(0); print('wrist ring', wrist.round(3), len(bd))
clh = abs(MJ['Bip01 L Clavicle'][0] - MJ['Bip01 R Clavicle'][0]) / 2
dz = MJ['Bip01 Neck'][2] - MJ['Bip01 L UpperArm'][2]; sh_off = np.linalg.norm((MJ['Bip01 L UpperArm'] - MJ['Bip01 R UpperArm'])[:2]) / 2
sh = np.array([sh_off, Y0, J['Bip01 Neck'][2] - dz])
ua, fa = L('L UpperArm', 'L Forearm'), L('L Forearm', 'L Hand')
el = sh + (wrist - sh) * ua / (ua + fa)
print('shoulder', sh.round(3), 'elbow', el.round(3), 'wrist', wrist.round(3), 'arm', round(float(np.linalg.norm(wrist - sh)), 3), 'MM9', round(ua + fa, 3))
# the arm's axis through the sleeve: the sleeve bends a little at the elbow in the mesh
s = np.linalg.norm(co[(comp == pid['sleeves']) & (co[:, 0] > 0)] - el, axis=1).min(); print('sleeve dist at elbow', s)
cl = np.array([0.03, Y0, J['Bip01 Neck'][2]])
arms = dict(Clavicle=cl, UpperArm=sh, Forearm=el, Hand=wrist)
for k, v in {**legs, **arms}.items():
    J[f'Bip01 L {k}'] = [float(x) for x in v]; J[f'Bip01 R {k}'] = [-float(v[0]), float(v[1]), float(v[2])]
# fingers, left hand: geodesic from the wrist ring
axis = (wrist - el) / np.linalg.norm(wrist - el)
hvi = np.where(hv)[0]; rem = -np.ones(len(co), int); rem[hvi] = np.arange(len(hvi))
e = np.vstack([ht[:, [0, 1]], ht[:, [1, 2]], ht[:, [2, 0]]]); w = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[rem[e[:, 0]], rem[e[:, 1]]], np.r_[rem[e[:, 1]], rem[e[:, 0]]])), shape=(len(hvi), len(hvi))).tocsr()
seeds = rem[np.unique(bd)]; dd = dijkstra(G, indices=seeds, min_only=True)
order = np.argsort(-dd); parent = {}; birth = {}; comps = {}; tips = {}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
adj = [[] for _ in hvi]
for a, b in zip(rem[e[:, 0]], rem[e[:, 1]]): adj[a].append(b); adj[b].append(a)
done = np.zeros(len(hvi), bool); fingers = []
LONG = 0.025
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
                    if tips.get(r, 1) == 1: fingers.append((birth[r], dd[i], [hvi[q] for q in comps[r]]))
            nt = tips.get(ri, 1) + tips.get(rj, 1) if (li and lj) else max(tips.get(ri, 1), tips.get(rj, 1)) if (li or lj) else 1
            if len(comps[ri]) < len(comps[rj]): ri, rj = rj, ri
            parent[rj] = ri; comps[ri] += comps[rj]; birth[ri] = max(birth[ri], birth[rj]); tips[ri] = nt
# tips: local maxima of the geodesic distance, well down the hand
isl = np.array([dd[i] >= max([dd[j] for j in adj[i]] + [0]) for i in range(len(hvi))])
tips_ = [i for i in np.where(isl & np.isfinite(dd))[0] if co[hvi[i], 2] < wrist[2] - 0.13]
tips_ = sorted(tips_, key=lambda i: -dd[i])
sel = []
for i in tips_:
    if all(np.linalg.norm(co[hvi[i]] - co[hvi[j]]) > 0.02 for j in sel): sel.append(i)
sel = sel[:5]; print('tips', [co[hvi[i]].round(3).tolist() for i in sel], [round(float(dd[i]), 3) for i in sel])
def comp_of(i, tau):
    seen = {i}; st = [i]
    while st:
        x = st.pop()
        for y in adj[x]:
            if y not in seen and dd[y] > tau: seen.add(y); st.append(y)
    return seen
info = []
for i in sel:
    others = set(sel) - {i}; lo = None
    for tau in np.arange(dd[i] - 0.01, 0.02, -0.003):
        c_ = comp_of(i, tau)
        if c_ & others: break
        lo = tau; keepc = c_
    vs = hvi[list(keepc)]; dv = dd[list(keepc)]
    info.append(dict(tip=co[hvi[i]], base=co[vs[np.abs(dv - dv.min()) < 0.008]].mean(0), vs=vs, dv=dv, based=lo, length=dd[i] - lo))
tp_ = np.array([f['tip'] for f in info])
far = [np.linalg.norm(tp_[k] - np.delete(tp_, k, 0).mean(0)) for k in range(5)]
thumb = info[int(np.argmax(far))]; rest = [f for f in info if f is not thumb]
ctr = np.mean([f['base'] for f in rest], axis=0)
ac = ctr - thumb['base']; ac -= axis * (ac @ axis); ac /= np.linalg.norm(ac)
rest.sort(key=lambda f: f['base'] @ ac)
print('thumb tip', thumb['tip'].round(3))
labels = np.zeros(len(co), int); F = {}
for fi, f in enumerate([thumb] + rest):          # MM9: Finger0 thumb, Finger1 index .. Finger4 pinky
    vs, dv = f['vs'], f['dv']; labels[vs] = fi + 1
    a, b = dv.min(), dv.max(); LL = b - a
    def ring(t):
        m_ = np.abs(dv - (a + LL * t)) < max(0.004, LL * 0.06)
        return co[vs[m_]].mean(0)
    p1, p2, p3, tip = ring(0.02), ring(0.40), ring(0.68), f['tip']
    dirn = (p2 - p1) / np.linalg.norm(p2 - p1); p0 = p1 - dirn * (0.012 if fi else 0.02)
    F[str(fi)] = [p0.tolist(), p2.tolist(), p3.tolist(), tip.tolist()]
    print('Finger', fi, 'len', round(float(LL), 3), 'verts', len(vs), 'base', p0.round(3).tolist(), 'tip', tip.round(3).tolist())
# the thumb: thumb against palm by the nearer axis (the branch level split its surface in two and stretched it 12 x)
def seg_d(q, a, b):
    ab = b - a; t = np.clip(((q - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(q - (a + t[:, None] * ab), axis=1)
TH = np.array(F['0']); pv_ = np.where(hv & ~np.isin(labels, [2, 3, 4, 5]))[0]; q_ = co[pv_]
dt_ = np.min([seg_d(q_, TH[k], TH[k + 1]) for k in range(3)], 0)
ctr_k = np.mean([np.array(F[str(k)][0]) for k in (1, 2, 3, 4)], axis=0)
dp_ = np.min([seg_d(q_, wrist, np.array(F[str(k)][0])) for k in (1, 2, 3, 4)], 0)
labels[pv_] = np.where(dt_ < dp_ * 1.15, 1, 0); print('thumb verts', int((labels == 1).sum()))
d_, m_ = cKDTree(co * [-1, 1, 1]).query(co)
print('mirror residual hands', d_[comp == pid['hands']].max())
labels = np.maximum(labels, labels[m_])
np.save(HERE / 'work/finger_labels.npy', labels)
json.dump(dict(joints=J, fingers=F, palm_axis=axis.tolist(), across=ac.tolist(), hip_z=hip_z, mm9={k: v.tolist() for k, v in MJ.items()}), open(out, 'w'), indent=1)
