import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig.blend'))
body=bpy.data.objects['Body']
body.modifiers.clear();body.parent=None
for o in list(bpy.data.objects):
 if o!=body:bpy.data.objects.remove(o,do_unlink=True)
body.vertex_groups.clear();body.select_set(True);bpy.context.view_layer.objects.active=body
uv=body.data.uv_layers.active.data
areas=[]
for f in body.data.polygons:
 a,b,c=[uv[i].uv for i in f.loop_indices]
 areas.append(abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5)
assert min(areas)>1e-10
assert all(0<=v.uv.x<=1 and 0<=v.uv.y<=1 for v in uv)
bpy.ops.export_scene.gltf(filepath=str(P/'work/boulder_texture_upload_v2.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
request={'model_url':'@file:work/boulder_texture_upload_v2.glb','multiview_image_urls':['@file:references_hd/'+n+'.png' for n in ['01_front','03_left','02_back','04_right']],'ai_model':'meshy-7','enable_original_uv':True,'enable_pbr':True,'texture_resolution':'2k','target_formats':['glb']}
(P/'requests/texture_v2.json').write_text(json.dumps(request,indent=2)+'\n')
(P/'work/uv_check.json').write_text(json.dumps({'triangles':len(areas),'min_uv_area':min(areas),'total_uv_area':sum(areas),'island_margin':.006,'unique_smart_project':True},indent=2)+'\n')
