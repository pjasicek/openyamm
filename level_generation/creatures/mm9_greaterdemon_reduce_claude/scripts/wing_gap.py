"""Wing attachment gap on a runtime GLB (the measure of ../mm9_greaterdemon_claude/scripts/wing_review.py, which needs the
master blend's 'piece'/'anchor' attributes): anchors = wing vertices (membrane material, and wing-bone pieces = connected
pieces of the body material dominated by Xwing*/Xwarm* weights) that carry any non-wing bone weight (> 0.01) and lie inside
or within 3 cm of the body skin in the bind pose: the membrane's body line and the buried root of the arm. Per clip (the creature's nine role clips, every 2nd frame) the largest
signed distance of an anchor outside the posed body skin (body-material pieces that are not wing bones; sign by the
nearest face normal). Usage: blender -b -P wing_gap.py -- <glb> <out.json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
glb, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
o = bpy.data.objects['GreaterDemon']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
me = o.data
mats = [m.name.split('.')[0] for m in me.materials]
gname = {g.index: g.name for g in o.vertex_groups}
wingbone_g = {i for i, n in gname.items() if n.startswith(('Xwing', 'Xwarm'))}
nv = len(me.vertices)
nonwing = np.array([sum(g.weight for g in v.groups if g.group not in wingbone_g) for v in me.vertices])
dom_wing = np.array([max(v.groups, key=lambda g: g.weight).group in wingbone_g if len(v.groups) else False for v in me.vertices])
vmat = np.full(nv, -1)
for p in me.polygons:
    for i in p.vertices:
        vmat[i] = p.material_index
# body-material pieces by connectivity (welded by position)
bm = bmesh.new(); bm.from_mesh(me)
key = {}
for v in bm.verts:
    key.setdefault(tuple(round(c, 5) for c in v.co), []).append(v.index)
parent = list(range(nv))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for vs in key.values():
    for j in vs[1:]:
        parent[find(j)] = find(vs[0])
for e in me.edges:
    a, b = find(e.vertices[0]), find(e.vertices[1])
    if a != b:
        parent[a] = b
root = np.array([find(i) for i in range(nv)])
bm.free()
body_i = mats.index('GreaterDemon'); wing_i = mats.index('GreaterDemon_Wing')
piece_wing = {}
for r in np.unique(root[vmat == body_i]):
    m = (root == r) & (vmat == body_i); piece_wing[r] = dom_wing[m].mean() > 0.5
is_wingbone = np.array([vmat[i] == body_i and piece_wing.get(root[i], False) for i in range(nv)])
anchors = np.flatnonzero(((vmat == wing_i) | is_wingbone) & (nonwing > 0.01))
skin_faces = [p.index for p in me.polygons if p.material_index == body_i and not is_wingbone[p.vertices[0]]]
print('ANCHORS', len(anchors), 'skin faces', len(skin_faces))
sc = bpy.context.scene
acts = [a for a in bpy.data.actions if a.name in ('Standing', 'Walking', 'Running', 'Fidget', 'AttackMelee', 'AttackRanged',
                                                  'Hit', 'Death', 'Dead')]
rig.animation_data_create()


def posed():
    dg = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(dg).to_mesh()
    co = np.array([tuple(o.matrix_world @ v.co) for v in ev.vertices])
    polys = [tuple(ev.polygons[f].vertices) for f in skin_faces]
    o.evaluated_get(dg).to_mesh_clear(); return co, polys


def signed(co, polys):
    bv = BVHTree.FromPolygons([tuple(c) for c in co], polys)
    d = []
    for i in anchors:
        loc, nrm, _, dd = bv.find_nearest(Vector(co[i]))
        d.append(dd if (Vector(co[i]) - loc).dot(nrm) > 0 else -dd)
    return np.array(d)


rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co, polys = posed(); d0 = signed(co, polys)
# as wing_review.py: the anchors are the attachment vertices, inside or within 3 cm of the body in the bind pose (the
# Coons-blended membrane interior also carries some body weight but hangs free of the body)
anchors = anchors[d0 < 0.03]; d0 = d0[d0 < 0.03]
print('ANCHORS attached', len(anchors))
per_anchor = d0.copy()
res = {'anchors': int(len(anchors)), 'bind_outside_5mm': int((d0 > 0.005).sum()), 'bind_max_m': round(float(d0.max()), 4), 'clips': {}}
for act in acts:
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); mx = (-1.0, 0)
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f); co, polys = posed(); d = signed(co, polys); per_anchor = np.maximum(per_anchor, d)
        if d.max() > mx[0]:
            mx = (float(d.max()), f)
    res['clips'][act.name] = {'max_outside_m': round(mx[0], 4), 'frame': mx[1]}
    print('GAP', act.name, res['clips'][act.name], flush=True)
res['per_anchor'] = [[round(float(x), 5) for x in me.vertices[int(i)].co] + [round(float(v), 4)] for i, v in zip(anchors, per_anchor)]
json.dump(res, open(out, 'w'), indent=1)
print('WINGGAP', json.dumps(res))
