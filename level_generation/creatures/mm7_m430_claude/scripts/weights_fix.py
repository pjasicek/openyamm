"""m430 weight rules, applied to the Meshy-transferred weights right after build_rig.py (before the twist bones split
the arm weights). The robe, head and hair are ONE connected piece (P00) with the legs hidden inside, so:
- head/neck/hair (above the shoulder line near the axis, or weighted mostly to head/neck): Meshy's weights, limited to
  B_Head, B_Neck, B_Spine2;
- sleeves: a robe vertex is a sleeve vertex when it lies closer to its arm's bone segments (shoulder-elbow-wrist,
  extended along the hanging torn strips) than to the trunk axis; it takes Meshy's weights limited to that arm's
  clavicle, upper arm, forearm and hand plus B_Spine2, so a hanging strip never takes the leg or pelvis weight it lies
  next to (batch note: no weight across a gap);
- upper robe (above the hip joints): Meshy's weights without leg and arm weight (moved to B_Pelvis / the clavicle);
- skirt (below the hip joints): a dress: B_Pelvis at the hips blending to LEG_MAX of leg weight at the hem, the leg
  share split left/right by ONE smooth function of x (no seam between the legs) and thigh/calf by height;
- hands (P01 left, P02 right): Meshy's weights limited to their own arm (fingers come in finger_weights.py);
- cord strands and inner hem: the mean weights of the nearest robe vertices (rigid per strand / per vertex copy).
Then the robe is smoothed 3 passes along its edges. Prints a gap check (arm weight off the sleeves/hands, leg weight
off the skirt). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
LEG_MAX = float(os.environ.get('LEG_MAX', '0.45'))   # 0.6 lifted the hem ~10 cm in the walk
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
J = lambda n: np.array(rig.data.bones[n].head_local)
idx = lambda keys: [gi[n] for n in names if any(k in n for k in keys)]
ARM = {s: idx((f'B_{s}_Clavicle', f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand', f'B_{s}_Finger')) for s in 'LR'}
ARMNC = {s: idx((f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand', f'B_{s}_Finger')) for s in 'LR'}
LEG = {s: idx((f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot', f'B_{s}_Toe')) for s in 'LR'}
HEADB = [gi['B_Head'], gi['B_Neck'], gi['B_Spine2']]


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def seg_dist(p, a, b):
    d = b - a; t = np.clip(((p - a) @ d) / (d @ d), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, d)), axis=1)


def keep(rows, cols):
    W = np.zeros((len(rows), len(names))); W[:, cols] = Wt[np.ix_(rows, cols)]
    s = W.sum(1); return W / np.maximum(s, 1e-9)[:, None], s < 1e-6


NEW = Wt.copy()
robe = np.where(pv == 0)[0]
P = co[robe]
zh = J('B_L_Thigh')[2]; zsh = (J('B_L_UpperArm')[2] + J('B_R_UpperArm')[2]) / 2
# sleeves by GEODESIC distance over the robe's edges (a strip hangs from its sleeve, the skirt's flank beside it is
# reached from the trunk): seeds on each forearm (robe within 7 cm of elbow-wrist) and along the trunk axis (robe
# within 10 cm of the vertical centre line between the hem and the shoulders); each vertex takes its nearest seed set
import heapq
E2 = np.array([tuple(e.vertices) for e in me.edges]); inrobe = np.zeros(nv, bool); inrobe[robe] = True
E2 = E2[inrobe[E2[:, 0]] & inrobe[E2[:, 1]]]
adj = {}
for a_, b_ in E2:
    L_ = float(np.linalg.norm(co[a_] - co[b_])); adj.setdefault(a_, []).append((b_, L_)); adj.setdefault(b_, []).append((a_, L_))


def geodesic(seeds):
    dist = np.full(nv, np.inf); h = [(0.0, int(i)) for i in seeds]
    for _, i in h:
        dist[i] = 0.0
    heapq.heapify(h)
    while h:
        d, i = heapq.heappop(h)
        if d > dist[i]:
            continue
        for j, L_ in adj.get(i, ()):
            if d + L_ < dist[j]:
                dist[j] = d + L_; heapq.heappush(h, (d + L_, j))
    return dist[robe]


axis_xy = np.array([0.0, J('B_Pelvis')[1]])
trunk_seed = robe[(np.linalg.norm(P[:, :2] - axis_xy, axis=1) < 0.10) & (P[:, 2] < zsh - 0.05)]
D = {'T': geodesic(trunk_seed)}
for s in 'LR':
    D[s] = geodesic(robe[seg_dist(P, J(f'B_{s}_Forearm'), J(f'B_{s}_Hand')) < 0.07])
sleeve = {s: (D[s] < D['T']) & (D[s] < D['RL'.replace(s, '')]) for s in 'LR'}
print('RULE seeds trunk', len(trunk_seed))
head = (P[:, 2] > zsh + 0.02) & ~sleeve['L'] & ~sleeve['R']
nf = 0
for s in 'LR':
    rows = robe[sleeve[s]]
    W, z = keep(rows, ARM[s] + [gi['B_Spine2']]); W[z, gi[f'B_{s}_UpperArm']] = 1; NEW[rows] = W; nf += int(z.sum())
rows = robe[head]
W, z = keep(rows, HEADB); W[z, gi['B_Head']] = 1; NEW[rows] = W
body_ = ~head & ~sleeve['L'] & ~sleeve['R']
up = robe[body_ & (P[:, 2] >= zh)]
W = Wt[up].copy()
for s in 'LR':
    W[:, gi['B_Pelvis']] += W[:, LEG[s]].sum(1); W[:, LEG[s]] = 0
    a = W[:, ARMNC[s]].sum(1); W[:, gi[f'B_{s}_Clavicle']] += a; W[:, ARMNC[s]] = 0
NEW[up] = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
lo = robe[body_ & (P[:, 2] < zh)]
Q = co[lo]; depth = ss((zh - Q[:, 2]) / max(zh - 0.05, 1e-3))
leg = depth * LEG_MAX
wl = ss((Q[:, 0] + 0.12) / 0.24)                       # one smooth left/right mix across the front and back
kz = J('B_L_Calf')[2]; calf = ss((kz + 0.1 - Q[:, 2]) / 0.3) * 0.4
W = np.zeros((len(lo), len(names)))
W[:, gi['B_Pelvis']] = 1 - leg
for s, w in (('L', wl), ('R', 1 - wl)):
    W[:, gi[f'B_{s}_Thigh']] = leg * w * (1 - calf); W[:, gi[f'B_{s}_Calf']] = leg * w * calf
NEW[lo] = W
print('RULE robe vertices: sleeves', int(sleeve['L'].sum()), int(sleeve['R'].sum()), 'head', int(head.sum()),
      'upper', len(up), 'skirt', len(lo), 'sleeve vertices without arm weight', nf)
for s, p in (('L', 1), ('R', 2)):
    rows = np.where(pv == p)[0]; W, z = keep(rows, ARMNC[s]); W[z, gi[f'B_{s}_Hand']] = 1; NEW[rows] = W
    print('RULE hand', s, 'vertices without arm weight', int(z.sum()))
# smooth the robe along its own edges (keeps sleeves on arms: neighbours are sleeve vertices too): 3 passes
# everywhere, then SEAM_PASSES more around the shoulders (within SEAM_R 25 cm of a shoulder joint: the armpit sits 22 cm below it), where the hard
# sleeve/trunk boundary stretched the armpit up to 8x with the arm overhead (G4, first build)
SEAM_PASSES = int(os.environ.get('SEAM_PASSES', '12'))
edges = np.array([tuple(e.vertices) for e in me.edges])
rb = pv == 0; E = edges[rb[edges[:, 0]] & rb[edges[:, 1]]]
near_sh = rb & (np.minimum(np.linalg.norm(co - J('B_L_UpperArm'), axis=1), np.linalg.norm(co - J('B_R_UpperArm'), axis=1)) < float(os.environ.get('SEAM_R', '0.25')))
for it in range(3 + SEAM_PASSES):
    sel = rb if it < 3 else near_sh
    acc = NEW.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], NEW[E[:, 1]]); np.add.at(acc, E[:, 1], NEW[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    NEW[sel] = (acc / deg[:, None])[sel]
# cord strands rigid on the mean of the nearest robe weights; inner hem per vertex
kd = KDTree(len(robe))
for i, r in enumerate(robe):
    kd.insert(co[r], i)
kd.balance()
for p in sorted(set(pv.tolist()) - {0, 1, 2}):
    rows = np.where(pv == p)[0]
    C = np.array([np.mean([NEW[robe[j]] for _, j, _ in kd.find_n(co[i], 6)], 0) for i in rows])
    NEW[rows] = np.tile(C.mean(0), (len(rows), 1)) if p in (3, 4) else C
NEW /= np.maximum(NEW.sum(1, keepdims=True), 1e-9)
ARMB = idx(('UpperArm', 'Forearm', 'Hand', 'Finger')); LEGB = idx(('Thigh', 'Calf', 'Foot', 'Toe'))
skirt = np.zeros(nv, bool); skirt[lo] = True; skirt |= np.isin(pv, (3, 4, 5))
armok = np.zeros(nv, bool); armok[robe[sleeve['L'] | sleeve['R']]] = True; armok |= np.isin(pv, (1, 2))
print('G4GAP arm weight > 0.05 off the sleeves/hands', int(((NEW[:, ARMB].sum(1) > 0.05) & ~armok).sum()),
      'leg weight > 0.05 off the skirt', int(((NEW[:, LEGB].sum(1) > 0.05) & ~skirt).sum()))
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(NEW[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(NEW[i, j]), 'REPLACE')
# a check render: vertex colours by group class (arm red/blue by side, legs green, head yellow, trunk grey)
ca = me.color_attributes.new('wcol', 'FLOAT_COLOR', 'POINT')
for i in range(nv):
    c = np.array([0.6, 0.6, 0.6]) * NEW[i, [gi['B_Pelvis'], gi['B_Spine'], gi['B_Spine1'], gi['B_Spine2']]].sum()
    c += np.array([0.9, 0.2, 0.2]) * NEW[i, ARM['L']].sum() + np.array([0.2, 0.3, 0.95]) * NEW[i, ARM['R']].sum()
    c += np.array([0.2, 0.85, 0.3]) * NEW[i, LEGB].sum() + np.array([0.95, 0.85, 0.2]) * NEW[i, [gi['B_Head'], gi['B_Neck']]].sum()
    ca.data[i].color = (*np.clip(c, 0, 1), 1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
