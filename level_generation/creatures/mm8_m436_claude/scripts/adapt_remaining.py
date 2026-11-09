"""Fit native stance and claw anticipation while retaining source strike/recovery motion."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_raw.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
co=np.array([tuple(v.co) for v in body.data.vertices]);part=np.array([a.value for a in body.data.attributes['piece'].data]);feet={s:np.flatnonzero((part==0)&(co[:,2]<.15)&(co[:,0]*(1 if s=='L' else -1)>0)) for s in 'LR'}
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap():return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def sample(a,f):
 act(a);sc.frame_set(int(f),subframe=f-int(f));return snap()
def restore(x):
 act(None)
 for n,m in x.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def points():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();x=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();return x
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def mix(a,b,w):
 out={}
 for n in a:
  q=a[n].to_quaternion();r=b[n].to_quaternion()
  if q.dot(r)<0:r=-r
  m=q.slerp(r,w).to_matrix().to_4x4();m.translation=a[n].translation.lerp(b[n].translation,w);out[n]=m
 return out
def leg(side,target,R,pole=Vector((0,-1,0))):
 ns=[f'B_{side}_{n}' for n in ('Thigh','Calf','Foot')];U,F,H=[armik.W(rig,n) for n in ns];S,E,A=[m.translation.copy() for m in (U,F,H)];a,b=(E-S).length,(A-E).length;d=target-S;dist=min(d.length,(a+b)*.998);u=d.normalized();v=(pole-u*pole.dot(u)).normalized();ca=np.clip((a*a+dist*dist-b*b)/(2*a*dist),-1,1);K=S+a*(u*ca+v*math.sqrt(max(0,1-ca*ca)))
 q=(E-S).normalized().rotation_difference((K-S).normalized());armik.set_world(rig,ns[0],armik.rot_world(U,q.to_matrix()@U.to_3x3()));F=armik.W(rig,ns[1]);cur=armik.W(rig,ns[2]).translation-F.translation;q=cur.normalized().rotation_difference((target-F.translation).normalized());armik.set_world(rig,ns[1],armik.rot_world(F,q.to_matrix()@F.to_3x3()));armik.set_world(rig,ns[2],armik.rot_world(armik.W(rig,ns[2]),R));rig.pose.bones[f'B_{side}_Toe0'].matrix_basis=Matrix()
def write(name,frames):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;act(a)
 for f,x in enumerate(frames):
  for n,m in x.items():
   b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=m.to_quaternion();b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.location=m.translation;b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(frames)-1;action_curves.continuous(a);return a
def ground():
 x=points();M=armik.W(rig,'B_Pelvis');M.translation.z+=.004-min(float(x[ix,2].min()) for ix in feet.values());armik.set_world(rig,'B_Pelvis',M)
def fingers(amount):
 for b in rig.pose.bones:
  if 'Finger' in b.name:b.rotation_quaternion=Quaternion().slerp(b.rotation_quaternion,amount)
raw={n:[sample(bpy.data.actions[n],f) for f in range(int(bpy.data.actions[n].frame_range[1])+1)] for n in ['Hit','Fidget','Death','Running']}
home=sample(bpy.data.actions['Standing'],0);restore(home);hp=armik.W(rig,'B_Pelvis').translation.copy();foot={s:armik.W(rig,f'B_{s}_Foot').copy() for s in 'LR'};report={}
for name in ['Hit','Fidget','Death','Running']:
 frames=[];N=len(raw[name])-1;restore(raw[name][0]);start=armik.W(rig,'B_Pelvis').translation.copy();restore(raw[name][-1]);end=armik.W(rig,'B_Pelvis').translation.copy()
 for f,x in enumerate(raw[name]):
  restore(x);M=armik.W(rig,'B_Pelvis')
  if name=='Running':M.translation-=Vector((start.x+(end.x-start.x)*f/N,start.y+(end.y-start.y)*f/N,0));M.translation+=Vector((hp.x,hp.y,0))
  elif name=='Death':M.translation.x=hp.x+(M.translation.x-start.x)*.65;M.translation.y=hp.y+(M.translation.y-start.y)*.65
  else:M.translation=hp+(M.translation-start)*.5
  armik.set_world(rig,'B_Pelvis',M)
  for sd in 'LR':
   rig.pose.bones[f'B_{sd}_Toe0'].matrix_basis=Matrix()
   if name in ('Hit','Fidget'):leg(sd,foot[sd].translation,foot[sd].to_3x3())
  fingers(.40 if name=='Hit' else .35)
  if name!='Running':
   w=smooth(f/(3 if name=='Hit' else 6))
   if name!='Death':w=min(w,smooth((N-f)/(4 if name=='Hit' else 6)))
   restore(mix(home,snap(),w));low=float(points()[:,2].min()) if name=='Death' else min(float(points()[ix,2].min()) for ix in feet.values());M=armik.W(rig,'B_Pelvis');M.translation.z+=.006-low;armik.set_world(rig,'B_Pelvis',M)
  frames.append(snap())
 if name=='Running':frames[-1]=frames[0]
 elif name!='Death':frames[0]=home;frames[-1]=home
 else:frames[0]=home
 write(name,frames);report[name]={'duration':N/30,'source_speed_preserved':True}
 if name=='Death':write('Dead',[frames[-1],frames[-1]])
act(None);sc.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_fitted.blend'));(p/'review/full_adaptation.json').write_text(json.dumps(report,indent=2))
