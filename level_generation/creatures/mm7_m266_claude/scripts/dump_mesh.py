"""Dump 'Body' vertex positions, 'piece' labels and triangles to an .npz for numpy measurement outside Blender.
Args: -- <blend> <out npz>"""
import bpy, sys, os
import numpy as np
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects.get('Body') or next(o for o in bpy.data.objects if o.type == 'MESH'); me = ob.data
co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32)
if 'piece' in me.attributes:
    me.attributes['piece'].data.foreach_get('value', pv)
me.calc_loop_triangles()
tri = np.array([tuple(t.vertices) for t in me.loop_triangles])
np.savez(os.path.abspath(out), co=co, piece=pv, tri=tri)
print('DUMP', len(co), len(tri))
