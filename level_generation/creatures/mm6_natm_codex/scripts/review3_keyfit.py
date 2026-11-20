"""Fit the attack through feasible native key poses, preserving the library-derived body and planted legs."""
import bpy,sys,json,math,importlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,common
D=json.loads((P/'work/round3_pose_reference.json').read_text());base={n:Matrix(v)for n,v in D['standing_basis'].items()};impact=json.loads((P/'work/round3_feasible_impacts.json').read_text())[5];lg=json.loads((P/'work/round3_left_grip.json').read_text());poses=[]
def ease(t):
 t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round3_key_baseline/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
 if level==0:
  import arm_ik as IK;importlib.reload(IK);left=IK.Side('L');left.grip_hand=Vector(lg['handle_centre_hand_local']);rows=[]
  for f in range(77):C.activate('Attack',f/48);rows.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
  r.animation_data.action=None;names=[f'B_{sd}_{part}'for sd in 'LR'for part in ['UpperArm','Forearm','Hand']];keys={0:{n:base[n].to_quaternion()for n in names},21:{n:rows[21][n].to_quaternion()for n in names},34:{n:Quaternion(impact['bones'][n])for n in names},50:{n:Quaternion(impact['bones'][n])for n in names},76:{n:base[n].to_quaternion()for n in names}}
  for n,m in rows[34].items():r.pose.bones[n].matrix_basis=m
  for n,q in keys[34].items():r.pose.bones[n].rotation_quaternion=q
  bpy.context.view_layer.update();hand=r.pose.bones['B_L_Hand'];sp=r.pose.bones['Spear'].matrix;sol=left.pose_anatomical(sp@Vector((0,0,impact['spacing'])),hand.matrix.to_3x3(),r.pose.bones['B_L_Forearm'].head-r.pose.bones['B_L_UpperArm'].head);left.apply(sol)
  for n in names:
   if '_L_'in n:keys[34][n]=keys[50][n]=r.pose.bones[n].rotation_quaternion.copy()
  bpy.context.view_layer.update();relL=r.pose.bones['Spear'].matrix.inverted()@r.pose.bones['B_L_Hand'].matrix
  previous_tw={};coil=Vector((0,-.70710678,.70710678)).rotation_difference(Vector((.5,0,.8660254)))
  for f,row in enumerate(rows):
   for n,m in row.items():r.pose.bones[n].matrix_basis=m
   ks=[0,21,34,50,76]
   for j in range(4):
    if f<=ks[j+1]:break
   t=(f-ks[j])/(ks[j+1]-ks[j]);blend=ease(t)
   for n in names:r.pose.bones[n].rotation_quaternion=keys[ks[j]][n].slerp(keys[ks[j+1]][n],blend)
   for n in ['B_L_ForearmTwist','B_R_ForearmTwist','B_L_UpperArmTwist','B_R_UpperArmTwist']:r.pose.bones[n].matrix_basis=base[n]
   for n,q in IK.GDATA['finger_local'].items():r.pose.bones[n].rotation_quaternion=Quaternion(q)
   close=ease((f-20)/14)*(1-ease((f-43)/18))
   for n,q in lg['finger_local'].items():r.pose.bones[n].rotation_quaternion=base[n].to_quaternion().slerp(Quaternion(q),close)
   bpy.context.view_layer.update()
   # Native wind-up carries the spear diagonally upward across the facing, then drives it forward.
   amount=ease(f/21)*(1-ease((f-21)/13))
   if amount:
    if f==0:
     # The original wind-up shaft direction was diagonal in depth; match the native's lateral/upward silhouette.
     old_axis=Vector((0,-.70710678,.70710678));coil=old_axis.rotation_difference(Vector((.5,0,.8660254)))
    b=r.pose.bones['B_R_Clavicle'];m=b.matrix.copy();q=Quaternion().slerp(coil,amount);rotation=q.to_matrix()@m.to_3x3();m2=rotation.to_4x4();m2.translation=m.translation;b.matrix=m2;bpy.context.view_layer.update()
   # Carry the body farther over the planted front leg for the native full lunge.
   drive=ease((f-21)/13)*(1-ease((f-43)/33))
   if drive:
    targets={sd:r.pose.bones[f'B_{sd}_Foot'].matrix.copy()for sd in 'LR'}
    m=r.pose.bones['B_Pelvis'].matrix.copy();m.translation.y-=.24*drive;r.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update();targets['L'].translation.y-=.20*drive
    for sd in 'LR':
     ns=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H,K,A=[r.pose.bones[n].head.copy()for n in ns];aa=(K-H).length;bb=(A-K).length;target=targets[sd].translation;u=(target-H).normalized();dist=min((target-H).length,(aa+bb)*.997);v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();xx=(aa*aa+dist*dist-bb*bb)/(2*dist);knee=H+u*xx+v*math.sqrt(max(0,aa*aa-xx*xx))
     for n,c,T in [(ns[0],ns[1],knee),(ns[1],ns[2],H+u*dist)]:
      pb=r.pose.bones[n];q=(r.pose.bones[c].head-pb.head).rotation_difference(T-pb.head);m=(q@pb.matrix.to_quaternion()).to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
     pb=r.pose.bones[ns[2]];m=targets[sd].copy();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
   if f>50:
    angle=math.radians(32)*math.sin(math.pi*(f-50)/26)**2
    for sd in 'LR':
     pb=r.pose.bones[f'B_{sd}_UpperArm'];m=pb.matrix.copy();q=Quaternion((0,-1,0),angle*(1 if sd=='L'else-1));m2=(q@pb.matrix.to_quaternion()).to_matrix().to_4x4();m2.translation=m.translation;pb.matrix=m2;bpy.context.view_layer.update()
   for sd in 'LR':
    fn=f'B_{sd}_Forearm';hn=f'B_{sd}_Hand';un=f'B_{sd}_UpperArm';fb=r.data.bones[fn];hb=r.data.bones[hn];ub=r.data.bones[un];ax=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(r.pose.bones[fn].matrix.inverted()@r.pose.bones[hn].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=IK.swing_twist_deg(rel@rr.inverted(),ax)[1]
    if sd in previous_tw:
     while tw-previous_tw[sd]>180:tw-=360
     while tw-previous_tw[sd]<-180:tw+=360
    previous_tw[sd]=tw
    if sd=='R':r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(ax,math.radians(max(-80,min(80,.6*tw))))
    ax=(ub.matrix_local.inverted()@fb.head_local).normalized();tw=IK.swing_twist_deg(r.pose.bones[un].rotation_quaternion,ax)[1];r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*tw))
   bpy.context.view_layer.update();poses.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
 a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];previous={}
 for f,row in enumerate(poses):
  for n,m in row.items():
   # Bake the full corrected pose, including the discrete leg placement and shoulder wind-up.
   b=r.pose.bones[n];b.matrix_basis=m;q=b.rotation_quaternion
   if n in previous and previous[n].dot(q)<0:q.negate()
   previous[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f,group=n)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
 if level==0:
  bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'));common.workbench_clay(sc)
  for f in [21,28,31,34,43,55,65]:
   C.activate('Attack',f/48);common.render_views(str(P/f'review/round3_motion/keyfit_{f:02}'),.9,2.6,views=('front','left','three_quarter'),resolution=(650,750),target=(0,-.15))
