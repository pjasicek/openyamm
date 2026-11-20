"""Standing, in-place owned walk, and native left rising strike pilot on the fitted rig."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/walk_raw_v6.blend'))
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
# Remove horizontal travel, retaining the owned source's gait and timing.
a=bpy.data.actions['Walking'];setact(a);poses=[];roots=[]
for f in range(44):
 scene.frame_set(f);poses.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names});roots.append(rig.pose.bones['B_Pelvis'].head.copy())
setact(None);bpy.data.actions.remove(a);walk=new('Walking',43/30);previous={}
stride=(roots[-1]-roots[0]).xy.length
for f,pose in enumerate(poses):
 reset()
 for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
 for sd in ['L','R']:
  rig.pose.bones[f'B_{sd}_Hand'].rotation_quaternion=Quaternion()
  for part,amount in [('UpperArm',.55),('Forearm',.30)]:
   bone=rig.pose.bones[f'B_{sd}_{part}'];bone.rotation_quaternion=Quaternion().slerp(bone.rotation_quaternion,amount)
 bpy.context.view_layer.update();pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy()
 displacement=roots[0].lerp(roots[-1],f/43)-rig.data.bones['B_Pelvis'].head_local
 m.translation-=Vector((displacement.x,displacement.y,0));pb.matrix=m
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps);me=ev.to_mesh();floor=min(v.co.z for v in me.vertices);ev.to_mesh_clear()
 pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z-=floor;pb.matrix=m
 write(walk,f/30,previous)
reset();standing=new('Standing',2.4);previous={}
for t in np.linspace(0,2.4,73):
 reset();v=math.sin(2*math.pi*t/2.4)
 rotate('B_Spine1',(0,0,1),.8*v);rotate('B_Neck',(0,0,1),-.5*v)
 write(standing,float(t),previous)
reset()
ready={sd:rig.pose.bones[f'B_{sd}_Hand'].head-rig.pose.bones[f'B_{sd}_UpperArm'].head for sd in ['L','R']}
keys=np.array([
 [0,*ready['L'],*ready['R'],0,0],
 [.20,.08,-.30,-.52,-.07,-.30,-.45,5,-2],
 [.43,-.10,-.35,-.48,-.10,-.35,-.45,16,-9],
 [.60,.03,-.47,-.25,-.11,-.33,-.40,6,-2],
 [.75,.55,-.32,.08,-.13,-.30,-.32,-18,12],
 [.90,.61,-.25,.24,-.12,-.28,-.29,-24,9],
 [1.15,.27,-.39,-.13,-.07,-.31,-.37,-10,5],
 [1.50,*ready['L'],*ready['R'],0,0]],float)
def anchor(t):
 j=int(np.clip(np.searchsorted(keys[:,0],t,side='right')-1,0,len(keys)-2));a,b=keys[j:j+2];dt=b[0]-a[0];u=(t-a[0])/dt
 def slope(k):
  if k==0 or k==len(keys)-1:return np.zeros(8)
  v0=(keys[k,1:]-keys[k-1,1:])/(keys[k,0]-keys[k-1,0]);v1=(keys[k+1,1:]-keys[k,1:])/(keys[k+1,0]-keys[k,0])
  out=np.zeros(8);same=v0*v1>0;out[same]=2*v0[same]*v1[same]/(v0[same]+v1[same]);return out
 return (2*u**3-3*u*u+1)*a[1:]+(u**3-2*u*u+u)*dt*slope(j)+(-2*u**3+3*u*u)*b[1:]+(u**3-u*u)*dt*slope(j+1)
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
attack=new('Attack',1.5);previous={}
for t in np.linspace(0,1.5,91):
 reset();v=anchor(float(t));yaw,lean=v[6:]
 for n,amount in [('B_Spine',.25),('B_Spine1',.45),('B_Spine2',.30)]:
  rotate(n,(0,0,1),yaw*amount);rotate(n,(1,0,0),lean*amount)
 rotate('B_Neck',(0,0,1),-yaw*.55);rotate('B_Head',(1,0,0),-lean*.5)
 chest=(rig.pose.bones['B_Spine2'].matrix@rig.data.bones['B_Spine2'].matrix_local.inverted()).to_3x3().normalized()
 arm('L',v[:3],chest);arm('R',v[3:6],chest);write(attack,float(t),previous)
for a in [standing,walk,attack]:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
reset();scene['walk_stride_m']=stride
(P/'work/pilot_motion.json').write_text(json.dumps({'walk_stride_m':stride,'walk_duration':43/30,'attack_duration':1.5,'impact':.75,'attack_anchors':keys.tolist()},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots_v6.blend'))
out=P/'review/pilots_v6';out.mkdir(exist_ok=True);rows=[]
common.workbench_clay(scene);scene.display.shading.color_type='OBJECT';body.color=(.55,.56,.57,1)
for name in ['Walking','Attack']:
 a=bpy.data.actions[name];setact(a)
 for view in ['front','left','three_quarter']:
  row=[]
  for i in range(7):
   frame=a.frame_range[1]*i/6;scene.frame_set(math.floor(frame),subframe=frame%1)
   path=common.render_views(str(out/f'{name}_{view}_{i}'),1.2,2.85,views=(view,),resolution=(320,420))[0]
   row.append([path,f'{name} {view} {frame/30:.2f}s'])
  rows.append(row)
(out/'frames.json').write_text(json.dumps(rows))
print('PILOTS',stride,'m/cycle')
