"""Jogging upper-body retarget over accepted, stride-matched short-leg IK cycle."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round6/jog_source.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene

def act(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 act(a);scene.frame_set(int(f),subframe=f%1)
 return {b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
def apply(p):
 act(None)
 for n,(q,l) in p.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
rest=sample(bpy.data.actions['Standing'],0)
old=[sample(bpy.data.actions['Running'],i/4)for i in range(97)]
src=[sample(bpy.data.actions['JogSource'],.5+26*i/96)for i in range(97)]
# Smooth the small source-cycle drift throughout the loop, with exact endpoints.
for i,p in enumerate(src):
 for n,(q,l)in list(p.items()):
  delta=src[-1][n][0].rotation_difference(src[0][n][0]);p[n]=(q@Quaternion().slerp(delta,i/96),l)
# Measure fore/aft sole patch direction on the unchanged accepted body.
body=bpy.data.objects['Body'];sole_axes={}
for sd in 'LR':
 pts=[v.co for v in body.data.vertices if (v.co.x>0)==(sd=='L')and v.co.z<.06]
 yy=np.array([v.y for v in pts]);heel=sum((v for v in pts if v.y>=np.quantile(yy,.7)),Vector())/sum(yy>=np.quantile(yy,.7));toe=sum((v for v in pts if v.y<=np.quantile(yy,.3)),Vector())/sum(yy<=np.quantile(yy,.3))
 sole_axes[sd]=rig.data.bones[f'B_{sd}_Foot'].matrix_local.to_3x3().inverted()@(toe-heel)
frames=[]
for i,p in enumerate(old):
 for n in p:
  if any(t in n for t in ['Spine','Neck','Head','Clavicle','UpperArm','Forearm']):p[n]=(src[i][n][0],rest[n][1])
  if 'Hand' in n or 'Finger' in n:p[n]=rest[n]
 apply(p)
 for sd in 'LR':
  pb=rig.pose.bones[f'B_{sd}_Foot'];M=pb.matrix.copy();v=M.to_3x3()@sole_axes[sd];yaw=math.atan2(v.y,v.x);t=M.translation.copy();M=Matrix.Rotation(-math.pi/2-yaw-(math.radians(1)if sd=='R'else 0),4,'Z')@M;M.translation=t;pb.matrix=M
 bpy.context.view_layer.update()
 # Carry the axe outside the torso; retain source forward/back swing.
 for sd in 'LR':
  un,fn,hn=[f'B_{sd}_{n}'for n in ['UpperArm','Forearm','Hand']]
  pb=rig.pose.bones[un];M=pb.matrix.copy();t=M.translation.copy()
  M=Matrix.Rotation(math.radians(12 if sd=='R'else -4),4,'Y')@M;M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
  # Rotate the upper-arm hinge onto the elbow path, preserving forearm and hand world frames.
  U=rig.pose.bones[un].matrix.copy();F=rig.pose.bones[fn].matrix.copy();H=rig.pose.bones[hn].matrix.copy()
  u=(F.translation-U.translation).normalized();v=(H.translation-F.translation).normalized();h=U.to_3x3()@Vector((0,0,-1));target=u.cross(v).normalized()
  h=(h-u*h.dot(u)).normalized();angle=math.atan2(u.dot(h.cross(target)),h.dot(target))
  M=Matrix.Rotation(angle,4,u)@U;M.translation=U.translation;rig.pose.bones[un].matrix=M;bpy.context.view_layer.update()
  rig.pose.bones[fn].matrix=F;bpy.context.view_layer.update();rig.pose.bones[hn].matrix=H;bpy.context.view_layer.update()
 for sd in 'LR':
  for base,child,helper,share in [('Forearm','Hand','ForearmTwist',.5),('UpperArm','Forearm','UpperArmTwist',-.5)]:
   bn=f'B_{sd}_{base}';cn=f'B_{sd}_{child}';b=rig.data.bones[bn];c=rig.data.bones[cn];axis=(b.matrix_local.inverted()@c.head_local).normalized()
   if base=='Forearm':q=(rig.pose.bones[bn].matrix.inverted()@rig.pose.bones[cn].matrix).to_quaternion()@(b.matrix_local.inverted()@c.matrix_local).to_quaternion().inverted()
   else:q=rig.pose.bones[bn].rotation_quaternion
   angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);angle=(angle+math.pi)%(2*math.pi)-math.pi
   rig.pose.bones[f'B_{sd}_{helper}'].rotation_quaternion=Quaternion(axis,angle*share)
 bpy.context.view_layer.update()
 frames.append({b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones})
frames[-1]=frames[0]
act(None);bpy.data.actions.remove(bpy.data.actions['Running']);a=bpy.data.actions.new('Running');a.use_fake_user=True;prev={}
worlds=[]
for i,p in enumerate(frames):
 apply(p);worlds.append({b.name:[list(r)for r in rig.matrix_world@b.matrix]for b in rig.pose.bones})
 act(a)
 for n,(q,l)in p.items():
  pb=rig.pose.bones[n]
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;pb.rotation_quaternion=q;pb.location=l
  pb.keyframe_insert('rotation_quaternion',frame=i/4);pb.keyframe_insert('location',frame=i/4)
a.use_frame_range=True;a.frame_start=0;a.frame_end=24
for lay in a.layers:
 for strip in lay.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.render.fps=30
(P/'work/round6/running_world.json').write_text(json.dumps({'times':list(np.linspace(0,.8,97)),'poses':worlds,'rest':{b.name:[list(r)for r in rig.matrix_world@b.matrix_local]for b in rig.data.bones}}))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round6/running_author.blend'))
print('RUNNING JOG RETARGET READY')
