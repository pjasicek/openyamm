"""Retain source toe-off pitch through vertical; do not infer yaw from its vanishing ground projection."""
from pathlib import Path
import bpy,sys,math,numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
parts=np.array([a.value for a in body.data.attributes['piece'].data]);co=np.array([tuple(v.co) for v in body.data.vertices]);feet={s:np.flatnonzero(parts==k) for s,k in [('L',4),('R',5)]};soles={s:ix[co[ix,2]<co[ix,2].min()+.005] for s,ix in feet.items()}
def act(a):
 rig.animation_data.action=a
 if a is not None:rig.animation_data.action_slot=a.slots[0]
def points():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();x=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();return x
def axis(x,s):
 ix=soles[s];ys=co[ix,1];d=x[ix[ys<=np.quantile(ys,.3)]].mean(0)-x[ix[ys>=np.quantile(ys,.7)]].mean(0);return Vector(d).normalized()
restframe={}
for side in 'LR':
 f=axis(co,side);up=Vector((0,0,1));right=up.cross(f).normalized();up=f.cross(right).normalized();restframe[side]=Matrix((right,-f,up)).transposed()
with bpy.data.libraries.load(str(p/'work/full_runfit.blend'),link=False) as (a,b):b.actions=['Running']
source=b.actions[0];target=bpy.data.actions['Running'];N=int(target.frame_range[1]);source_data={s:[] for s in 'LR'}
for i in range(2*N+1):
 f=i/2;act(source);sc.frame_set(int(f),subframe=f-int(f));x=points()
 for side in 'LR':
  d=axis(x,side);yaw=math.radians(8 if side=='L' else -8);forward=Vector((math.sin(yaw),-math.cos(yaw),0));source_data[side].append([math.atan2(d.z,d.dot(forward)),armik.W(rig,f'B_{side}_Foot').translation.z])
for side in 'LR':
 data=np.array(source_data[side]);data[:,0]=np.unwrap(data[:,0]);source_data[side]=data
# Smooth the source pitch's support transition over 0.1 s; the foot's ground projection may reverse in flight.
pitches={}
for side in 'LR':
 raw=[]
 for i,(pitch,height) in enumerate(source_data[side][:-1]):
  rise=height-min(source_data[k][i,1] for k in 'LR');g=float(np.clip((.10-rise)/.06,0,1));g=g*g*(3-2*g)
  raw.append(float(np.clip(pitch,math.radians(-105),math.radians(35)))*(1-g))
 kernel=np.exp(-.5*(np.arange(-4,5)/1.6)**2);kernel/=kernel.sum();raw=np.array(raw);pad=np.r_[raw[-4:],raw,raw[:4]];v=np.convolve(pad,kernel,'valid');pitches[side]=np.r_[v,v[0]]
frames=[]
for i in range(2*N+1):
 f=i/2;act(target);sc.frame_set(int(f),subframe=f-int(f));snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};act(None)
 for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 for side in 'LR':
  pitch=pitches[side][i]
  yaw=math.radians(8 if side=='L' else -8);right=Vector((math.cos(yaw),math.sin(yaw),0));fw=Vector((math.sin(yaw)*math.cos(pitch),-math.cos(yaw)*math.cos(pitch),math.sin(pitch)));up=fw.cross(right).normalized();frame=Matrix((right,-fw,up)).transposed();R=frame@restframe[side].inverted()@rig.data.bones[f'B_{side}_Foot'].matrix_local.to_3x3();F=armik.W(rig,f'B_{side}_Foot');armik.set_world(rig,f'B_{side}_Foot',armik.rot_world(F,R))
 x=points();low=min(x[ix,2].min() for ix in feet.values());P=armik.W(rig,'B_Pelvis');P.translation.z+=.004-float(low);armik.set_world(rig,'B_Pelvis',P);frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
frames[-1]=frames[0];act(target);action_curves.remove_rotations(target,['B_L_Foot','B_R_Foot']);previous={}
for i,snap in enumerate(frames):
 for n in ['B_L_Foot','B_R_Foot','B_Pelvis']:
  b=rig.pose.bones[n];m=snap[n];q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i/2)
  if n=='B_Pelvis':b.location=m.translation;b.keyframe_insert('location',frame=i/2)
bpy.data.actions.remove(source);act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'))
