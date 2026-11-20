import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'rig_pilots_v2.blend'))
body=bpy.data.objects['Lizardman_Body'];rig=bpy.data.objects['Lizardman_Rig']
rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=True
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
obj=body.copy();obj.data=body.data.copy();bpy.context.collection.objects.link(obj)
world=body.matrix_world.copy();obj.parent=None;obj.matrix_world=world
for mod in list(obj.modifiers):obj.modifiers.remove(mod)
obj.name='Lizardman_Static_UV';obj.vertex_groups.clear()
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
path=ROOT/'body_for_texture_v1.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_yup=True)
request={'model_url':'@file:3d_20261006/body_for_texture_v1.glb','ai_model':'meshy-7','enable_original_uv':True,'enable_pbr':True,'texture_resolution':'2k','multiview_image_urls':['@file:3d_20261006/references/'+n+'.png' for n in ('front_v1','back_v1','left_v1','right_v1')],'target_formats':['glb']}
(ROOT/'requests/body_texture_v1.json').write_text(json.dumps(request,indent=2))
obj.data.calc_loop_triangles();uv=obj.data.uv_layers.active.data
areas=[]
for tri in obj.data.loop_triangles:
    a,b,c=[uv[i].uv for i in tri.loops];areas.append(abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5)
assert min(areas)>1e-12,'Degenerate UV triangle'
(ROOT/'texture_upload.json').write_text(json.dumps({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'master':'rig_pilots_v2.blend','triangles':len(areas),'uv_layers':[u.name for u in obj.data.uv_layers],'zero_area_uv_triangles':sum(a<=1e-12 for a in areas),'uv_area':sum(areas),'height_m':1.7,'changes':'Static rest surface; same per-corner UVs. Removed skin and animation from upload only.'},indent=2))
print('Static UV upload and retexture request ready',flush=True)
