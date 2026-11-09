"""Fit the free arm's spacing around the Swordsman's wider cloak; no changes to the sword arm."""
import bpy,sys,math,runpy
from pathlib import Path
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v15_clearance.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene
for role in ['Running','Hit']:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 end=int(a.frame_range[1]);poses=[]
 for f in range(end+1):
  sc.frame_set(f)
  chest=r.pose.bones['B_Spine2'];D=chest.matrix@chest.bone.matrix_local.inverted()
  forward=(D.to_3x3()@Vector((0,-1,0) if role=='Running' else (-1,0,0))).normalized()
  pb=r.pose.bones['B_L_UpperArm'];M=pb.matrix.copy()
  angle=math.radians(10 if role=='Running' else 20*math.sin(math.pi*f/end))
  R=Matrix.Rotation(angle,3,forward)@M.to_3x3();Mnew=R.to_4x4();Mnew.translation=M.translation
  poses.append(Mnew)
 for f,M in enumerate(poses):
  sc.frame_set(f);pb=r.pose.bones['B_L_UpperArm'];pb.matrix=M
  pb.keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v15.blend'))
sys.argv=['g6_contacts.py','--',str(p/'work/rig_v15.blend'),'Running','Hit']
runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
