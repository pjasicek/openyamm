"""Fit secondary loin-panel hinges around the unchanged source animation."""
from pathlib import Path
import bpy,json,math,numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v13.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=body.data;piece=[a.value for a in me.attributes['piece'].data]
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for part,name in [(14,'LoinBack'),(19,'LoinFront')]:
 ids=[v.index for v in me.vertices if piece[v.index]==part]
 for g in body.vertex_groups:g.remove(ids)
 body.vertex_groups[name].add(ids,1,'REPLACE')
 # Leave modest static clearance for the thick leather above moving legs.
 for i in ids:me.vertices[i].co.y += .012 if part==14 else -.008
me.update();faces=[tuple(f.vertices) for f in me.polygons if all(piece[i]==0 for i in f.vertices)]
report={};axes={name:(rig.data.bones[name].matrix_local.to_3x3().inverted()@Vector((1,0,0))).normalized() for name in ['LoinBack','LoinFront']}
for an in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 act=bpy.data.actions[an];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];frames=[]
 for f in range(int(act.frame_range[1])+1):
  sc.frame_set(f);frames.append({pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones})
 rig.animation_data.action=None;values={14:[],19:[]};worsts={14:0,19:0}
 for f,pose in enumerate(frames):
  for n,(q,l) in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
  bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();skin=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(skin,faces)
  for part,name,sign in [(14,'LoinBack',1),(19,'LoinFront',-1)]:
   fs=[fa for fa in me.polygons if piece[fa.vertices[0]]==part];pb=rig.pose.bones[name];probes=[]
   for angle in range(0,66,3):
    pb.rotation_quaternion=Quaternion(axes[name],math.radians(angle*sign));bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();depth=0
    for fa in fs:
     pts=[co[i] for i in fa.vertices]+[sum((co[i] for i in fa.vertices),Vector())/len(fa.vertices)]
     for v in pts:
      loc,n,fi,d=tree.find_nearest(v,.06)
      if loc is not None and (v-loc).dot(n)<-.707*d:depth=max(depth,d)
    probes.append((angle,depth))
    if depth<.002:break
   best=min(probes,key=lambda a:(a[1]>.002,a[0] if a[1]<.002 else a[1]));values[part].append(best[0]);worsts[part]=max(worsts[part],best[1])
 for part,name,sign in [(14,'LoinBack',1),(19,'LoinFront',-1)]:
  angles=values[part];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
  for f,angle in enumerate(angles):
   pb=rig.pose.bones[name];pb.rotation_quaternion=Quaternion(axes[name],math.radians(angle*sign));pb.keyframe_insert('rotation_quaternion',frame=f)
  rig.animation_data.action=None
 report[an]={'depth_m':worsts,'angles_deg':values};print('CLOTH_HINGE',an,worsts,{k:(min(v),max(v)) for k,v in values.items()},flush=True)
# Held corpse shares Death's final fitting.
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));pose={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones};a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in [0,30]:
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v14.blend'));(p/'revision_02/motion/cloth_fit.json').write_text(json.dumps(report,indent=2)+'\n')
