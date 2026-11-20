"""Dump Body vertex positions, piece ids and edges of a blend to work/pieces.npz (analysis helper). Args: -- <blend>"""
import bpy, sys, os
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
me = bpy.data.objects['Body'].data
co = np.array([tuple(bpy.data.objects['Body'].matrix_world @ v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
E = np.array([tuple(e.vertices) for e in me.edges])
np.savez(os.path.join(HERE, 'work', 'pieces.npz'), co=co, pv=pv, E=E)
print('DUMP', len(co))
