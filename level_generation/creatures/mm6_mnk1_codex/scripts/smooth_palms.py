"""Resolve authored palm-return spikes before the final deformation gates; preserve event timing and limb paths."""
import bpy,math,json,numpy as np
from mathutils import Quaternion,Vector,Matrix
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def setworld(n,q):
 pb=r.pose.bones[n];m=q.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
for name in ['Attack']:
 act=bpy.data.actions[name];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];N=int(act.frame_range[1]);world={s:[] for s in 'LR'}
 for f in range(N+1):
  sc.frame_set(f)
  for s in 'LR':world[s].append(r.pose.bones[f'B_{s}_Hand'].matrix.to_quaternion().copy())
 for s in 'LR':
  values=world[s]
  for i in range(1,len(values)):
   if values[i].dot(values[i-1])<0:values[i].negate()
  if name=='Death':
   world[s]=[values[0].slerp(values[-1],smooth(f/24)) for f in range(N+1)]
  else:
   # Two five-key geodesic averages remove the abrupt return roll without retiming the strike.
   for _ in range(2):
    new=[values[0]]
    for i in range(1,N):
     center=values[i];total=np.zeros(4)
     for delta,weight in [(-2,1),(-1,2),(0,3),(1,2),(2,1)]:
      q=values[max(0,min(N,i+delta))].copy()
      if q.dot(center)<0:q.negate()
      total+=np.array(q)*weight
     new.append(Quaternion(total/np.linalg.norm(total)))
    values=new+[values[-1]]
   world[s]=values
 previous={}
 for f in range(N+1):
  sc.frame_set(f)
  for s in 'LR':
   n=f'B_{s}_Hand';setworld(n,world[s][f]);pb=r.pose.bones[n];q=pb.rotation_quaternion.copy()
   if n in previous and q.dot(previous[n])<0:q.negate()
   previous[n]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 # Recompute the forearm roll from the corrected palm path; the sleeve follows the same measured .6 share.
 for s in 'LR':
  fb=r.data.bones[f'B_{s}_Forearm'];hb=r.data.bones[f'B_{s}_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();angles=[]
  for f in range(N+1):
   sc.frame_set(f);rel=(r.pose.bones[fb.name].matrix.inverted()@r.pose.bones[hb.name].matrix).to_quaternion();q=rel@rest.inverted();a=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)
   if angles:a=angles[-1]+(a-angles[-1]+math.pi)%(2*math.pi)-math.pi
   angles.append(a)
  if name=='Attack':
   turns=round((angles[-1]-angles[0])/(2*math.pi));angles=[a-turns*2*math.pi*smooth(f/N) for f,a in enumerate(angles)]
  if name=='Death':
   # A swing/twist decomposition is ill-conditioned at a half-turn; average the unwrapped scalar roll.
   for _ in range(2):angles=[angles[0]]+[sum(angles[max(0,min(N,i+d))]*w for d,w in [(-2,1),(-1,2),(0,3),(1,2),(2,1)])/9 for i in range(1,N)]+[angles[-1]]
  prev=None;pb=r.pose.bones[f'B_{s}_ForearmTwist']
  for f,a in enumerate(angles):
   sc.frame_set(f);q=Quaternion(axis,a*.6)
   if prev and q.dot(prev)<0:q.negate()
   prev=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
