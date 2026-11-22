"""Debug: posed bone heads and piece centroids for one clip frame. Args: -- clip frame"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Guard_Rig']; mesh = bpy.data.objects['Guard']
act = bpy.data.actions[a[0]]
rig.animation_data.action = act
if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[1]))
dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg).to_mesh()
P = np.array([v.co[:] for v in ev.vertices])
gi = {g.index: g.name for g in mesh.vertex_groups}
vb = np.array([gi[v.groups[0].group] for v in mesh.data.vertices])
R = np.array([v.co[:] for v in mesh.data.vertices])
for pb in rig.pose.bones:
    if 'L_' in pb.name or pb.name in ('B_Pelvis', 'B_Spine2', 'B_Head'):
        m = vb == pb.name
        print('BONE', pb.name, 'head', [round(x, 3) for x in pb.head], 'rest', [round(x, 3) for x in pb.bone.head_local],
              'posed centroid', P[m].mean(0).round(3) if m.any() else None, 'rest centroid', R[m].mean(0).round(3) if m.any() else None)
        print('   basis loc', [round(x, 3) for x in pb.location], 'q', [round(x, 3) for x in pb.rotation_quaternion])
