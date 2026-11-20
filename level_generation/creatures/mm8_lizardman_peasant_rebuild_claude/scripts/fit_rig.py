"""Fit the Meshy body to the original MM9 skeleton and weight it (MM9 rig reuse for humanoid NPCs).

Args: <meshy glb> <mm9 glb> <out blend> <report json> <config json>

The HD masters are in the MM9 bind pose, so the Meshy mesh needs no posing:
1. Body: every Meshy mesh joined into 'Body', scaled uniformly to the MM9 mesh height, floor and centre matched.
2. Joints (the MM9 skeleton, names and rest ROTATIONS unchanged, so the MM9 clips' local rotations play as they are):
   - centre chain (pelvis/spine/neck/head): the joint keeps its height; its depth (y) follows our torso centroid at
     that height relative to the MM9 torso centroid there;
   - arms: our arm centreline is measured in slices along the MM9 arm axis (shoulder -> fingertip); every arm joint
     keeps its fractional position along the arm and its offset from the MM9 centreline;
   - legs (config legs: 'fit'): the same along the vertical leg axis; 'keep' (a long dress hides the legs) leaves them;
   - every other joint (fingers, tunic ring, skirt, braids, hood tail) moves with its nearest fitted ancestor (fingers
     also scale with the arm).
   Bones are translated (head and tail together), never rotated.
3. Weights: the MM9 skin is rigid; the MM9 mesh is carried onto the fitted joints (each vertex with its bone's
   displacement) and each body vertex takes the bone of the nearest MM9 surface point, then the labels diffuse along
   our mesh (config diffuse iterations); at most four influences.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
MESHY, MM9, OUT, REP, CFG = argv
cfg = json.load(open(CFG))
rep = {}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
arm.name = 'MM9_Rig'
if arm.animation_data:
    arm.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
mm9 = max(meshes, key=lambda o: len(o.data.vertices))
for o in meshes:
    if o is not mm9:
        bpy.data.objects.remove(o)
mm9.name = 'MM9_Mesh'
bpy.context.view_layer.update()
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in existing]
parts = [o for o in new if o.type == 'MESH']
for o in new:
    if o.type != 'MESH':
        for c in o.children:
            m = c.matrix_world.copy()
            c.parent = None
            c.matrix_world = m
for o in new:
    if o.type != 'MESH':
        bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.select_set(o in parts)
bpy.context.view_layer.objects.active = parts[0]
if len(parts) > 1:
    bpy.ops.object.join()
body = parts[0]
body.name = 'Body'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = body.data
me.materials.clear()


def verts_world(ob):
    M = np.array(ob.matrix_world)
    co = np.array([v.co for v in ob.data.vertices])
    return co @ M[:3, :3].T + M[:3, 3]


mp = verts_world(mm9)
bp = np.array([v.co for v in me.vertices])
yaw = cfg.get('yaw_degrees', 0.0)
if yaw:
    a = np.radians(yaw)
    R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    bp = bp @ R.T
s = (mp[:, 2].max() - mp[:, 2].min()) / (bp[:, 2].max() - bp[:, 2].min())
bp = bp * s
bp[:, 2] += mp[:, 2].min() - bp[:, 2].min()
# centre x from the whole bbox, y from the torso (between hips and shoulders, narrow band)
def torso_y(p, z0, z1, half):
    m = (p[:, 2] > z0) & (p[:, 2] < z1) & (np.abs(p[:, 0]) < half)
    return 0.5 * (p[m, 1].min() + p[m, 1].max())


bp[:, 0] -= 0.5 * (bp[:, 0].min() + bp[:, 0].max()) - 0.5 * (mp[:, 0].min() + mp[:, 0].max())
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
zc0, zc1 = cfg['torso_band']
bp[:, 1] += torso_y(mp, zc0, zc1, 0.12) - torso_y(bp, zc0, zc1, 0.12)
for i, v in enumerate(me.vertices):
    v.co = Vector(bp[i])
rep['scale'] = float(s)
rep['height'] = float(bp[:, 2].max() - bp[:, 2].min())

# ---- joints
names = [b.name for b in arm.data.bones]
parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
newJ = {}


def slice_centroid(p, origin, axis, s0, s1, radius):
    t = (p - origin) @ axis
    m = (t > s0) & (t < s1)
    if m.sum() < 4:
        return None
    q = p[m]
    perp = q - origin - np.outer((q - origin) @ axis, axis)
    # keep the dominant cluster near the axis
    d = np.linalg.norm(perp, axis=1)
    q = q[d < radius]
    if len(q) < 4:
        return None
    return 0.5 * (q.min(0) + q.max(0))


for name in cfg['centre_chain']:
    j = J[name]
    half = cfg.get('centre_half_width', 0.12)
    band = 0.03
    def cy(p):
        m = (np.abs(p[:, 2] - j[2]) < band) & (np.abs(p[:, 0]) < half)
        return 0.5 * (p[m, 1].min() + p[m, 1].max()) if m.sum() > 4 else None
    def fy(p):
        m = (np.abs(p[:, 2] - j[2]) < band) & (np.abs(p[:, 0]) < half)
        return p[m, 1].min() if m.sum() > 4 else None
    a, b = (fy(mp), fy(bp)) if name in cfg.get('centre_front', []) else (cy(mp), cy(bp))
    newJ[name] = j + np.array([0, (b - a) if (a is not None and b is not None) else 0.0, 0])

# hip joints: width ratio of the hips at their height, depth with the pelvis joint
for name in cfg.get('hips', []):
    j = J[name]
    def hw(p):
        m = np.abs(p[:, 2] - j[2]) < 0.08
        return np.percentile(np.abs(p[m, 0]), 98)
    pel = cfg['centre_chain'][0]
    newJ[name] = np.array([j[0] * hw(bp) / hw(mp), j[1] + newJ[pel][1] - J[pel][1], j[2]])

arm_rep = {}
for side in cfg['arms']:
    chain = side['chain']          # shoulder ... hand (fitted joints in order)
    tipbone = side['tip']          # last finger joint; the tip is the mesh extent along the axis
    o = J[chain[0]]
    axis = J[tipbone] - o
    axis /= np.linalg.norm(axis)
    def extent(p):
        t = (p - o) @ axis
        perp = np.linalg.norm(p - o - np.outer(t, axis), axis=1)
        return t[(perp < 0.25) & (t > 0)].max()
    Lm, Lb = extent(mp), extent(bp)
    k = Lb / Lm
    for name in chain:
        sj = (J[name] - o) @ axis
        cm = slice_centroid(mp, o, axis, sj - 0.02, sj + 0.02, side.get('radius', 0.12))
        cb = slice_centroid(bp, o, axis, sj * k - 0.02, sj * k + 0.02, side.get('radius', 0.12))
        off = (J[name] - cm) if cm is not None else np.zeros(3)
        base = cb if cb is not None else o + axis * sj * k
        if name in side.get('axis_only', []):
            # wide sleeves: the slice centre is not the arm; keep the MM9 joint, moved along the arm only
            newJ[name] = J[name] + axis * sj * (k - 1)
        else:
            newJ[name] = base + off
    arm_rep[chain[0]] = {'mm9_len': float(Lm), 'our_len': float(Lb), 'scale': float(k)}
    for name in side.get('scaled_children', []):
        hand = side['scale_root']
        newJ[name] = newJ[hand] + (J[name] - J[hand]) * k
rep['arms'] = arm_rep

if cfg.get('legs') == 'fit':
    floor = bp[:, 2].min()
    for side in cfg['leg_chains']:
        chain = side['chain']
        o = J[chain[0]]
        axis = np.array([0, 0, -1.0])
        Lm = o[2] - mp[:, 2].min()
        Lb = o[2] - floor
        k = Lb / Lm
        sx = np.sign(o[0])
        for name in chain:
            sj = (J[name] - o) @ axis
            def cen(p, s0):
                t = (p - o) @ axis
                m = (np.abs(t - s0) < 0.025) & (np.sign(p[:, 0]) == sx) & (np.abs(p[:, 0]) > 0.02)
                if m.sum() < 4:
                    return None
                q = p[m]
                return 0.5 * (q.min(0) + q.max(0))
            cm, cb = cen(mp, sj), cen(bp, sj * k)
            off = (J[name] - cm) if cm is not None else np.zeros(3)
            newJ[name] = (cb if cb is not None else o + axis * sj * k) + off

# legs hidden by a dress: each leg moves with its shoe (lowest verts on that side)
for side in cfg.get('feet', []):
    def shoe(p, sx):
        floor = p[:, 2].min()
        m = (p[:, 2] < floor + side.get('height', 0.06)) & (np.sign(p[:, 0]) == sx) & (np.abs(p[:, 0]) > 0.02)
        q = p[m]
        return 0.5 * (q.min(0) + q.max(0))
    sx = np.sign(J[side['chain'][-1]][0])
    d = shoe(bp, sx) - shoe(mp, sx)
    d[2] = 0
    for name in side['chain']:
        newJ[name] = J[name] + d

# everything else follows its nearest fitted ancestor
for name in names:
    if name in newJ:
        continue
    p = parent[name]
    while p is not None and p not in newJ:
        p = parent[p]
    d = (newJ[p] - J[p]) if p is not None else np.zeros(3)
    newJ[name] = J[name] + d
rep['joint_moves_cm'] = {n: round(float(np.linalg.norm(newJ[n] - J[n]) * 100), 1) for n in names}

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

# ---- weights: carry the rigid MM9 mesh with its bones, nearest surface label, diffusion
lab = []
for v in mm9.data.vertices:
    g = max(v.groups, key=lambda g: g.weight)
    lab.append(mm9.vertex_groups[g.group].name)
mp2 = np.array([mp[i] + (newJ[lab[i]] - J[lab[i]]) for i in range(len(lab))])
faces = [list(p.vertices) for p in mm9.data.polygons]
bvh = BVHTree.FromPolygons([Vector(x) for x in mp2], faces)
bones = names
bidx = {b: i for i, b in enumerate(bones)}
n = len(me.vertices)
W = np.zeros((n, len(bones)))
override = cfg.get('label_override', {})
for i, v in enumerate(me.vertices):
    loc, nrm, fi, dist = bvh.find_nearest(v.co)
    fv = faces[fi]
    best = min(fv, key=lambda k: (mp2[k] - np.array(loc)) @ (mp2[k] - np.array(loc)))
    L = lab[best]
    L = override.get(L, L)
    W[i, bidx[L]] = 1
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b)
    nbr[b].append(a)
for _ in range(cfg.get('diffuse', 8)):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    W = 0.5 * W + 0.5 * avg
# arm bands: along each arm the weights are set by the position on the arm axis (clavicle -> upper arm -> forearm
# -> hand), so the shoulder (a vest cap, a sleeve) follows the raised or lowered arm and the elbow bends evenly.
co = np.array([v.co for v in me.vertices])


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


band = cfg.get('bands', {'shoulder': [-0.07, 0.04], 'elbow': 0.045, 'wrist': 0.025})
for side in cfg['arms']:
    ua, fa, hd = side['chain']
    cl = parent[ua]
    S = [bidx[b] for b in (cl, ua, fa, hd)]
    o = newJ[ua]
    ax = newJ[hd] - o
    L = np.linalg.norm(ax)
    ax /= L
    t = (co - o) @ ax
    te = (newJ[fa] - o) @ ax
    share = W[:, S].sum(1)
    sx = np.sign(o[0])
    m = (share > 0.5) & (t > band['shoulder'][0]) & (t < L + band['wrist']) & (np.sign(co[:, 0]) == sx)
    w_ua = sstep(t, band['shoulder'][0], band['shoulder'][1])
    w_fa = sstep(t, te - band['elbow'], te + band['elbow'])
    w_hd = sstep(t, L - band['wrist'], L + band['wrist'])
    new = np.stack([1 - w_ua, w_ua * (1 - w_fa), w_fa * (1 - w_hd), w_hd], 1)
    # keep the hand/finger labels near the wrist: blend only up to where the hand share already was
    rows = np.nonzero(m)[0]
    for i in rows:
        tot = share[i]
        W[i, S] = new[i] * tot
    rep.setdefault('arm_band_verts', {})[ua] = int(m.sum())

order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones))
    row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0):
        body.vertex_groups.remove(g)
body.parent = arm
body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE')
mod.object = arm
bpy.data.objects.remove(mm9)
rep['verts'] = n
rep['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
rep['dominant_counts'] = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('FIT ' + json.dumps({k: rep[k] for k in ('scale', 'height', 'arms', 'tris')}))
