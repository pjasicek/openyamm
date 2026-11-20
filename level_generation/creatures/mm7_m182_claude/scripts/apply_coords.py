"""Write a vertex-coordinate array into a blend's Body. Usage: apply_coords.py -- <in.blend> <coords.npy> <out.blend>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); me = bpy.data.objects['Body'].data; co = np.load(a[1])
assert len(co) == len(me.vertices)
me.vertices.foreach_set('co', co.astype(np.float32).ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[2]); print('APPLIED', len(co))
