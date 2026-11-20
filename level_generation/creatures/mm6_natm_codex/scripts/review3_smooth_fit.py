"""Smooth fitted hand trajectories, then restore anatomical elbows and exact shaft contact."""
import bpy,sys,json,math,importlib,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
def ease(t):
 t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
out=[]
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
 if level==0:
  import arm_ik as IK;importlib.reload(IK);sides={s:IK.Side(s)for s in 'LR'};lg=json.loads((P/'work/round3_left_grip.json').read_text());sides['L'].grip_hand=Vector(lg['handle_centre_hand_local']);la=Vector(lg['handle_axis_hand_local']);poses=[];wm=[]
  for f in range(77):
   C.activate('Attack',f/48);poses.append({b.name:b.matrix_basis.copy()for b in r.pose.bones});wm.append({b.name:b.matrix.copy()for b in r.pose.bones})
  def filtered(f,n,q=False):
   ids=list(range(max(0,f-6),min(77,f+7)));w=np.exp(-.5*((np.array(ids)-f)/1.8)**2)
   if q:
    ref=wm[f][n].to_quaternion();qs=[wm[i][n].to_quaternion()for i in ids];return Quaternion(np.average([list(v if ref.dot(v)>=0 else -v)for v in qs],0,weights=w)).normalized()
   return Vector(np.average([wm[i][n].translation[:]for i in ids],0,weights=w))
  r.animation_data.action=None;prior={};prior_tw={}
  for f,row in enumerate(poses):
   for n,m in row.items():r.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update();held=ease((f-18)/13)*(1-ease((f-46)/15))
   for sd in 'RL':
    side=sides[sd];hn=f'B_{sd}_Hand';fn=f'B_{sd}_Forearm';un=f'B_{sd}_UpperArm';rh=filtered(f,hn,True).to_matrix();S=r.pose.bones[un].head;E=filtered(f,fn);pole=E-S
    if sd=='R':target=filtered(f,'Spear')
    else:
     sp=r.pose.bones['Spear'].matrix;axis=sp.to_3x3()@Vector((0,0,1));q=(rh@la).rotation_difference(axis);rh=Quaternion().slerp(q,held).to_matrix()@rh;target=(filtered(f,hn)+rh@side.grip_hand).lerp(sp@Vector((0,0,.10)),held)
    direction=(target-rh@side.grip_hand-S).normalized();parent=r.pose.bones[f'B_{sd}_Clavicle'].matrix.to_3x3()@side.rel['Arm'];axis_h=(sum((r.data.bones[f'B_{sd}_Finger{i}'].head_local for i in range(5)),Vector())/5-r.data.bones[hn].head_local).normalized();axis_h=r.data.bones[hn].matrix_local.to_3x3().inverted()@axis_h;candidates=[]
    for pd in range(-15,16,2):
     sol=side.pose_anatomical(target,rh,Quaternion(direction,math.radians(pd))@pole);sw,tw=IK.swing_twist_deg(((sol['Rf']@side.rel['Hand']).inverted()@rh).to_quaternion(),axis_h);upper=IK.swing_twist_deg((parent.inverted()@sol['Ra']).to_quaternion(),side.uA)[1];cost=pd*pd*.1+max(0,sw-68)**2*100+max(0,abs(tw)-85)**2*100+max(0,abs(upper)-85)**2*100
     if sd in prior:cost+=math.degrees(2*math.acos(min(1,abs(prior[sd].dot(sol['Ra'].to_quaternion())))))**2*.2
     candidates.append((cost,sol))
    sol=min(candidates,key=lambda v:v[0])[1];side.apply(sol);prior[sd]=sol['Ra'].to_quaternion()
    if sd=='R':
     fb=r.data.bones[fn];hb=r.data.bones[hn];ax=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(r.pose.bones[fn].matrix.inverted()@r.pose.bones[hn].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=IK.swing_twist_deg(rel@rr.inverted(),ax)[1]
     if sd in prior_tw:
      while tw-prior_tw[sd]>180:tw-=360
      while tw-prior_tw[sd]<-180:tw+=360
     prior_tw[sd]=tw;r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(ax,math.radians(max(-80,min(80,.6*tw))))
    ub=r.data.bones[un];fb=r.data.bones[fn];ax=(ub.matrix_local.inverted()@fb.head_local).normalized();tw=IK.swing_twist_deg(r.pose.bones[un].rotation_quaternion,ax)[1];r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*tw))
   bpy.context.view_layer.update();out.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
 a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];prev={}
 for f,row in enumerate(out):
  for n,m in row.items():
   if not any(k in n for k in ['UpperArm','Forearm','Hand']):continue
   b=r.pose.bones[n];b.matrix_basis=m;q=b.rotation_quaternion
   if n in prev and prev[n].dot(q)<0:q.negate()
   prev[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
