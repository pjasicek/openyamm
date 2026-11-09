"""Joints on the assembled A-pose mesh (raw ABC space, Blender frame: faces -Y, z up, figure's L at -x).
Spine heights are MM9's, centred on our torso sections; legs and arms by plane sections of the body part; wrist at the
narrowest ring before the hand; fingers by geodesic merge levels on the hand (from mm9_evilsorcerer_claude/fit_rig.py).
Writes the rig json {joints, fingers, palm, mm9} and work/finger_labels.npy. Args: <asm npz> <mm9 glb> <out json>"""
import sys, json
import numpy as np
from pathlib import Path
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
from meshlib import section, nearest_loop
from mm9_mesh import load
npz, mm9, out = sys.argv[1:4]
D = np.load(npz); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
pid = {n: i for i, n in enumerate(names)}
body_t = tri[comp[tri[:, 0]] == pid['body']]
X, Y, Z = np.eye(3)
MJ = load(mm9)['J']
J = {}
# spine: MM9 heights, y centre of our torso section (|x| < 0.2 loop nearest the axis)
for k in ('Pelvis', 'Spine', 'Spine1', 'Spine2', 'Spine3', 'Neck', 'Head'):
    z = MJ['Bip01 ' + k][2]
    L = [l for l in section(co, body_t, np.array([0, 0, z]), Z) if abs(l['c'][0]) < 0.05]
    l = max(L, key=lambda q: q['per']) if L else None
    J['Bip01 ' + k] = [0.0, float(l['c'][1]) if l else None, float(z)]
    print(k, round(z, 3), None if l is None else (round(l['c'][1], 3), round(l['per'], 3)))
if J['Bip01 Pelvis'][1] is None: J['Bip01 Pelvis'][1] = J['Bip01 Spine'][1]
# head pivot: our skull base; neck centre from the neck section
for k in ('Neck', 'Head'):
    if J['Bip01 ' + k][1] is None: J['Bip01 ' + k][1] = J['Bip01 Spine3'][1]
# legs (the figure's R = +x half; L mirrored)
crotch = None
for z in np.arange(0.2, -0.3, -0.005):
    L = [l for l in section(co, body_t, np.array([0, 0, z]), Z) if l['per'] > 0.1 and abs(l['c'][0]) < 0.4]
    if len(L) == 2: crotch = z; break
print('crotch', crotch)
pts = []
for z in np.arange(crotch - 0.03, -0.74, -0.02):
    L = [q for q in section(co, body_t, np.array([0, 0, z]), Z) if q['c'][0] > 0.03 and q['c'][0] < 0.4]
    if L: pts.append(min(L, key=lambda q: q['per'])['c'] if z < -0.5 else max(L, key=lambda q: q['per'])['c'])
pts = np.array(pts)
hip = np.array([abs(MJ['Bip01 R Thigh'][0]) + 0.012, J['Bip01 Pelvis'][1], MJ['Bip01 R Thigh'][2]])
leg_line = np.vstack([hip, pts])
seg = np.linalg.norm(np.diff(leg_line, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
# knee and ankle at MM9's ratios of the hip -> ankle length; ankle height MM9's
ank_z = MJ['Bip01 R Foot'][2] + 0.0
fit = np.polyfit(pts[-5:, 2], pts[-5:, :2], 1); ank = np.array([*(fit[0] * ank_z + fit[1]), ank_z])
mm_th = np.linalg.norm(MJ['Bip01 R Calf'] - MJ['Bip01 R Thigh']); mm_cf = np.linalg.norm(MJ['Bip01 R Foot'] - MJ['Bip01 R Calf'])
line = np.vstack([hip, pts[pts[:, 2] > ank_z], ank]); seg = np.linalg.norm(np.diff(line, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
kk = s[-1] * mm_th / (mm_th + mm_cf)
knee = np.array([np.interp(kk, s, line[:, i]) for i in range(3)])
# toe: ball of the foot (shoe front), MM9's toe height
fv = co[(comp == pid['body']) & (co[:, 2] < -0.70) & (co[:, 0] > 0.03)]
tip_y, heel_y = fv[:, 1].min(), fv[:, 1].max(); ball_y = heel_y + (tip_y - heel_y) * 0.72
bv = fv[np.abs(fv[:, 1] - ball_y) < 0.02]; toe = np.array([bv[:, 0].mean(), ball_y, MJ['Bip01 R Toe0'][2] + 0.0])
print('leg hip', hip.round(3), 'knee', knee.round(3), 'ankle', ank.round(3), 'toe', toe.round(3), 'len', round(s[-1], 3), 'MM9', round(mm_th + mm_cf, 3))
leg = dict(Thigh=hip, Calf=knee, Foot=ank, Toe0=toe)
# right arm: march from the shoulder down the arm
d = np.array([0.068, 0.03, -0.10]); d /= np.linalg.norm(d)
p = np.array([0.215, 0.085, 0.545]); arm = []
for i in range(80):
    L = [q for q in section(co, body_t, p, d) if np.linalg.norm(q['c'] - p) < 0.07]
    l = min(L, key=lambda q: np.linalg.norm(q['c'] - p)) if L else None
    if l is None: print('arm stop', i, p.round(3)); break
    arm.append((*l['c'], l['per']))
    if len(arm) > 3:
        nd = np.array(arm[-1][:3]) - np.array(arm[-4][:3]); nd /= np.linalg.norm(nd); d = 0.7 * d + 0.3 * nd; d /= np.linalg.norm(d)
    p = l['c'] + d * 0.012
arm = np.array(arm)
per = arm[:, 3]
print('arm perims', per[::3].round(3).tolist())
# wrist: smallest ring in the last part of the arm before the hand widens
n = len(arm); i0 = int(n * 0.4)
ipalm = i0 + int(np.argmax(np.where(per[i0:] > 0.1, per[i0:], 0)))
iw = i0 + int(np.argmin(per[i0:ipalm])); wrist = arm[iw, :3]
print('wrist ring', iw, 'palm ring', ipalm, per[iw].round(3), per[ipalm].round(3))
sh = np.array([abs(MJ['Bip01 R UpperArm'][0]) + 0.012, arm[0, 1], arm[0, 2] + 0.0])
# shoulder: on the arm line extrapolated back to MM9's shoulder x
dir0 = arm[0, :3] - arm[4, :3]; dir0 /= np.linalg.norm(dir0)
sh = arm[0, :3] + dir0 * ((arm[0, 0] - (abs(MJ['Bip01 R UpperArm'][0]) + 0.01)) / max(abs(dir0[0]), .1))
poly = np.vstack([sh, arm[:iw + 1, :3]]); seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
ua, fa = np.linalg.norm(MJ['Bip01 R Forearm'] - MJ['Bip01 R UpperArm']), np.linalg.norm(MJ['Bip01 R Hand'] - MJ['Bip01 R Forearm'])
ek = s[-1] * ua / (ua + fa); el = np.array([np.interp(ek, s, poly[:, i]) for i in range(3)])
print('shoulder', sh.round(3), 'elbow', el.round(3), 'wrist', wrist.round(3), 'arm', round(s[-1], 3), 'MM9', round(ua + fa, 3))
cl = MJ['Bip01 R Clavicle']
arms = dict(Clavicle=np.array([abs(cl[0]), J['Bip01 Neck'][1], cl[2]]), UpperArm=sh, Forearm=el, Hand=wrist)
for k, v in {**leg, **arms}.items():
    J[f'Bip01 R {k}'] = v.tolist(); J[f'Bip01 L {k}'] = [-float(v[0]), float(v[1]), float(v[2])]
# fingers on the right hand: vertices past the wrist plane
axis = (wrist - el) / np.linalg.norm(wrist - el)
hand = (comp == pid['body']) & ((co - wrist) @ axis > -0.005) & (np.linalg.norm(co - wrist, axis=1) < 0.30) & (co[:, 0] > 0.1)
hv = np.where(hand)[0]; rem = -np.ones(len(co), int); rem[hv] = np.arange(len(hv))
tt = tri[hand[tri].all(1)]
e = np.vstack([tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]]); w = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[rem[e[:, 0]], rem[e[:, 1]]], np.r_[rem[e[:, 1]], rem[e[:, 0]]])), shape=(len(hv), len(hv))).tocsr()
ring = hv[np.abs((co[hv] - wrist) @ axis) < 0.006]
seeds = rem[ring]; dd = dijkstra(G, indices=seeds, min_only=True)
order = np.argsort(-dd); parent = {}; birth = {}; comps = {}; tips = {}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
adj = [[] for _ in hv]
for a, b in zip(rem[e[:, 0]], rem[e[:, 1]]): adj[a].append(b); adj[b].append(a)
done = np.zeros(len(hv), bool); fingers = []
LONG = 0.02
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
    a, b = dv.min(), dv.max(); Lf = b - a
    def ringp(t):
        m_ = np.abs(dv - (a + Lf * t)) < max(0.004, Lf * 0.06)
        return co[vs[m_]].mean(0)
    p1, p2, p3, tip = ringp(0.02), ringp(0.40), ringp(0.72), f['tip']
    dirn = (p2 - p1) / np.linalg.norm(p2 - p1); p0 = p1 - dirn * (0.012 if nm != 'Thumb' else 0.02)
    F[nm] = [p0.tolist(), p2.tolist(), p3.tolist(), tip.tolist()]
    print(nm, 'len', round(float(Lf), 3), 'verts', len(vs), 'base', p0.round(3).tolist(), 'tip', tip.round(3).tolist())
# mirror finger labels to the left hand
d_, m_ = cKDTree(co * [-1, 1, 1]).query(co)
labels = np.maximum(labels, labels[m_])
np.save(HERE / 'work/finger_labels.npy', labels)
palm = np.cross(thumb['base'] - wrist, ctr - wrist); palm /= np.linalg.norm(palm)
json.dump(dict(joints=J, fingers=F, palm_axis=axis.tolist(), across=ac.tolist(), palm=palm.tolist(), crotch=crotch,
               mm9={k: v.tolist() for k, v in MJ.items()}), open(out, 'w'), indent=0)
print('RIG', out)
