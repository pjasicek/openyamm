"""Settle the rigid scabbard at its belt hinge and keep the held sword above the death floor."""
import bpy,math,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_complete.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
# Smooth the fitted fidget's short IK transitions in local quaternion space, preserving its duration/end poses.
a=bpy.data.actions['Fidget'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
frames=np.arange(0,float(a.frame_range[1])+.001,.25);names=[b.name for b in rig.pose.bones if b.name not in ['Sword','Scabbard']];samples={n:[] for n in names}
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1))
 for n in names:
  q=rig.pose.bones[n].rotation_quaternion.copy()
  if samples[n] and q.dot(samples[n][-1])<0:q=-q
  samples[n].append(q)
k=np.exp(-.5*(np.arange(-16,17)/4.4)**2);k/=k.sum()
for n in names:
 ar=np.array([tuple(q) for q in samples[n]]);sm=np.stack([np.convolve(np.pad(ar[:,i],16,mode='edge'),k,mode='valid') for i in range(4)],-1);sm/=np.linalg.norm(sm,axis=1)[:,None]
 for j,f in enumerate(frames):
  w=min(1,float(f)/3,float(frames[-1]-f)/3);b=rig.pose.bones[n];b.rotation_quaternion=samples[n][j].slerp(Quaternion(sm[j]),w);b.keyframe_insert('rotation_quaternion',frame=float(f))
# Retain the original pose samples before any contact keys are written.
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
frames=np.arange(0,109.001,.25);poses=[]
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1));poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
rig.animation_data.action=None

def apply(pose):
 for n,(q,l) in pose.items():b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l
 bpy.context.view_layer.update()
def coords(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[obj.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return co
angles={n:[] for n in ['Scabbard','Sword']};axes={n:[] for n in angles}
for pose in poses:
 apply(pose)
 for prop,bone,direction in [('Scabbard','Scabbard',-1),('Sword','B_R_Hand',1)]:
  matrix=rig.pose.bones[bone].matrix.copy();pivot=matrix.translation
  vector=rig.pose.bones[prop].matrix.to_3x3().col[1]*direction
  outward=rig.pose.bones['B_Pelvis'].matrix.to_3x3()@rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()@Vector((1,0,0))
  outward.z=0;outward.normalize()
  target=outward+Vector((0,0,.35)) if prop=='Scabbard' else Vector((0,0,1))
  axis=vector.cross(target)
  if axis.length<1e-5:axis=Vector((1,0,0))
  axis.normalize();points=coords(bpy.data.objects[prop+'Mesh'])
  def low(angle):
   R=Matrix.Rotation(angle,3,axis);return min((pivot+R@(v-pivot)).z for v in points)
  angle=0.
  if low(0)<.008:
   found=next((math.radians(d) for d in range(1,181) if low(math.radians(d))>=.008),None)
   if found is None:
    found=max((math.radians(d) for d in range(181)),key=low)
    print('HINGE support',prop,float(frames[len(angles[prop])]),'residual cm',round(low(found)*100,2))
   angle=found
  angles[prop].append(angle);axes[prop].append(axis)
# Anticipate contact by 50ms and soften the angle envelope; never reduce the required clearance.
for n,values in angles.items():
 ar=np.array(values);held=np.array([ar[max(0,i-6):i+7].max() for i in range(len(ar))]);k=np.exp(-.5*(np.arange(-10,11)/4)**2);k/=k.sum();angles[n]=np.maximum(ar,np.convolve(np.pad(held,10,mode='edge'),k,mode='valid'))
rows=[]
for i,pose in enumerate(poses):
 apply(pose)
 for prop,bone in [('Scabbard','Scabbard'),('Sword','B_R_Hand')]:
  b=rig.pose.bones[bone];m=b.matrix.copy();c=m.translation;R=Matrix.Rotation(float(angles[prop][i]),4,axes[prop][i]);b.matrix=Matrix.Translation(c)@R@Matrix.Translation(-c)@m;bpy.context.view_layer.update()
 rows.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['Scabbard','B_R_Hand']})
rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f,row in zip(frames,rows):
 for n,q in row.items():b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=float(f))
print('FLOOR HINGES maximum deg',{n:float(np.degrees(max(v))) for n,v in angles.items()})
# A small final neck roll clears the right cheekguard during the backward fall.
rows=[]
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1));q=rig.pose.bones['B_Neck'].rotation_quaternion.copy()@Quaternion(Vector((0,1,0)),math.radians(-5*math.exp(-.5*((f-84)/5)**2)));rows.append((f,q))
for f,q in rows:b=rig.pose.bones['B_Neck'];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=float(f))
# Hard equipment participates in the floor contact during the fall.
inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();floor_report={}
for name in ['Death','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[];lifts=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.25):
  sc.frame_set(int(f),subframe=float(f%1));objects=[body]+([bpy.data.objects[n] for n in ['SwordMesh','ScabbardMesh']] if name=='Death' else [])
  low=min(v.z for ob in objects for v in coords(ob));lift=.002-low;lifts.append(lift)
  rows.append((float(f),rig.pose.bones['B_Pelvis'].location.copy()+inv@Vector((0,0,lift))))
 for f,loc in rows:b=rig.pose.bones['B_Pelvis'];b.location=loc;b.keyframe_insert('location',frame=f)
 floor_report[name]={'max_lift_cm':max(lifts)*100,'min_lift_cm':min(lifts)*100}
print('FLOOR support',floor_report)
(P/'review/equipment_floor.json').write_text(json.dumps({'hinge_max_deg':{n:float(np.degrees(max(v))) for n,v in angles.items()},'root_adjustment':floor_report},indent=2))
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_settled.blend'))
