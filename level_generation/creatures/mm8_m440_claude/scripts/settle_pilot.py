"""Keep the walk's original heavy ankle paths and blend the strike into the fitted ready pose."""
from pathlib import Path
import bpy,sys,math,json,numpy as np
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_grip.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
parts=np.array([a.value for a in body.data.attributes['piece'].data]);feet={s:np.flatnonzero(parts==n) for s,n in [('L',4),('R',5)]};rest=np.array([tuple(v.co) for v in body.data.vertices]);soles={s:ix[rest[ix,2]<rest[ix,2].min()+.005] for s,ix in feet.items()}
for side,ids in [('L',[19,24]),('R',[18,23])]:
 vi=np.flatnonzero(np.isin(parts,ids)).tolist()
 for group in body.vertex_groups:group.remove(vi)
 body.vertex_groups[f'B_{side}_ForearmTwist'].add(vi,1,'REPLACE')
def act(a):
 rig.animation_data.action=a
 if a is not None:rig.animation_data.action_slot=a.slots[0]
def snapshot(a,f):
 act(a);sc.frame_set(f);return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def restore(snap):
 act(None)
 for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def points():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return co
def ground():
 co=points();low=min(co[ix,2].min() for ix in feet.values());M=armik.W(rig,'B_Pelvis');M.translation.z+=.002-float(low);armik.set_world(rig,'B_Pelvis',M)
def write(a,frames):
 act(a);prev={}
 for f,snap in enumerate(frames):
  for n,m in snap.items():
   b=rig.pose.bones[n];q=m.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.location=m.translation;b.keyframe_insert('location',frame=f)
with bpy.data.libraries.load(str(p/'work/pilot_carried.blend'),link=False) as (src,dst):dst.actions=['Walking']
source=dst.actions[0];target=bpy.data.actions['Walking'];N=int(target.frame_range[1]);legs=[n for n in rig.pose.bones.keys() if any(x in n for x in ('Thigh','Calf','Foot','Toe'))]+['B_Pelvis'];frames=[];yaw={s:[] for s in 'LR'}
source_frames=[snapshot(source,f) for f in range(N+1)];target_frames=[snapshot(target,f) for f in range(N+1)]
for f in range(N+1):
 snap=target_frames[f].copy();snap.update({n:source_frames[f][n] for n in legs});restore(snap)
 for side in 'LR':rig.pose.bones[f'B_{side}_Toe0'].matrix_basis=Matrix()
 co=points()
 for side in 'LR':
  ids=soles[side];ys=rest[ids,1];h=co[ids[ys>=np.quantile(ys,.7)]].mean(0);t=co[ids[ys<=np.quantile(ys,.3)]].mean(0);d=t-h
  yaw[side].append(math.atan2(d[0],-d[1]))
 frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
offset={s:math.radians(8 if s=='L' else -8)-float(np.median(yaw[s])) for s in 'LR'}
for f,snap in enumerate(frames):
 restore(snap)
 for side in 'LR':
  F=armik.W(rig,f'B_{side}_Foot');armik.set_world(rig,f'B_{side}_Foot',armik.rot_world(F,Matrix.Rotation(offset[side],3,'Z')@F.to_3x3()))
 ground();frames[f]={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
frames[-1]=frames[0];write(target,frames);bpy.data.actions.remove(source)
standing=bpy.data.actions['Standing'];st=snapshot(standing,0);attack=bpy.data.actions['Attack'];N=int(attack.frame_range[1]);frames=[]
for f in range(N+1):
 snap=snapshot(attack,f);w=min(1,f/6,(N-f)/10);w=w*w*(3-2*w)
 if w<1:
  for n in snap:
   q0=st[n].to_quaternion();q=snap[n].to_quaternion()
   if q0.dot(q)<0:q=-q
   m=q0.slerp(q,w).to_matrix().to_4x4();m.translation=st[n].translation.lerp(snap[n].translation,w);snap[n]=m
 restore(snap);ground();frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
write(attack,frames);act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_grip.blend'))
print('SETTLED original walk ankle paths, rigid bracers, attack ready endpoints')
