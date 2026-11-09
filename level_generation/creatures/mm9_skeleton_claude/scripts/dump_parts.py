"""Dump vertices and faces per part to npz. Args: <blend> <npz>"""
import bpy, sys
import numpy as np
BL, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=BL)
o = bpy.data.objects['Meshy']; me = o.data
pa = next(a for a in me.attributes if a.data_type == 'INT' and a.name.startswith('part'))
p = np.zeros(len(me.vertices), int); pa.data.foreach_get('value', p)
v = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
f = np.array([q.vertices[:] for q in me.polygons])
np.savez(OUT, v=v, f=f, p=p)
