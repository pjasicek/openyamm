"""Hand faces only, for views. Args: <hands blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
for o in list(bpy.data.objects):
    if o is not b: bpy.data.objects.remove(o)
for m in list(b.modifiers): b.modifiers.remove(m)
h = np.zeros(len(me.polygons), int); me.attributes['hand'].data.foreach_get('value', h)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if h[f.index] == 0], context='FACES')
bm.to_mesh(me); bm.free()
Q = np.array([v.co[:] for v in me.vertices if v.co.x < 0]); print('HAND', Q.min(0).round(3), Q.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
