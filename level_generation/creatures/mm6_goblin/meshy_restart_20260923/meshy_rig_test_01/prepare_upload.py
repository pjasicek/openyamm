import bpy,numpy as np,json,traceback
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'meshy_rig_test_01'
with bpy.data.libraries.load(str(ROOT/'detail_rebuild_01/goblin_simplified_10577.blend'),link=False) as (a,b):b.scenes=[a.scenes[0]]
s=b.scenes[0];s.name='Goblin - Meshy Upload Preserved Detail';bpy.context.window.scene=s
meshes=[o for o in s.objects if o.type=='MESH'];atlas=np.empty((4096,4096,4),dtype=np.float32);atlas[:]=(.5,.5,1,1);placed={}
for o in meshes:
 o.data=o.data.copy();uv=o.data.uv_layers.active;uv.name='MeshyUV'
 for p in o.data.polygons:
  m=o.data.materials[p.material_index];textures=[n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m and m.use_nodes else []
  if textures:
   img=textures[0];tile=(1,0) if 'Skirt' in img.name else (0,0)
   if tile not in placed:
    data=np.empty(2048*2048*4,dtype=np.float32);img.pixels.foreach_get(data);x,y=tile;atlas[y*2048:(y+1)*2048,x*2048:(x+1)*2048,:]=data.reshape((2048,2048,4));placed[tile]=img.name
  else:tile=(0,1)
  for i in p.loop_indices:uv.data[i].uv=uv.data[i].uv*.5+__import__('mathutils').Vector((tile[0]*.5,tile[1]*.5))
img=bpy.data.images.new('MM6_Goblin_Meshy_PreservedNormal_4096',width=4096,height=4096,alpha=False);img.colorspace_settings.name='Non-Color';img.pixels.foreach_set(atlas.ravel());img.update();img.file_format='PNG';img.filepath_raw=str(OUT/'normal_4096.png');img.save();img.pack()
mat=bpy.data.materials.new('MM6_Goblin_Meshy_SingleMaterial');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.34,.36,1);bs.inputs['Roughness'].default_value=.7;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');nm.uv_map='MeshyUV';mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
 o.hide_set(False);o.select_set(True);o.data.materials.clear();o.data.materials.append(mat)
 for p in o.data.polygons:p.material_index=0
bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join();o=bpy.context.object;o.name='MM6_Goblin_Meshy_RigTest'
assert sum(len(p.vertices)-2 for p in o.data.polygons)==10577
s.camera.location=(0,-4,0);s.camera.rotation_euler=(-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=2.15

def run():
 try:
  bpy.context.window.scene=s
  bpy.ops.export_scene.gltf(filepath=str(OUT/'mm6_goblin_10577_meshy_upload.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_tangents=True)
  bpy.data.libraries.write(str(OUT/'meshy_upload.blend'),{s},fake_user=True,compress=True)
  (OUT/'report.json').write_text(json.dumps({'triangles':10577,'objects':1,'materials':1,'uv_layers':1,'normal_atlas':4096,'operation':'Original 2K normal maps placed without resampling in a shared 4K atlas; affine UV remap; meshes joined without welding.','geometry_changed':False,'supersedes':'The initial re-baked 2K upload study was replaced to avoid extra projection/resampling defects.'},indent=2))
  s.render.filepath=str(OUT/'upload_front.png');bpy.ops.render.render(write_still=True);(OUT/'exact_atlas_done.txt').write_text('complete')
 except Exception:(OUT/'exact_atlas_error.txt').write_text(traceback.format_exc())
 return None
bpy.app.timers.register(run,first_interval=.1);print('Packing original normal pixels into one atlas with unchanged geometry.')
