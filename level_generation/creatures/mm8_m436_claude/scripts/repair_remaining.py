"""Fit native stance and claw anticipation while retaining source strike/recovery motion."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_fitted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
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
home=sample(bpy.data.actions['Standing'],0);report={}
for name in ['Hit','Fidget','Death','Running']:
 a=bpy.data.actions[name];N=int(a.frame_range[1]);raw=[sample(a,i*.5) for i in range(N*2+1)];frames=[]
 for i,x in enumerate(raw):
  f=i*.5;restore(x)
  if name=='Hit':
   for n in x:
    if any(k in n for k in ('Clavicle','UpperArm','Forearm','Hand','Finger','Neck','Head')):rig.pose.bones[n].rotation_quaternion=home[n].to_quaternion().slerp(x[n].to_quaternion(),.20)
  if name=='Hit':
   for n in ('B_Spine','B_Spine1','B_Spine2'):rig.pose.bones[n].rotation_quaternion=home[n].to_quaternion().slerp(x[n].to_quaternion(),.75)
  if name=='Death':
   for n in ('B_Neck','B_Head'):rig.pose.bones[n].rotation_quaternion=home[n].to_quaternion().slerp(x[n].to_quaternion(),.25)
  bpy.context.view_layer.update();frames.append(snap())
 if name=='Death':
  raw=frames;targets={s:[] for s in 'LR'};rows={};paths={}
  for sd,sg in [('L',1),('R',-1)]:
   opts=[]
   for i,x in enumerate(raw):
    restore(x);C=armik.W(rig,'B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted();S=armik.W(rig,f'B_{sd}_UpperArm').translation;T=armik.W(rig,f'B_{sd}_Hand').translation;d=C.inverted()@(T-S);d=d.lerp(Vector((sg*.20,-.08,-.40)),.60);d.x=sg*max(d.x*sg,.18);d.y=min(d.y,-.06);T=S+C@d;settle=smooth((i*.5-20)/19);T.z=T.z*(1-settle)+.12*settle;T+=C@Vector((sg*.20,0,0))*settle;targets[sd].append(T);opts.append(armik.arm_options(rig,sd,T,C@Vector((sg*.4,.1,-1))))
   cost=np.array([o[0] for o in opts[0]]);backs=[]
   for previous,current in zip(opts,opts[1:]):
    qa=np.array([list(o[1].to_quaternion()) for o in previous]);qb=np.array([list(o[1].to_quaternion()) for o in current]);angle=np.degrees(2*np.arccos(np.clip(abs(qa@qb.T),0,1)));M=cost[:,None]+angle**2*1.2;back=np.argmin(M,axis=0);cost=M[back,np.arange(len(back))]+[o[0] for o in current];backs.append(back)
   j=int(np.argmin(cost));path=[j]
   for back in reversed(backs):j=int(back[j]);path.append(j)
   path.reverse();phi=np.unwrap(np.radians([opts[i][j][4] for i,j in enumerate(path)]));phi=np.convolve(np.pad(phi,(2,2),mode='edge'),[1/16,4/16,6/16,4/16,1/16],'valid');rows[sd]=[]
   for i,x in enumerate(raw):
    restore(x);C=armik.W(rig,'B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted();rows[sd].append(armik.arm_options(rig,sd,targets[sd][i],C@Vector((sg*.4,.1,-1)),[math.degrees(phi[i])])[0])
  frames=[]
  for i,x in enumerate(raw):
   restore(x)
   for sd in 'LR':
    _,R,Rf,T,_=rows[sd][i];un,fn,hn=[f'B_{sd}_{bn}' for bn in ('UpperArm','Forearm','Hand')];armik.set_world(rig,un,armik.rot_world(armik.W(rig,un),R));armik.set_world(rig,fn,armik.rot_world(armik.W(rig,fn),Rf));neutral=Rf@rig.data.bones[fn].matrix_local.to_3x3().inverted()@rig.data.bones[hn].matrix_local.to_3x3();armik.set_world(rig,hn,armik.rot_world(armik.W(rig,hn),neutral))
   fitted=snap();w=smooth(i/14)
   for sd in 'LR':
    for bn in ('UpperArm','Forearm','Hand'):
     n=f'B_{sd}_{bn}';fitted[n]=x[n].lerp(fitted[n],w)
   restore(fitted);settle=smooth((i*.5-19)/20)
   for sd in 'LR':
    F=armik.W(rig,f'B_{sd}_Foot');T=F.translation.copy();R=rig.data.bones[f'B_{sd}_Foot'].matrix_local.to_3x3();T.z=rig.data.bones[f'B_{sd}_Foot'].head_local.z+.004;H=armik.W(rig,f'B_{sd}_Thigh').translation;d=T-H;dxy=Vector((d.x,d.y,0));L=(rig.data.bones[f'B_{sd}_Calf'].head_local-rig.data.bones[f'B_{sd}_Thigh'].head_local).length+(rig.data.bones[f'B_{sd}_Foot'].head_local-rig.data.bones[f'B_{sd}_Calf'].head_local).length;maxxy=math.sqrt(max(0,(L*.96)**2-d.z*d.z))
    if dxy.length>maxxy:T.x=H.x+dxy.x*maxxy/dxy.length;T.y=H.y+dxy.y*maxxy/dxy.length
    leg(sd,F.translation.lerp(T,settle),F.to_quaternion().slerp(R.to_quaternion(),settle).to_matrix(),Vector((0,0,1)))
   P=armik.W(rig,'B_Pelvis');P.translation.z+=.004-float(points()[:,2].min());armik.set_world(rig,'B_Pelvis',P);frames.append(snap())
 if name=='Running':
  raw=frames;frames=[]
  for i,x in enumerate(raw):
   restore(x);xyz=points()
   for sd in 'LR':
    ids=feet[sd];sole=ids[co[ids,2]<co[ids,2].min()+.006];ys=co[sole,1];d=Vector(xyz[sole[ys<np.quantile(ys,.3)]].mean(0)-xyz[sole[ys>np.quantile(ys,.7)]].mean(0));dr=Vector(co[sole[ys<np.quantile(ys,.3)]].mean(0)-co[sole[ys>np.quantile(ys,.7)]].mean(0));pitch=math.asin(float(np.clip(d.normalized().z,-1,1)));yaw=math.radians(5 if sd=='L' else -5);fw=Vector((math.sin(yaw)*math.cos(pitch),-math.cos(yaw)*math.cos(pitch),math.sin(pitch)));right=Vector((math.cos(yaw),math.sin(yaw),0));frame=Matrix((right,-fw,fw.cross(right))).transposed();rr=Vector((0,0,1)).cross(dr).normalized();dr.normalize();rest=Matrix((rr,-dr,dr.cross(rr))).transposed();R=frame@rest.inverted()@rig.data.bones[f'B_{sd}_Foot'].matrix_local.to_3x3();F=armik.W(rig,f'B_{sd}_Foot');armik.set_world(rig,f'B_{sd}_Foot',armik.rot_world(F,R));rig.pose.bones[f'B_{sd}_Toe0'].matrix_basis=Matrix()
   low=min(float(points()[ix,2].min()) for ix in feet.values());P=armik.W(rig,'B_Pelvis');P.translation.z+=.004-low;armik.set_world(rig,'B_Pelvis',P);frames.append(snap())
 if name=='Fidget':
  for j,x in enumerate(frames):
   restore(x);P=armik.W(rig,'B_Pelvis');P.translation.z-=.002;armik.set_world(rig,'B_Pelvis',P);frames[j]=snap()
 if name in ('Hit','Fidget'):frames[0]=home;frames[-1]=home
 if name=='Death':frames[0]=home
 if name=='Running':frames[-1]=frames[0]
 # Half-frame keys survive the final 60 Hz export.
 old=bpy.data.actions[name];bpy.data.actions.remove(old);a=bpy.data.actions.new(name);a.use_fake_user=True;act(a)
 for i,x in enumerate(frames):
  for n,m in x.items():
   b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=m.to_quaternion();b.keyframe_insert('rotation_quaternion',frame=i*.5)
   if n=='B_Pelvis':b.location=m.translation;b.keyframe_insert('location',frame=i*.5)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=N;action_curves.continuous(a)
 for fc in action_curves.curves(a):
  for k in fc.keyframe_points:k.interpolation='LINEAR'
 if name=='Death':write('Dead',[frames[-1],frames[-1]])
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'))
