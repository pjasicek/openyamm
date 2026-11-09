"""Final joints on the symmetric master-pose mesh (work/joined.npz), Blender frame (faces -Y, z up). Limb axes by plane sections, fingers from geodesic merge levels.
Writes work/rig.json {joints: {name: xyz}, parents..., fingers: {...}} and work/finger_labels.npy (per vertex: 0 none, 1..5 finger on either hand).
Args: <npz> <out json>"""
import sys, json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from meshlib import section, nearest_loop
npz, out = sys.argv[1:3]
D = np.load(npz); co, tri, head = D['co'], D['tri'], D['head']
tri_b = tri[head == 0]
X, Y, Z = np.eye(3)
def loop(p, n):
    return nearest_loop(section(co, tri_b, np.asarray(p, float), np.asarray(n, float)), np.asarray(p, float))
J = {}
crotch = None
for z in np.arange(1.2, 0.6, -0.005):
    L = [l for l in section(co, tri_b, np.array([0, 0, z]), Z) if l['per'] > 0.1]
    if len(L) == 2: crotch = z; break
hip_z = crotch + 0.085
pel = loop((0, 0, hip_z), Z)['c']
print('crotch', crotch, 'pelvis', pel)
neck_z, head_z = 1.585, 1.625
ratios = dict(Pelvis=0, Spine=.161, Spine1=.345, Spine2=.528, Spine3=.711, Neck=.894, Head=1.0)
for k, r in ratios.items():
    z = hip_z + (head_z - hip_z) * r
    l = loop((0, pel[1], z), Z)
    y = l['c'][1] if l is not None and abs(l['c'][0]) < 0.03 else pel[1]
    J['Bip01 ' + k] = [0.0, float(y), float(z)]
J['Bip01 Head'][1] = J['Bip01 Neck'][1]
# left leg, mirrored
pts = []
for z in np.arange(crotch - 0.03, 0.12, -0.02):
    l = nearest_loop([q for q in section(co, tri_b, np.array([0, 0, z]), Z) if q['c'][0] < 0], np.array([-(0.11 + (crotch - z) * .25), 0, z]))
    pts.append(l['c'])
pts = np.array(pts)
hip = np.array([-0.085, pel[1], hip_z])
fit = np.polyfit(pts[-8:, 2], pts[-8:, :2], 1); ank_z = 0.105
ank = np.array([*(fit[0] * ank_z + fit[1]), ank_z])
poly = np.vstack([hip, pts, ank]); seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
knee = np.array([np.interp(s[-1] / 2, s, poly[:, i]) for i in range(3)])
fv = co[(co[:, 2] < 0.1) & (co[:, 0] < 0)]
tip_y, heel_y = fv[:, 1].min(), fv[:, 1].max()
ball_y = heel_y + (tip_y - heel_y) * 0.70
bv = fv[np.abs(fv[:, 1] - ball_y) < 0.02]
toe = np.array([bv[:, 0].mean(), ball_y, 0.025])
leg = dict(Thigh=hip, Calf=knee, Foot=ank, Toe0=toe)
print('leg', {k: v.round(3).tolist() for k, v in leg.items()}, 'len', s[-1].round(3), 'heel', heel_y, 'tip', tip_y)
# left arm from the known bend points: march along the upper arm
d = np.array([-np.cos(np.radians(40)), -0.03, -np.sin(np.radians(40))]); d /= np.linalg.norm(d)
p = np.array([-0.30, 0.0, 1.40]); arm = []
l0 = None
# march outward to the wrist
for i in range(80):
    l = nearest_loop(section(co, tri_b, p, d), p)
    if l is None or np.linalg.norm(l['c'] - p) > 0.06: print('stop', i); break
    arm.append((*l['c'], l['per']))
    if len(arm) > 3:
        nd = np.array(arm[-1][:3]) - np.array(arm[-4][:3]); nd /= np.linalg.norm(nd); d = 0.7 * d + 0.3 * nd; d /= np.linalg.norm(d)
    p = l['c'] + d * 0.01
arm = np.array(arm)
for a in arm[::3]: print('  arm', a.round(3).tolist())
np.save(out.replace('rig.json', 'armline.npy'), arm)
# wrist: smallest perimeter before the palm widens
iw = None
idx = [i for i in range(5, len(arm) - 2) if arm[i, 3] < arm[i - 3, 3] and arm[i, 3] < arm[i + 2, 3]]
print('min per idx', idx)
per = arm[:, 3]
wi = 24 + int(np.argmin(per[24:36]))
wrist = arm[wi, :3]
print('wrist', wi, wrist.round(3), per[wi].round(3))
upper_dir = arm[0, :3] - arm[6, :3]; upper_dir /= np.linalg.norm(upper_dir)
sh = arm[0, :3] + upper_dir * ((abs(arm[0, 0]) - 0.175) / abs(upper_dir[0]))
lenarm = np.linalg.norm(wrist - sh)
# elbow: MM9's ratio along the line, on the centre line
el_t = 0.559
poly = np.vstack([sh, arm[:wi + 1, :3]]); seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
el = arm[12, :3].copy()    # the bend of the Meshy arm (step2_sym.py)
print('shoulder', sh.round(3), 'elbow', el.round(3), 'wrist', wrist.round(3), 'arm', s[-1].round(3), 'MM9 .477')
nk = np.array(J['Bip01 Neck'])
arms = dict(Clavicle=np.array([-0.035, nk[1], nk[2]]), UpperArm=sh, Forearm=el, Hand=wrist)
for k, v in {**leg, **arms}.items():
    J[f'Bip01 L {k}'] = v.tolist(); J[f'Bip01 R {k}'] = [-float(v[0]), float(v[1]), float(v[2])]
# fingers, left hand, geodesic from the wrist on the body vertices beyond the wrist plane
axis = (wrist - el) / np.linalg.norm(wrist - el)
bverts = np.unique(tri_b)
isb = np.zeros(len(co), bool); isb[bverts] = True
hand = isb & (((co - wrist) @ axis) > -0.002) & (co[:, 0] < -0.3)
hv = np.where(hand)[0]; rem = -np.ones(len(co), int); rem[hv] = np.arange(len(hv))
tt = tri_b[hand[tri_b].all(1)]
e = np.vstack([tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]]); w = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[rem[e[:, 0]], rem[e[:, 1]]], np.r_[rem[e[:, 1]], rem[e[:, 0]]])), shape=(len(hv), len(hv))).tocsr()
seeds = np.where(np.abs((co[hv] - wrist) @ axis) < 0.012)[0]
dd = dijkstra(G, indices=seeds, min_only=True)
# union-find top-down
order = np.argsort(-dd); parent = {}; birth = {}; comps = {}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
adj = [[] for _ in hv]
for a, b in zip(rem[e[:, 0]], rem[e[:, 1]]): adj[a].append(b); adj[b].append(a)
done = np.zeros(len(hv), bool); fingers = []; tips = {}
for i in order:
    if not np.isfinite(dd[i]): continue
    parent[i] = i; birth[i] = dd[i]; comps[i] = [i]; done[i] = True
    for j in adj[i]:
        if done[j] and j in parent:
            ri, rj = find(i), find(j)
            if ri == rj: continue
            long_i = birth[ri] - dd[i] > 0.035; long_j = birth[rj] - dd[i] > 0.035
            if long_i and long_j:
                for r in (ri, rj):
                    if tips.get(r, 1) == 1: fingers.append((birth[r], dd[i], [hv[q] for q in comps[r]]))
            nt = tips.get(ri, 1) + tips.get(rj, 1) if (long_i and long_j) else max(tips.get(ri, 1), tips.get(rj, 1)) if (long_i or long_j) else 1
            if len(comps[ri]) < len(comps[rj]): ri, rj = rj, ri
            parent[rj] = ri; comps[ri] += comps[rj]; birth[ri] = max(birth[ri], birth[rj]); tips[ri] = nt
# keep the five longest distinct (merged comps can report a partial)
fingers.sort(key=lambda f: -len(f[2]))
keep = []
for f in fingers:
    s_ = set(f[2])
    if any(len(s_ & set(k[2])) > 0.5 * len(s_) for k in keep): continue
    keep.append(f)
print('finger candidates', [(round(f[0], 3), round(f[1], 3), len(f[2])) for f in keep[:8]])
keep = keep[:5]
# order by position across the hand; thumb = the one with the base closest to the wrist
info = []
for tipd, based, vs in keep:
    vs = np.array(vs); q = co[vs]; dv = dd[rem[vs]]
    tip = q[dv.argmax()]
    base = q[np.abs(dv - dv.min()) < 0.006].mean(0)
    info.append(dict(tip=tip, base=base, vs=vs, dv=dv, based=based, length=tipd - based))
thumb = min(info, key=lambda f: f['based'])
rest = [f for f in info if f is not thumb]
# across-hand axis from the thumb side to the others
ctr = np.mean([f['base'] for f in rest], axis=0)
ac = ctr - thumb['base']; ac -= axis * (ac @ axis); ac /= np.linalg.norm(ac)
rest.sort(key=lambda f: f['base'] @ ac)
names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']; labels = np.zeros(len(co), int); F = {}
palm_c = np.mean([f['base'] for f in rest], axis=0)
for fi, (nm, f) in enumerate(zip(names, [thumb] + rest), 1):
    vs, dv = f['vs'], f['dv']
    labels[vs] = fi
    a, b = dv.min(), dv.max()
    base = f['base']; L = b - a
    # chain: ring centroids by distance; back the first joint 1.2 cm into the palm
    def ring(t):
        m = np.abs(dv - (a + L * t)) < max(0.004, L * 0.06)
        return co[vs[m]].mean(0)
    p1 = ring(0.02); p2 = ring(0.40); p3 = ring(0.72); tip = f['tip']
    dirn = (p2 - p1) / np.linalg.norm(p2 - p1)
    p0 = p1 - dirn * (0.012 if nm != 'Thumb' else 0.02)
    F[nm] = [p0.tolist(), p2.tolist(), p3.tolist(), tip.tolist()]
    print(nm, 'len', round(float(L), 3), 'verts', len(vs), 'base', p0.round(3).tolist(), 'tip', tip.round(3).tolist())
# mirrored labels
mirror = np.zeros(len(co), int)
from scipy.spatial import cKDTree
tree = cKDTree(co * [-1, 1, 1])
d, m = tree.query(co)
print('mirror residual max', d[isb].max())
labels = np.maximum(labels, labels[m])
np.save(out.replace('rig.json', 'finger_labels.npy'), labels)
pn = np.cross(thumb['base'] - wrist, ctr - wrist)
json.dump(dict(joints=J, fingers=F, palm_axis=axis.tolist(), across=ac.tolist(), hip_z=hip_z, crotch=crotch), open(out, 'w'), indent=0)
