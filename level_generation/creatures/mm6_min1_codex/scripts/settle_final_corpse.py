"""Settle the terminal back-fall onto heel, back and head; preserve all held-axe gates."""
import bpy,json,math,sys
import numpy as np
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;rate=sc.render.fps;co0=np.array([v.co[:] for v in b.data.vertices]);feet={s:np.where((co0[:,2]<.14)&(co0[:,0]*(1 if s=='L' else -1)>0))[0] for s in 'RL'}
def update():bpy.context.view_layer.update()
def M(n):return r.pose.bones[n].matrix.copy()
def setmat(n,m):r.pose.bones[n].matrix=m;r.pose.bones[n].scale=(1,1,1);update()
def aim(n,c,d):
 m=M(n);q=(M(c).translation-m.translation).normalized().rotation_difference(d.normalized());setmat(n,Matrix.LocRotScale(m.translation,q@m.to_quaternion(),Vector((1,1,1))))
def ik(s,target,rot):
 a,c,d=['B_'+s+'_'+n for n in ['Thigh','Calf','Foot']];h,k,e=[M(n).translation for n in [a,c,d]];la=(k-h).length;lb=(e-k).length;u=(target-h).normalized();dist=min((target-h).length,(la+lb)*.98);pol=k-h;pol-=u*pol.dot(u);pol.normalize();cosine=max(-1,min(1,(la*la+dist*dist-lb*lb)/(2*la*dist)));kn=h+la*(u*cosine+pol*math.sqrt(1-cosine*cosine));aim(a,c,kn-h);aim(c,d,h+u*dist-M(c).translation);setmat(d,Matrix.LocRotScale(M(d).translation,rot.to_quaternion(),Vector((1,1,1))))
def co():
 e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();p=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();return p
def smooth(t):t=min(1,max(0,t));return t*t*(3-2*t)
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));v=(M('B_L_Foot').translation+M('B_R_Foot').translation)*.5-M('B_Pelvis').translation;yawAngle=(-math.pi/2-math.atan2(v.y,v.x)+math.pi)%(2*math.pi)-math.pi;rows=[]
for f in range(int(a.frame_range[1])+1):
 sc.frame_set(f);u=smooth((f/rate-.5)/.6)
 if u:
  for s in 'RL':
   n='B_'+s+'_Foot';old=M(n);target=old.translation.copy();target.z=target.z*(1-u)+.105*u;toe=M('B_'+s+'_Toe0').translation-old.translation;flat=Vector((toe.x,toe.y,0)).normalized();new=toe.normalized().rotation_difference(flat).to_matrix()@old.to_3x3();rot=old.to_quaternion().slerp(new.to_quaternion(),u).to_matrix();ik(s,target,rot)
   for _ in range(3):
    low=float(co()[feet[s],2].min());m=M(n);target=m.translation.copy();target.z-=low*u;ik(s,target,m.to_3x3())
  # Relax the head backward while keeping the nose upward, like the native rearward corpse.
  n='B_Neck';m=M(n);axis=(M('B_L_UpperArm').translation-M('B_R_UpperArm').translation).normalized();rot=Matrix.Rotation(math.radians(-70)*u,3,axis)@m.to_3x3();setmat(n,Matrix.LocRotScale(m.translation,rot.to_quaternion(),Vector((1,1,1))))
 # Ground the body at the baked sample rate, retaining the released axe's independent floor pose.
 axe=M('Axe')
 if u:
  root=M('B_Pelvis');rot=Matrix.Rotation(yawAngle*u,3,'Z')@root.to_3x3();setmat('B_Pelvis',Matrix.LocRotScale(root.translation,rot.to_quaternion(),Vector((1,1,1))))
 low=float(co().min(0)[2]);m=M('B_Pelvis');m.translation.z-=low;setmat('B_Pelvis',m)
 if f/rate>=1/6:setmat('Axe',axe)
 rows.append({n:(p.rotation_quaternion.copy(),p.location.copy()) for n,p in r.pose.bones.items()})
for name,data in [('Death',rows),('Dead',[rows[-1]]*121)]:
 bpy.data.actions.remove(bpy.data.actions[name]);act=bpy.data.actions.new(name);act.use_fake_user=True;act.use_frame_range=True;act.frame_start=0;act.frame_end=len(data)-1;r.animation_data.action=act;prev={}
 for f,row in enumerate(data):
  for n,(q,l) in row.items():
   q=q.copy()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();p=r.pose.bones[n];p.rotation_quaternion=q;p.location=l;p.keyframe_insert('rotation_quaternion',frame=f);p.keyframe_insert('location',frame=f)
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=bpy.data.actions['Dead'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);p=co();print('CORPSE HEIGHT',float(np.ptp(p[:,2])),flush=True)
common.workbench_clay(sc);common.render_views(str(P/'review/corpse_settle'),.5,2.6,views=['front','left','three_quarter'],resolution=(640,480))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/corpse_settled.blend'))
