"""Joint heights at chosen frames of one action (world z/x/y of pelvis, spine, head, hands, feet). Args: -- <blend> <action> <frames,..>"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); rig = bpy.data.objects['Rig']; act = bpy.data.actions[a[1]]
rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
for f in [int(x) for x in a[2].split(',')]:
    bpy.context.scene.frame_set(f)
    print('POSE', a[1], f, {n: [round(v, 2) for v in (rig.matrix_world @ rig.pose.bones[n].head)] for n in
                           ('B_Pelvis', 'B_Spine2', 'B_Head', 'B_L_Hand', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot')})
if len(a) > 3:                                     # lowest vertices at the last listed frame: garment and dominant bone
    import numpy as np
    body = bpy.data.objects['Body']; me = body.data; vg = [g.name for g in body.vertex_groups]
    gv = np.array([x.value for x in me.attributes['garment'].data])
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
    TR = {'B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head'}
    dom = [vg[max(v.groups, key=lambda e: e.weight).group] if v.groups else '' for v in me.vertices]
    sel = [i for i in np.argsort(z) if (dom[i] in TR) == (len(a) > 4)][:int(a[3])]
    for i in sel:
        v = me.vertices[int(i)]
        print('LOW', round(float(z[i]), 3), 'garment', int(gv[i]), vg[max(v.groups, key=lambda e: e.weight).group] if v.groups else None)
