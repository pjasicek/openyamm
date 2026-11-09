"""Fit native stance and claw anticipation while retaining source strike/recovery motion."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_raw.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
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
footR={};footZ={}
for s in 'LR':
 F=rig.data.bones[f'B_{s}_Foot'].matrix_local;D=rig.data.bones[f'B_{s}_Toe0'].head_local-F.translation;yaw=math.atan2(D.x,-D.y);footR[s]=Matrix.Rotation(math.radians(7 if s=='L' else -7)-yaw,3,'Z')@F.to_3x3();footZ[s]=-min((footR[s]@(F.inverted()@Vector(co[i]))).z for i in feet[s])+.003
raw={n:[sample(bpy.data.actions[n],f) for f in range(int(bpy.data.actions[n].frame_range[1])+1)] for n in ['Standing','Walking','Attack']}
frames=[]
for f,x in enumerate(raw['Standing']):
 restore(x);M=armik.W(rig,'B_Pelvis');M.translation=Vector((0,-.015,.985+(M.translation.z-.927)*.5));armik.set_world(rig,'B_Pelvis',M)
 for n,deg in [('B_Spine',-5),('B_Neck',-6),('B_Head',-14)]:
  M=armik.W(rig,n);armik.set_world(rig,n,armik.rot_world(M,Matrix.Rotation(math.radians(deg),3,'X')@M.to_3x3()))
 for s,sg in [('L',1),('R',-1)]:
  H=armik.W(rig,f'B_{s}_Hand');target=H.translation.copy();target.x*=.88;target.y-=.025;target.z+=.055;armik.solve(rig,s,target,hand_rot=H.to_3x3());leg(s,Vector((sg*.19,.015 if s=='L' else -.025,footZ[s])),footR[s])
 expression(.1);ground();frames.append(snap())
frames[-1]=frames[0];write('Standing',frames);home=frames[0];restore(home);left_guard=armik.W(rig,'B_L_Hand').to_quaternion();head_guard=armik.W(rig,'B_Head').to_quaternion()
# Attack retains all source keys through the swipe, then returns to the authored guard.
frames=[]
for out_f in range(61):
 f=out_f*26/32 if out_f<32 else out_f-6;lo=int(f);hi=min(lo+1,len(raw['Attack'])-1);x=mix(raw['Attack'][lo],raw['Attack'][hi],f-lo);restore(x)
 P=armik.W(rig,'B_Pelvis');P.translation.x*=.45;P.translation.y=-.015+(P.translation.y+.036)*.35;P.translation.z=.985+(P.translation.z-.929)*.40;armik.set_world(rig,'B_Pelvis',P)
 # The spine carries the source's turn, with the excessive low fold softened for the native silhouette.
 for n in ('B_Spine','B_Spine1','B_Spine2'):
  b=rig.pose.bones[n];q=b.rotation_quaternion.copy();b.rotation_quaternion=Quaternion().slerp(q,.72)
 bpy.context.view_layer.update()
 D=armik.W(rig,'B_L_UpperArm').translation-armik.W(rig,'B_R_UpperArm').translation;yaw=math.atan2(D.y,D.x);desired=math.radians(35)*math.tanh(yaw/math.radians(35));P=armik.W(rig,'B_Pelvis');armik.set_world(rig,'B_Pelvis',armik.rot_world(P,Matrix.Rotation(desired-yaw,3,'Z')@P.to_3x3()))
 P=armik.W(rig,'B_Pelvis');D=armik.W(rig,'B_Neck').translation-P.translation;lean=math.atan2(-D.y,D.z);limit=math.radians(25);desired=limit*math.tanh(lean/limit);armik.set_world(rig,'B_Pelvis',armik.rot_world(P,Matrix.Rotation(desired-lean,3,'X')@P.to_3x3()))
 for n,deg in [('B_Neck',-4),('B_Head',-9)]:
  M=armik.W(rig,n);armik.set_world(rig,n,armik.rot_world(M,Matrix.Rotation(math.radians(deg),3,'X')@M.to_3x3()))
 b=rig.pose.bones['B_L_Clavicle'];b.rotation_quaternion=b.rotation_quaternion.slerp(home['B_L_Clavicle'].to_quaternion(),.65);bpy.context.view_layer.update()
 w=math.exp(-.5*((f-18)/6)**2)*smooth(f/8)
 H=armik.W(rig,'B_R_Hand');T=H.translation.copy();T+=Vector((-.20,-.25,.58))*w;T+=Vector((-.10,-.06,0))*math.exp(-.5*((f-26)/4)**2);T.y-=.10*math.exp(-.5*((f-39)/6)**2);armik.solve(rig,'R',T,hand_rot=H.to_3x3())
 F=armik.W(rig,'B_R_Forearm').to_3x3();neutral=F@rig.data.bones['B_R_Forearm'].matrix_local.to_3x3().inverted()@rig.data.bones['B_R_Hand'].matrix_local.to_3x3();H=armik.W(rig,'B_R_Hand');R=H.to_quaternion().slerp(neutral.to_quaternion(),w*.65).to_matrix();armik.set_world(rig,'B_R_Hand',armik.rot_world(H,R))
 H=armik.W(rig,'B_L_Hand');T=H.translation.lerp(Vector((.43,-.32,1.26)),.85);armik.solve(rig,'L',T,hand_rot=H.to_quaternion().slerp(left_guard,.78).to_matrix())
 H=armik.W(rig,'B_Head');armik.set_world(rig,'B_Head',armik.rot_world(H,H.to_quaternion().slerp(head_guard,.65).to_matrix()))
 for s,sg in [('L',1),('R',-1)]:
  pivot=math.radians((10 if s=='L' else -14)*math.sin(math.pi*min(f/48,1)));R=Matrix.Rotation(pivot,3,'Z')@footR[s];leg(s,Vector((sg*.205,.055 if s=='R' else -.045,footZ[s])),R)
 expression(math.exp(-.5*((f-28)/9)**2));ground();x=snap()
 blend=min(smooth(out_f/7),smooth((60-out_f)/15));restore(mix(home,x,blend));ground();frames.append(snap())
frames[0]=home;frames[-1]=home;write('Attack',frames)
# Walking stays in place; retain source stride rhythm while narrowing its lateral stance.
frames=[];travel=None
for f,x in enumerate(raw['Walking']):
 restore(x);P=armik.W(rig,'B_Pelvis')
 if f==0:start=P.translation.copy()
 if f==len(raw['Walking'])-1:pass
# Remove the source's net travel once, with its small cyclic sway retained.
restore(raw['Walking'][-1]);end=armik.W(rig,'B_Pelvis').translation.copy();travel=end-start
for f,x in enumerate(raw['Walking']):
 restore(x);phase=f/(len(raw['Walking'])-1);P=armik.W(rig,'B_Pelvis');P.translation-=start+travel*phase;P.translation+=Vector((0,-.015,.985));armik.set_world(rig,'B_Pelvis',P)
 for n,deg in [('B_Spine',-3),('B_Neck',-4),('B_Head',-10)]:
  M=armik.W(rig,n);armik.set_world(rig,n,armik.rot_world(M,Matrix.Rotation(math.radians(deg),3,'X')@M.to_3x3()))
 xco=points();base=min(float(xco[ix,2].min()) for ix in feet.values())
 for s in 'LR':
  F=armik.W(rig,f'B_{s}_Foot');T=F.translation.copy();T.x*=.65;T.y*=.80;lift=max(0,float(xco[feet[s],2].min())-base);T.z-=base+lift*.4;leg(s,T,F.to_3x3())
 xco=points()
 for sd in 'LR':
  ids=feet[sd];sole=ids[co[ids,2]<co[ids,2].min()+.005];along=co[sole,1];heel=xco[sole[along>=np.quantile(along,.7)]].mean(0);toe=xco[sole[along<=np.quantile(along,.3)]].mean(0);delta=toe-heel;yaw=math.atan2(delta[0],-delta[1]);want=math.radians(7 if sd=='L' else -3);F=armik.W(rig,f'B_{sd}_Foot');armik.set_world(rig,f'B_{sd}_Foot',armik.rot_world(F,Matrix.Rotation(want-yaw,3,'Z')@F.to_3x3()))
 expression(.12);ground();frames.append(snap())
frames[-1]=frames[0];write('Walking',frames)
act(None);sc.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_fitted.blend'))
(p/'review/pilot_adaptation.json').write_text(json.dumps({'Standing':'native narrow stance, raised gaze and open claws','Attack':{'source_contact_s':1.0,'authored_contact_s':1.2,'duration_s':2.0,'strike_frames_preserved_at_source_speed':[26,40],'lead_in_frames':[26,32],'recovery_blend_last_frames':15},'Walking':'source net travel removed, stance narrowed; foot contacts require evaluated verification'},indent=2))
