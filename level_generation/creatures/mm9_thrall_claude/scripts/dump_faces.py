"""All faces: rest positions, PartUV, mat; arm joints. Args: <uv blend> <out npz>"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
mat = np.zeros(len(me.polygons), int); me.attributes['mat'].data.foreach_get('value', mat)
uv = me.uv_layers['PartUV'].data
P = np.array([v.co[:] for v in me.vertices]); fv = np.array([p.vertices[:] for p in me.polygons]); fu = np.array([[uv[l].uv[:] for l in p.loop_indices] for p in me.polygons])
J = {f'{s}{k}': np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} {b}'].head_local) for s in 'LR' for k, b in (('u', 'UpperArm'), ('f', 'Forearm'))}
np.savez(a[1], co=P[fv], uv=fu, mat=mat, **J)
print('DUMP', fv.shape)
