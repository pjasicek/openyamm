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
 x=points();M=armik.W(rig,'B_Pelvis');M.translation.z+=.003-min(float(x[ix,2].min()) for ix in feet.values());armik.set_world(rig,'B_Pelvis',M)
def expression(phase):
 for b in rig.pose.bones:
  if 'Finger' in b.name:b.rotation_quaternion=Quaternion().slerp(b.rotation_quaternion,.30+phase*.15)
 jb=rig.pose.bones['B_Jaw'];axis=rig.data.bones['B_Jaw'].matrix_local.to_3x3().inverted()@Vector((1,0,0));jb.rotation_mode='QUATERNION';jb.rotation_quaternion=Quaternion(axis,math.radians(-6+phase*12))

# The elbow plane is chosen over the whole clip; near-straight source elbows must not switch branches.

home=sample(bpy.data.actions['Standing'],0);restore(home);homefeet={s:armik.W(rig,f'B_{s}_Foot').copy() for s in 'LR'}
roles=['Cast','Death','Fidget','Hit','Running'];report={}
for name in roles:
 action=bpy.data.actions[name];N=int(action.frame_range[1]);raw=[sample(action,f) for f in range(N+1)];targets={s:[] for s in 'LR'};hands={s:[] for s in 'LR'}
 for f,x in enumerate(raw):
  restore(x)
  for s,sg in [('L',1),('R',-1)]:
   H=armik.W(rig,f'B_{s}_Hand');T=H.translation.copy()
   if name=='Cast' and s=='R':T=armik.W(rig,'B_L_Hand').translation.copy();T.x=2*armik.W(rig,'B_Pelvis').translation.x-T.x
   if name=='Running':T.x+=sg*.075
   targets[s].append(np.array(T));hands[s].append(H.to_quaternion())
 for s in 'LR':
  data=np.array(targets[s]);kernel=np.array([1,4,6,4,1])/16
  if name in ('Death','Cast'):
   pad=np.pad(data,((2,2),(0,0)),mode='edge');data=np.stack([np.convolve(pad[:,i],kernel,'valid') for i in range(3)],1)
  targets[s]=data
 paths={};options={}
 for s,sg in [('L',1),('R',-1)]:
  rows=[]
  for f,x in enumerate(raw):
   restore(x);pole=Vector((sg*.3,.2,-1))
   if name=='Death':pole=armik.W(rig,'B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((sg*.4,.1,-1))
   rows.append(armik.arm_options(rig,s,Vector(targets[s][f]),pole))
  costs=np.array([o[0] for o in rows[0]]);backs=[]
  for f in range(1,len(rows)):
   prev=np.array([[*o[1].to_quaternion()] for o in rows[f-1]]);cur=np.array([[*o[1].to_quaternion()] for o in rows[f]]);dist=np.degrees(2*np.arccos(np.clip(abs(prev@cur.T),0,1)));matrix=costs[:,None]+dist**2*1.2;back=np.argmin(matrix,axis=0);costs=matrix[back,np.arange(len(back))]+[o[0] for o in rows[f]];backs.append(back)
  idx=int(np.argmin(costs));path=[idx]
  for back in reversed(backs):idx=int(back[idx]);path.append(idx)
  paths[s]=path[::-1];options[s]=rows
  phi=np.unwrap(np.radians([rows[i][j][4] for i,j in enumerate(paths[s])]));phi=np.convolve(np.pad(phi,(1,1),mode='edge'),[.25,.5,.25],'valid')
  for i,j in enumerate(paths[s]):
   restore(raw[i]);pole=Vector((sg*.3,.2,-1))
   if name=='Death':pole=armik.W(rig,'B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((sg*.4,.1,-1))
   rows[i][j]=armik.arm_options(rig,s,Vector(targets[s][i]),pole,[math.degrees(phi[i])])[0]
 frames=[]
 for f,x in enumerate(raw):
  restore(x)
  for s in 'LR':
   _,R,Rf,T,_=options[s][f][paths[s][f]];un,fn,hn=[f'B_{s}_{n}' for n in ('UpperArm','Forearm','Hand')];armik.set_world(rig,un,armik.rot_world(armik.W(rig,un),R));armik.set_world(rig,fn,armik.rot_world(armik.W(rig,fn),Rf));F=armik.W(rig,fn);H=armik.W(rig,hn);fr=rig.data.bones[fn].matrix_local.to_3x3();hr=rig.data.bones[hn].matrix_local.to_3x3();neutral=F.to_3x3()@fr.inverted()@hr;desired=hands[s][0] if name=='Hit' else hands[s][f]
   roots=[rig.data.bones[f'B_{s}_Finger{i}'].head_local for i in range(5)];w=rig.data.bones[hn].head_local;axis=hr.inverted()@(sum(roots,Vector())/5-w).normalized()
   if name=='Cast':
    normal=(roots[1]-w).cross(roots[4]-w).normalized()*(1 if s=='R' else -1);palm=hr.inverted()@normal;palm=(palm-axis*palm.dot(axis)).normalized();local=Matrix((axis,palm,axis.cross(palm))).transposed();fw=Vector((0,-.55,.835)).normalized();pn=Vector((0,-.835,-.55)).normalized();desired=(Matrix((fw,pn,fw.cross(pn))).transposed()@local.transposed()).to_quaternion();desired=hands[s][0].slerp(desired,min(smooth(f/9),smooth((N-f)/8)))
   q=neutral.to_quaternion().inverted()@desired;sw,tw=armik.split_swing_twist(q,axis);angle=sw.angle
   if angle>math.pi:sw=-sw;angle=sw.angle
   cap=math.radians(48 if name=='Death' else 60)
   if angle>cap:sw=Quaternion().slerp(sw,cap/angle)
   roll_cap=math.radians(65 if name=='Death' else 85);tw=float(np.clip(tw,-roll_cap,roll_cap));Rhand=neutral@((sw@Quaternion(axis,tw)).to_matrix());armik.set_world(rig,hn,armik.rot_world(H,Rhand))
  if name=='Fidget':
   for s in 'LR':leg(s,homefeet[s].translation,homefeet[s].to_3x3())
  current=snap()
  if name=='Hit':current=mix(home,current,min(smooth(f/3),smooth((N-f)/4)))
  frames.append(current)
 if name in ('Hit','Fidget','Cast'):frames[0]=home;frames[-1]=home
 if name=='Running':frames[-1]=frames[0]
 if name=='Cast':frames=frames[:9]+[frames[8]]*20+frames[9:]
 if name=='Death':
  frames[0]=home
  for iteration in range(3):
   original=frames;frames=[]
   for i,x in enumerate(original):
    y={n:m.copy() for n,m in x.items()}
    if 0<i<len(original)-1:
     for side in 'LR':
      for bn in ('UpperArm','Forearm','Hand'):
       n=f'B_{side}_{bn}';q=original[i-1][n].to_quaternion().slerp(original[i+1][n].to_quaternion(),.5);R=x[n].to_quaternion().slerp(q,.5).to_matrix().to_4x4();R.translation=x[n].translation;y[n]=R
    frames.append(y)
  frames[0]=home;old=frames;times=list(np.linspace(0,8,13))+list(range(9,len(old)));frames=[mix(old[int(t)],old[min(int(t)+1,len(old)-1)],t-int(t)) for t in times]
 write(name,frames);report[name]={'frames':len(frames),'elbow_plane_path_degrees':{s:[options[s][i][j][4] for i,j in enumerate(paths[s])] for s in 'LR'}}
 if name=='Death':write('Dead',[frames[-1],frames[-1]])
# The imported wrist weights jump over one short edge. Blend the actual wrist band, retaining digit ownership.
for side in 'LR':
 names=[f'B_{side}_{n}' for n in ('Forearm','ForearmTwist','Hand')];groups=[body.vertex_groups[n] for n in names];indices={g.index for g in groups};w=rig.data.bones[f'B_{side}_Hand'].head_local;d=(w-rig.data.bones[f'B_{side}_Forearm'].head_local).normalized()
 for v,part in zip(body.data.vertices,body.data.attributes['piece'].data):
  along=(v.co-w).dot(d)
  if part.value!=0 or (v.co-w).length>.08 or not -.035<along<.045:continue
  total=sum(e.weight for e in v.groups if e.group in indices)
  if total<.99:continue
  hand=float(np.clip((along+.035)/.08,0,1));groups[0].remove([v.index]);groups[1].add([v.index],total*(1-hand),'REPLACE');groups[2].add([v.index],total*hand,'REPLACE')
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'));(p/'review/arm_plane_fit.json').write_text(json.dumps(report,indent=2))
