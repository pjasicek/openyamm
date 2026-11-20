import bpy,sys,runpy,math
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_final.blend'))
rig=bpy.data.objects['Rig'];s=bpy.context.scene;a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
rows=[]
for f in range(61):
 s.frame_set(f);w=max(0,min(1,(f-16)/22));w=w*w*(3-2*w);row={}
 back=rig.pose.bones['B_Pelvis'].head-rig.pose.bones['B_Spine2'].head;back.z=0
 if back.length<1e-5:back=Vector((0,1,0))
 back.normalize();back.z=-.08;back.normalize()
 for side in ('L','R'):
  for part,child in [('Thigh','Calf'),('Calf','Foot')]:
   n=f'B_{side}_{part}';b=rig.pose.bones[n];before=b.rotation_quaternion.copy();M=b.matrix.copy()
   direction=rig.pose.bones[f'B_{side}_{child}'].head-b.head
   Mnew=(direction.normalized().rotation_difference(back).to_matrix()@M.to_3x3()).to_4x4();Mnew.translation=M.translation
   b.matrix=Mnew;bpy.context.view_layer.update();q=before.slerp(b.rotation_quaternion,w);b.rotation_quaternion=q;bpy.context.view_layer.update();row[n]=q.copy()
 rows.append(row)
for f,row in enumerate(rows):
 for n,q in row.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/death_planar.blend'))
sys.argv=['skirt_sim.py','--',str(p/'work/death_planar.blend'),str(p/'work/motion_final.blend'),'Death']
runpy.run_path(str(p/'scripts/skirt_sim.py'),run_name='__main__')
sys.argv=['twist_bones.py','--',str(p/'work/motion_final.blend'),str(p/'work/motion_twist.blend')]
runpy.run_path(str(p/'scripts/twist_bones.py'),run_name='__main__')
for view in ('front','left','three_quarter'):
 sys.argv=['clip_sheet.py','--',str(p/'work/motion_twist.blend'),str(p/'review'/('settled_'+view)),view,'6','Run','Death']
 runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
