"""Blender decimate of an npz mesh with per-vertex protect (0..1). Args: <in npz> <out npz> <target tris>. Keeps seam/ring vertices by the group (protect 1 = untouched as far as COLLAPSE allows)."""
import bpy, bmesh, sys
import numpy as np
IN, OUT, TGT = sys.argv[sys.argv.index('--') + 1:]; TGT = int(TGT)
D = np.load(IN); co, tri, pr = D['co'], D['tri'], D['protect']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('m'); ob = bpy.data.objects.new('m', me); bpy.context.collection.objects.link(ob)
me.from_pydata(co.tolist(), [], tri.tolist()); me.update()
g = ob.vertex_groups.new(name='free')
for i, v in enumerate(pr): g.add([i], float(1 - v), 'REPLACE')
ob['oid'] = 1
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
at = me.attributes.new('oid', 'INT', 'POINT'); at.data.foreach_set('value', list(range(len(co))))
m = ob.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = min(1, TGT / len(tri)); m.use_collapse_triangulate = True; m.vertex_group = 'free'; m.vertex_group_factor = 1.0
bpy.ops.object.modifier_apply(modifier='d')
me = ob.data
print('REDUCED', len(tri), '->', len(me.polygons))
Q = np.array([v.co[:] for v in me.vertices]); F = np.array([p.vertices[:] for p in me.polygons])
extra = {}
np.savez(OUT, co=Q, tri=F, oid=np.array([me.attributes['oid'].data[i].value for i in range(len(Q))]) if 'oid' in me.attributes else np.zeros(len(Q)))
