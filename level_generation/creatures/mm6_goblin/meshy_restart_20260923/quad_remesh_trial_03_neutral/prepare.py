import bpy,json,sys
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/quad_remesh_trial_03_neutral')
p=sys.modules['quad_remesher_1_4.qr_operators'].QREMESHER_OT_remesh.progressData.RemeshingProcess
assert p is None or p.poll() is not None
assert 'MM6 Goblin - Quad Remesh Neutral' not in bpy.data.scenes
previous=bpy.data.scenes['MM6 Goblin - Quad Remesh 200K']
s=bpy.data.scenes.new('MM6 Goblin - Quad Remesh Neutral');bpy.context.window.scene=s
sources=[previous.objects['Goblin_QR_200K_DensityGuided']]+[o for o in previous.objects if o.type=='MESH' and 'Upper-back plate' in o.name]
for source in sources:
 o=source.copy();o.data=source.data.copy();s.collection.objects.link(o)
 o.hide_viewport=False;o.hide_render=False;o.hide_set(False);o.select_set(False)
 for attr in list(o.data.color_attributes):o.data.color_attributes.remove(attr)
 if len(o.data.polygons)>1000:
  body=o;body.name='Goblin_QR_200K_Neutral'
body.select_set(True);bpy.context.view_layer.objects.active=body
settings=json.loads((ROOT.parent/'quad_remesh_trial_02_200k/prepared_settings.json').read_text())['settings']
settings['use_vertex_color']=False
for k,v in settings.items():setattr(s.qremesher,k,v)
report={'scene':s.name,'selected_source':body.name,'source_triangles':len(body.data.polygons),'settings':settings,'operation':'Prepared only; user clicks Remesh It.','reason':'Controlled comparison: same reviewed 198K body and 9000 target, with excessive painted density guidance disabled.','acceptance':'Inspect shape preservation and allocation before rigging or texturing. Manual topology work remains possible.'}
(ROOT/'prepared_settings.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'prepared_trial.blend'),copy=True,compress=True)
print(json.dumps(report))
