"""Pin the belt and give the skirt two outward drape controls; bake to ordinary skin joints."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v8.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
pv=np.array([a.value for a in body.data.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];cloth=[v for v in body.data.vertices if pv[v.index]==1]
weights={v.index:[(names[g.group],g.weight) for g in v.groups] for v in cloth};used=sorted({n for w in weights.values() for n,v in w if v>.001});originals=list(r.pose.bones.keys());directions={'F':Vector((0,-1,0)),'B':Vector((0,1,0)),'L':Vector((1,0,0)),'R':Vector((-1,0,0))}
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for n in used:
 for sd in directions:
  eb=r.data.edit_bones.new('Skirt_'+sd+'_'+n);eb.matrix=r.data.edit_bones[n].matrix.copy();eb.length=.05;eb.parent=r.data.edit_bones[n]
eb=r.data.edit_bones.new('Socket_Axe_Head');eb.head=(0,0,1.14);eb.tail=(0,0,1.19);eb.parent=r.data.edit_bones['Axe'];eb.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
for pb in r.pose.bones:pb.rotation_mode='QUATERNION'
for n in used:
 for sd in directions:body.vertex_groups.new(name='Skirt_'+sd+'_'+n)
for v in cloth:
 t=min(1,max(0,(1.015-v.co.z)/.13));x,y=v.co.x,v.co.y-.09;xx=abs(x)/(abs(x)+abs(y)+1e-8);shares={'L' if x>0 else 'R':xx,'B' if y>0 else 'F':1-xx}
 for n,w in weights[v.index]:
  if n in used:
   body.vertex_groups[n].add([v.index],w*(1-t),'REPLACE')
   for sd,share in shares.items():body.vertex_groups['Skirt_'+sd+'_'+n].add([v.index],w*t*share,'REPLACE')
# Match the runtime's four-influence skinning before the last gate.
for v in body.data.vertices:
 groups=sorted([(g.group,g.weight) for g in v.groups],key=lambda g:-g[1]);keep=groups[:4];total=sum(w for _,w in keep)
 for i,w in groups:body.vertex_groups[i].remove([v.index])
 for i,w in keep:body.vertex_groups[i].add([v.index],w/total,'REPLACE')
for act in list(bpy.data.actions):
 if act.name not in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']:continue
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
 for f in range(int(act.frame_range[1])+1):
  sc.frame_set(f);ch=r.pose.bones['B_Pelvis'].matrix.to_3x3()@r.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();u=min(1,max(0,(f-5)/15));u=u*u*(3-2*u);d=.12*u if act.name=='Death' else (.05 if act.name in ['Walking','Running'] else .015)
  for n in used:
   for sd in directions:
    pb=r.pose.bones['Skirt_'+sd+'_'+n];pb.location=r.data.bones[n].matrix_local.to_3x3().inverted()@(directions[sd]*d);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
# Dead holds the physical terminal pose, including the dropped axe and draped skirt.
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));held={p.name:(p.rotation_quaternion.copy(),p.location.copy()) for p in r.pose.bones};a=bpy.data.actions.new('Dead');a.use_fake_user=True;r.animation_data.action=a
for f in [0,30]:
 for pb in r.pose.bones:
  pb.rotation_mode='QUATERNION';pb.rotation_quaternion,pb.location=held[pb.name];pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=30
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
print('FINAL RIG',len(r.data.bones),'bones',len(body.data.polygons),'body triangles');assert len(r.data.bones)<=128
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/gated_master.blend'))
