import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
roles=['Standing','Walking','Running','Attack','Hit','Fidget','Death']
def setact(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[o.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return co
setact(bpy.data.actions['Standing']);scene.frame_set(0);idle={n:rig.pose.bones[n].rotation_quaternion.copy() for n in rig.pose.bones.keys()}
# Carrying the broad axe and kite shield requires a restrained battle cry rather than a rearward weapon sweep.
act=bpy.data.actions['Fidget'];setact(act);poses=[]
ns=['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_UpperArm','B_L_Forearm','B_L_Hand']
for f in range(int(act.frame_range[1])+1):
 scene.frame_set(f);poses.append({n:idle[n].slerp(rig.pose.bones[n].rotation_quaternion,.35) for n in ns})
for f,pose in enumerate(poses):
 for n,q in pose.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
# Keep the carrying arm in its guard until the shield is released; then blend to the falling source arm.
act=bpy.data.actions['Death'];setact(act);ns=['B_L_UpperArm','B_L_Forearm','B_L_Hand'];poses=[]
for f in range(int(act.frame_range[1])+1):
 scene.frame_set(f);t=max(0,min(1,(f-26)/12));t=t*t*(3-2*t);poses.append({n:idle[n].slerp(rig.pose.bones[n].rotation_quaternion,t) for n in ns})
for f,pose in enumerate(poses):
 for n,q in pose.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
# Recompute twist channels after the equipment-carry correction.
def twist(q,axis):return (2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
for name in roles:
 act=bpy.data.actions[name];setact(act)
 for f in range(int(act.frame_range[1])+1):
  scene.frame_set(f)
  for s in ['L','R']:
   fb,hb,ub=[rig.data.bones[f'B_{s}_{n}'] for n in ['Forearm','Hand','UpperArm']]
   axis=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();pb=rig.pose.bones[f'B_{s}_ForearmTwist'];pb.rotation_quaternion=Quaternion(axis,.6*twist(rel@rest.inverted(),axis));pb.keyframe_insert('rotation_quaternion',frame=f)
   axis=(ub.matrix_local.inverted()@fb.head_local).normalized();pb=rig.pose.bones[f'B_{s}_UpperArmTwist'];pb.rotation_quaternion=Quaternion(axis,-.5*twist(rig.pose.bones[ub.name].rotation_quaternion,axis));pb.keyframe_insert('rotation_quaternion',frame=f)
# Root height derives from the final steel boot/body surface, not the source mannequin's ankle height.
floors={}
for name in roles:
 act=bpy.data.actions[name];setact(act);keys=[]
 for f in np.arange(0,float(act.frame_range[1])+.001,.25):
  scene.frame_set(int(f),subframe=float(f%1));low=min(v.z for v in coords(body));pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z+=max(0,.012-low);keys.append((float(f),M))
 for f,M in keys:
  scene.frame_set(int(f),subframe=f%1);pb=rig.pose.bones['B_Pelvis'];pb.matrix=M;pb.keyframe_insert('location',frame=f)
 floors[name]=len(keys)
# Release both heavy props during the fall; land beside the supine body and preserve this in the corpse hold.
death=bpy.data.actions['Death'];setact(death);end=int(death.frame_range[1]);release=26;settle=48
for prop,side,offset in [('Axe','R',-.55),('Shield','L',.55)]:
 pb=rig.pose.bones[prop];ob=bpy.data.objects[prop];rest=rig.data.bones[prop].matrix_local;parent=rig.data.bones[f'B_{side}_Hand'].matrix_local
 scene.frame_set(release);start=pb.matrix.copy();scene.frame_set(end);pel=rig.pose.bones['B_Pelvis'].head.copy();dest=Vector((start.translation.x+offset,start.translation.y-.35,.06));finalq=Quaternion((1,0,0),math.pi/2) if prop=='Shield' else Quaternion((0,0,1),.3)
 # Retain the rest prop's shape, choose a flat landing by its actual local bounds.
 local=[rest.inverted()@v.co for v in ob.data.vertices]
 # Fit the actual prop plane, so the dropped axe and shield lie flat rather than balancing on an edge.
 pts=np.array([tuple(v) for v in local]);axes=np.linalg.svd(pts-pts.mean(0))[2];long=Vector(axes[0]);normal=Vector(axes[2])
 if long.y<0:long=-long
 planeSide=long.cross(normal).normalized();normal=planeSide.cross(long).normalized();worldlong=Vector((.6,.8,0) if prop=='Axe' else (.15,.99,0)).normalized();worldnormal=Vector((0,0,1));worldside=worldlong.cross(worldnormal)
 localframe=Matrix((planeSide,long,normal)).transposed();worldframe=Matrix((worldside,worldlong,worldnormal)).transposed();finalq=(worldframe@localframe.inverted()).to_quaternion()
 for f in range(end+1):
  scene.frame_set(f)
  if f<release:M=rig.pose.bones[f'B_{side}_Hand'].matrix@parent.inverted()@rest
  else:
   t=min(1,(f-release)/(settle-release));s=t*t*(3-2*t);pos=start.translation.lerp(dest,s);pos.z+=.22*math.sin(math.pi*t);q=start.to_quaternion().slerp(finalq,s);M=Matrix.Translation(pos)@q.to_matrix().to_4x4();low=min((M@v).z for v in local)
   if low<.008:M.translation.z+=.008-low
  pb.matrix=M;pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
setact(death);scene.frame_set(end);held={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones};dead=bpy.data.actions.new('Dead');dead.use_fake_user=True;setact(dead)
for f in [0,30]:
 for n,(q,l) in held.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
dead.use_frame_range=True;dead.frame_start=0;dead.frame_end=30
for act in list(bpy.data.actions):
 if act.name not in roles+['Dead']:bpy.data.actions.remove(act);continue
 curves={}
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
     if fc.data_path.endswith('rotation_quaternion'):curves.setdefault(fc.data_path,{})[fc.array_index]=fc
 for cs in curves.values():
  if len(cs)!=4:continue
  keys=[cs[i].keyframe_points for i in range(4)];prev=None
  for j in range(min(map(len,keys))):
   q=[keys[i][j].co.y for i in range(4)]
   if prev and sum(a*b for a,b in zip(q,prev))<0:
    for i in range(4):keys[i][j].co.y*=-1
    q=[-x for x in q]
   prev=q
setact(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_motion.blend'));print('FLOOR_KEYS',floors)
