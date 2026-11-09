"""Rigid reptilian toes, grounded soles, and a tail that settles onto the floor during death."""
import bpy,numpy as np,json,math,sys,runpy
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_weighted_final.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
for side in 'LR':
 foot=body.vertex_groups['B_'+side+'_Foot'];toe=body.vertex_groups['B_'+side+'_Toe0']
 for v in body.data.vertices:
  w=sum(g.weight for g in v.groups if g.group==toe.index)
  if w:foot.add([v.index],w,'ADD');toe.remove([v.index])
 for act in [a for a in bpy.data.actions if a.use_fake_user]:
  rig.animation_data.action=act
  if len(act.slots):rig.animation_data.action_slot=act.slots[0]
  for f in range(int(act.frame_range[1])+1):
   pb=rig.pose.bones['B_'+side+'_Toe0'];pb.rotation_quaternion=Quaternion();pb.keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_toes.blend'))
sys.argv=['foot_level.py','--',str(p/'work/rig_toes.blend'),str(p/'work/rig_feet.blend'),'Standing','Walking:const','Attack','Hit','Fidget','Death:until=15']
runpy.run_path(str(p/'scripts/foot_level.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/fit_feet.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_feet_fitted.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;names=list(rig.pose.bones.keys())
taildata=json.load(open(p/'work/tail_fit.json'));tail=np.zeros(len(body.data.vertices),bool);tail[taildata['vertices']]=True
vnames={g.index:g.name for g in body.vertex_groups};feet=np.array([sum(g.weight for g in v.groups if 'Foot' in vnames[g.group])>.5 for v in body.data.vertices])
root_support=np.array([sum(g.weight for g in v.groups if vnames[g.group]=='B_Pelvis')>.05 for v in body.data.vertices])
rest=np.array([v.co[:] for v in body.data.vertices]);skin=np.array([v.value in (0,7) for v in body.data.attributes['piece'].data])
def setact(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def posed():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return co
# Sample the same linear interpolation exported to the game.
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
report={}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 poses=[];stats=[]
 for f in np.arange(0,float(act.frame_range[1])+.01,.25):
  setact(act);sc.frame_set(int(f),subframe=float(f%1));snap={n:rig.pose.bones[n].matrix_basis.copy() for n in names};setact(None)
  for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
  if act.name=='Death' and f>15:
   t=min(1,(f-15)/15);t=t*t*(3-2*t)
   direction=armik.W(rig,'B_Pelvis').translation-armik.W(rig,'B_Head').translation;direction.z=0;direction.normalize()
   for i in range(7):
    pb=rig.pose.bones['Tail'+str(i)];start=pb.head.copy();d=pb.tail-start;length=d.length
    flat=Quaternion((0,0,1),i*.045)@direction;flat.z=-.10 if i<3 else -.025;flat.normalize()
    desired=d.normalized().slerp(flat,t);q=d.rotation_difference(desired*length)
    M=(q.to_matrix()@pb.matrix.to_3x3()).to_4x4();M.translation=start;pb.matrix=M;bpy.context.view_layer.update()
  co=posed();support=skin&(~tail|root_support) if act.name=='Death' else feet
  delta=.002-float(co[support,2].min());M=armik.W(rig,'B_Pelvis');M.translation.z+=delta;armik.set_world(rig,'B_Pelvis',M)
  if float(posed()[tail,2].min())<.002:
   for i in range(7):
    pb=rig.pose.bones['Tail'+str(i)];start=pb.head.copy();end=pb.tail.copy();d=end-start;length=d.length
    floor=.04+.13*(1-i/7)
    if end.z<floor:
     dz=min(length*.99,floor-start.z);xy=Vector((d.x,d.y,0)).normalized()*math.sqrt(max(0,length*length-dz*dz));wanted=Vector((xy.x,xy.y,dz))
     q=d.rotation_difference(wanted);M=pb.matrix.copy();R=q.to_matrix()@M.to_3x3();M=R.to_4x4();M.translation=start;pb.matrix=M;bpy.context.view_layer.update()
  if float(posed()[tail,2].min())<.001:
   pb=rig.pose.bones['Tail0'];base=pb.matrix.copy();axis=(pb.tail-pb.head).cross(Vector((0,0,1))).normalized()
   def trial(angle):
    M=(Quaternion(axis,angle).to_matrix()@base.to_3x3()).to_4x4();M.translation=base.translation;pb.matrix=M
    return float(posed()[tail,2].min())
   lo,hi=0.,math.radians(55)
   if trial(hi)>=.001:
    for _ in range(14):
     mid=(lo+hi)/2
     if trial(mid)<.001:lo=mid
     else:hi=mid
    trial(hi)
   else:
    pb.matrix=base;bpy.context.view_layer.update()
  co=posed();stats.append({'body_min':float(co[skin&~tail,2].min()),'foot_min':float(co[feet,2].min()),'tail_min':float(co[tail,2].min())})
  poses.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names})
 setact(act)
 prev={}
 for index,pose in enumerate(poses):
  f=index/4
  for n,(q,l) in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 report[act.name]={'minimum_body_z':min(s['body_min'] for s in stats),'minimum_tail_z':min(s['tail_min'] for s in stats),'support_min_range':[min(s['foot_min'] for s in stats),max(s['foot_min'] for s in stats)]}
 print('FLOOR',act.name,report[act.name])
# A held corpse is a real clip, and the native attack2 uses the same overhead sword motion.
for src,dst in [('Attack','Attack2'),('Death','Dead')]:
 a=bpy.data.actions[src];setact(a);sc.frame_set(int(a.frame_range[1]) if dst=='Dead' else 0)
 if dst=='Attack2':n=a.copy();n.name=dst;n.use_fake_user=True
 else:
  pose={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
  n=bpy.data.actions.new(dst);n.use_fake_user=True;setact(n)
  for f in (0,4):
   for name,(q,l) in pose.items():
    pb=rig.pose.bones[name];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
    if name=='B_Pelvis':pb.keyframe_insert('location',frame=f)
  n.use_frame_range=True;n.frame_start=0;n.frame_end=4
setact(None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
json.dump(report,open(p/'work/floor_report.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_motion.blend'))
