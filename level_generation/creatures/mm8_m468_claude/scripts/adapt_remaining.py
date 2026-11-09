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
 x=points();M=armik.W(rig,'B_Pelvis');M.translation.z+=.003-min(float(x[ix,2].min()) for ix in feet.values());armik.set_world(rig,'B_Pelvis',M)
def expression(phase):
 for b in rig.pose.bones:
  if 'Finger' in b.name:b.rotation_quaternion=Quaternion().slerp(b.rotation_quaternion,.30+phase*.15)
 jb=rig.pose.bones['B_Jaw'];axis=rig.data.bones['B_Jaw'].matrix_local.to_3x3().inverted()@Vector((1,0,0));jb.rotation_mode='QUATERNION';jb.rotation_quaternion=Quaternion(axis,math.radians(-6+phase*12))

raw={n:[sample(bpy.data.actions[n],f) for f in range(int(bpy.data.actions[n].frame_range[1])+1)] for n in ['Hit','Fidget','Cast','Death','Running']}
home=sample(bpy.data.actions['Standing'],0);restore(home);guard={s:armik.W(rig,f'B_{s}_Hand').copy() for s in 'LR'};homefeet={s:armik.W(rig,f'B_{s}_Foot').copy() for s in 'LR'};homepelvis=armik.W(rig,'B_Pelvis').translation.copy()
report={}
for name in ['Hit','Fidget','Cast','Death','Running']:
 frames=[];N=len(raw[name])-1
 restore(raw[name][0]);start=armik.W(rig,'B_Pelvis').translation.copy();restore(raw[name][-1]);end=armik.W(rig,'B_Pelvis').translation.copy()
 for f,x in enumerate(raw[name]):
  restore(x);P=armik.W(rig,'B_Pelvis');rawpoints=points();rawlow=min(float(rawpoints[ix,2].min()) for ix in feet.values())
  if name=='Running':
   P.translation.x-=start.x+(end.x-start.x)*f/N;P.translation.y-=start.y+(end.y-start.y)*f/N
  elif name!='Death':
   P.translation.x=homepelvis.x+(P.translation.x-start.x)*.4;P.translation.y=homepelvis.y+(P.translation.y-start.y)*.4;P.translation.z=homepelvis.z+(P.translation.z-start.z)*.5
  else:
   P.translation.x-=start.x-homepelvis.x;P.translation.y-=start.y-homepelvis.y
  armik.set_world(rig,'B_Pelvis',P)
  if name not in ('Death','Running'):
   for s in 'LR':leg(s,homefeet[s].translation,homefeet[s].to_3x3())
  if name not in ('Death',):
   for n,deg in [('B_Neck',-4),('B_Head',-10)]:
    M=armik.W(rig,n);armik.set_world(rig,n,armik.rot_world(M,Matrix.Rotation(math.radians(deg),3,'X')@M.to_3x3()))
  for s,sg in [('L',1),('R',-1)]:
   H=armik.W(rig,f'B_{s}_Hand');T=H.translation.copy()
   if name=='Fidget':T=T.lerp(guard[s].translation,.65);R=H.to_quaternion().slerp(guard[s].to_quaternion(),.65).to_matrix()
   else:T.x+=sg*(.035 if name!='Death' else .02);R=H.to_3x3()
   armik.solve(rig,s,T,hand_rot=R)
   F=armik.W(rig,f'B_{s}_Forearm').to_3x3();neutral=F@rig.data.bones[f'B_{s}_Forearm'].matrix_local.to_3x3().inverted()@rig.data.bones[f'B_{s}_Hand'].matrix_local.to_3x3();H=armik.W(rig,f'B_{s}_Hand');armik.set_world(rig,f'B_{s}_Hand',armik.rot_world(H,H.to_quaternion().slerp(neutral.to_quaternion(),.25).to_matrix()))
  expression((.6 if name in ('Hit','Cast') else .15)*math.sin(math.pi*f/max(1,N)))
  if name=='Running':
   xco=points()
   for s in 'LR':
    ids=feet[s];sole=ids[co[ids,2]<co[ids,2].min()+.005];yy=co[sole,1];d=Vector(xco[sole[yy<=np.quantile(yy,.3)]].mean(0)-xco[sole[yy>=np.quantile(yy,.7)]].mean(0)).normalized();dr=Vector(co[sole[yy<=np.quantile(yy,.3)]].mean(0)-co[sole[yy>=np.quantile(yy,.7)]].mean(0)).normalized();pitch=math.asin(np.clip(d.z,-1,1));yaw=math.radians(5 if s=='L' else -3);fw=Vector((math.sin(yaw)*math.cos(pitch),-math.cos(yaw)*math.cos(pitch),math.sin(pitch)));right=Vector((math.cos(yaw),math.sin(yaw),0));up=fw.cross(right).normalized();frame=Matrix((right,-fw,up)).transposed();r=Vector((0,0,1)).cross(dr).normalized();rest=Matrix((r,-dr,dr.cross(r))).transposed();R=frame@rest.inverted()@rig.data.bones[f'B_{s}_Foot'].matrix_local.to_3x3();F=armik.W(rig,f'B_{s}_Foot');armik.set_world(rig,f'B_{s}_Foot',armik.rot_world(F,R));rig.pose.bones[f'B_{s}_Toe0'].matrix_basis=Matrix()
   low=min(float(points()[ix,2].min()) for ix in feet.values());P=armik.W(rig,'B_Pelvis');P.translation.z+=max(0,rawlow)+.003-low;armik.set_world(rig,'B_Pelvis',P)
  else:
   w=smooth(f/(3 if name=='Hit' else 6))
   if name!='Death':w=min(w,smooth((N-f)/(4 if name=='Hit' else 8)))
   restore(mix(home,snap(),w));xco=points();low=float(xco[:,2].min()) if name=='Death' else min(float(xco[ix,2].min()) for ix in feet.values());P=armik.W(rig,'B_Pelvis');P.translation.z+=.003-low;armik.set_world(rig,'B_Pelvis',P)
  frames.append(snap())
 if name=='Running':frames[-1]=frames[0]
 elif name!='Death':frames[0]=home;frames[-1]=home
 write(name,frames);report[name]={'duration':N/30,'source_speed_preserved':True}
 if name=='Death':write('Dead',[frames[-1],frames[-1]])
act(None);sc.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_fitted.blend'));(p/'review/full_adaptation.json').write_text(json.dumps(report,indent=2))
