"""Let long cuffs slide back along the forearms before the palms turn out."""
import bpy,json,math
import numpy as np
from mathutils import Vector
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'review/round3/before/work/animation_finish.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
tags=[v.value for v in me.attributes['cuff'].data]
selected=set(i for f in me.polygons if tags[f.index] in (1,2) for i in f.vertices)
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for sd in ['L','R']:
 parent=r.data.edit_bones[f'B_{sd}_Forearm'];eb=r.data.edit_bones.new(f'Cuff_{sd}');eb.head=parent.head;eb.tail=parent.tail;eb.roll=parent.roll;eb.parent=parent;eb.use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
for sd in ['L','R']:
 gi=b.vertex_groups.new(name=f'Cuff_{sd}');fn=f'B_{sd}_Forearm';old=b.vertex_groups[fn];el=r.data.bones[fn].head_local;d=r.data.bones[f'B_{sd}_Hand'].head_local-el
 for i in selected:
  v=me.vertices[i];ws={g.group:g.weight for g in v.groups}
  if old.index not in ws:continue
  t=(v.co-el).dot(d)/d.length_squared;u=max(0,min(1,(t-.18)/.55));u=u*u*(3-2*u);w=ws[old.index]*u
  if w>0:old.add([i],ws[old.index]-w,'REPLACE');gi.add([i],w,'REPLACE')
for act in bpy.data.actions:
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];end=float(act.frame_range[1])
 for f in np.arange(0,end+.01,.5):
  u=0
  if act.name in ['Attack','Cast']:
   start=8 if act.name=='Attack' else 0
   x=max(0,min(1,(f-start)/3));y=max(0,min(1,(end-f)/3));u=x*x*(3-2*x)*y*y*(3-2*y)
  for sd in ['L','R']:
   pb=r.pose.bones[f'Cuff_{sd}'];el=r.data.bones[f'B_{sd}_Forearm'].head_local;d=(r.data.bones[f'B_{sd}_Hand'].head_local-el).normalized();pb.location=pb.bone.matrix_local.to_3x3().inverted()@(-d*.10*u);pb.keyframe_insert('location',frame=float(f))
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     if 'Cuff_' in fc.data_path:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
(p/'work/review3_sleeves.json').write_text(json.dumps({'bones':['Cuff_L','Cuff_R'],'retraction_m':.1,'ramp_frames':3,'rest_geometry_unchanged':True},indent=2))
