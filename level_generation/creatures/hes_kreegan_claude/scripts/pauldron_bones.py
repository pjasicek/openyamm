"""hkr: pauldron bones. A rigid pauldron on the clavicle let the raised upper arm push 4 cm into it (Attack); on the
upper arm it would scrape the neck. Bone B_<S>_Pauldron (child of B_<S>_Clavicle, head at the shoulder joint, the
upper arm's rest frame) turns by K (0.5) of the upper arm's swing relative to the clavicle (twist removed), baked
into every action; the shoulder-spike bone (Bone_041 / Bone_036) is re-parented to it, so the spikes stay where they
pierce the pauldron (their roots slide under it). Args: -- <in> <out>"""
import bpy, sys, os, math
from mathutils import Quaternion, Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
K = float(os.environ.get('K', '0.5'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
bpy.context.view_layer.objects.active = rig
rig.animation_data_create(); rig.animation_data.action = None
bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
for s, spk in (('L', 'Bone_041'), ('R', 'Bone_036')):
    n = f'B_{s}_Pauldron'
    if n in eb: eb.remove(eb[n])
    ua = eb[f'B_{s}_UpperArm']
    b = eb.new(n); b.head = ua.head.copy(); b.tail = ua.head + (ua.tail - ua.head).normalized() * 0.08; b.roll = ua.roll
    b.parent = eb[f'B_{s}_Clavicle']; b.use_deform = True
    eb[spk].parent = b
bpy.ops.object.mode_set(mode='OBJECT')
for act in [x for x in bpy.data.actions if x.use_fake_user]:
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    keys = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for s in 'LR':
            ua = rig.pose.bones[f'B_{s}_UpperArm']; pb = rig.pose.bones[f'B_{s}_Pauldron']
            # the upper arm's swing in the clavicle frame: rest direction -> posed direction (both in clavicle space)
            cl = rig.pose.bones[f'B_{s}_Clavicle']
            Mc = cl.matrix.to_3x3(); Mc_r = rig.data.bones[cl.name].matrix_local.to_3x3()
            d_rest = Mc_r.inverted() @ (rig.data.bones[ua.name].matrix_local.to_3x3().col[1])
            d_pose = Mc.inverted() @ ua.matrix.to_3x3().col[1]
            q = d_rest.rotation_difference(d_pose)
            q = Quaternion(q.axis, q.angle * K) if q.angle > 1e-6 else Quaternion()
            # as the pauldron's basis: rotation in clavicle space -> bone-local space
            Rb = (Mc_r.inverted() @ rig.data.bones[pb.name].matrix_local.to_3x3())
            keys[(f, s)] = (Rb.inverted() @ q.to_matrix() @ Rb).to_quaternion()
    for (f, s), q in keys.items():
        pb = rig.pose.bones[f'B_{s}_Pauldron']; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
        pb.keyframe_insert('rotation_quaternion', frame=f)
    print('PAULDRON baked', act.name, f0, f1)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[1]))
