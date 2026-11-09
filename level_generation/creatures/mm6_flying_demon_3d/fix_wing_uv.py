"""Repair rim UVs independently of retained body maps, then prepare dark wing PBR."""
from pathlib import Path
import json, bpy
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/texturing_master.blend'))
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');report={}
for obj in scene.objects:
 if obj.get('material_role')!='wing': continue
 uv=obj.data.uv_layers.active.data
 rims=[f for f in obj.data.polygons if max(uv[i].uv.y for i in f.loop_indices)-min(uv[i].uv.y for i in f.loop_indices)>.3]
 # The mesh is already triangulated. Pair triangles into 26 small edge boxes.
 for i,face in enumerate(rims):
  pair=i//2;u=(.65 if 'Left' in obj.name else .825)+(pair%13)*.0116;v=.950+(pair//13)*.010
  corners=[(0,0),(1,0),(1,1)] if i%2==0 else [(0,0),(1,1),(0,1)]
  for li,(x,y) in zip(face.loop_indices,corners): uv[li].uv=(u+.0007+.0102*x,v+.0007+.0086*y)
 report[obj.name]={'rim_triangles_recharted':len(rims),'geometry_weights_bind_unchanged':True,'body_uvs_unchanged':True}
 assert len(rims)<=104
for o in scene.objects:
 for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
  if owner and owner.animation_data:
   owner.animation_data.action=None
   for t in owner.animation_data.nla_tracks: t.mute=t.name!='Flight'
scene.frame_set(6);bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get();clones=[]
for obj in list(scene.objects):
 if obj.get('material_role') not in ('wing','wing_strut'): continue
 data=bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph),preserve_all_data_layers=True,depsgraph=depsgraph)
 clone=bpy.data.objects.new('Upload_'+obj.name,data);scene.collection.objects.link(clone);clone.matrix_world=obj.matrix_world.copy();clones.append(clone)
for o in scene.objects: o.select_set(o in clones)
bpy.context.view_layer.objects.active=clones[0];bpy.ops.object.join();upload=bpy.context.object
mat=bpy.data.materials['Neutral_Texture_Upload'];upload.data.materials.clear();upload.data.materials.append(mat)
for face in upload.data.polygons: face.material_index=0
bpy.ops.export_scene.gltf(filepath=str(P/'work/wings_upload.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_skins=False)
bpy.data.objects.remove(upload,do_unlink=True);scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_uv_master.blend'),compress=True)
request={'model_url':'@file:work/wings_upload.glb','ai_model':'meshy-7','enable_original_uv':True,'enable_pbr':True,'texture_resolution':'4k','target_formats':['glb'],
 'text_style_prompt':'Two enormous dark bat wings of the original Might and Magic 6 flying devil. Thin dark charcoal-brown leathery translucent-looking opaque membranes, very dark almost black outside, desaturated grey-purple subtle mottling inside, dense branching fine veins, stretched wrinkled leather between long dark bony finger struts, scars and irregular weathering. The membranes are much darker than purple demon skin. Matte nonmetallic natural tissue, no pink skin, no bright flesh, no gold, no armour, no fabric, no eyes, no decoration. Preserve every membrane and finger shape and the original UVs.'}
(P/'requests/texture_wings.json').write_text(json.dumps(request,indent=2)+'\n')
(P/'work/wing_uv_repair.json').write_text(json.dumps(report,indent=2)+'\n')
print('Separate wing UV / texture handoff',report,flush=True)
