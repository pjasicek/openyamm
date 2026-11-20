"""Body rest vertices, faces and part attribute (Blender axes) to npz. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['Body']; me = o.data
P = np.array([o.matrix_world @ v.co for v in me.vertices]); F = np.array([p.vertices[:] for p in me.polygons])
pa = np.zeros(len(P), int); me.attributes['part'].data.foreach_get('value', pa)
np.savez(a[1], P=P, F=F, part=pa); print('DUMP', P.shape, F.shape)
