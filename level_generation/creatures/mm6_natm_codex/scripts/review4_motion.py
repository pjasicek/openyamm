"""Fit the attack through feasible native key poses, preserving the library-derived body and planted legs."""
import bpy,sys,json,math,importlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,common
D=json.loads((P/'work/round3_pose_reference.json').read_text());base={n:Matrix(v)for n,v in D['standing_basis'].items()};impact=json.loads((P/'work/round4_right_grip_impacts.json').read_text())[0];lg=json.loads((P/'work/round3_left_grip.json').read_text());poses=[]
impact['spacing']=impact['spacing']

def ramp(t):
 t=max(0,min(1,t));r=1/3
 return .5*t*t/(r*(1-r))if t<r else 1-.5*(1-t)**2/(r*(1-r))if t>1-r else (t-r/2)/(1-r)
def ease(t):
 t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/review_round4_before/work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
 if level==0:
  import arm_ik as IK;importlib.reload(IK);right=IK.Side('R');left=IK.Side('L');left.grip_hand=Vector(lg['handle_centre_hand_local']);rows=[]
  ref={};refw={}
  for ff in [21,42]:
   C.activate('Attack',ff/48);ref[ff]={b.name:b.matrix_basis.copy()for b in r.pose.bones};refw[ff]={b.name:b.matrix.copy()for b in r.pose.bones}
  for f in range(109):
   source=float(f);C.activate('Attack',source/48);rows.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
  old_left={}
  for ff in range(60,109):
   C.activate('Attack',(60+48*ease((ff-72)/36))/48);old_left[ff]={f'B_L_{part}':r.pose.bones[f'B_L_{part}'].rotation_quaternion.copy()for part in ['UpperArm','Forearm','Hand']}
  r.animation_data.action=None;names=[f'B_{sd}_{part}'for sd in 'LR'for part in ['UpperArm','Forearm','Hand']];keys={0:{n:base[n].to_quaternion()for n in names},21:{n:ref[21][n].to_quaternion()for n in names},42:{n:Quaternion(impact['bones'][n])for n in names},60:{n:Quaternion(impact['bones'][n])for n in names},108:{n:base[n].to_quaternion()for n in names}}
  keys[21].update({n:Quaternion(q)for n,q in json.loads((P/'work/round3_windups.json').read_text())[0]['bones'].items()})
  for n,m in ref[42].items():r.pose.bones[n].matrix_basis=m
  for n,q in keys[42].items():r.pose.bones[n].rotation_quaternion=q
  bpy.context.view_layer.update();hand=r.pose.bones['B_L_Hand'];sp=r.pose.bones['Spear'].matrix;sol=left.pose_anatomical(sp@Vector((0,0,impact['spacing'])),hand.matrix.to_3x3(),r.pose.bones['B_L_Forearm'].head-r.pose.bones['B_L_UpperArm'].head);left.apply(sol)
  for n in names:
   if '_L_'in n:keys[42][n]=keys[60][n]=r.pose.bones[n].rotation_quaternion.copy()
  bpy.context.view_layer.update();relL=r.pose.bones['Spear'].matrix.inverted()@r.pose.bones['B_L_Hand'].matrix
  clavicle={};handaxes={};coil=(refw[21]['Spear'].to_3x3()@Vector((0,0,1))).rotation_difference(Vector((.5,0,.8660254)))
  for sd in 'LR':
   n=f'B_{sd}_Clavicle';w0=Matrix(D['standing'][n]).to_quaternion();w12=refw[21][n].to_quaternion();w21=refw[42][n].to_quaternion()
   clavicle[sd]={0:w0,21:w12,42:w21,60:w21,108:w0}
   h=r.data.bones[f'B_{sd}_Hand'];ax=(sum((r.data.bones[f'B_{sd}_Finger{i}'].head_local for i in range(5)),Vector())/5-h.head_local).normalized();handaxes[f'B_{sd}_Hand']=h.matrix_local.to_3x3().inverted()@ax
  def mixhand(a,b,t,axis):
   def parts(q):
    v=Vector((q.x,q.y,q.z)).project(axis);tw=Quaternion((q.w,*v));tw.normalize();angle=(2*math.atan2(v.dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi;return q@tw.inverted(),angle
   sa,ta=parts(a);sb,tb=parts(b);return sa.slerp(sb,t)@Quaternion(axis,ta*(1-t)+tb*t)
  previous_tw={};coil=Vector((0,-.70710678,.70710678)).rotation_difference(Vector((.5,0,.8660254)))
  for f,row in enumerate(rows):
   for n,m in row.items():r.pose.bones[n].matrix_basis=m
   for bone in r.pose.bones:
    if bone.name.startswith('Feather'):bone.matrix_basis.identity()
   ks=[0,21,42,60,108]
   for j in range(4):
    if f<=ks[j+1]:break
   t=(f-ks[j])/(ks[j+1]-ks[j]);blend=ramp(t)
   for n in names:r.pose.bones[n].rotation_quaternion=mixhand(keys[ks[j]][n],keys[ks[j+1]][n],blend,handaxes[n])if n in handaxes else keys[ks[j]][n].slerp(keys[ks[j+1]][n],blend)
   for n in ['B_L_ForearmTwist','B_R_ForearmTwist','B_L_UpperArmTwist','B_R_UpperArmTwist']:r.pose.bones[n].matrix_basis=base[n]
   for n,q in IK.GDATA['finger_local'].items():r.pose.bones[n].rotation_quaternion=Quaternion(q)
   for n,q in lg['finger_local'].items():
    release=1-ramp((f-52)/12);close=max(0,min(1,(f-34)/8));close=((32/7)*close*close if close<1/8 else 1-(32/7)*(1-close)**2 if close>7/8 else (8/7)*(close-1/16))*release;r.pose.bones[n].rotation_quaternion=base[n].to_quaternion().slerp(Quaternion(q),close)
   if f>=50:
    t=max(0,min(1,(f-50)/12));t=t*t*(3-2*t)
    for n,q in lg['finger_local'].items():
     if n.startswith('B_L_Finger0'):r.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(base[n].to_quaternion(),t)
   bpy.context.view_layer.update()
   # Keep the aimed weapon steady while the torso and legs drive it forward.
   for sd in 'LR':
    pb=r.pose.bones[f'B_{sd}_Clavicle'];q=clavicle[sd][ks[j]].slerp(clavicle[sd][ks[j+1]],blend);m=q.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
   # Guide the dominant hand around the right flank, keeping the long tail outside the body.
   if 21<f<42:
    t=ramp((f-21)/21);h=r.pose.bones['B_R_Hand'];sp=r.pose.bones['Spear'].matrix;axis=sp.to_3x3()@Vector((0,0,1));aim=Vector((.5*(1-t),-t,.8660254*(1-t))).normalized();rh=axis.rotation_difference(aim).to_matrix()@h.matrix.to_3x3();target=Vector((-.4,.1,1.35)).lerp(Vector(impact['grip']),t);target.x-=.10*math.sin(math.pi*t);sol=right.pose_anatomical(target,rh,r.pose.bones['B_R_Forearm'].head-r.pose.bones['B_R_UpperArm'].head);right.apply(sol)
   hold=ramp((f-31)/11) if f<=60 else 0
   if hold>0:
    h=r.pose.bones['B_L_Hand'];sp=r.pose.bones['Spear'].matrix;rh=h.matrix.to_quaternion().slerp((sp@relL).to_quaternion(),hold).to_matrix();free=h.matrix@left.grip_hand;target=free.lerp(sp@Vector((0,0,impact['spacing'])),hold);target.z+=.018*math.sin(math.pi*(f-31)/11)**2 if 31<f<42 else 0;sol=left.pose_anatomical(target,rh,r.pose.bones['B_L_Forearm'].head-r.pose.bones['B_L_UpperArm'].head);left.apply(sol)
   if f==52:left_release={n:r.pose.bones[n].rotation_quaternion.copy()for n in old_left[60]}
   if f==60:
    recovery={n:r.pose.bones[n].matrix.copy()for n in ['B_Pelvis']+[f'B_R_{part}'for part in ['UpperArm','Forearm','Hand']]}
   if f>60:
    t=ease((f-60)/48);bulge=math.sin(math.pi*t)**2;hip=r.pose.bones['B_Pelvis'].head;h0=recovery['B_Pelvis'].translation;h1=Matrix(D['standing']['B_Pelvis']).translation;start=recovery['B_R_Hand'];end=Matrix(D['standing']['B_R_Hand']);rh=start.to_quaternion().slerp(end.to_quaternion(),t).to_matrix();pole=(recovery['B_R_Forearm'].translation-recovery['B_R_UpperArm'].translation).lerp(Matrix(D['standing']['B_R_Forearm']).translation-Matrix(D['standing']['B_R_UpperArm']).translation,t);target=hip+(start@right.grip_hand-h0).lerp(end@right.grip_hand-h1,t);target.x-=.20*bulge;right.apply(right.pose_anatomical(target,rh,pole))
   if f>52:
    for n,q in old_left[max(60,f)].items():r.pose.bones[n].rotation_quaternion=left_release[n].slerp(q,ramp((f-52)/20))if f<=72 else q
    bpy.context.view_layer.update()
   if 60<f<70:
    h=r.pose.bones['B_L_Hand'];target=h.matrix@left.grip_hand;target+=Vector((-.0144337565,-.0144337565,.0144337565))*math.sin(math.pi*(f-60)/10)**2;left.apply(left.pose_anatomical(target,h.matrix.to_3x3(),r.pose.bones['B_L_Forearm'].head-r.pose.bones['B_L_UpperArm'].head))
   for sd in 'LR':
    fn=f'B_{sd}_Forearm';hn=f'B_{sd}_Hand';un=f'B_{sd}_UpperArm';fb=r.data.bones[fn];hb=r.data.bones[hn];ub=r.data.bones[un];ax=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(r.pose.bones[fn].matrix.inverted()@r.pose.bones[hn].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=IK.swing_twist_deg(rel@rr.inverted(),ax)[1]
    if sd in previous_tw:
     while tw-previous_tw[sd]>180:tw-=360
     while tw-previous_tw[sd]<-180:tw+=360
    previous_tw[sd]=tw
    if sd=='R':r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(ax,math.radians(max(-80,min(80,.6*tw))))
    ax=(ub.matrix_local.inverted()@fb.head_local).normalized();tw=IK.swing_twist_deg(r.pose.bones[un].rotation_quaternion,ax)[1];r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*tw))
   bpy.context.view_layer.update();poses.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
 a=bpy.data.actions['Attack'];a.use_frame_range=True;a.frame_start=0;a.frame_end=108;r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];previous={}
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
  for f in []:
   C.activate('Attack',f/48);common.render_views(str(P/f'review/round3_motion/staged_{f:02}'),.9,2.6,views=('front','left','three_quarter'),resolution=(650,750),target=(0,-.15))
