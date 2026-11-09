import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_source.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.ops.object.select_all(action='DESELECT');copies=[]
for name in ['Body','Head']:
 o=bpy.data.objects[name];dup=o.copy();dup.data=o.data.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();bpy.context.scene.collection.objects.link(dup);copies.append(dup)
 dup.data.materials.clear();mat=bpy.data.materials.new('Neutral'+name);mat.diffuse_color=(.5,.5,.5,1);dup.data.materials.append(mat)
for o in copies:o.select_set(True)
bpy.context.view_layer.objects.active=copies[0]
path=P/'texturing/whole_creature_upload.glb'
bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='EXPORT')
request={'model_url':'@file:texturing/whole_creature_upload.glb','multiview_image_urls':['@file:references_hd/'+x+'.png' for x in ['01_front','03_left','02_back','04_right']],'ai_model':'meshy-7','enable_original_uv':False,'enable_pbr':True,'texture_resolution':'4k','target_formats':['glb'],'alpha_thumbnail':True}
(P/'requests/body_texture_v2.json').write_text(json.dumps(request,indent=2)+'\n')
(P/'work/body_texture_revision.json').write_text(json.dumps({'reason':'V1 body-only (head-excluded) return is smooth and weakly detailed compared with HD stone references; retain its raw output, request full-silhouette guidance and 4K source detail. The independently detailed head set remains selected.','upload_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'runtime_body_resolution':'decide after close-range comparison; no automatic 4K runtime installation'},indent=2))
print('TEXTURE_REVISION_READY',str(path))
