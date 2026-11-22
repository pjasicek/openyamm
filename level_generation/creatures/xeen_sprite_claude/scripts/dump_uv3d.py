"""Per-triangle UVs, rest positions, normals and piece ids of 'Body' (bind pose) for the compose step.
Writes an npz: uv (T,3,2, glTF v-down image space 0..1), pos (T,3,3), nrm (T,3), piece (T,), vpos/vpiece per vertex.
Args: -- <blend> <out npz>"""
import bpy, sys, os
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
import numpy as np
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; ob = bpy.data.objects['Body']; me = ob.data
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me.calc_loop_triangles()
uvl = me.uv_layers['UVMap'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices])
T = me.loop_triangles
uv = np.array([[tuple(uvl[l].uv) for l in t.loops] for t in T]); uv[..., 1] = 1 - uv[..., 1]
vid = np.array([tuple(t.vertices) for t in T])
nrm = np.array([tuple(t.normal) for t in T])
np.savez(out, uv=uv, pos=co[vid], nrm=nrm, piece=pv[vid[:, 0]], vid=vid, vpos=co, vpiece=pv)
print('DUMPUV', len(T), 'triangles')
