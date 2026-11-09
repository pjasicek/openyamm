import bpy,json
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');src=bpy.data.scenes['Goblin - Skirt Clearance v3'];oa=src.objects['Goblin_SkirtClearance_Rig'];om=src.objects['Goblin_SkirtClearance_10577'];s=bpy.data.scenes.new('Goblin - Sword and Native Attack');bpy.context.window.scene=s
for attr in ['engine','resolution_x','resolution_y','resolution_percentage']:setattr(s.render,attr,getattr(src.render,attr))
s.render.fps=24;s.render.image_settings.file_format='PNG';s.cycles.samples=16;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=src.world;s.view_settings.view_transform='AgX'
r=oa.copy();r.data=oa.data.copy();r.name='Goblin_Combat_Rig';s.collection.objects.link(r);r.animation_data_clear();r.animation_data_create()
m=om.copy();m.data=om.data.copy();m.name='Goblin_Combat_Body';s.collection.objects.link(m);mw=om.matrix_world.copy();m.parent=r;m.matrix_world=mw
for mod in m.modifiers:
 if mod.type=='ARMATURE':mod.object=r
for o in src.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp
for p in r.pose.bones:p.matrix_basis.identity()
s.frame_set(0);bpy.context.view_layer.update()
report={'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':list(map(list,b.matrix_local))} for b in r.data.bones},'matrix_world':list(map(list,m.matrix_world)),'vertices':[list(m.matrix_world@v.co) for v in m.data.vertices],'faces':[list(p.vertices) for p in m.data.polygons],'weights':[[[m.vertex_groups[g.group].name,g.weight] for g in v.groups] for v in m.data.vertices]};(OUT/'source_geometry.json').write_text(json.dumps(report))
print('Prepared separate combat scene and source geometry audit')
