import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Guard_Rig']; mesh = bpy.data.objects['Guard']
act = bpy.data.actions[a[0]]; rig.animation_data.action = act
if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[1]))
dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg).to_mesh()
P = np.array([v.co[:] for v in ev.vertices]); R = np.array([v.co[:] for v in mesh.data.vertices])
gi = {g.index: g.name for g in mesh.vertex_groups}
vb = np.array([gi[v.groups[0].group] for v in mesh.data.vertices])
for b in ['B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand']:
    pb = rig.pose.bones[b]; m = vb == b
    print('ARM', b, 'pose head', np.round(pb.head, 3), 'tail', np.round(pb.tail, 3), '| rest head', np.round(pb.bone.head_local, 3), 'tail', np.round(pb.bone.tail_local, 3))
    print('PIECE rest min', R[m].min(0).round(3), 'max', R[m].max(0).round(3))
    print('PIECE pose min', P[m].min(0).round(3), 'max', P[m].max(0).round(3))
    print('BASIS q', np.round(pb.rotation_quaternion, 3), 'loc', np.round(pb.location, 3), 'mode', pb.rotation_mode)
