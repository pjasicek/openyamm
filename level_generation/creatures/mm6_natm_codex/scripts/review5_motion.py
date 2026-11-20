"""Short simultaneous world-space recovery using the accepted strike, skinning and geometry."""
import bpy,sys,json,math,importlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
B=P/'work/review_round5_before';end=57
bpy.ops.wm.open_mainfile(filepath=str(B/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
import arm_ik as IK;importlib.reload(IK);sides={s:IK.Side(s)for s in 'LR'};sides['L'].grip_hand=Vector(json.loads((P/'work/round3_left_grip.json').read_text())['handle_centre_hand_local'])
poses=[];basis={};world={}
for f in [45,108]:
 C.activate('Attack',f/48);basis[f]={b.name:b.matrix_basis.copy()for b in r.pose.bones};world[f]={b.name:b.matrix.copy()for b in r.pose.bones}
for f in range(end+1):
 C.activate('Attack',(f if f<=45 else 52+56*(f-45)/12)/48);poses.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
r.animation_data.action=None
for f in range(46,end+1):
 u=(f-45)/12;t=u*u*(3-2*u)
 for n,m in poses[f].items():r.pose.bones[n].matrix_basis=m
 for sd in 'LR':
  for n in r.pose.bones.keys():
   if n.startswith(f'B_{sd}_Finger'):r.pose.bones[n].rotation_quaternion=basis[45][n].to_quaternion().slerp(basis[108][n].to_quaternion(),u if sd=='L'else t)
 bpy.context.view_layer.update()
 for sd in 'LR':
  n=f'B_{sd}_Clavicle';pb=r.pose.bones[n];m=world[45][n].to_quaternion().slerp(world[108][n].to_quaternion(),t).to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
  solver=sides[sd];n=f'B_{sd}_Hand';hip=r.pose.bones['B_Pelvis'].head;h0=world[45]['B_Pelvis'].translation;h1=world[108]['B_Pelvis'].translation
  target=hip+(world[45][n]@solver.grip_hand-h0).lerp(world[108][n]@solver.grip_hand-h1,t)
  target.x+=(-.045 if sd=='R'else .22)*math.sin(math.pi*t)**2
  if sd=='L':target.y-=.28*math.sin(math.pi*t)**2
  if sd=='L'and f<49:target+=Vector((.06,-.02,-.04))*math.sin(math.pi*(f-45)/4)**2
  rh=world[45][n].to_quaternion().slerp(world[108][n].to_quaternion(),t).to_matrix()
  pole=(world[45][f'B_{sd}_Forearm'].translation-world[45][f'B_{sd}_UpperArm'].translation).lerp(world[108][f'B_{sd}_Forearm'].translation-world[108][f'B_{sd}_UpperArm'].translation,t)
  if sd=='L':
   normals=[]
   for key in [45,108]:
    shoulder=world[key]['B_L_UpperArm'].translation;elbow=world[key]['B_L_Forearm'].translation;wrist=world[key]['B_L_Hand'].translation;normals.append((elbow-shoulder).cross(wrist-elbow).normalized())
   normal=Quaternion().slerp(normals[0].rotation_difference(normals[1]),t)@normals[0]
   direction=target-rh@solver.grip_hand-r.pose.bones['B_L_UpperArm'].head;pole=direction.cross(normal)
  solver.apply(solver.pose_anatomical(target,rh,pole));bpy.context.view_layer.update()
  fn=f'B_{sd}_Forearm';hn=f'B_{sd}_Hand';un=f'B_{sd}_UpperArm';fb=r.data.bones[fn];hb=r.data.bones[hn];ub=r.data.bones[un];ax=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(r.pose.bones[fn].matrix.inverted()@r.pose.bones[hn].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=IK.swing_twist_deg(rel@rr.inverted(),ax)[1]
  if sd=='R':r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(ax,math.radians(max(-80,min(80,.6*tw))))
  ax=(ub.matrix_local.inverted()@fb.head_local).normalized();tw=IK.swing_twist_deg(r.pose.bones[un].rotation_quaternion,ax)[1];r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*tw))
 bpy.context.view_layer.update();poses[f]={b.name:b.matrix_basis.copy()for b in r.pose.bones}
poses[-1]=basis[108]
for iteration in range(3):
 old=[{n:m.copy()for n,m in row.items()}for row in poses]
 for f in range(47,end):
  for n in [f'B_L_{part}'for part in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']]:
   a=old[f-1][n].to_quaternion();b=old[f][n].to_quaternion();c=old[f+1][n].to_quaternion();q=b.slerp(a.slerp(c,.5),.4);m=q.to_matrix().to_4x4();m.translation=old[f][n].translation;poses[f][n]=m
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(B/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];bpy.data.actions.remove(bpy.data.actions['Attack']);a=bpy.data.actions.new('Attack');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=end;r.animation_data.action=a;previous={}
 for f,row in enumerate(poses):
  for n,m in row.items():
   pb=r.pose.bones[n];pb.matrix_basis=m;q=pb.rotation_quaternion
   if n in previous and previous[n].dot(q)<0:q.negate()
   previous[n]=q.copy();pb.rotation_quaternion=q
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group=n)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
s=(P/'scripts/quick_export.py').read_text().replace('range(4)','range(1)').replace('export/mm6_natm_raw_lod{level}.glb','work/round5_animation.glb');exec(compile(s,str(P/'scripts/quick_export.py'),'exec'))
