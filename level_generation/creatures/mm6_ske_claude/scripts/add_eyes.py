"""Red glowing eye points (native: a bright red dot deep in each socket): find each eye socket by ray-casting the
cranium (piece 2000) from the front on a grid (the socket is the deepest hollow on each side above the nose), and put
a small low-poly sphere (piece 2010, material 'Eyes', on Head) at the socket's centre just in front of its floor.
Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Skeleton_Rig']; body = bpy.data.objects['Skeleton']; me = body.data
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
pv = np.zeros(len(me.vertices), dtype=np.int32); me.attributes['piece'].data.foreach_get('value', pv)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if pv[v.index] != 2000], context='VERTS')
co = np.array([tuple(v.co) for v in bm.verts])
tree = BVHTree.FromBMesh(bm)
lo, hi = co.min(0), co.max(0)
cx = (lo[0] + hi[0]) / 2
eyes = []
for side in (-1, 1):
    best = []
    # sockets: about 2.5 cm either side of the midline, a third of the way up the cranium (front render)
    for x in np.linspace(cx + side * 0.013, cx + side * 0.037, 25):
        for z in np.linspace(lo[2] + (hi[2] - lo[2]) * 0.24, lo[2] + (hi[2] - lo[2]) * 0.46, 30):
            hit = tree.ray_cast(Vector((x, lo[1] - 0.1, z)), Vector((0, 1, 0)), 1.0)
            if hit[0] is not None and hit[0].y < lo[1] + 0.05:     # through the opening = skull interior: skip
                best.append((hit[0].y, x, z))
    best.sort(reverse=True)
    deep = np.array(best[:12])                   # deepest hits on this side = the socket floor
    y, x, z = deep[:, 0].mean(), deep[:, 1].mean(), deep[:, 2].mean()
    eyes.append(Vector((x, y - 0.006, z)))
    print('EYE', 'right' if side < 0 else 'left', np.round([x, y, z], 4), 'depth from face', round(y - lo[1], 4))
bm.free()
R = 0.0065
emat = bpy.data.materials.get('Eyes') or bpy.data.materials.new('Eyes')
emat.diffuse_color = (1.0, 0.08, 0.04, 1)
me.materials.append(emat) if 'Eyes' not in me.materials else None
ei = list(me.materials).index(me.materials['Eyes'])
for c in eyes:
    m2 = bpy.data.meshes.new('Eye'); b2 = bmesh.new()
    bmesh.ops.create_uvsphere(b2, u_segments=8, v_segments=6, radius=R)
    b2.to_mesh(m2); b2.free()
    o = bpy.data.objects.new('Eye', m2); bpy.context.scene.collection.objects.link(o)
    o.location = c
    for p in m2.polygons:
        p.material_index = 0; p.use_smooth = True
    m2.materials.append(emat)
    g = o.vertex_groups.new(name='mixamorig:Head'); g.add(list(range(len(m2.vertices))), 1.0, 'REPLACE')
    m2.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [2010] * len(m2.vertices))
    m2.uv_layers.new(name='UVMap')
    for o2 in bpy.data.objects:
        o2.select_set(o2 in (o, body))
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
print('EYES tris', sum(len(p.vertices) - 2 for p in me.polygons if p.material_index == ei))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
