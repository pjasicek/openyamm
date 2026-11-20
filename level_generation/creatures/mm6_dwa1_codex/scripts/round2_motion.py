"""Round 2: source Hit reaction and sole targets solved by leg rotations; no root floor shift."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
scene=bpy.context.scene
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_hit_source.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene

def act(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 act(a);scene.frame_set(int(f),subframe=f-int(f))
 return {b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
sources={name:[sample(bpy.data.actions[name],f)for f in range(14)]for name in ['HitAlternate','HitAlternateFull']}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_before/work/textured_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
names=[b.name for b in rig.pose.bones];roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
poses={n:[sample(bpy.data.actions[n],f)for f in range(int(bpy.data.actions[n].frame_range[1])+1)]for n in roles}
rest=poses['Standing'][0]
def smooth(x):
 x=min(1,max(0,x));return x*x*(3-2*x)
def apply(p):
 act(None)
 for n,(q,l)in p.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
def capture():return {b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
# The source is 0.433 s; retain its original 30 Hz timing and spend the final 2 frames returning to rest.
hit=[]
for f in range(16):
 i=min(f,13);raw=sources['HitAlternate'][i];full=sources['HitAlternateFull'][i]
 p={n:(q.copy(),l.copy())for n,(q,l)in rest.items()}
 for n in raw:
  if n not in p or 'Finger'in n or any(t in n for t in ['Thigh','Calf','Foot','Toe']):continue
  if n=='B_Pelvis':
   delta=sources['HitAlternateFull'][0][n][0].rotation_difference(full[n][0]);p[n]=(rest[n][0]@Quaternion().slerp(delta,.2),rest[n][1]+.2*(full[n][1]-sources['HitAlternateFull'][0][n][1]));continue
  # Keep the relaxed hand/arm baseline and transfer the source reaction, not its foreign resting guard.
  q0=sources['HitAlternate'][0][n][0];delta=q0.rotation_difference(raw[n][0])
  if any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand']):delta=Quaternion().slerp(delta,.30)
  q=rest[n][0]@delta
  w=min(smooth(f/2),smooth((15-f)/4));p[n]=(rest[n][0].slerp(q,w),rest[n][1])
 w=min(smooth(f/2),smooth((15-f)/4));q,l=p['B_Pelvis'];p['B_Pelvis']=(rest['B_Pelvis'][0].slerp(q,w),rest['B_Pelvis'][1].lerp(l,w))
 apply(p)
 axis=rig.pose.bones['B_Spine2'].matrix.to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,1,0))
 pb=rig.pose.bones['B_R_UpperArm'];M=pb.matrix.copy();c=M.translation.copy();M=Matrix.Rotation(math.radians(24)*w,4,axis)@M;M.translation=c;pb.matrix=M;bpy.context.view_layer.update()
 # Recompute the existing twist helpers for this new reaction only, keeping the accepted weights.
 for sd in 'LR':
  for base,child,helper,share in [('Forearm','Hand','ForearmTwist',.5),('UpperArm','Forearm','UpperArmTwist',-.5)]:
   bn=f'B_{sd}_{base}';cn=f'B_{sd}_{child}';b=rig.data.bones[bn];c=rig.data.bones[cn];axis=(b.matrix_local.inverted()@c.head_local).normalized()
   if base=='Forearm':q=(rig.pose.bones[bn].matrix.inverted()@rig.pose.bones[cn].matrix).to_quaternion()@(b.matrix_local.inverted()@c.matrix_local).to_quaternion().inverted()
   else:q=rig.pose.bones[bn].rotation_quaternion
   a=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);a=(a+math.pi)%(2*math.pi)-math.pi
   rig.pose.bones[f'B_{sd}_{helper}'].rotation_quaternion=Quaternion(axis,a*share)
 bpy.context.view_layer.update();hit.append(capture())
# Preserve exact accepted rest endpoint, including twist helpers.
hit[0]={n:(q.copy(),l.copy())for n,(q,l)in rest.items()};hit[-1]={n:(q.copy(),l.copy())for n,(q,l)in rest.items()};poses['Hit']=hit
# Align the humeral hinge plane with the existing elbow/wrist path; keep all joint centres and hand/axe motion.
source_rest=json.loads((P/'work/source_rest.json').read_text());hinges={};roll_report={}
for sd in 'LR':
 n=f'B_{sd}_UpperArm';su=Vector(source_rest[n]['seg']).normalized();hinges[sd]=Matrix(source_rest[n]['rot']).inverted()@su.cross(Vector((0,-1,0))).normalized()
for name in ['Attack','Fidget']:
 out=[];roll_report[name]={sd:[]for sd in 'LR'}
 for p in poses[name]:
  apply(p)
  for sd in 'LR':
   un,fn,hn=[f'B_{sd}_{k}'for k in ['UpperArm','Forearm','Hand']]
   U=world(un);F=world(fn);H=world(hn);u=(F.translation-U.translation).normalized();v=(H.translation-F.translation).normalized()
   # Transform the source hinge through the authored rest swing, then the current upper-arm frame.
   rest_h=rig.data.bones[un].matrix_local.to_3x3()@hinges[sd];local_h=rig.data.bones[un].matrix_local.to_3x3().inverted()@rest_h
   h=(U.to_3x3()@local_h).normalized();target=u.cross(v);bend=math.acos(max(-1,min(1,u.dot(v))));angle=0.
   if target.length>1e-5 and h.dot(target)>0:
    target.normalize();h=(h-u*h.dot(u)).normalized();angle=math.atan2(u.dot(h.cross(target)),h.dot(target))*smooth((math.degrees(bend)-3)/7)
    M=Matrix.Rotation(angle,4,u)@U;M.translation=U.translation;rig.pose.bones[un].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
    rig.pose.bones[fn].matrix=rig.matrix_world.inverted()@F;bpy.context.view_layer.update()
    assert (world(hn).translation-H.translation).length<1e-5
    b=rig.data.bones[un];axis=(b.matrix_local.inverted()@rig.data.bones[fn].head_local).normalized();q=rig.pose.bones[un].rotation_quaternion
    a=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);a=(a+math.pi)%(2*math.pi)-math.pi
    rig.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*a)
   roll_report[name][sd].append(math.degrees(angle))
  bpy.context.view_layer.update();out.append(capture())
 poses[name]=out
(P/'review/round2/hinge_correction.json').write_text(json.dumps({n:{sd:[min(x),max(x)]for sd,x in sides.items()}for n,sides in roll_report.items()},indent=2))
# Sole vertices are selected on the original bind-space bottom surface, never by each posed minimum.
sole={};flat={};home={};forward={};old_home_z={};extension={};old_home={}
for sd in 'LR':
 n=f'B_{sd}_Foot';M=rig.data.bones[n].matrix_local
 ids=[v.index for v in body.data.vertices if (v.co.x>0)==(sd=='L') and v.co.z<.008]
 assert len(ids)>12
 sole[sd]={'ids':ids,'local':[M.inverted()@body.data.vertices[i].co for i in ids]}
 apply(rest);W=world(n);D=W.to_3x3()@M.to_3x3().inverted();normal=D@Vector((0,0,1))
 flat[sd]=normal.rotation_difference(Vector((0,0,1)))@W.to_quaternion()
 old_home[sd]=W.translation.copy();old_home_z[sd]=W.translation.z;T=W.translation.copy();T.z=.004-min((flat[sd]@v).z for v in sole[sd]['local']);home[sd]=T
 d=D@Vector((0,-1,0));d.z=0;forward[sd]=d.normalized()


def aim(n,child,direction):
 M=world(n);current=world(child).translation-M.translation
 R=current.normalized().rotation_difference(direction.normalized()).to_matrix().to_4x4();t=M.translation.copy();M=R@M;M.translation=t
 rig.pose.bones[n].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()

def solve(sd,T,Q):
 th,ca,ft=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']]
 H=world(th).translation;K=world(ca).translation;A=world(ft).translation;a=(K-H).length;b=(A-K).length
 if name=='Walking' and (T-H).length>(a+b)*1.032:
  reach=(a+b)*1.032;dz=H.z-T.z;off=Vector((T.x-H.x,T.y-H.y,0));radius=math.sqrt(max(0,reach*reach-dz*dz))
  if off.length>radius:off*=radius/off.length;T.x=H.x+off.x;T.y=H.y+off.y
 # Bounded IK extension reaches the flat target without shifting the accepted hip/body keys.
 distance=(T-H).length;stretch=max(1,(distance+.0005)/(a+b));assert stretch<1.04,('IK reach',name,f,sd,stretch)
 extension.setdefault(name,{}).setdefault(sd,[]).append(stretch);a*=stretch;b*=stretch
 u=(T-H).normalized();v=(forward[sd]-u*forward[sd].dot(u)).normalized();c=(a*a+distance*distance-b*b)/(2*a*distance)
 knee=H+a*(u*c+v*math.sqrt(max(0,1-c*c)))
 aim(th,ca,knee-H)
 M=world(ca);M.translation=knee;rig.pose.bones[ca].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
 aim(ca,ft,T-knee)
 M=Q.to_matrix().to_4x4();M.translation=T;rig.pose.bones[ft].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
 assert (world(ft).translation-T).length<1e-5

for name in ['Standing','Fidget','Hit','Attack','Walking']:
 out=[]
 for f,p in enumerate(poses[name]):
  apply(p);pelvis=world('B_Pelvis').copy()
  for sd in 'LR':
   n=f'B_{sd}_Foot';W=world(n);R=rig.data.bones[n].matrix_local;normal=(W.to_3x3()@R.to_3x3().inverted())@Vector((0,0,1))
   Q=normal.rotation_difference(Vector((0,0,1)))@W.to_quaternion()
   if name in ['Standing','Fidget','Hit']:T=home[sd].copy();Q=flat[sd].copy()
   else:
    T=W.translation.copy();low=min((W@v).z for v in sole[sd]['local'])
    if name=='Walking':
     T.z=max(.004,low)-min((Q@v).z for v in sole[sd]['local'])
    else:
     # Keep the authored discrete steps; flatten landing soles without changing pelvis motion.
     T.z=home[sd].z+max(0,W.translation.z-old_home_z[sd])
   solve(sd,T,Q)
  assert np.max(np.abs(np.array(world('B_Pelvis'))-np.array(pelvis)))<1e-7
  out.append(capture())
 poses[name]=out

def write(name,frames):
 act(None);old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;prev={}
 for f,p in enumerate(frames):
  act(a)
  for n,(q,l)in p.items():
   pb=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis' or any(t in n for t in ['Calf','Foot']):pb.location=l;pb.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(frames)-1
 for lay in a.layers:
  for strip in lay.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 act(None)
for name in ['Standing','Fidget','Hit','Attack','Walking']:write(name,poses[name])
(P/'review/round2/leg_ik_extension.json').write_text(json.dumps({n:{sd:max(vals)for sd,vals in sides.items()}for n,sides in extension.items()},indent=2))
(P/'work/round2_sole.json').write_text(json.dumps({sd:{'ids':s['ids'],'local':[list(v)for v in s['local']],'target_ankle':list(home[sd]),'target_rotation':list(flat[sd])}for sd,s in sole.items()},indent=2))
act(bpy.data.actions['Standing']);scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
print('ROUND2 MOTION COMPLETE')
