"""Fit native stance and claw anticipation while retaining source strike/recovery motion."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
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
 x=points();M=armik.W(rig,'B_Pelvis');M.translation.z+=.003-min(float(x[ix,2].min()) for ix in feet.values());armik.set_world(rig,'B_Pelvis',M)
def expression(phase):
 for b in rig.pose.bones:
  if 'Finger' in b.name:b.rotation_quaternion=Quaternion().slerp(b.rotation_quaternion,.30+phase*.15)
 jb=rig.pose.bones['B_Jaw'];axis=rig.data.bones['B_Jaw'].matrix_local.to_3x3().inverted()@Vector((1,0,0));jb.rotation_mode='QUATERNION';jb.rotation_quaternion=Quaternion(axis,math.radians(-6+phase*12))

for name in ('Cast','Death','Dead','Fidget','Hit','Running'):
 a=bpy.data.actions[name];N=int(a.frame_range[1]);raw=[sample(a,f/2) for f in range(N*2+1)];frames=[]
 for x in raw:
  restore(x)
  if name=='Running':
   xco=points()
   for s in 'LR':
    ids=feet[s];sole=ids[co[ids,2]<co[ids,2].min()+.005];yy=co[sole,1];d=Vector(xco[sole[yy<=np.quantile(yy,.3)]].mean(0)-xco[sole[yy>=np.quantile(yy,.7)]].mean(0)).normalized();dr=Vector(co[sole[yy<=np.quantile(yy,.3)]].mean(0)-co[sole[yy>=np.quantile(yy,.7)]].mean(0)).normalized();pitch=float(np.clip(math.asin(np.clip(d.z,-1,1)),math.radians(-70),math.radians(30)));yaw=math.radians(3 if s=='L' else -2);fw=Vector((math.sin(yaw)*math.cos(pitch),-math.cos(yaw)*math.cos(pitch),math.sin(pitch)));right=Vector((math.cos(yaw),math.sin(yaw),0));frame=Matrix((right,-fw,fw.cross(right))).transposed();r=Vector((0,0,1)).cross(dr).normalized();rest=Matrix((r,-dr,dr.cross(r))).transposed();R=frame@rest.inverted()@rig.data.bones[f'B_{s}_Foot'].matrix_local.to_3x3();F=armik.W(rig,f'B_{s}_Foot');armik.set_world(rig,f'B_{s}_Foot',armik.rot_world(F,R))
  if name in ('Fidget','Running'):
   xco=points()
   for s in 'LR':
    ids=feet[s];sole=ids[co[ids,2]<co[ids,2].min()+.005];yy=co[sole,1];d=xco[sole[yy<=np.quantile(yy,.3)]].mean(0)-xco[sole[yy>=np.quantile(yy,.7)]].mean(0);yaw=math.atan2(d[0],-d[1]);want=math.radians(3 if s=='L' else -2);F=armik.W(rig,f'B_{s}_Foot');armik.set_world(rig,f'B_{s}_Foot',armik.rot_world(F,Matrix.Rotation(want-yaw,3,'Z')@F.to_3x3()))
   if name=='Fidget':
    for s in 'LR':
     xco=points();ids=feet[s];sole=ids[co[ids,2]<co[ids,2].min()+.005];normal=Vector(np.linalg.svd(xco[sole]-xco[sole].mean(0))[2][-1]);normal=normal if normal.z>0 else -normal;F=armik.W(rig,f'B_{s}_Foot');R=normal.rotation_difference(Vector((0,0,1))).to_matrix()@F.to_3x3();T=F.translation.copy();leg(s,T,R);low=float(points()[ids,2].min());T=armik.W(rig,f'B_{s}_Foot').translation.copy();T.z+=.003-low;leg(s,T,R)
  xco=points();low=float(xco[:,2].min()) if name in ('Death','Dead') else min(float(xco[ix,2].min()) for ix in feet.values());target=.004+max(0,low)*.06 if name=='Running' else .003;P=armik.W(rig,'B_Pelvis');P.translation.z+=target-low;armik.set_world(rig,'B_Pelvis',P);frames.append(snap())
 if name=='Running':frames[-1]=frames[0]
 a=write(name,frames)
 for fc in action_curves.curves(a):
  for k in fc.keyframe_points:k.co.x/=2;k.handle_left.x/=2;k.handle_right.x/=2
 a.frame_end=N;action_curves.continuous(a)
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'))
