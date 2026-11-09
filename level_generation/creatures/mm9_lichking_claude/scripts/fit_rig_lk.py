"""Joints on the assembled A-pose mesh (Blender frame: faces -Y, z up). Spine heights are MM9's (LICHKING bind), neck and head on our skull;
legs from plane sections of pants and boots; arms from the axes of the upper-arm tubes and the bracers (PCA), wrist = the hand's open ring;
fingers by geodesic merge levels on the +x hand (the Evil Sorcerer's method). Writes rig.json {joints, fingers, ...} and work/finger_labels.npy.
Args: <asm npz> <mm9 glb> <out json>"""
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
lo = min(p[:, 1].min() for p, t in m.skinned_positions(w0))
MJ = {n: np.array([w0[i][0, 3], -w0[i][2, 3], w0[i][1, 3] - lo]) for i, n in enumerate(nn)}     # glTF -> Blender, soles at 0
J = {}
SPY = -0.025
for k in ('Pelvis', 'Spine', 'Spine1', 'Spine2', 'Spine3'):
    J['Bip01 ' + k] = [0.0, SPY, float(MJ['Bip01 ' + k][2])]
J['Bip01 Neck'] = [0.0, 0.005, 1.300]; J['Bip01 Head'] = [0.0, 0.0, 1.375]
pel = np.array(J['Bip01 Pelvis']); hip_z = pel[2]
# legs: knee and ankle from boot sections, hip on the pants' line
def sec(part, z, side=1):
    L = [l for l in section(co, T(part), np.array([0, 0, z]), Z) if l['c'][0] * side > 0.02 and l['per'] > 0.1]
    return max(L, key=lambda l: l['per'])['c'] if L else None
knee_z = 0.47
knee = sec('boots', knee_z)
pp = np.array([sec('pants', z) for z in (0.55, 0.6, 0.65, 0.7, 0.75)]); fit = np.polyfit(pp[:, 2], pp[:, :2], 1)
hip = np.array([*(fit[0] * hip_z + fit[1]), hip_z]); hip[1] = SPY
bp = np.array([sec('boots', z) for z in (0.15, 0.2, 0.25, 0.3)]); fb = np.polyfit(bp[:, 2], bp[:, :2], 1)
ank_z = 0.09; ank = np.array([*(fb[0] * ank_z + fb[1]), ank_z])
fv = co[comp == pid['boots']]; fv = fv[fv[:, 0] > 0]
tip_y, heel_y = fv[:, 1].min(), fv[:, 1].max(); ball_y = heel_y + (tip_y - heel_y) * 0.70
bv = fv[np.abs(fv[:, 1] - ball_y) < 0.02]; toe = np.array([bv[:, 0].mean(), ball_y, 0.02])
print('leg hip', hip.round(3), 'knee', knee.round(3), 'ankle', ank.round(3), 'toe', toe.round(3))
leg = dict(Thigh=hip, Calf=knee, Foot=ank, Toe0=toe)
# arms: PCA axes of the +x upper-arm tube and bracer
def axis(part):
    v = co[(comp == pid[part]) & (co[:, 0] > 0)]; c = v.mean(0); u = np.linalg.svd(v - c)[2][0]
    if u[2] > 0: u = -u                       # pointing down the arm
    t = (v - c) @ u; return c, u, t.min(), t.max()
cu, uu, u0, u1 = axis('uarms'); cb, ub, b0, b1 = axis('bracers')
sh = cu + uu * (u0 + 0.045)
EL_Z = 1.045                              # just above the bracer's top: forearm 0.24, upper arm 0.27 (MM9 0.223 / 0.296)
el = cu + uu * ((EL_Z - cu[2]) / uu[2])
ht = T('hands'); ht = ht[co[ht[:, 0], 0] > 0]
e = np.sort(np.vstack([ht[:, [0, 1]], ht[:, [1, 2]], ht[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True); bd = u[c == 1]
wrist = co[np.unique(bd)].mean(0)
print('shoulder', sh.round(3), 'elbow', el.round(3), 'wrist', wrist.round(3), 'upper', round(float(np.linalg.norm(el - sh)), 3), 'fore', round(float(np.linalg.norm(wrist - el)), 3),
      'MM9', round(float(np.linalg.norm(MJ['Bip01 L Forearm'] - MJ['Bip01 L UpperArm'])), 3), round(float(np.linalg.norm(MJ['Bip01 L Finger0'] - MJ['Bip01 L Forearm'])), 3))
cl = MJ['Bip01 L Clavicle']
arms = dict(Clavicle=np.array([abs(cl[0]), 0.0, 1.27]), UpperArm=sh, Forearm=el, Hand=wrist)
for k, v in {**leg, **arms}.items():
    J[f'Bip01 R {k}'] = v.tolist(); J[f'Bip01 L {k}'] = [-float(v[0]), float(v[1]), float(v[2])]    # raw ABC space: L at -x; mirror_glb.py makes it true-handed last
# fingers, left hand: geodesic from the wrist ring
axis_ = (wrist - el) / np.linalg.norm(wrist - el)
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
ac = ctr - thumb['base']; ac -= axis_ * (ac @ axis_); ac /= np.linalg.norm(ac)
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
pfz = co[comp == pid['tabard']]
json.dump(dict(joints=J, panel_y=dict(F=float(pfz[:, 1].mean())), fingers=F, palm_axis=axis_.tolist(), across=ac.tolist(), palm=palm.tolist(), hip_z=hip_z, mm9={k: v.tolist() for k, v in MJ.items()}), open(out, 'w'), indent=0)
print('RIG written')
