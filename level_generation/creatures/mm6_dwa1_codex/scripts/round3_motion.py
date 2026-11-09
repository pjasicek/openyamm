"""Cycle-locked sole targets for the short legs; accepted non-locomotion actions are untouched."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3_before/work/textured_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30

def act(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def apply(p):
 act(None)
 for n,(q,l)in p.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
def capture():return {b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
def sample(a,f):
 act(a);scene.frame_set(int(f),subframe=f%1);return capture()
def smooth(x):
 x=min(1,max(0,x));return x*x*(3-2*x)
poses={n:[sample(bpy.data.actions[n],f/4)for f in range(97)]for n in ['Walking','Running']}
rest=sample(bpy.data.actions['Standing'],0);sole={};flat={};lens={}
for sd in 'LR':
 n=f'B_{sd}_Foot';M=rig.data.bones[n].matrix_local
 ids=[v.index for v in body.data.vertices if (v.co.x>0)==(sd=='L') and v.co.z<.008]
 sole[sd]=[M.inverted()@body.data.vertices[i].co for i in ids]
 apply(rest);W=world(n);normal=(W.to_3x3()@M.to_3x3().inverted())@Vector((0,0,1))
 flat[sd]=normal.rotation_difference(Vector((0,0,1)))@W.to_quaternion()
 # Use fitted bind lengths; locomotion does not need the rest-pose reach extension.
 H,K,A=[rig.data.bones[f'B_{sd}_{k}'].head_local for k in ['Thigh','Calf','Foot']];lens[sd]=((K-H).length,(A-K).length)

def aim(n,child,direction):
 M=world(n);current=world(child).translation-M.translation;R=current.normalized().rotation_difference(direction.normalized()).to_matrix().to_4x4();t=M.translation.copy();M=R@M;M.translation=t
 rig.pose.bones[n].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
def solve(sd,T,Q):
 th,ca,ft=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H=world(th).translation;a,b=lens[sd];d=(T-H).length
 assert abs(a-b)<d<a+b,('reach',name,f,sd,d,a+b)
 u=(T-H).normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);K=H+a*(u*c+v*math.sqrt(max(0,1-c*c)))
 aim(th,ca,K-H);M=world(ca);M.translation=K;rig.pose.bones[ca].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update();aim(ca,ft,T-K)
 M=Q.to_matrix().to_4x4();M.translation=T;rig.pose.bones[ft].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
 assert (world(ft).translation-T).length<1e-5

def target(name,sd,phase):
 run=name=='Running';stance=.48 if run else .56;stride=.89*(1.55 if run else 1);travel=stride*stance
 if phase<stance:
  s=phase/stance;y=-travel/2+stride*phase;lift=0
  pitch=-8*(1-smooth(s/.12)) + 12*smooth((s-.84)/.16)
 else:
  s=(phase-stance)/(1-stance)
  # Recovery initially lifts behind the body, then the leg advances into heel strike.
  progress=smooth(s**(1.8 if run else 2.5));y=travel/2-travel*progress
  lift=(.12 if run else .09)*math.sin(math.pi*s)**1.25
  pitch=12*(1-smooth(s/.28))-8*smooth((s-.75)/.25)
 Q=Quaternion(Vector((1,0,0)),math.radians(pitch))@flat[sd]
 T=Vector((.135 if sd=='L' else -.135,y,0));T.z=.004+lift-min((Q@v).z for v in sole[sd])
 return T,Q

for name in poses:
 frames=[]
 for sample_index,p in enumerate(poses[name]):
  f=sample_index/4
  # The first and last sample describe the same cyclic pose.
  if f==24:p=poses[name][0]
  apply(p);targets={}
  for sd in 'LR':
   phase=(f/24+(.75 if name=='Running' else .28)+(0 if sd=='L' else .5))%1;targets[sd]=target(name,sd,phase)
  pel=world('B_Pelvis');z=.704 if name=='Running' else .78
  for sd,(T,Q)in targets.items():
   H=world(f'B_{sd}_Thigh').translation;a,b=lens[sd];reach=a+b-.003
   planar=(T.x-H.x)**2+(T.y-H.y)**2;assert planar<reach*reach
   z=min(z,T.z+math.sqrt(reach*reach-planar)+pel.translation.z-H.z)
  pel.translation.z=z;rig.pose.bones['B_Pelvis'].matrix=rig.matrix_world.inverted()@pel;bpy.context.view_layer.update()
  for sd,(T,Q)in targets.items():solve(sd,T,Q)
  frames.append(capture())
 act(None);bpy.data.actions.remove(bpy.data.actions[name]);a=bpy.data.actions.new(name);a.use_fake_user=True;prev={}
 for f,p in enumerate(frames):
  act(a)
  for n,(q,l)in p.items():
   pb=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f/4)
   if n=='B_Pelvis' or any(t in n for t in ['Calf','Foot']):pb.location=l;pb.keyframe_insert('location',frame=f/4)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=24
 for lay in a.layers:
  for strip in lay.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
act(None)
# This continuous tunic has no slit between the front/back panels. Keep each central panel coherent,
# and blend smoothly into its side-thigh strip, with the belt anchored to the pelvis.
me=body.data;pv=np.array([x.value for x in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);names={g.index:g.name for g in body.vertex_groups};changed=[]
def put(i,w):
 for e in me.vertices[i].groups[:]:body.vertex_groups[e.group].remove([i])
 for n,v in w.items():
  if v>1e-7:body.vertex_groups[n].add([i],float(v),'REPLACE')
def cloth(x,z):
 h=smooth((.73-z)/.30);wl=.5+.5*np.sign(x)*smooth((abs(x)-.075)/.20)
 return {'B_Pelvis':1-h,'B_L_Thigh':h*wl,'B_R_Thigh':h*(1-wl)}
for i in np.where(pv==2)[0]:put(int(i),cloth(co[i,0],co[i,2]));changed.append(int(i))
# Covered trouser cuffs and metal studs follow the same host shell; no stud bridges panels.
from mathutils.kdtree import KDTree
kd=KDTree(int((pv==2).sum()))
for i in np.where(pv==2)[0]:kd.insert(co[i],int(i))
kd.balance()
for i in np.where((pv==5)&(co[:,2]>.32))[0]:
 t=float(np.clip((co[i,2]-.32)/.08,0,1));w={names[g.group]:g.weight*(1-t)for g in me.vertices[int(i)].groups};_,j,_=kd.find(co[i])
 for g in me.vertices[j].groups:w[names[g.group]]=w.get(names[g.group],0)+t*g.weight
 total=sum(w.values());put(int(i),{n:v/total for n,v in w.items()});changed.append(int(i))
owners=json.loads((P/'work/stud_owners.json').read_text())
for piece,host in owners.items():
 if host!=2:continue
 ids=np.where(pv==int(piece))[0];c=co[ids].mean(0);_,j,_=kd.find(c);w={names[g.group]:g.weight for g in me.vertices[j].groups}
 for i in ids:put(int(i),w);changed.append(int(i))
(P/'work/round3_weight_changes.json').write_text(json.dumps({'vertices':changed,'positions':co.tolist(),'weights':[{names[g.group]:g.weight for g in v.groups}for v in me.vertices],'pieces':pv.tolist()},indent=2))
act(bpy.data.actions['Standing']);scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
print('ROUND3 MOTION AND CLOTH COMPLETE',len(changed),'weight vertices')
