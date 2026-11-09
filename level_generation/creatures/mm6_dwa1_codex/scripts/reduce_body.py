"""Reduce flat armour after final weighting. Keep helmet, gauntlet fingers and silhouette fittings intact."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fixed.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='LOOSE');bpy.ops.object.mode_set(mode='OBJECT')
parts=[o for o in bpy.data.objects if o.type=='MESH'];report=[]
for ob in parts:
 p=ob.data.attributes['piece'].data[0].value;n=sum(len(f.vertices)-2 for f in ob.data.polygons)
 ratio={1:.70,2:.75,5:.60,6:.55,7:.55,8:.80,9:.90,10:.90}.get(p,.60 if p>=14 else 1)
 bpy.context.view_layer.objects.active=ob
 if ratio<1:
  md=ob.modifiers.new('Final density','DECIMATE');md.ratio=ratio;md.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=md.name)
 report.append({'piece':p,'before':n,'after':sum(len(f.vertices)-2 for f in ob.data.polygons)})
for o in bpy.data.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Body'
# Quantise collapsed-vertex interpolation to the engine's exact four influences.
for v in body.data.vertices:
 w=sorted([(g.group,g.weight) for g in v.groups],key=lambda e:-e[1])[:4];total=sum(x for _,x in w)
 for g in v.groups[:]:body.vertex_groups[g.group].remove([v.index])
 for i,x in w:body.vertex_groups[i].add([v.index],x/total,'REPLACE')
(P/'work/reduction.json').write_text(json.dumps(report,indent=2));print('REDUCED',sum(r['before'] for r in report),sum(r['after'] for r in report))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_body.blend'))
