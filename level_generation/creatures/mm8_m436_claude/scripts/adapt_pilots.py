"""Fit native stance and claw anticipation while retaining source strike/recovery motion."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_twist.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
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
footR={s:rig.data.bones[f'B_{s}_Foot'].matrix_local.to_3x3() for s in 'LR'}
footTarget={s:rig.data.bones[f'B_{s}_Foot'].head_local.copy() for s in 'LR'}
root=rig.data.bones['B_Pelvis'].head_local.copy()
raw={n:[sample(bpy.data.actions[n],f) for f in range(int(bpy.data.actions[n].frame_range[1])+1)] for n in ['Standing','Walking','Attack']}
restore(raw['Standing'][0]);origin=armik.W(rig,'B_Pelvis').translation.copy();frames=[]
for x in raw['Standing']:
 restore(x);M=armik.W(rig,'B_Pelvis');M.translation=root+Vector((0,0,-.012))+(M.translation-origin)*.5;armik.set_world(rig,'B_Pelvis',M)
 for sd in 'LR':leg(sd,footTarget[sd],footR[sd])
 fingers(.35);ground();frames.append(snap())
frames[-1]=frames[0];write('Standing',frames);home=frames[0]
# Keep the source strike at its original speed after a continuous preparatory draw-back.
frames=[]
restore(raw['Attack'][0]);attack0=armik.W(rig,'B_Pelvis').translation.copy()
restore(home);homeP=armik.W(rig,'B_Pelvis').translation.copy()
for out_f in range(65):
 sf=out_f*.2 if out_f<=20 else min(24,out_f-16);lo=int(sf);hi=min(lo+1,24);restore(mix(raw['Attack'][lo],raw['Attack'][hi],sf-lo))
 M=armik.W(rig,'B_Pelvis');delta=M.translation-attack0;M.translation=homeP+Vector((delta.x*.5,delta.y*.45,delta.z*.5));armik.set_world(rig,'B_Pelvis',M)
 for n in ('B_Spine','B_Spine1','B_Spine2'):
  b=rig.pose.bones[n];b.rotation_quaternion=home[n].to_quaternion().slerp(b.rotation_quaternion,.78)
 bpy.context.view_layer.update()
 for sd in 'LR':
  R=Matrix.Rotation(math.radians(6 if sd=='L' else -6)*math.sin(math.pi*sf/24),3,'Z')@footR[sd];leg(sd,footTarget[sd],R)
 fingers(.55);ground();x=snap();blend=min(smooth(out_f/16),smooth((64-out_f)/24));restore(mix(home,x,blend));ground();frames.append(snap())
frames[0]=home;frames[-1]=home;write('Attack',frames)
# Retain the broad source arm swing; use the original ankle trajectories in the following pass.
frames=[]
for x in raw['Walking']:
 restore(x);fingers(.35);frames.append(snap())
write('Walking',frames)
act(None);sc.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_fitted.blend'))
(p/'review/pilot_adaptation.json').write_text(json.dumps({'Standing':'relaxed source breathing, fitted flat feet and upright skull frame; open fingers','Attack':{'source':'UnarmedAttackR2','lead_in_source_frames':[0,4],'lead_in_output_frames':[0,20],'unchanged_source_speed_frames':[4,24],'duration_s':64/30,'return_to_standing_frames':24},'Walking':'original Orc Walk ankle/toe trajectories fitted to measured Ogre leg lengths'},indent=2))
