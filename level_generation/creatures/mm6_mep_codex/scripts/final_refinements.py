import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1]
RELEASE=4.5

def apply(r,b):
 smooth_attack(r)
 fit_running_stride(r)
 sc=bpy.context.scene;pv=np.array([v.value for v in b.data.attributes['piece'].data]);M=r.data.bones['Staff'].matrix_local;inv=M.inverted()
 # Preserve the visible staff, tightening only the concealed hand contact band.
 for v in b.data.vertices:
  if pv[v.index]!=100:continue
  x=inv@v.co;fade=min(1,max(0,(.14-abs(x.y))/.055));fac=1-fade*(1-.0109/.0125);x.x*=fac;x.z*=fac;v.co=M@x
 for a in bpy.data.actions:
  if not a.use_fake_user:continue
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
  for f in np.arange(0,float(a.frame_range[1])+.01,.5):
   sc.frame_set(int(f),subframe=f%1);row={}
   fade=max(0,1-f/10) if a.name=='Death' else 0 if a.name=='Dead' else 1
   for sd,degrees in [('L',-11.63773),('R',6.24394)]:
    pb=r.pose.bones[f'B_{sd}_Foot'];pos=pb.head.copy();q=Quaternion((0,0,1),math.radians(degrees)*fade)@pb.matrix.to_quaternion();mat=q.to_matrix().to_4x4();mat.translation=pos;pb.matrix=mat;bpy.context.view_layer.update();row[pb.name]=pb.rotation_quaternion.copy()
   rows.append((float(f),row))
  for f,row in rows:
   for name,q in row.items():pb=r.pose.bones[name];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 # Release the stick as the backward flinch begins, before its lower end can penetrate the floor.
 a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 sc.frame_set(int(RELEASE),subframe=RELEASE%1);start=r.pose.bones['Staff'].matrix.copy();sc.frame_set(int(a.frame_range[1]));end=r.pose.bones['Staff'].matrix.copy()
 grip=json.loads((P/'work/grip_pose.json').read_text())['finger_local'];rows=[]
 for f in np.arange(0,float(a.frame_range[1])+.01,.5):
  sc.frame_set(int(f),subframe=f%1);pb=r.pose.bones['Staff']
  if f>RELEASE:
   t=min(1,(f-RELEASE)/(26-RELEASE));u=t*t*(3-2*t);m=start.to_quaternion().slerp(end.to_quaternion(),u).to_matrix().to_4x4();m.translation=start.translation.lerp(end.translation,u);m.translation.z+=.08*4*t*(1-t);pb.matrix=m;bpy.context.view_layer.update()
  row={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy())}
  t=min(1,max(0,(f-RELEASE)/8));t=t*t*(3-2*t)
  for name,values in grip.items():
   if not name.startswith('B_R_Finger'):continue
   q=Quaternion(values).slerp(Quaternion(),t);row[name]=(q,None)
  rows.append((float(f),row))
 for f,row in rows:
  for name,(q,loc) in row.items():
   pb=r.pose.bones[name];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
   if loc is not None:pb.location=loc;pb.keyframe_insert('location',frame=f)

 ground_running(r,b)

def smooth_attack(r):
 # Filter the fitted library stroke in world space; local filtering loses the clavicle compensation.
 a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene
 local_names=[pb.name for pb in r.pose.bones if ('Forearm' in pb.name or 'Twist' in pb.name) and pb.name.startswith('B_')]
 world_names=[f'B_{s}_{n}' for s in 'LR' for n in ['UpperArm','Hand']];frames=np.arange(0,float(a.frame_range[1])+.01,1.);rows=[]
 for f in frames:
  sc.frame_set(int(f));rows.append({n:(r.pose.bones[n].matrix.to_quaternion().copy() if n in world_names else r.pose.bones[n].rotation_quaternion.copy()) for n in local_names+world_names})
 output=[]
 for j,f in enumerate(frames):
  sc.frame_set(int(f));filtered={}
  for n in local_names+world_names:
   anchor=rows[j][n];v=np.zeros(4)
   for off,w in [(-2,1),(-1,4),(0,6),(1,4),(2,1)]:
    q=rows[min(len(rows)-1,max(0,j+off))][n];v+=np.array(q)*w*(1 if anchor.dot(q)>=0 else -1)
   q=Quaternion(v.tolist());q.normalize();filtered[n]=q
  for side in 'LR':
   for n in [f'B_{side}_UpperArm',f'B_{side}_Forearm',f'B_{side}_Hand']:
    pb=r.pose.bones[n]
    if n in world_names:
     m=filtered[n].to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m
    else:pb.rotation_quaternion=filtered[n]
    bpy.context.view_layer.update()
  for n in local_names:
   if 'Twist' in n:r.pose.bones[n].rotation_quaternion=filtered[n]
  output.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in local_names+world_names})
 previous={}
 for f,row in zip(frames,output):
  for n,q in row.items():
   if n in previous and previous[n].dot(q)<0:q.negate()
   previous[n]=q.copy();pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))

 # Filtering must still return exactly to the native relaxed arm pose.
 end=float(frames[-1]);start=output[-1]
 for step in range(1,7):
  u=step/6;u=u*u*(3-2*u)
  for n,q in start.items():
   target=rows[0][n]
   if n in world_names:
    # Recover the original local idle value from the first sampled frame.
    sc.frame_set(0);target=r.pose.bones[n].rotation_quaternion.copy()
   value=q.slerp(target,u);pb=r.pose.bones[n];pb.rotation_quaternion=value;pb.keyframe_insert('rotation_quaternion',frame=end+step)
 a.frame_end=end+6

def fit_running_stride(r):
 # WorldFxSystem advances Running with 1.55 times the walking stride.
 import pose_helpers as ph
 ph.init(r);a=bpy.data.actions['Running'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;rows=[]
 sc.frame_set(0);first=r.pose.bones['B_L_Foot'].head.y;sc.frame_set(1);stride=(r.pose.bones['B_L_Foot'].head.y-first)*float(a.frame_range[1]);assert stride>0
 factor=(.34*1.55/.55)/stride
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);feet={s:(r.pose.bones[f'B_{s}_Foot'].head.copy(),r.pose.bones[f'B_{s}_Foot'].matrix.to_quaternion().copy()) for s in 'LR'}
  for side,(target,q) in feet.items():
   center=r.data.bones[f'B_{side}_Foot'].head_local.y;target.y=center+(target.y-center)*factor
   ph.chain(side,target,r.pose.bones[f'B_{side}_Thigh'].head+Vector((0,-1,0)),leg=True);ph.worldrot(f'B_{side}_Foot',q)
  rows.append({f'B_{s}_{n}':r.pose.bones[f'B_{s}_{n}'].rotation_quaternion.copy() for s in 'LR' for n in ['Thigh','Calf','Foot']})
 previous={}
 for f,row in enumerate(rows):
  for n,q in row.items():
   if n in previous and q.dot(previous[n])<0:q.negate()
   previous[n]=q.copy();pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)


def ground_running(r,b):
 # The longer runtime stride changes heel skinning by a few millimetres.
 a=bpy.data.actions['Running'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene
 pieces=np.array([v.value for v in b.data.attributes['piece'].data]);soles=np.flatnonzero(np.isin(pieces,[10,11]));assert len(soles)>10
 rows=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.25):
  sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(mesh.vertices[int(i)].co.z for i in soles);ev.to_mesh_clear()
  pb=r.pose.bones['B_Pelvis'];mat=pb.matrix.copy();mat.translation.z+=max(0,.001-low);pb.matrix=mat;bpy.context.view_layer.update();rows.append((float(f),pb.location.copy()))
 for f,loc in rows:
  pb=r.pose.bones['B_Pelvis'];pb.location=loc;pb.keyframe_insert('location',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
