"""Dump Body vertices (world), edges, faces (triangulated) and piece ids to an npz. Args: -- <blend> <out npz>"""
import bpy, sys, os
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
import numpy as np
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']; me = ob.data
co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges])
me.calc_loop_triangles()
F = np.array([tuple(t.vertices) for t in me.loop_triangles])
pv = np.zeros(len(co), np.int32)
if 'piece' in me.attributes: me.attributes['piece'].data.foreach_get('value', pv)
np.savez(out, co=co, E=E, F=F, piece=pv)
print('DUMP', len(co), len(F))
