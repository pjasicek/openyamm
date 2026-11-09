"""Dump the posed mesh (positions, garment) and every robe/sheet chain joint at one frame to an npz.
Args: -- <blend> <action> <frame> <out.npz>"""
import bpy, sys, os, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; act = bpy.data.actions[a[1]]
rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(float(a[2])), subframe=float(a[2]) % 1)
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
gv = np.array([x.value for x in body.data.attributes['garment'].data])
CH = json.loads(bpy.context.scene['cloak_chains'])
J = np.array([[list(rig.matrix_world @ rig.pose.bones[b].head) for b in c['bones']] + [list(rig.matrix_world @ rig.pose.bones[c['bones'][-1]].tail)] for c in CH])
np.savez(a[3], P=P, gv=gv, J=J)
print('DUMPPOSE', P.shape, J.shape)
