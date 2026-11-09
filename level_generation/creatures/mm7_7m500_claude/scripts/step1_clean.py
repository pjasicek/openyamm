"""Step 1 (Rat): Smart Topology return -> work/step1.blend with one mesh 'Body'.
Length (y extent, snout to tail tip) normalised to LENGTH m, lowest point (paws) at
z = 0, centred in x/y, facing -Y (as returned). Point attributes: 'piece' (loose part index by connectivity, 0 = the largest = skin), 'orig_co' (positions
as uploaded to Meshy's auto-rig, for the nearest-vertex weight transfer). Nothing is edited.
Args: -- <glb> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
LENGTH = float(os.environ.get("LENGTH", "0.95"))   # 7m500 cat: nose to tail tip
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
s = LENGTH / (co[:, 1].max() - co[:, 1].min())
co = (co - np.array([(co[:, 0].max() + co[:, 0].min()) / 2, (co[:, 1].max() + co[:, 1].min()) / 2, co[:, 2].min()])) * s
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
print('CLEAN verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'pieces', len(parts),
      'skin verts', int((piece == 0).sum()), 'scale', round(s, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
