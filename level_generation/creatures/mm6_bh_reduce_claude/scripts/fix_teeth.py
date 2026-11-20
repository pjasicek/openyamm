"""Teeth on a ladder candidate (work/ladder.blend): the six separate tooth pieces (work/teeth_labels.npy label 3) are
replaced by clean fitted cones (8 sides, root ring, a 0.55 shoulder ring, tip; root sunk 15 % into the gum, rigid on
the piece's dominant bone); the big fangs (label 1) and the gum spikes (label 2) keep their geometry and take UVs in
the painted ivory cell (work/ivory_cell.json), root to tip along v, around the axis along u.
Usage: REA_CAND=Cand_50 blender -b -P fix_teeth.py  -> work/teeth.blend (candidate renamed Cand_teeth)"""
import os, json, math, bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_50')]; body = bpy.data.objects['Body']
d = np.load(os.path.join(HERE, 'work/mesh_in.npz')); sv, sf = d['verts'], d['faces']
lab = np.load(os.path.join(HERE, 'work/teeth_labels.npy')); comp = np.load(os.path.join(HERE, 'work/components.npy'))
cell = json.load(open(os.path.join(HERE, 'work/ivory_cell.json')))['cell_uv']   # u0, v0, u1, v1
U = lambda s: cell[0] + (cell[2] - cell[0]) * s
V = lambda t: cell[3] - (cell[3] - cell[1]) * t                                  # t 0 root (top row) -> 1 tip
sctr = sv[sf].mean(1); tree = KDTree(len(sctr))
for i, p in enumerate(sctr):
    tree.insert(p, i)
tree.balance()

bm = bmesh.new(); bm.from_mesh(cand.data); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv.active; dl = bm.verts.layers.deform.verify()
tl = bm.faces.layers.int.new('tooth')                                            # survives the deletion below
for fc in bm.faces:
    _, i, dist = tree.find(fc.calc_center_median())
    fc[tl] = int(lab[i]) if dist < 1e-5 else 0
print('CAND faces by label', {k: sum(1 for fc in bm.faces if fc[tl] == k) for k in range(4)})

# 1. delete the separate tooth pieces
bmesh.ops.delete(bm, geom=[fc for fc in bm.faces if fc[tl] == 3], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.faces.ensure_lookup_table()


def axis_of(P, down):
    mu = P.mean(0); ax = np.linalg.svd(P - mu)[2]
    a = ax[0] if (ax[0][2] < 0) == down else -ax[0]                              # a points root -> tip
    return mu, a, ax[1], ax[2]


# 2. remap fangs and gum spikes onto the ivory cell
def remap(faces, mu, a, b, c, t0, t1):
    for fc in faces:
        for lp in fc.loops:
            p = np.array(lp.vert.co) - mu; t = (p @ a - t0) / (t1 - t0)
            ang = (math.atan2(p @ c, p @ b) / (2 * math.pi)) % 1
            lp[uvl].uv = (U(.1 + .8 * ang), V(min(max(t, 0), 1)))


groups = {g.index: g.name for g in cand.vertex_groups}
for s in (1, -1):                                                                 # fangs: root at the top
    fs = [fc for fc in bm.faces if fc[tl] == 1 and np.sign(fc.calc_center_median().x) == s]
    P = np.array([v.co[:] for fc in fs for v in fc.verts]); mu, a, b, c = axis_of(P, True)
    t = (P - mu) @ a; remap(fs, mu, a, b, c, t.min(), t.max()); print('FANG', s, len(fs), 'faces')
spikes = [fc for fc in bm.faces if fc[tl] == 2]
if spikes:
    P = np.array([v.co[:] for fc in spikes for v in fc.verts]); zt = P[:, 2].max(); zb = P[:, 2].min()
    for fc in spikes:
        for lp in fc.loops:
            x, y, z = lp.vert.co
            lp[uvl].uv = (U(.1 + .8 * ((x + .11) / .22)), V((zt - z) / (zt - zb)))
    print('SPIKES', len(spikes), 'faces')

# 3. cones for the separate tooth pieces
bone_of = {}
for k in sorted(set(comp[lab == 3].tolist())):
    vi = np.unique(sf[comp == k]); P = sv[vi]
    w = {}
    for i in vi:
        for gg in body.data.vertices[int(i)].groups:
            n = body.vertex_groups[gg.group].name; w[n] = w.get(n, 0) + gg.weight
    bone = max(w, key=w.get); upper = P[:, 2].mean() > .35
    mu, a, b, c = axis_of(P, upper)                                              # upper teeth hang down
    t = (P - mu) @ a; L = t.max() - t.min(); root = mu + a * (t.min() - .15 * L); tip = mu + a * t.max()
    near = t < t.min() + .4 * L
    rb = np.percentile(np.abs((P[near] - mu) @ b), 90); rc = np.percentile(np.abs((P[near] - mu) @ c), 90)
    gi = cand.vertex_groups[bone].index
    rings = []
    for tt, sc in ((0, 1.0), (.55, .72)):
        ring = []
        centre = root + (tip - root) * (tt if tt else 0)
        for j in range(8):
            ang = 2 * math.pi * j / 8
            pv = bm.verts.new(Vector(centre + (math.cos(ang) * rb * b + math.sin(ang) * rc * c) * sc))
            pv[dl][gi] = 1.0; ring.append((pv, j / 8, tt))
        rings.append(ring)
    tv = bm.verts.new(Vector(tip)); tv[dl][gi] = 1.0
    new = []
    for j in range(8):
        (a0, u0, t0), (a1, u1, _) = rings[0][j], rings[0][(j + 1) % 8]
        (b0, _, t1), (b1, _, _) = rings[1][j], rings[1][(j + 1) % 8]
        for tri, uvs in (((a0, a1, b1), ((u0, t0), (u0 + 1 / 8, t0), (u0 + 1 / 8, t1))),
                         ((a0, b1, b0), ((u0, t0), (u0 + 1 / 8, t1), (u0, t1)))):
            new.append((bm.faces.new(tri), uvs))
        new.append((bm.faces.new((b0, b1, tv)), ((u0, t1), (u0 + 1 / 8, t1), (u0 + 1 / 16, 1))))
    cap = bm.faces.new([rings[0][j][0] for j in reversed(range(8))])
    for fc, uvs in new:
        for lp, (u, tt) in zip(fc.loops, uvs):
            lp[uvl].uv = (U(.1 + .8 * u), V(tt))
    for lp in cap.loops:
        lp[uvl].uv = (U(.5), V(0))
    capt = bmesh.ops.triangulate(bm, faces=[cap])
    # outward winding: the side faces' normals must point away from the axis
    fc0 = new[0][0]; fc0.normal_update()
    if (np.array(fc0.calc_center_median()) - (root + (tip - root) * .25)) @ np.array(fc0.normal) < 0:
        for fc, _ in new:
            fc.normal_flip()
        for fc in capt['faces']:
            fc.normal_flip()
    print('TOOTH', k, bone, 'upper' if upper else 'lower', 'len %.3f r %.4f/%.4f' % (L * 1.15, rb, rc))
bm.normal_update(); bm.to_mesh(cand.data); bm.free(); cand.data.update()
cand.name = 'Cand_teeth'
print('TRIS', sum(len(p.vertices) - 2 for p in cand.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'teeth.blend'))
