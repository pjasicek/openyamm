"""Align anatomical elbow hinges while preserving the independently draped sleeve matrices."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;source=json.loads((p/'work/source_rest.json').read_text())
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');supports={}
for sd in ['L','R']:
 for part in ['UpperArm','Forearm']:
  n=f'B_{sd}_{part}';name=f'ClothArm_{sd}_{part}';supports[n]=name;parent=r.data.edit_bones[n];eb=r.data.edit_bones.new(name);eb.head=parent.head;eb.tail=parent.tail;eb.roll=parent.roll;eb.parent=parent
bpy.ops.object.mode_set(mode='OBJECT')
for n,name in supports.items():
 group=b.vertex_groups.new(name=name);old=b.vertex_groups[n]
 for v in b.data.vertices:
  w=next((g.weight for g in v.groups if g.group==old.index),0)
  if w:group.add([v.index],w,'REPLACE');old.remove([v.index])
B=r.data.bones;cal={}
for sd in ['L','R']:
 U,F,H=[B[f'B_{sd}_{k}'] for k in ['UpperArm','Forearm','Hand']];su=Vector(source[U.name]['seg']).normalized();hinge=Matrix(source[U.name]['rot']).inverted()@su.cross(Vector((0,-1,0))).normalized();cal[sd]=(hinge,U.matrix_local.to_3x3().inverted()@F.matrix_local.to_3x3(),F.matrix_local.to_3x3().inverted()@(H.head_local-F.head_local).normalized())
affected=list(supports)+list(supports.values())+[f'B_{sd}_{part}' for sd in ['L','R'] for part in ['Hand','UpperArmTwist','ForearmTwist']]+['Cuff_L','Cuff_R']
report={}
for act in bpy.data.actions:
 r.animation_data.action=None
 for n in ['Cuff_L','Cuff_R']+list(supports.values()):r.pose.bones[n].rotation_quaternion=Quaternion()
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];cache=[]
 for f in np.arange(0,float(act.frame_range[1])+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));old={n:r.pose.bones[n].matrix.copy() for n in affected if n not in supports.values()};cache.append((float(f),old))
 rows=[];worst=0
 for f,old in cache:
  sc.frame_set(int(f),subframe=float(f%1))
  for sd in ['L','R']:
   un,fn,hn=[f'B_{sd}_{k}' for k in ['UpperArm','Forearm','Hand']];u=(old[fn].translation-old[un].translation).normalized();v=(old[hn].translation-old[fn].translation).normalized();wanted=u.cross(v).normalized();hinge,relative,restf=cal[sd];h=old[un].to_3x3()@hinge
   # Axial upper-arm roll aligns the hinge without changing shoulder, elbow or wrist locations.
   angle=math.atan2(u.dot(h.cross(wanted)),h.dot(wanted));ru=Quaternion(u,angle).to_matrix()@old[un].to_3x3();rf=ru@relative;rf=(rf@restf).rotation_difference(v).to_matrix()@rf
   for n,rot in [(un,ru),(fn,rf)]:
    m=rot.to_4x4();m.translation=old[n].translation;r.pose.bones[n].matrix=m;bpy.context.view_layer.update()
  # Loose cloth keeps its reviewed drape; hands retain the original world-space palm release.
  for n in list(supports.values())+[f'B_{sd}_{part}' for sd in ['L','R'] for part in ['Hand','UpperArmTwist','ForearmTwist']]+['Cuff_L','Cuff_R']:
   src=next((k for k,v in supports.items() if v==n),n);r.pose.bones[n].matrix=old[src];bpy.context.view_layer.update()
  rows.append((f,{n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in affected}))
 previous={}
 for f,pose in rows:
  for n,(q,l) in pose.items():
   if n in previous and q.dot(previous[n])<0:q.negate()
   previous[n]=q.copy();pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     if any('"'+n+'"' in fc.data_path for n in affected):
      for key in fc.keyframe_points:key.interpolation='LINEAR'
 error=0
 for f,old in cache:
  sc.frame_set(int(f),subframe=float(f%1))
  for n,m in old.items():
   target=supports.get(n,n);error=max(error,float(abs(np.array(r.pose.bones[target].matrix)-np.array(m)).max()))
 assert error<.0001,(act.name,error)
 report[act.name]={'samples_60hz':len(rows),'max_preserved_cloth_hand_matrix_error':error}
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'));(p/'work/review3_arm_frames.json').write_text(json.dumps(report,indent=2))
