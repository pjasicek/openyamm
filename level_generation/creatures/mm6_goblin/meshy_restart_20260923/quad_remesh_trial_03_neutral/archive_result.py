import bpy,json,shutil
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/quad_remesh_trial_03_neutral')
s=bpy.context.scene
candidates=[o for o in s.objects if o.type=='MESH' and o.name!='Goblin_QR_200K_Neutral' and len(o.data.polygons)>1000]
if len(candidates)!=1:raise RuntimeError('Expected exactly one completed retopology mesh')
result=candidates[0]
info={'name':result.name,'vertices':len(result.data.vertices),'polygons':len(result.data.polygons),'quads':sum(len(p.vertices)==4 for p in result.data.polygons),'triangles':sum(len(p.vertices)-2 for p in result.data.polygons),'uv_layers':len(result.data.uv_layers),'color_layers':[a.name for a in result.data.color_attributes]}
shutil.copy2('/tmp/Exoside/QuadRemesher/Blender/retopo.fbx',ROOT/'meshy_goblin_quad_remesher_raw.fbx')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'completed_trial.blend'),copy=True,compress=True)
# Export copies with density colors removed; preserve the raw result and dense source.
e=bpy.data.scenes.new('MM6 Goblin - Quad Remesh Neutral Export');bpy.context.window.scene=e
for source in [result]+[o for o in s.objects if o.type=='MESH' and 'Upper-back plate' in o.name]:
 obj=source.copy();obj.data=source.data.copy();e.collection.objects.link(obj)
 for color in list(obj.data.color_attributes):obj.data.color_attributes.remove(color)
 obj.hide_set(False);obj.hide_viewport=False;obj.hide_render=False;obj.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in e.objects if len(o.data.polygons)>1000)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'mm6_goblin_quad_trial_03.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False)
info['export_meshes']=len(e.objects);info['export_triangles']=sum(len(p.vertices)-2 for o in e.objects for p in o.data.polygons)
(ROOT/'result_report.json').write_text(json.dumps(info,indent=2)+'\n')
bpy.context.window.scene=s
print(json.dumps(info,indent=2))
