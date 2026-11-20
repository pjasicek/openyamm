"""Rest-pose top heights of the m414 body (rig_v6): overall, without the crest (piece 5), the head joint and the
shoulders; with SCALE (units per metre) printed in game units. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
z = np.array([(body.matrix_world @ v.co).z for v in me.vertices])
S = float(os.environ.get('SCALE', '1'))
vals = {'top (crest)': z[pv < 1000].max(), 'top without the crest': z[(pv < 1000) & (pv != 5)].max(),
        'head joint': rig.data.bones['B_Head'].head_local.z, 'shoulder': rig.data.bones['B_R_UpperArm'].head_local.z}
print('HEIGHTS', {k: (round(float(v), 3), round(float(v) * S, 1)) for k, v in vals.items()})
