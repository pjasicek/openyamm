import sys,runpy,os,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('author_carry.py',P/'work/pilot.blend',P/'work/pilot_carry.blend','Standing:0.15','Walking:0.2')
import bpy
from mathutils import Matrix
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_carry.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
poses=[]
for f in range(int(act.frame_range[1])+1):
 scene.frame_set(f);pb=rig.pose.bones['B_Spine'];d=rig.pose.bones['B_Neck'].head-pb.head
 lean=math.atan2(-d.y,d.z);m=pb.matrix.copy();t=m.translation.copy()
 m=Matrix.Rotation(-.6*lean,4,'X')@m;m.translation=t;pb.matrix=m;bpy.context.view_layer.update()
 poses.append(pb.rotation_quaternion.copy())
for f,q in enumerate(poses):
 pb=rig.pose.bones['B_Spine'];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilot_refined.blend'))
# Recompute twist from changed hand motion; weights are re-established before fingers.
run('twist_bones.py',P/'work/pilot_refined.blend',P/'work/pilot_twist.blend')
run('weights_fix.py',P/'work/pilot_twist.blend',P/'work/pilot_weight.blend')
run('finger_weights.py',P/'work/pilot_weight.blend',P/'work/pilot_final.blend')
run('g5_hand_stretch.py',P/'work/pilot_final.blend','Standing','Walking','Attack')
run('g4_weights.py',P/'work/pilot_final.blend','pilot','Standing:0','Walking:5','Attack:7','Attack:14','Attack:21','Attack:28')
run('sole_probe.py',P/'work/pilot_final.blend','Standing','Walking','Attack')
for view in ('front','left','three_quarter'):run('clip_sheet.py',P/'work/pilot_final.blend',P/f'review/pilot_refined_{view}',view,7,'Standing','Walking','Attack')
