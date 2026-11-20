"""Fit the light shell and existing shoulder helpers, preserving shared-body geometry and weights."""
from pathlib import Path
import bpy,numpy as np,json,sys,math
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_fitted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
# Narrow sternum/collarbone plate; open ankle articulation and gaps between spine segments.
for o in bpy.data.objects:
 if o.name=='Arm_chest':
  for v in o.data.vertices:v.co.x*=.55
 if o.name.startswith('Arm_knee_'):
  centre=sum(v.co.x for v in o.data.vertices)/len(o.data.vertices)
  for v in o.data.vertices:v.co.x=centre+(v.co.x-centre)*.82
 if o.name.startswith('Arm_shin_'):
  z0=min(v.co.z for v in o.data.vertices);z1=max(v.co.z for v in o.data.vertices)
  for v in o.data.vertices:v.co.z=.34+(v.co.z-z0)/(z1-z0)*(z1-.34)
 if o.name.startswith('Arm_spine_'):
  c=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
  for v in o.data.vertices:v.co.z=c.z+(v.co.z-c.z)*.85
 if o.name.startswith('Arm_forearm_'):
  side=o.name[-1];a=rig.data.bones[f'B_{side}_Forearm'].head_local;b=rig.data.bones[f'B_{side}_Hand'].head_local;axis=(b-a).normalized()
  for v in o.data.vertices:
   off=v.co-a;rad=off-axis*off.dot(axis)
   if rad.length>1e-6:v.co+=rad.normalized()*.012
 if o.name.startswith('Arm_pauldron_'):
  side=o.name[-1];d=Vector((1 if side=='L' else -1,0,0))
  for v in o.data.vertices:v.co+=d*.035
# No rest vertices or body weights change. Measure the expected torso influences separately.
GI={g.index:g.name for g in body.vertex_groups};bad=[]
for v in body.data.vertices:
 w=sum(g.weight for g in v.groups if ('UpperArm' in GI[g.group]) and abs(v.co.x)<.16 and v.co.z>1.1)
 if w>.05:bad.append((v.index,list(v.co),w))
(P/'review/torso_weights.json').write_text(json.dumps(bad,indent=2)+'\n')
# The native Demon's wide head needs less lateral roar tilt than the human mocap source.
standing=bpy.data.actions['Harrower_Standing'];rig.animation_data.action=standing;rig.animation_data.action_slot=standing.slots[0];sc.frame_set(0)
head_rest={n:rig.pose.bones[n].rotation_quaternion.copy() for n in ('B_Neck','B_Head')}
roar=bpy.data.actions['Harrower_Roar'];rig.animation_data.action=roar;rig.animation_data.action_slot=roar.slots[0];head_keys={}
for f in range(int(roar.frame_range[1])+1):
 sc.frame_set(f)
 for n,q in head_rest.items():head_keys[(f,n)]=q.slerp(rig.pose.bones[n].rotation_quaternion,.45)
for (f,n),q in head_keys.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
REST=lambda n:rig.data.bones[n].matrix_local.to_3x3()
for act in [a for a in bpy.data.actions if a.name.startswith('Harrower_') and not a.name.endswith('_Dead')]:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];frames=range(int(act.frame_range[1])+1);keys={}
 if act.name in ('Harrower_Standing','Harrower_Walking','Harrower_Running'):
  sc.frame_set(0)
  for pb in rig.pose.bones:
   for prop in ('rotation_quaternion','location','scale'):pb.keyframe_insert(prop,frame=frames[-1])
 for f in frames:
  sc.frame_set(f)
  for s in 'LR':
   ua=rig.pose.bones[f'B_{s}_UpperArm'];cl=rig.pose.bones[f'B_{s}_Clavicle'];name=f'B_{s}_Pauldron'
   q=(REST(cl.name).inverted()@REST(ua.name).col[1]).rotation_difference(cl.matrix.to_3x3().inverted()@ua.matrix.to_3x3().col[1])
   q=Quaternion(q.axis,q.angle*.8) if q.angle>1e-6 else Quaternion();Rb=REST(cl.name).inverted()@REST(name)
   keys[(f,s)]=(Rb.inverted()@q.to_matrix()@Rb).to_quaternion()
 for (f,s),q in keys.items():
  pb=rig.pose.bones[f'B_{s}_Pauldron'];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 # Small root correction covers subframe sole penetration without altering the fitted stride.
 samples=[]
 for f in np.arange(0,act.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();samples.append(max(0.,.0005-z))
 lifts={f:max(samples[max(0,2*f-1):min(len(samples),2*f+2)]) for f in frames}
 pose={}
 for f in frames:
  sc.frame_set(f);M=armik.W(rig,'B_Pelvis');M.translation.z+=lifts[f] if lifts[f]>.002 else 0;armik.set_world(rig,'B_Pelvis',M);pose[f]=rig.pose.bones['B_Pelvis'].location.copy()
 for f,p in pose.items():rig.pose.bones['B_Pelvis'].location=p;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
 print('FIT_SHELL',act.name,'root max',max(lifts.values()),flush=True)
# Dead is the final complete fall, including cloth, tail and shoulder helpers.
a=bpy.data.actions['Harrower_Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));pose={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
bpy.data.actions.remove(bpy.data.actions['Harrower_Dead']);a=bpy.data.actions.new('Harrower_Dead');a.use_fake_user=True;rig.animation_data.action=a
for f in (0,30):
 for n,m in pose.items():
  pb=rig.pose.bones[n];pb.matrix_basis=m
  for prop in ('rotation_quaternion','location','scale'):pb.keyframe_insert(prop,frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final.blend'))
