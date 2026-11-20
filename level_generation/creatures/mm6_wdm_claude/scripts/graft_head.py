"""Graft the head-only Meshy model (meshy/head_v1, from the Codex HD head views) onto the rigged HD body.

Run on work/rig_hd.blend; saves work/rig_head.blend. The full-body model gave the face ~70 reference pixels and 8% of
one 2k texture (stretched teeth, smeared eyes); the head model, decimated to ~6k triangles, gets its own texture.
  - place: uniform scale + translation fitted visually to the old head (snout, crown, back of skull; review/graft_*),
  - body: delete the old head (Head weight > 0.5) and every body face lying inside the new head; body boundary
    vertices left outside the new head are pulled just inside its surface so the cut never shows,
  - head: joined as material slot 1 'DemonHead' (body stays slot 0); weights copied from the nearest non-wing body
    vertex of the original mesh, so the neck blend matches the body,
  - the wing flag is kept as the point attribute 'wing' (vertex indices change; dump_uv3d/check_wings read it)."""
import bpy, bmesh, os
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE, OFFSET, PITCH = 0.165, Vector((0.0, -0.155, 1.257)), 0.0
INSET = 0.0015
NEAR = 0.03       # only body boundary vertices this close to the head belong to the neck cut
HEAD_RATIO = 0.5  # head 12.5k -> ~6.2k triangles (runtime cost; teeth and horns survive)
BAND = 0.04       # head neck band (m above its lowest vertex) buried under the body surface

body = bpy.data.objects['Demon']; rig = bpy.data.objects['Demon_Rig']; me = body.data
wing = np.load(os.path.join(HERE, 'work', 'wing_mask.npy'))
att = me.attributes.new('wing', 'BOOLEAN', 'POINT'); att.data.foreach_set('value', wing.tolist())

# ---- new head, placed in the body frame ---------------------------------------------------------------------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', 'head_v1', 'model_urls_glb.glb'))
new = set(bpy.data.objects) - before
head = next(o for o in new if o.type == 'MESH')
for o in new:
    if o is not head:
        bpy.data.objects.remove(o, do_unlink=True)
head.parent = None
for o in bpy.context.view_layer.objects:
    o.select_set(o is head)
bpy.context.view_layer.objects.active = head
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(head.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.transform(Matrix.Translation(OFFSET) @ Matrix.Rotation(np.radians(PITCH), 4, 'X') @ Matrix.Scale(SCALE, 4))
bm.to_mesh(head.data); bm.free()
head.name = head.data.name = 'Head'
for p in head.data.polygons:
    p.use_smooth = True
dec = head.modifiers.new('decimate', 'DECIMATE'); dec.ratio = HEAD_RATIO; dec.use_symmetry = True; dec.symmetry_axis = 'X'
bpy.ops.object.modifier_apply(modifier=dec.name)
print('HEAD triangles after decimation', sum(len(p.vertices) - 2 for p in head.data.polygons))
hbm = bmesh.new(); hbm.from_mesh(head.data); hbm.faces.ensure_lookup_table()
head_bvh = BVHTree.FromBMesh(hbm)


def inside_head(p):
    loc, nrm, _, _ = head_bvh.find_nearest(p)
    return (p - loc).dot(nrm) < 0, loc, nrm


# ---- weights for the head from the original body (before any deletion) ---------------------------------------------
groups = {g.index: g.name for g in body.vertex_groups}
co = np.array([tuple(v.co) for v in me.vertices])
kd = KDTree(int((~wing).sum()))
for i in np.nonzero(~wing)[0]:
    kd.insert(Vector(co[i]), int(i))
kd.balance()
head_weights = []
for v in head.data.vertices:
    near = kd.find_n(v.co, 6)
    acc = {}
    for _, i, d in near:
        wt = 1.0 / max(d, 1e-4)
        for g in me.vertices[i].groups:
            acc[groups[g.group]] = acc.get(groups[g.group], 0.0) + g.weight * wt
    s = sum(acc.values())
    head_weights.append({k: w / s for k, w in acc.items() if w / s > 0.01})

# ---- body: delete the old head and faces inside the new head -------------------------------------------------------
hw = np.zeros(len(co))
gi = body.vertex_groups['mixamorig:Head'].index
for v in me.vertices:
    for g in v.groups:
        if g.group == gi:
            hw[v.index] = g.weight
hco = np.array([tuple(v.co) for v in head.data.vertices]); lo, hi = hco.min(0), hco.max(0)
inbox = np.all((co > lo) & (co < hi), axis=1)
ins = np.array([bool(b) and inside_head(Vector(c))[0] for c, b in zip(co, inbox)])
bbm = bmesh.new(); bbm.from_mesh(me)
doomed = [f for f in bbm.faces if (np.mean([hw[v.index] for v in f.verts]) > 0.5 and not wing[[v.index for v in f.verts]].any())
          or all(ins[v.index] for v in f.verts)]
print('BODY faces deleted', len(doomed), 'of', len(bbm.faces))
bmesh.ops.delete(bbm, geom=doomed, context='FACES')
loose = [v for v in bbm.verts if not v.link_faces]
bmesh.ops.delete(bbm, geom=loose, context='VERTS')
boundary = {v for e in bbm.edges if e.is_boundary for v in e.verts}
moved = 0
for v in boundary:
    inside, loc, nrm = inside_head(v.co)
    if (v.co - loc).length > NEAR:     # other open edges of the Meshy body (e.g. a hole at the right foot) stay put
        continue
    if not inside:
        v.co = loc - nrm * INSET; moved += 1
print('BODY boundary verts', len(boundary), 'pulled inside the head', moved)
bbm.to_mesh(me); bbm.free(); me.update()

# ---- head: the lowest neck band is pulled just inside the body's surface (feathered by height), burying its rim ----
body_bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get(), deform=False)
hz = np.array([v.co.z for v in head.data.vertices]); z0 = hz.min()
pulled = 0
for v in head.data.vertices:
    w = 1.0 - (v.co.z - z0) / BAND
    if w <= 0:
        continue
    loc, nrm, _, d = body_bvh.find_nearest(v.co)
    if loc is None or d > 0.04 or (v.co - loc).dot(nrm) <= -INSET:
        continue
    w = w * w * (3 - 2 * w)
    v.co = v.co.lerp(loc - nrm * INSET, w); pulled += 1
print('HEAD neck band verts pulled under the body surface', pulled)

# ---- join: head becomes material slot 1 of the body object ---------------------------------------------------------
if len(me.materials) == 0:
    me.materials.append(bpy.data.materials.new('Demon'))
head_mat = bpy.data.materials.new('DemonHead')
head.data.materials.clear(); head.data.materials.append(head_mat)
for o in (body, head):
    o.data.uv_layers.active.name = 'UVMap'
    while len(o.data.uv_layers) > 1:
        o.data.uv_layers.remove(next(l for l in o.data.uv_layers if not l.active))
for name in {k for w in head_weights for k in w}:
    vg = head.vertex_groups.get(name) or head.vertex_groups.new(name=name)
for i, w in enumerate(head_weights):
    for k, x in w.items():
        head.vertex_groups[k].add([i], x, 'REPLACE')
n_body = len(me.vertices)
for o in bpy.context.view_layer.objects:
    o.select_set(o in (body, head))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data
mats = list(me.materials)
print('MATERIALS', [m.name for m in mats], 'verts body', n_body, 'head', len(me.vertices) - n_body)
unweighted = sum(1 for v in me.vertices if not v.groups)
print('UNWEIGHTED', unweighted)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_head.blend'))
print('SAVED rig_head.blend')
