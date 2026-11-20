"""Rest vertices and part ids of the master. Args: <blend> <npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices]); pid = np.zeros(len(co), np.int32); me.attributes['pid'].data.foreach_get('value', pid)
np.savez(a[1], co=co, pid=pid)
print('DUMP', len(co))
