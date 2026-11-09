"""Dump rest positions and garments of the Body to an npz. Args: -- <blend> <out.npz>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
me = bpy.data.objects['Body'].data
np.savez(a[1], co=np.array([v.co[:] for v in me.vertices]), gv=np.array([x.value for x in me.attributes['garment'].data]),
         pv=np.array([x.value for x in me.attributes['piece'].data]))
print('DUMPREST', len(me.vertices))
