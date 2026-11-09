"""Head UVs only (uv_atlas.py), on the head faces of joined.blend; body corners of work/uv_dump.npz stay. Args: <blend> <uv npz> <out blend>"""
import bpy, sys, os, bmesh
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, NPZ, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data
head = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', head)
d = ob.copy(); d.data = me.copy(); bpy.context.scene.collection.objects.link(d)
bm = bmesh.new(); bm.from_mesh(d.data); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not head[f.index]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(d.data); bm.free(); d.data.update(); d.vertex_groups.clear()
for o in bpy.data.objects: o.select_set(o == d)
bpy.context.view_layer.objects.active = d
print('UVH', uv_atlas.unwrap(d, fine=200, steps=0))
bm = bmesh.new(); bm.from_mesh(d.data); uvl = bm.loops.layers.uv.active; bmesh.ops.triangulate(bm, faces=bm.faces)
pos = []; uv = []
for f in bm.faces:
    for l in f.loops: pos.append(tuple(l.vert.co)); uv.append(tuple(l[uvl].uv))
bm.free()
U = dict(np.load(NPZ)); U['ph'] = np.array(pos); U['uh'] = np.array(uv); np.savez(NPZ, **U)
d.name = 'HeadUV'; bpy.data.objects.remove(ob); bpy.ops.wm.save_as_mainfile(filepath=OUT)
