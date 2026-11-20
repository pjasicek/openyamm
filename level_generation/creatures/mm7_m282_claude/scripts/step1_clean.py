"""Step 1 (Medusa): Smart Topology return -> work/step1.blend with one mesh 'Body' (adapted from mm7_m278_claude).
Rotated about Z by YAW degrees (env, so the face looks along -Y and the tail runs back along +Y), total height normalised
to HEIGHT m, lowest point at z = 0, the upright column centred at x = y = 0. Point attributes: 'piece' (loose part index
by connectivity, 0 = the largest), 'orig_co'. Nothing is edited. Args: -- <glb> <out blend>"""
import bpy, bmesh, sys, os, math
import numpy as np
HEIGHT = 1.8
YAW = float(os.environ.get('YAW', '0'))
glb, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in list(bpy.data.objects):
    if o is not ob:
        bpy.data.objects.remove(o, do_unlink=True)
me = ob.data
co = np.array([tuple(v.co) for v in me.vertices])
c, s_ = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
co = co @ np.array([[c, s_, 0], [-s_, c, 0], [0, 0, 1]])
s = HEIGHT / (co[:, 2].max() - co[:, 2].min())
co = (co - [0, 0, co[:, 2].min()]) * s
upper = co[co[:, 2] > 0.55 * HEIGHT]                 # the upright torso/column decides the horizontal origin
cx = (np.percentile(upper[:, 0], 5) + np.percentile(upper[:, 0], 95)) / 2
low = co[(co[:, 2] > 0.25 * HEIGHT) & (co[:, 2] < 0.45 * HEIGHT)]
cy = (np.percentile(low[:, 1], 5) + np.percentile(low[:, 1], 95)) / 2
co -= [cx, cy, 0]
me.vertices.foreach_set('co', co.ravel()); me.update()
ob.name = me.name = 'Body'
me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
label = -np.ones(len(co), np.int64); parts = []
for v in bm.verts:
    if label[v.index] >= 0:
        continue
    stack = [v]; label[v.index] = len(parts); comp = [v.index]
    while stack:
        x = stack.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if label[y.index] < 0:
                label[y.index] = len(parts); stack.append(y); comp.append(y.index)
    parts.append(comp)
bm.free()
order = np.argsort([-len(p) for p in parts])
rank = np.empty(len(parts), np.int64); rank[order] = np.arange(len(parts))
piece = rank[label].astype(np.int32)
me.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', piece)
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
np.savez_compressed(os.path.join(os.path.dirname(os.path.abspath(out)), 'step1_mesh.npz'), co=co, piece=piece,
                    tri=np.array([list(t.vertices) for t in (me.calc_loop_triangles() or me.loop_triangles)]))
print('CLEAN verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'pieces', len(parts),
      'sizes', [len(parts[i]) for i in order[:12]], 'scale', round(s, 4), 'extent', np.round(co.min(0), 3), np.round(co.max(0), 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
