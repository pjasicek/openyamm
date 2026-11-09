"""Fit the MM9 Imp skeleton onto the Meshy body (the approved Yrsa route: joints TRANSLATED, rest rotations unchanged, so
MM9's clips play as they are). Args: <mm9 source blend> <meshy glb> <config json> <out blend> <report json>

1. Body: height scale, x centred, y so that the torso centre matches MM9's; the over-long Meshy tail is curve-deformed
   onto the MM9 chain (moved to our tail root, `tail.length` x as long).
2. Joints from the mesh: centre chain by torso slices, arms by slices along the arm axis with the wrist at the bracer,
   legs by slices along the MM9 leg chain, fingers and toes from digits found by connectivity (digits.py).
3. Writes 'Body' (static), 'MM9_Rig' with the moved joints; the MM9 meshes stay, moved with their bones, for the weights.
"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scipy_free_tail import tail_curve
import digits as DG

SRC, MESHY, CFG, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG))
rep = {}
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects['MM9_Rig']
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
mm9_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
A = np.array([tuple(o.matrix_world @ v.co) for o in mm9_meshes if 'trident' not in o.name for v in o.data.vertices])
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
body = next(o for o in new if o.type == 'MESH')
for o in new:
    if o is not body:
        bpy.data.objects.remove(o)
body.parent = None
body.name = 'Body'
Mw = np.array(body.matrix_world)
me = body.data
P = np.array([tuple(v.co) for v in me.vertices]) @ Mw[:3, :3].T + Mw[:3, 3]
body.matrix_world = Matrix.Identity(4)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.to_mesh(me); bm.free()
P = np.array([tuple(Mw[:3, :3] @ np.array(v.co) + Mw[:3, 3]) for v in me.vertices])
s = np.ptp(A[:, 2]) / np.ptp(P[:, 2]) * cfg.get('scale', 1.0)
P = P * s
P[:, 2] += A[:, 2].min() - P[:, 2].min()
P[:, 0] -= 0.5 * (P[:, 0].min() + P[:, 0].max())


def tcy(Q, z0, z1, half):
    m = (Q[:, 2] > z0) & (Q[:, 2] < z1) & (np.abs(Q[:, 0]) < half)
    return 0.5 * (Q[m, 1].min() + Q[m, 1].max())


z0, z1 = cfg['torso_band']
ti = (P[:, 1] < cfg['tail']['start_y_raw'])
dy = tcy(A, z0, z1, 0.12) - tcy(P[ti], z0, z1, 0.12)
P[:, 1] += dy
rep['dy'] = float(dy)
rep['scale'] = float(s)
newJ = {}
edges = np.array([tuple(e.vertices) for e in me.edges])
nbr = [[] for _ in range(len(P))]
for a, b in edges:
    nbr[a].append(b); nbr[b].append(a)

# centre chain: the MM9 joints as they are (the torso band aligned the bodies)
for name in cfg['centre_chain']:
    newJ[name] = J[name].copy()

# tail: root on our surface, chain = MM9's shape, longer by tail.length
tc = cfg['tail']
tm = (P[:, 1] > tc['y_root']) & (np.abs(P[:, 0]) < tc['half_x']) & (P[:, 2] < tc['z_max'])
chain = np.array([J[n] for n in tc['chain']])
root = np.array(tc['root'])
ch2 = root + (chain - chain[0]) * tc['length']
tip = root + (np.array(tc['tip_mm9']) - chain[0]) * tc['length']
P, rep['tail'] = tail_curve(P, tm, ch2, tip, tc)
rep['tail_verts'] = int(tm.sum())
for n, c in zip(tc['chain'], ch2):
    newJ[n] = c

# limbs: Meshy joint estimates E (config, raw placed coordinates + the y shift), FK with MM9's directions and our lengths,
# and the mesh posed to them by a transient skin so that every bone offset points as in MM9 (MM9's clips then give
# MM9's poses, not poses tilted by the rest difference)
E = {k: np.array(v) + np.array([0, dy, 0]) for k, v in cfg['estimates'].items()}
limbs = cfg['limbs']          # [[bone, child or null], ...] root to tip per limb


def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); s_ = np.linalg.norm(v)
    if s_ < 1e-9:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s_ ** 2)


T = {}
for limb in limbs:
    bones = limb['bones']
    for k, b in enumerate(bones):
        if k == 0:
            newJ[b] = E[b].copy()
        if b in cfg.get('yaw_only', []):
            tgt = J[limb['end_mm9']] - J[b]; src = E[limb['end_est']] - E[b]
            ang = np.arctan2(tgt[1], tgt[0]) - np.arctan2(src[1], src[0])
            ca, sa = np.cos(ang), np.sin(ang)
            R = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])
        elif k + 1 < len(bones):
            c = bones[k + 1]
            R = rot_between(E[c] - E[b], J[c] - J[b])
            newJ[c] = newJ[b] + (J[c] - J[b]) / np.linalg.norm(J[c] - J[b]) * np.linalg.norm(E[c] - E[b])
        else:
            R = rot_between(E[limb['end_est']] - E[b], J[limb['end_mm9']] - J[b])
        T[b] = (R, E[b].copy(), newJ[b].copy())
    rep.setdefault('limb_rot_deg', {}).update({b: round(float(np.degrees(np.arccos(np.clip((np.trace(T[b][0]) - 1) / 2, -1, 1)))), 1) for b in bones})

# transient labels: nearest limb segment (own side), torso and tail stay
names = [b for limb in limbs for b in limb['bones']]
lab = np.zeros((len(P), len(names) + 1))
seg = {}
for limb in limbs:
    bs = limb['bones']
    for k, b in enumerate(bs):
        c = bs[k + 1] if k + 1 < len(bs) else None
        seg[b] = (E[b], E[c] if c else E[limb['end_est']])


def seg_d(Q, a, b):
    ab = b - a
    t = np.clip((Q - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(Q - a - np.outer(t, ab), axis=1)


D = np.stack([seg_d(P, *seg[b]) for b in names], 1)
side = np.array([np.sign(J[b][0]) for b in names])
D[:, :] = np.where((np.sign(P[:, 0])[:, None] == side), D, 1e3)
best = D.argmin(1); dbest = D.min(1)
limb_r = cfg.get('limb_radius', 0.11)
# the belt line stays: thighs start below the hips
hipz = cfg.get('thigh_top_z', -0.16)
isleg = np.array([('Thigh' in names[b]) for b in best])
free = (dbest < limb_r) & ~tm & ~(isleg & (P[:, 2] > hipz))
lab[np.arange(len(P)), np.where(free, best + 1, 0)] = 1
for b, r in cfg.get('radius', {}).items():
    i = names.index(b)
    m = (best == i) & (dbest >= r)
    lab[m] = 0; lab[m, 0] = 1
for _ in range(cfg.get('blend_iters', 6)):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
Q = lab[:, 0:1] * P
for i, b in enumerate(names):
    R, e, n_ = T[b]
    Q = Q + lab[:, i + 1:i + 2] * ((P - e) @ R.T + n_)
# small loose pieces (bracers, studs) rigid with their centroid's label
comp = -np.ones(len(P), int); c_ = 0
for i in range(len(P)):
    if comp[i] >= 0:
        continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0:
                comp[y] = c_; st.append(y)
    c_ += 1
for c in range(c_):
    ids = np.nonzero(comp == c)[0]
    if len(ids) > 300:
        continue
    if np.abs(P[ids, 0].mean()) < cfg.get('static_x', 0.25) and P[ids, 2].mean() < 0.1:
        Q[ids] = P[ids]            # belt, flap, buckle, studs
        continue
    w = lab[ids].mean(0)
    Mx = w[0] * np.eye(4)
    for i, b in enumerate(names):
        R, e, n_ = T[b]
        M = np.eye(4); M[:3, :3] = R; M[:3, 3] = n_ - R @ e
        Mx = Mx + w[i + 1] * M
    Q[ids] = P[ids] @ Mx[:3, :3].T + Mx[:3, 3]
P = Q
rep['floor_after'] = float(P[:, 2].min())
for v, p in zip(me.vertices, P):
    v.co = Vector(p)

# digits: hands and feet
dig = DG.find_digits(P, nbr, cfg['digits'], newJ, J)
rep['digits'] = dig['report']
newJ.update(dig['joints'])

# everything else follows its nearest fitted ancestor
for name in J:
    if name in newJ:
        continue
    p = parent[name]
    while p is not None and p not in newJ:
        p = parent[p]
    newJ[name] = J[name] + ((newJ[p] - J[p]) if p else np.zeros(3))
rep['joint_moves_cm'] = {n: round(float(np.linalg.norm(newJ[n] - J[n]) * 100), 1) for n in J}
json.dump({n: newJ[n].tolist() for n in J}, open(OUT + '.joints.json', 'w'), indent=0)
np.savez(OUT + '.digits.npz', **{k: np.array(v) for k, v in dig['labels'].items()})

# move the MM9 meshes with their bones (their rigid labels are the weight source)
for o in mm9_meshes:
    lab = []
    Mi = o.matrix_world.inverted()
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        n = o.vertex_groups[g.group].name
        d = Vector(newJ[n] - J[n])
        v.co = v.co + Mi.to_3x3() @ d
# translate the bones (orientation unchanged)
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
Mi = arm.matrix_world.inverted()
for eb in arm.data.edit_bones:
    d = Mi.to_3x3() @ Vector(newJ[eb.name] - J[eb.name])
    eb.head += d
    eb.tail += d
bpy.ops.object.mode_set(mode='OBJECT')
for p_ in me.polygons:
    p_.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('FIT ' + json.dumps({k: v for k, v in rep.items() if k != 'joint_moves_cm'})[:1800])
