"""Open the dog's mouth slit along the lip line. The Smart Topology head has a real mouth pocket (palate, floor, back
wall; head_section.py) but the 3.5 mm voxel pass fused the narrow slit along the sides, so upper and lower jaw are one
skin. A thin wedge (flat in plan, across the whole snout, tapering to nothing at the mouth corners) is cut from the
main body by an exact Boolean, the body is voxelised again (one closed surface, rolled lips) and the 'chain' attribute
is carried over from the nearest old vertex. Separate pieces (teeth, eyes, claws) are untouched.

Args: <in blend> <out blend> <report json> <y corner> <half thickness> <z at y=-0.5> <dz/dy> <voxel>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
YC, H0, Z0, SLOPE, VOX = [float(x) for x in argv[3:8]]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
co = np.array([tuple(v.co) for v in me.vertices])


def part(name, keep_body):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if (piece[v.index] == 0) != keep_body], context='VERTS')
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    for a in list(m.attributes):
        if a.name in ('piece', 'chain'):
            m.attributes.remove(a)
    o = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(o)
    o.matrix_world = body.matrix_world
    return o


skin = part('Skin', True)
parts = part('Parts', False)
# the wedge
stations = np.r_[np.linspace(-0.62, YC - 0.04, 3), np.linspace(YC - 0.03, YC, 9)]
bm = bmesh.new()
top, bot = [], []
for y in stations:
    t = np.clip((YC - y) / 0.03, 0, 1)
    h = max(H0 * t * t * (3 - 2 * t), 0.0003)
    z = Z0 + SLOPE * (y + 0.5)
    for x, tl, bl in ((-0.24, top, bot), (0.24, top, bot)):
        tl.append(bm.verts.new((x, float(y), z + h)))
        bl.append(bm.verts.new((x, float(y), z - h)))
n = len(stations)
for i in range(n - 1):
    a, b, c, d = top[2 * i], top[2 * i + 1], top[2 * i + 3], top[2 * i + 2]
    bm.faces.new((a, b, c, d))
    a, b, c, d = bot[2 * i], bot[2 * i + 2], bot[2 * i + 3], bot[2 * i + 1]
    bm.faces.new((a, b, c, d))
    bm.faces.new((top[2 * i], top[2 * i + 2], bot[2 * i + 2], bot[2 * i]))
    bm.faces.new((top[2 * i + 1], bot[2 * i + 1], bot[2 * i + 3], top[2 * i + 3]))
bm.faces.new((top[0], bot[0], bot[1], top[1]))
bm.faces.new((top[-2], top[-1], bot[-1], bot[-2]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
cm = bpy.data.meshes.new('Cutter'); bm.to_mesh(cm); bm.free()
cutter = bpy.data.objects.new('Cutter', cm); bpy.context.scene.collection.objects.link(cutter)
for o in bpy.data.objects:
    o.select_set(o == skin)
bpy.context.view_layer.objects.active = skin
mod = skin.modifiers.new('cut', 'BOOLEAN')
mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter
bpy.ops.object.modifier_apply(modifier='cut')
skin.data.remesh_voxel_size = VOX
skin.data.remesh_voxel_adaptivity = 0.0
bpy.ops.object.voxel_remesh()
sm = skin.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 2
bpy.ops.object.modifier_apply(modifier='smooth')
# the voxel pass can leave a thin bridge beside the teeth: the same wedge again, no voxel pass after it
mod = skin.modifiers.new('cut2', 'BOOLEAN')
mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter
bpy.ops.object.modifier_apply(modifier='cut2')
bpy.data.objects.remove(cutter)
# keep the largest shell (the wedge can pinch off crumbs)
b3 = bmesh.new(); b3.from_mesh(skin.data); b3.verts.ensure_lookup_table()
seen, comps = set(), []
for v in b3.verts:
    if v.index in seen:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    comps.append(c)
big = set(max(comps, key=len))
bmesh.ops.delete(b3, geom=[v for v in b3.verts if v not in big], context='VERTS')
b3.to_mesh(skin.data); b3.free()
# attributes back
k = KDTree(int((piece == 0).sum()))
idx = np.nonzero(piece == 0)[0]
for j, i in enumerate(idx):
    k.insert(co[i], j)
k.balance()
new_chain = [int(chain[idx[k.find(v.co)[1]]]) for v in skin.data.vertices]
a = skin.data.attributes.new('piece', 'INT', 'POINT'); b = skin.data.attributes.new('chain', 'INT', 'POINT')
for i, c in enumerate(new_chain):
    b.data[i].value = c
a2 = parts.data.attributes.new('piece', 'INT', 'POINT'); b2 = parts.data.attributes.new('chain', 'INT', 'POINT')
for i in range(len(parts.data.vertices)):
    a2.data[i].value = 2; b2.data[i].value = -1
for o in bpy.data.objects:
    o.select_set(o in (skin, parts))
bpy.context.view_layer.objects.active = skin
bpy.ops.object.join()
mw = body.matrix_world.copy()
bpy.data.objects.remove(body)
skin.name = 'Body'; skin.data.name = 'Body'
skin.matrix_world = mw
for p in skin.data.polygons:
    p.use_smooth = True
rep = {'shells': len(comps), 'verts': len(skin.data.vertices), 'tris': sum(len(p.vertices) - 2 for p in skin.data.polygons)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'))
print('CARVE ' + json.dumps(rep))
