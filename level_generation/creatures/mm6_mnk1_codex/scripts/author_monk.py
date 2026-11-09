"""Native folded-arm identity over selected library motion; fixed-length arm IK."""
import bpy,math,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/retarget_raw.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;B=r.data.bones;names=[b.name for b in B]
def update():bpy.context.view_layer.update()
def setact(a):
 r.animation_data_create();r.animation_data.action=a
 if a and len(a.slots):r.animation_data.action_slot=a.slots[0]
def capture():return {n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 setact(None)
 for n,(q,l) in pose.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].location=l
 update()
def worldrot(n,q):
 pb=r.pose.bones[n];m=q.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;update()
def aim(n,child,target):
 pb=r.pose.bones[n];a=r.pose.bones[child].head-pb.head;b=Vector(target)-pb.head
 rest=B[child].head_local-B[n].head_local
 carry=pb.parent.matrix.to_3x3()@B[n].parent.matrix_local.to_3x3().inverted() if pb.parent else Matrix.Identity(3)
 ref=carry@B[n].matrix_local.to_3x3()
 worldrot(n,(carry@rest).rotation_difference(b)@ref.to_quaternion())
def ik(sd,target,pole,handdir=None):
 u,f,h=[f'B_{sd}_{n}' for n in ['UpperArm','Forearm','Hand']]
 sh=r.pose.bones[u].head.copy();L1=(B[f].head_local-B[u].head_local).length;L2=(B[h].head_local-B[f].head_local).length
 dv=Vector(target)-sh;D=min(dv.length,L1+L2-.001);d=dv.normalized();target=sh+d*D
 a=(L1*L1-L2*L2+D*D)/(2*D);b=math.sqrt(max(0,L1*L1-a*a));v=Vector(pole)-sh;v=(v-d*v.dot(d)).normalized();el=sh+d*a+v*b
 aim(u,f,el);aim(f,h,target)
 if handdir:
  restdir=B[f'B_{sd}_Finger2'].head_local-B[h].head_local
  q=restdir.rotation_difference(Vector(handdir))
  worldrot(h,q@B[h].matrix_local.to_quaternion())
 assert (r.pose.bones[h].head-target).length<.0001

def leg(sd,target,pole=(0,-1,0),prone=0):
 u,f,h=[f'B_{sd}_{n}' for n in ['Thigh','Calf','Foot']];sh=r.pose.bones[u].head.copy()
 L1=(B[f].head_local-B[u].head_local).length;L2=(B[h].head_local-B[f].head_local).length
 dv=Vector(target)-sh;D=min(dv.length,L1+L2-.002);d=dv.normalized();target=sh+d*D
 a=(L1*L1-L2*L2+D*D)/(2*D);b=math.sqrt(max(0,L1*L1-a*a));v=Vector(pole);v=(v-d*v.dot(d)).normalized()
 aim(u,f,sh+d*a+v*b);aim(f,h,target);worldrot(h,Quaternion((1,0,0),prone)@B[h].matrix_local.to_quaternion())

def smooth(t):t=min(1,max(0,t));return t*t*(3-2*t)
def write(n,frames):
 old=bpy.data.actions.get(n)
 if old:bpy.data.actions.remove(old)
 act=bpy.data.actions.new(n);act.use_fake_user=True;setact(act);prev={}
 for i,pose in enumerate(frames):
  for bn,(q,l) in pose.items():
   q=q.copy()
   if bn in prev and q.dot(prev[bn])<0:q.negate()
   prev[bn]=q.copy();pb=r.pose.bones[bn];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
   pb.keyframe_insert('rotation_quaternion',frame=i)
   if bn=='B_Pelvis':pb.keyframe_insert('location',frame=i)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=len(frames)-1;setact(None)
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 return act
# Cache before replacing actions; every pose has all bones and the source cadence.
raw={}
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']:
 act=bpy.data.actions[name];setact(act);raw[name]=[]
 for f in range(int(act.frame_range[1])+1):scene.frame_set(f);raw[name].append(capture())
setact(None)
apply(raw['Standing'][0]);standing_root_z=r.pose.bones['B_Pelvis'].head.z;standing_world={n:r.pose.bones[n].matrix.to_quaternion().copy() for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2']}

def folded(dz=0):
 # Wrist stagger keeps the two broad sleeves from occupying one plane.
 ik('R',(-.055,-.34,1.19+dz),(-.35,-.42,1.20+dz),(.9,-.05,.10))
 ik('L',(.055,-.30,1.30+dz),(.35,-.42,1.20+dz),(-.9,-.05,-.15))
 for n in names:
  if 'Finger' in n:r.pose.bones[n].rotation_quaternion=Quaternion().slerp(raw['Attack'][0][n][0],.70)
 update()

pv=np.zeros(len(body.data.vertices),np.int32);body.data.attributes['piece'].data.foreach_get('value',pv)
def ground():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices if pv[v.index]!=1);ev.to_mesh_clear()
 root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z-=lo;root.matrix=m;update()

out={}
for name in ['Standing','Walking','Running','Fidget']:
 frames=[]
 for i,pose in enumerate(raw[name]):
  apply(pose)
  if name in ['Walking','Running']:
   # Preserve leg cadence, calm the source's stylized hip/spine oscillation.
   for n in standing_world:worldrot(n,standing_world[n].slerp(r.pose.bones[n].matrix.to_quaternion(),.16 if name=='Walking' else .28))
  if name in ['Walking','Running']:
   for sd,sign,phase in [('L',1,0),('R',-1,math.pi)]:
    a=i/max(1,len(raw[name])-1)*math.tau+phase
    leg(sd,(sign*.16,-.03+.12*math.sin(a),.11+.035*max(0,math.cos(a))))
  folded()
  if name=='Fidget':
   a=math.sin(i/max(1,len(raw[name])-1)*math.tau)*.17
   worldrot('B_Head',Quaternion((0,0,1),a)@r.pose.bones['B_Head'].matrix.to_quaternion())
  ground();frames.append(capture())
 frames[-1]=frames[0];out[name]=frames;write(name,frames)
base=out['Standing'][0];apply(base);base_palms={sd:r.pose.bones[f'B_{sd}_Hand'].matrix.to_quaternion().copy() for sd in ['L','R']}
for name in ['Attack','Cast','Hit','Death']:
 frames=[];N=len(raw[name])-1
 for i,pose in enumerate(raw[name]):
  apply(pose)
  if name!='Death':
   for n in ['B_Spine','B_Spine1','B_Spine2']:worldrot(n,standing_world[n].slerp(r.pose.bones[n].matrix.to_quaternion(),.5))
  # Open casting fingers retain a little of the original articulation.
  for n in names:
   if 'Finger' in n:r.pose.bones[n].rotation_quaternion=Quaternion().slerp(raw['Attack'][0][n][0],.70).slerp(r.pose.bones[n].rotation_quaternion,.2)
  update();target=capture()
  if name=='Hit':target={n:(base[n][0].slerp(q,.30),base[n][1].lerp(l,.30)) for n,(q,l) in target.items()}
  u=smooth(i/(3 if name=='Hit' else 9))
  if name!='Death':u*=smooth((N-i)/(4 if name=='Hit' else 9))
  apply({n:(base[n][0].slerp(target[n][0],u),base[n][1].lerp(target[n][1],u)) for n in names})
  if name=='Death' and i>20:
   original=capture();u=smooth((i-20)/18)
   for sd,sign in [('L',1),('R',-1)]:
    hip=r.pose.bones[f'B_{sd}_Thigh'].head.copy();leg(sd,(hip.x+sign*.025,hip.y+.70,.19),pole=(0,0,-1),prone=math.pi/2)
   straight=capture();apply({n:(original[n][0].slerp(straight[n][0],u),original[n][1]) for n in names})
  # Reconstruct limb roll from the A-pose while retaining the selected joint trajectory.
  for sd,sign in [('R',-1),('L',1)]:
   hn=f'B_{sd}_Hand';wrist=r.pose.bones[hn].head.copy();palm=r.pose.bones[hn].matrix.to_quaternion().copy();pole=r.pose.bones[f'B_{sd}_Forearm'].head.copy()
   if name=='Death':
    u=smooth(i/12);neck=r.pose.bones['B_Neck'].head;target=Vector((neck.x+sign*.34,neck.y+.08,max(.14,neck.z-.30)))
    wrist=wrist.lerp(target,u);pole=pole.lerp(Vector((neck.x+sign*.44,neck.y+.20,max(.20,neck.z-.24))),u)
   if name!='Death':
    u=smooth(i/3)*smooth((N-i)/5);want=wrist.copy();want.x=sign*max(.22,sign*wrist.x);want.y=min(-.32,wrist.y);wrist=wrist.lerp(want,u);wrist.y-=.035*u if sd=='L' else 0;pole=pole.lerp(Vector((sign*.36,-.30,pole.z)),u)
   if name=='Cast':
    if sd=='L':wrist.z+=.065*u
    palm=base_palms[sd].slerp(palm,smooth(i/6)*smooth((N-i)/9))
   ik(sd,wrist,pole);worldrot(hn,palm)
   if name=='Death':
    rf=(B[f'B_{sd}_Finger2'].head_local-B[hn].head_local).normalized();rn=rf.cross(B[f'B_{sd}_Finger1'].head_local-B[f'B_{sd}_Finger4'].head_local).normalized()
    if rn.y>0:rn=-rn
    rt=rn.cross(rf).normalized();rn=rf.cross(rt).normalized();df=Vector((0,-1,0));dn=Vector((0,0,-1));dt=dn.cross(df)
    src=Matrix((rf,rt,rn)).transposed();dst=Matrix((df,dt,dn)).transposed();q=(dst@src.transposed()).to_quaternion()@B[hn].matrix_local.to_quaternion()
    worldrot(hn,palm.slerp(q,smooth(i/12)))
  if name=='Hit':
   dz=r.pose.bones['B_Pelvis'].head.z-standing_root_z;folded(dz);ik('L',(.055,-.30,1.30+dz+.06*math.sin(i/max(1,N)*math.pi)),(.35,-.42,1.20+dz),(-.9,-.05,-.15))
  ground();frames.append(capture())
 # Attack2 pushes at 0.45 s: add 0.25 s of native folded ready, not a stretched source gesture.
 if name=='Attack':frames=[base]*8+frames
 out[name]=frames;write(name,frames)
write('Running',out['Walking']);out['Running']=out['Walking']
write('Dead',[out['Death'][-1]]*31)
apply(base);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/anim_pilot.blend'))
# Pilot views at actual rest/gesture extremes.
common.workbench_clay(scene,textured=True)
for name,fs in [('Standing',[0]),('Walking',[0,8,16]),('Attack',[0,15,22,30]),('Death',[30,len(out['Death'])-1])]:
 setact(bpy.data.actions[name])
 for f in fs:
  scene.frame_set(f);common.render_views(str(p/'review'/f'pilot_{name}_{f}'),.86,1.95,views=('front','left','three_quarter'),resolution=(600,800))
