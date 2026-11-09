"""Step A: Meshy body on the MM9 bind pose (true handedness). Each limb segment maps its own estimated joints onto MM9's (rotation + stretch along the bone), a transient
smooth label blends the affine maps (fit_imp.py, zombie fit_pose.py). The flaps (open sheets hanging from the belt) are found by connectivity below the belt and stay on the
pelvis map. Bracer edge strips are dropped. Then the whole body is mirrored over x = 0 from the near side of the 3/4 master (MM9 is symmetric), and the head cut at the neck.
Parts: 0 skin, 2 hair sheet on the back, 3 belt studs and plate, 6 front flap, 7 back flap. Args: <meshy glb> <mm9 true glb> <config> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
MESHY, MM9, CFG, OUT = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name.replace('Bip01 ', ''): np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
dg = bpy.context.evaluated_depsgraph_get()
A = []
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.startswith('Icosphere'):
        me = o.evaluated_get(dg).to_mesh(); A += [tuple(o.matrix_world @ v.co) for v in me.vertices]
A = np.array(A)
exist = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in exist]
body = next(o for o in new if o.type == 'MESH')
Mw = body.matrix_world.copy()
for o in new:
    if o is not body: bpy.data.objects.remove(o)
body.parent = None; body.matrix_world = Mw; body.name = 'Body'
for o in bpy.data.objects:
    if o is not body: bpy.data.objects.remove(o, do_unlink=True)
me = body.data
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.to_mesh(me); bm.free()
P0 = np.array([tuple(v.co) for v in me.vertices])
n = len(P0)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)


def comps(mask):
    c = -np.ones(n, int); k = 0
    for i in np.nonzero(mask)[0]:
        if c[i] >= 0: continue
        st = [i]; c[i] = k
        while st:
            x = st.pop()
            for y in nbr[x]:
                if mask[y] and c[y] < 0: c[y] = k; st.append(y)
        k += 1
    return c, k


comp, c_ = comps(np.ones(n, bool))
sizes = np.bincount(comp)
main = int(np.argmax(sizes))
PART = np.zeros(n, int)
drop = np.zeros(n, bool)
for c in range(c_):
    if c == main: continue
    q = P0[comp == c]
    cen = q.mean(0)
    if sizes[c] > 150 and cen[1] > 0: PART[comp == c] = 2                # hair sheet
    elif cen[2] > 0.34: PART[comp == c] = 3                               # Meshy's teeth, eyes: cut below with the head
    elif abs(cen[0]) > 0.2: drop[comp == c] = True                        # bracer edge strips
    else: PART[comp == c] = 3                                             # belt studs, plate
# flaps: open sheets over the closed body. Below the crotch their surface is its own component; higher up a vertex of a sheet has the body right behind it along y,
# while the body's own front surface looks through the whole torso
low = (comp == main) & (P0[:, 2] < cfg['flap_cut_z'])
cl, k = comps(low)
s = np.bincount(cl[cl >= 0])
big = int(np.argmax(s))
ymid = 0.033
for c in range(k):
    if c == big or s[c] < 8: continue
    q = P0[cl == c]
    print('FLAP comp', s[c], q.min(0).round(3), q.max(0).round(3))
    PART[cl == c] = 6 if q[:, 1].mean() < ymid else 7
from mathutils.bvhtree import BVHTree
tree = BVHTree.FromPolygons([tuple(v) for v in P0], [tuple(p.vertices) for p in me.polygons])
for i in np.nonzero((comp == main) & (np.abs(P0[:, 0]) < 0.095) & (P0[:, 2] > -0.11) & (P0[:, 2] < 0.125) & (PART == 0))[0]:
    y = P0[i, 1]; dir_ = 1 if y < ymid else -1
    o = Vector(P0[i]) + Vector((0, dir_ * 1e-4, 0))
    # stay out of the sheet's own faces: start just past the vertex
    hit = tree.ray_cast(o, Vector((0, dir_, 0)), 0.024)
    if hit[0] is not None and abs(y - ymid) > 0.018 and (hit[3] > 2e-4):
        PART[i] = 6 if dir_ > 0 else 7
print('PARTS', {int(k): int((PART == k).sum()) for k in np.unique(PART)}, 'comps', c_, 'dropped', int(drop.sum()))
# scale and centre as the zombie's fit, the estimates with it
sc_ = np.ptp(A[:, 2]) / np.ptp(P0[:, 2])
P = P0 * sc_
dz = A[:, 2].min() - P[:, 2].min()
P[:, 2] += dz
m = (P[:, 2] > 0.0) & (P[:, 2] < 0.4) & (np.abs(P[:, 0]) < 0.12); ma = (A[:, 2] > 0.0) & (A[:, 2] < 0.4) & (np.abs(A[:, 0]) < 0.12)
dy = 0.5 * (A[ma, 1].min() + A[ma, 1].max()) - 0.5 * (P[m, 1].min() + P[m, 1].max())
P[:, 1] += dy
dx = -0.5 * (P[:, 0].min() + P[:, 0].max()) + 0.5 * (A[:, 0].min() + A[:, 0].max())
P[:, 0] += dx
E = {k: np.array(v) * sc_ + np.array([dx, dy, dz]) for k, v in cfg['estimates_raw'].items()}
print('scale', sc_, 'dz', dz, 'dy', dy, 'dx', dx)


def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); sn = np.linalg.norm(v)
    if sn < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / sn ** 2)


def seg_map(ea, eb, ja, jb):
    u = eb - ea; L = np.linalg.norm(u); u = u / L
    k = np.linalg.norm(jb - ja) / L
    Rm = rot(u, jb - ja)
    S = np.eye(3) + (k - 1) * np.outer(u, u)
    A_ = Rm @ S
    print('SEG stretch %.2f' % k)
    return A_, ja - A_ @ ea


src = np.array([E['pelvis'], E['L UpperArm'], E['R UpperArm'], E['neck']]); dst = np.array([J['Pelvis'], J['L UpperArm'], J['R UpperArm'], J['Neck']])
sc, dc = src.mean(0), dst.mean(0)
H = (src - sc).T @ (dst - dc); U, _, Vt = np.linalg.svd(H); Rt = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
print('torso rot deg', np.degrees(np.arccos(min(1, (np.trace(Rt) - 1) / 2))))
Tt = (Rt, dc - Rt @ sc)
SEGS = {}
for s_ in 'LR':
    SEGS[f'{s_} UpperArm'] = seg_map(E[f'{s_} UpperArm'], E[f'{s_} Forearm'], J[f'{s_} UpperArm'], J[f'{s_} Forearm'])
    SEGS[f'{s_} Forearm'] = seg_map(E[f'{s_} Forearm'], E[f'{s_} Hand'], J[f'{s_} Forearm'], J[f'{s_} Hand'])
    ej = J[f'{s_} Hand'] + (J[f'{s_} Finger1'] - J[f'{s_} Hand']) / np.linalg.norm(J[f'{s_} Finger1'] - J[f'{s_} Hand']) * np.linalg.norm(E[f'{s_} Knuckle'] - E[f'{s_} Hand']) * cfg.get('hand_scale', 1.0)
    SEGS[f'{s_} Hand'] = seg_map(E[f'{s_} Hand'], E[f'{s_} Knuckle'], J[f'{s_} Hand'], ej)
    SEGS[f'{s_} Thigh'] = seg_map(E[f'{s_} Thigh'], E[f'{s_} Calf'], J[f'{s_} Thigh'], J[f'{s_} Calf'])
    SEGS[f'{s_} Calf'] = seg_map(E[f'{s_} Calf'], E[f'{s_} Foot'], J[f'{s_} Calf'], J[f'{s_} Foot'])
    SEGS[f'{s_} Foot'] = seg_map(E[f'{s_} Foot'], E[f'{s_} Toe0'], J[f'{s_} Foot'], J[f'{s_} Toe0'])
names = list(SEGS)
ends = {f'{s_} UpperArm': (f'{s_} UpperArm', f'{s_} Forearm') for s_ in 'LR'}
ends.update({f'{s_} Forearm': (f'{s_} Forearm', f'{s_} Hand') for s_ in 'LR'})
ends.update({f'{s_} Hand': (f'{s_} Hand', f'{s_} Knuckle') for s_ in 'LR'})
ends.update({f'{s_} Thigh': (f'{s_} Thigh', f'{s_} Calf') for s_ in 'LR'})
ends.update({f'{s_} Calf': (f'{s_} Calf', f'{s_} Foot') for s_ in 'LR'})
ends.update({f'{s_} Foot': (f'{s_} Foot', f'{s_} Toe0') for s_ in 'LR'})


def seg_d(Q, a, b):
    ab = b - a
    t = (Q - a) @ ab / (ab @ ab)
    tc = np.clip(t, 0, 1)
    return np.linalg.norm(Q - a - np.outer(tc, ab), axis=1), t


D = np.ones((n, len(names))) * 1e3
zh = 0.5 * (E['L Thigh'][2] + E['R Thigh'][2])
for i, b in enumerate(names):
    d, t = seg_d(P, E[ends[b][0]], E[ends[b][1]])
    side = 1 if b[0] == 'L' else -1
    ok = (np.sign(P[:, 0]) == side) & (PART == 0)
    if 'Thigh' in b or 'Calf' in b or 'Foot' in b:
        ok &= P[:, 2] < zh + 0.12
        if 'Thigh' in b: ok &= (t > -0.05)
    else:
        ok &= (P[:, 2] > zh + 0.1) & (np.abs(P[:, 0]) > 0.14)
    if 'Hand' in b:
        d = np.where(t < 0, d + 0.02, d)
    D[:, i] = np.where(ok, d, 1e3)
best = D.argmin(1); dbest = D.min(1)
lab = np.zeros((n, len(names) + 1))
rad = {'UpperArm': 0.19, 'Forearm': 0.13, 'Hand': 0.40, 'Thigh': 0.24, 'Calf': 0.18, 'Foot': 0.30}
free = np.array([dbest[i] < rad[names[best[i]].split()[1]] for i in range(n)])
for s_ in 'LR':
    b = f'{s_} UpperArm'; o = E[b]; u = E[f'{s_} Forearm'] - o; u = u / np.linalg.norm(u)
    i = names.index(b)
    free &= ~((best == i) & ((P - o) @ u < -0.01))
lab[np.arange(n), np.where(free, best + 1, 0)] = 1
for _ in range(cfg.get('blend_iters', 8)):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
tw = np.clip((P[:, 2] - 0.12) / 0.25, 0, 1); tw = tw * tw * (3 - 2 * tw)
Pel = J['Pelvis'] - E['pelvis']
base = (P @ Tt[0].T + Tt[1]) * tw[:, None] + (P + Pel) * (1 - tw[:, None])
Q = lab[:, :1] * base
for i, b in enumerate(names):
    A_, t_ = SEGS[b]
    Q = Q + lab[:, i + 1:i + 2] * (P @ A_.T + t_)
P = Q
# ---- the right hand: palm rigid onto MM9's palm, each digit laid along MM9's own joint chain, so the MM9 finger joints stay where they are and MM9's curl reads as authored
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import digits as DG
def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
root = J['R Hand']; fw = root - J['R Forearm']; fw = fw / np.linalg.norm(fw)
import digits2 as D2
ax = (P - root) @ fw
region = (np.linalg.norm(P - root, axis=1) < 0.5) & (P[:, 0] < -0.2) & (ax > -0.10) & (PART == 0) & ~drop
seeds = [i for i in np.nonzero(region)[0] if ax[i] < -0.085]
print('SEEDS', len(seeds), int(region.sum()))
d = DG.geodesic(P, nbr, seeds, region)
ids = np.nonzero(np.isfinite(d))[0]
br = D2.digit_tree(d, nbr, ids, cfg.get('digit_min', 0.05))
print('BRANCHES', [(round(b['tip'] - b['base'], 3), len(b['verts'])) for b in br])
assert len(br) == 5
tips = np.array([P[b['tipv']] for b in br])
base = [DG.centreline(P, d, b['verts'], 10, b['base'])[0] for b in br]
# thumb: base nearest the wrist; the rest ordered across the palm from it
th = int(np.argmin([b['base'] for b in br]))
o = sorted([i for i in range(5) if i != th], key=lambda i: np.linalg.norm(base[i] - base[th]))
print('ORDER thumb', th, o, [round(br[i]['base'], 3) for i in [th] + o])
Ib, Pb = base[o[0]], base[o[3]]; Mb = 0.5 * (base[o[1]] + base[o[2]])
Ij, Mj, Pj = J['R Finger1'], 0.5 * (J['R Finger2'] + J['R Finger3']), J['R Finger3'] + (J['R Finger3'] - J['R Finger2'])
from mathutils import Quaternion, Matrix
srcp = np.array([Ib, Mb, Pb]) - root; dstp = np.array([Ij, Mj, Pj]) - root
H = srcp.T @ dstp; U, S_, Vt = np.linalg.svd(H); Rh = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
ks = float(np.clip(np.linalg.norm(dstp, axis=1).sum() / np.linalg.norm(srcp, axis=1).sum(), 0.75, 1.3))
q = Matrix(Rh.tolist()).to_quaternion()
ax3 = Vector(fw)
pr = ax3 * (Vector((q.x, q.y, q.z)).dot(ax3))
qt = Quaternion((q.w, pr.x, pr.y, pr.z)); qt.normalize()     # twist about the forearm
qs = q @ qt.inverted()                                         # swing at the wrist
print('PALM total', round(np.degrees(q.angle), 1), 'twist', round(np.degrees(qt.angle), 1), 'swing', round(np.degrees(qs.angle), 1), 'scale', round(ks, 3))
qi = Quaternion()
reg2 = (np.linalg.norm(P - root, axis=1) < 0.55) & (P[:, 0] < -0.2) & (ax > -0.26) & (PART == 0) & ~drop
for i in np.nonzero(reg2)[0]:
    a1 = float(sstep(np.array(ax[i]), -0.26, -0.02)); a2 = float(sstep(np.array(ax[i]), -0.03, 0.05))
    v = Vector(P[i] - root)
    v = qi.slerp(qt, a1) @ v
    v = qi.slerp(qs, a2) @ v
    P[i] = root + np.array(v) * (1 + (ks - 1) * a2)
CH = [['R Finger0', 'R Finger01', 'R Finger02'], ['R Finger1', 'R Finger11', 'R Finger12'], ['R Finger2', 'R Finger21', 'R Finger22'], ['R Finger3', 'R Finger31', 'R Finger32'], ['R Finger41', 'R Finger42']]
digit_info = {}


def tang(C, i):
    a, b = max(i - 1, 0), min(i + 1, len(C) - 1)
    v = C[b] - C[a]; return v / np.linalg.norm(v)


for chain, bi in zip(CH, [th] + o):
    b = br[bi]; vs = np.array(b['verts'])
    if chain[0] == 'R Finger0':
        vs = vs[d[vs] > b['tip'] - 0.15]; b = dict(b, verts=vs.tolist(), base=float(b['tip'] - 0.15))
    C = DG.centreline(P, d, b['verts'], 12, b['base'])
    LC = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
    jt = [J[c] for c in chain]
    last = jt[-1] - jt[-2]; last = last / np.linalg.norm(last)
    # the base of our digit lies along MM9's first bone (a web sits beyond the knuckle)
    u = jt[1] - jt[0]; s0 = float(np.clip((C[0] - jt[0]) @ u / (u @ u), 0, 0.9)) * np.linalg.norm(u)
    Lj = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.array(jt), axis=0), axis=1))]
    tiplen = LC[-1] + s0 - Lj[-1]
    print('DIGIT', chain[0], 'len', round(LC[-1], 3), 'mm9 joints span', round(Lj[-1], 3), 's0', round(s0, 3), 'past last joint', round(tiplen, 3))
    T = np.vstack([jt, jt[-1] + last * max(tiplen, 0.03)])
    LT = np.r_[0, np.cumsum(np.linalg.norm(np.diff(T, axis=0), axis=1))]
    new = np.zeros((len(vs), 3))
    for k, v in enumerate(vs):
        q = P[v]
        # nearest point of the centreline polyline
        bestd, bs_, bi_ = 1e9, 0, 0
        for i in range(len(C) - 1):
            ab = C[i + 1] - C[i]; t = float(np.clip((q - C[i]) @ ab / max(ab @ ab, 1e-12), 0, 1)); pt = C[i] + ab * t
            dd = np.linalg.norm(q - pt)
            if dd < bestd: bestd, bs_, bi_ = dd, LC[i] + t * (LC[i + 1] - LC[i]), i
        s = bs_ + s0
        pc = np.array([np.interp(bs_, LC, C[:, c]) for c in range(3)])
        off = q - pc
        tc = tang(C, bi_)
        j = min(int(np.searchsorted(LT, s, side='right')) - 1, len(T) - 2)
        tt = (T[j + 1] - T[j]); tt = tt / np.linalg.norm(tt)
        pt = T[j] + tt * (s - LT[j])
        new[k] = pt + rot(tc, tt) @ off
    w = sstep(d[vs] - b['base'], -0.005, 0.03)[:, None]
    P[vs] = P[vs] * (1 - w) + new * w
print('floor', P[:, 2].min(), 'bbox', P.min(0).round(3), P.max(0).round(3))
for v, p in zip(me.vertices, P): v.co = Vector(p)
pa = me.attributes.new('part', 'INT', 'POINT'); pa.data.foreach_set('value', PART.tolist())
dr = me.attributes.new('drop', 'INT', 'POINT'); dr.data.foreach_set('value', drop.astype(int).tolist())
me.update()
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int['part']; dl = bm.verts.layers.int['drop']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[dl]], context='VERTS')
# the sheets lean off-centre in the 3/4 master: each is sheared so its centre line is x = 0 before the mirror
for pid in (6, 7):
    vs = [v for v in bm.verts if v[lay] == pid]
    q = np.array([v.co[:] for v in vs])
    zs = np.linspace(q[:, 2].min(), q[:, 2].max(), 7); mid = []; zk = []
    for a, b in zip(zs[:-1], zs[1:]):
        m = (q[:, 2] >= a) & (q[:, 2] <= b)
        if m.sum() >= 2: mid.append(0.5 * (q[m, 0].min() + q[m, 0].max())); zk.append(q[m, 2].mean())
    c1, c0 = np.polyfit(zk, mid, 1)
    print('FLAP', pid, len(vs), 'shear', round(c1, 3), round(c0, 3), 'z', q[:, 2].min().round(3), q[:, 2].max().round(3), 'x', q[:, 0].min().round(3), q[:, 0].max().round(3), 'y', q[:, 1].min().round(3), q[:, 1].max().round(3))
    for v in vs: v.co.x -= c1 * v.co.z + c0
cut = cfg['neck_cut_z']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] == 3 and v.co.z > 0.5], context='VERTS')      # Meshy's own eyes and teeth
skin = [v for v in bm.verts if v[lay] == 0]
g = skin + list({e for v in skin for e in v.link_edges}) + list({f for v in skin for f in v.link_faces})
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, cut), plane_no=(0, 0, 1), clear_outer=True)
all_ = list(bm.verts) + list(bm.edges) + list(bm.faces)
if cfg['keep_side'] < 0:
    bmesh.ops.bisect_plane(bm, geom=all_, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
else:
    bmesh.ops.bisect_plane(bm, geom=all_, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.mirror(bm, geom=g, axis='X', merge_dist=1e-4)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if not all(v[lay] in (6, 7) for v in f.verts)])
# the flaps leave the skin as their own sheets
fs = [f for f in bm.faces if all(v[lay] in (6, 7) for v in f.verts)]
ret = bmesh.ops.split(bm, geom=fs + list({e for f in fs for e in f.edges}), use_only_faces=True)
bm.to_mesh(me); bm.free()
print('SYM verts', len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
np.savez(OUT + '.joints.npz', **{k: v for k, v in J.items()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
