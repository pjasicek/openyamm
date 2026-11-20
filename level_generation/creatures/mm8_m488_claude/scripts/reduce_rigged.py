"""Reduce the weighted master by surface; preserve the full face and finger topology."""
from pathlib import Path
import bpy,bmesh,sys,json,numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/cage.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
target={0:7800,1:800,2:450,3:220,4:220};parts=[];report={}
for piece,goal in target.items():
 ob=body.copy();ob.data=body.data.copy();bpy.context.collection.objects.link(ob)
 bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]!=piece],context='VERTS');bm.to_mesh(ob.data);bm.free()
 n=sum(len(f.vertices)-2 for f in ob.data.polygons);assert n>0
 protected=ob.vertex_groups.new(name='_protect');keys={g.index for g in ob.vertex_groups if g.name in ('B_Head','B_Neck') or 'Finger' in g.name or 'Hand' in g.name}
 if piece==0:
  for v in ob.data.vertices:
   if sum(g.weight for g in v.groups if g.group in keys)>.3:protected.add([v.index],1,'REPLACE')
 for o in bpy.data.objects:o.select_set(o==ob)
 bpy.context.view_layer.objects.active=ob
 if n>goal:
  mod=ob.modifiers.new('Weighted surface budget','DECIMATE');mod.ratio=goal/n;mod.vertex_group=protected.name;mod.invert_vertex_group=True
  bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
 ob.vertex_groups.remove(ob.vertex_groups['_protect'])
 for v in ob.data.vertices:
  keep=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-7],key=lambda x:x[1],reverse=True)[:4];total=sum(w for g,w in keep);assert total>0
  for g in list(v.groups):ob.vertex_groups[g.group].remove([v.index])
  for g,w in keep:ob.vertex_groups[g].add([v.index],w/total,'REPLACE')
 bm=bmesh.new();bm.from_mesh(ob.data)
 if piece==0:assert all(e.is_manifold for e in bm.edges),'Reduction opened the skin'
 bm.free();report[piece]={'before':n,'after':sum(len(f.vertices)-2 for f in ob.data.polygons)};parts.append(ob)
bpy.data.objects.remove(body,do_unlink=True)
for o in bpy.data.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=parts[0];body.name='Body'
for f in body.data.polygons:f.use_smooth=True
report['total']=sum(v['after'] for v in report.values());assert report['total']<11000
(p/'review/reduction.json').write_text(json.dumps(report,indent=2)+'\n');print('REDUCTION',report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/reduced.blend'))
common.workbench_clay(bpy.context.scene)
for action,frame in [('Standing',0),('Running',9),('Attack',30),('Fidget',36),('Death',45)]:
 act=bpy.data.actions[action];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(frame)
 common.render_views(str(p/'review/animation'/('reduced_'+action)),1.05,2.5,views=('front','back','three_quarter'),resolution=(768,768))
