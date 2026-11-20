"""Keep the library's breathing and looking motion with its fitted two-hand raised carry."""
import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/review_before_20261023/lancer_complete.blend'))
rig=bpy.data.objects['Rig']; rig.animation_data_create();scene=bpy.context.scene
source=bpy.data.actions['Carbine_Fidget']
rig.animation_data.action=source;rig.animation_data.action_slot=source.slots[0];scene.frame_set(15)
roots=[rig.data.bones[f'B_{s}_Clavicle'] for s in 'LR']
names={b.name for root in roots for b in [root,*root.children_recursive]}
carry={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
for name in ['Carbine_Standing','Carbine_Fidget']:
    action=bpy.data.actions[name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    for frame in range(int(action.frame_range[0]),int(action.frame_range[1])+1):
        scene.frame_set(frame)
        for n,m in carry.items():
            bone=rig.pose.bones[n];bone.matrix_basis=m
            bone.keyframe_insert('rotation_quaternion',frame=frame)
            bone.keyframe_insert('location',frame=frame)
    print('READY',name,action.frame_range[:])
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/lancer_review2.blend'))
