"""Native hit/fidget and the owned backward fall, with rigid closed fists."""
import bpy,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/death_raw.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
names=list(rig.pose.bones.keys())
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]

def reset():
 setact(None)
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4);pb.rotation_mode='QUATERNION'
 bpy.context.view_layer.update()

def new(name,end):
 a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=end*30;return a

def write(a,t,previous):
 setact(a)
 for pb in rig.pose.bones:
  q=pb.rotation_quaternion.copy()
  if pb.name in previous and q.dot(previous[pb.name])<0:q.negate()
  previous[pb.name]=q.copy();pb.rotation_quaternion=q
  pb.keyframe_insert('rotation_quaternion',frame=t*30,group=pb.name)
  if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=t*30,group=pb.name)
 setact(None)

def rotate(n,axis,angle):
 pb=rig.pose.bones[n];axis=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector(axis)
 pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(axis,math.radians(angle))
 bpy.context.view_layer.update()

def aim(n,child,target):
 pb=rig.pose.bones[n];direction=rig.pose.bones[child].head-pb.head;q=direction.rotation_difference(target-pb.head)
 m=(q@pb.matrix.to_quaternion()).to_matrix().to_4x4();m.translation=pb.head;location=pb.location.copy()
 pb.matrix=m;pb.location=location;pb.scale=(1,1,1);bpy.context.view_layer.update()

def arm(sd,offset,chest):
 up,fore,hand=[f'B_{sd}_{n}' for n in ['UpperArm','Forearm','Hand']]
 shoulder=rig.pose.bones[up].head.copy();target=shoulder+chest@Vector(offset)
 ul=(rig.data.bones[fore].head_local-rig.data.bones[up].head_local).length;fl=(rig.data.bones[hand].head_local-rig.data.bones[fore].head_local).length
 d=target-shoulder;length=d.length;assert abs(ul-fl)+.005<length<ul+fl-.002,(sd,length,ul,fl);d.normalize()
 ready_direction=(rig.pose.bones[hand].head-shoulder).normalized()
 pole=ready_direction.rotation_difference(d)@(rig.pose.bones[fore].head-shoulder);pole-=d*d.dot(pole);assert pole.length>.005;pole.normalize()
 along=(ul*ul-fl*fl+length*length)/(2*length);elbow=shoulder+d*along+pole*math.sqrt(max(0,ul*ul-along*along))
 aim(up,fore,elbow);aim(fore,hand,target)
 assert (rig.pose.bones[hand].head-target).length<.0001
def floor():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=min(v.co.z for v in me.vertices);ev.to_mesh_clear()
 pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z-=z;pb.matrix=m;bpy.context.view_layer.update()
def ease(x):
 x=max(0,min(1,float(x)));return x*x*(3-2*x)
reset()
ready={sd:rig.pose.bones[f'B_{sd}_Hand'].head-rig.pose.bones[f'B_{sd}_UpperArm'].head for sd in ['L','R']}
hit=new('Hit',.75);previous={}
for t in np.linspace(0,.75,46):
 reset();v=ease(t/.16) if t<.16 else 1-ease((t-.16)/.59)
 for n,k in [('B_Spine',.25),('B_Spine1',.45),('B_Spine2',.30)]:
  rotate(n,(1,0,0),-14*v*k);rotate(n,(0,0,1),-4*v*k)
 rotate('B_Head',(1,0,0),6*v);rotate('B_R_Thigh',(1,0,0),-16*v);rotate('B_R_Calf',(1,0,0),26*v)
 chest=(rig.pose.bones['B_Spine2'].matrix@rig.data.bones['B_Spine2'].matrix_local.inverted()).to_3x3().normalized()
 for sd,target in [('L',(.12,-.48,-.16)),('R',(-.12,-.47,-.16))]:arm(sd,ready[sd].lerp(Vector(target),v),chest)
 floor();write(hit,float(t),previous)
fidget=new('Fidget',2.4);previous={}
for t in np.linspace(0,2.4,73):
 reset();v=math.sin(t/2.4*2*math.pi)*math.sin(t/2.4*math.pi)**2
 rotate('B_Spine1',(0,0,1),6*v);rotate('B_Spine2',(0,1,0),2*v);rotate('B_Neck',(0,0,1),-4*v)
 rotate('B_L_UpperArm',(1,0,0),-5*v);rotate('B_R_UpperArm',(1,0,0),4*v)
 write(fidget,float(t),previous)
# Compress the long source lead-in, retaining the actual backfall and landing.
raw=bpy.data.actions['DeathRaw'];setact(raw);poses=[];roots=[]
times=np.linspace(0,1.8,109)
for t in times:
 st=float(np.interp(t,[0,.18,.38,.65,1.15,1.5,1.8],[0,.55,1.2,1.8,2.6,3.25,4.6]))
 frame=st*30;scene.frame_set(math.floor(frame),subframe=frame%1)
 poses.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names})
 roots.append(rig.pose.bones['B_Pelvis'].head.copy())
setact(None);death=new('Death',1.8);previous={}
for t,pose in zip(times,poses):
 reset();weight=ease(t/.20)
 for n,m in pose.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=Quaternion().slerp(m.to_quaternion(),weight)
  if n=='B_Pelvis':pb.location=m.translation*weight
 for sd in ['L','R']:rig.pose.bones[f'B_{sd}_Hand'].rotation_quaternion=Quaternion()
 bpy.context.view_layer.update();pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy()
 delta=roots[0]-rig.data.bones['B_Pelvis'].head_local
 m.translation-=Vector((delta.x,delta.y,0))*weight;pb.matrix=m
 floor();write(death,float(t),previous)
held={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
dead=new('Dead',1.0);previous={}
for t in [0.,1.]:
 reset()
 for n,m in held.items():rig.pose.bones[n].matrix_basis=m
 write(dead,t,previous)
bpy.data.actions.remove(raw)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_v1.blend'))
out=P/'review/full_motion_v1';out.mkdir(exist_ok=True);rows=[]
common.workbench_clay(scene);scene.display.shading.color_type='OBJECT';body.color=(.55,.56,.57,1)
for name in ['Hit','Fidget','Death','Dead']:
 a=bpy.data.actions[name];setact(a)
 for view in ['front','left','three_quarter']:
  row=[]
  for i in range(7 if name!='Dead' else 1):
   frame=a.frame_range[1]*i/6;scene.frame_set(math.floor(frame),subframe=frame%1)
   path=common.render_views(str(out/f'{name}_{view}_{i}'),1.0,3.3,views=(view,),resolution=(440,420))[0]
   row.append([path,f'{name} {view} {frame/30:.2f}s'])
  rows.append(row)
(out/'frames.json').write_text(json.dumps(rows))
