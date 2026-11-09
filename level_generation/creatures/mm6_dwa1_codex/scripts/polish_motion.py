import bpy,sys,json,math,runpy
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));runpy.run_path(str(P/'scripts/fix_clothing.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;names=[b.name for b in rig.pose.bones];roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget'];report={}
standing=bpy.data.actions['Standing'];rig.animation_data.action=standing;rig.animation_data.action_slot=standing.slots[0];scene.frame_set(0);st={n:rig.pose.bones[n].rotation_quaternion.copy()for n in names}
for name in roles:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];poses=[];end=int(a.frame_range[1])
 for f in range(end+1):
  scene.frame_set(f);poses.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names})
 if name=='Fidget':
  target=poses[24]
  for f in range(24):
   u=f/24;u=u*u*(3-2*u)
   for n in names:
    if n.startswith(('B_L_','B_R_'))and any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand','Finger']):poses[f][n]=(st[n].slerp(target[n][0],u),poses[f][n][1])
 if name=='Death':
  for pose in poses:
   for n in ['B_Neck','B_Head']:pose[n]=(st[n].slerp(pose[n][0],.35),pose[n][1])
 rig.animation_data.action=None
 new=bpy.data.actions.new(name+'_clear');new.use_fake_user=True;prev={}
 for f,pose in enumerate(poses):
  rig.animation_data.action=None
  for n,(q,l)in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
  bpy.context.view_layer.update();axis=rig.pose.bones['B_Spine2'].matrix.to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,1,0))
  deg=5.
  for sd,sgn in [('R',1),('L',-1)]:
   pb=rig.pose.bones[f'B_{sd}_UpperArm'];M=pb.matrix.copy();c=M.translation.copy();M=Matrix.Rotation(math.radians(deg)*sgn,4,axis)@M;M.translation=c;pb.matrix=M;bpy.context.view_layer.update()
  rig.animation_data.action=new
  if len(new.slots):rig.animation_data.action_slot=new.slots[0]
  for n in names:
   pb=rig.pose.bones[n];q=pb.rotation_quaternion.copy()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 new.use_frame_range=True;new.frame_start=0;new.frame_end=end;rig.animation_data.action=None;bpy.data.actions.remove(a);new.name=name;report[name]={'arm_abduction_deg':5,'early_taunt_extra_peak_deg':17 if name=='Fidget'else 0}
(P/'work/motion_corrections.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_fixed.blend'))
