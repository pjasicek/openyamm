"""Export the selected rebaked geometry with the unchanged fitted rig."""
import bpy,json,sys,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];row=json.loads((P/'review/round2/reduction/selection.json').read_text());maps=P/row['maps'];bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for ob in list(bpy.data.objects):
 if ob not in [body,rig]:bpy.data.objects.remove(ob,do_unlink=True)
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0);sc.render.fps=240
destination=P/'textures/rebaked';destination.mkdir(exist_ok=True)
for path in maps.glob('*.png'):shutil.copy2(path,destination/path.name)
ramps=json.loads((P/'textures/jak1_ramps.json').read_text())
for entry,tag in zip(ramps['materials'],['body','head']):entry['mask']=f'rebaked/{tag}_region_mask.png'
(P/'textures/jak1_ramps_runtime.json').write_text(json.dumps(ramps,indent=2))
for mat,tag in zip(body.data.materials,['body','head','staff']):
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image:
   name=Path(node.image.filepath).name
   if (destination/name).exists():node.image=bpy.data.images.load(str(destination/name),check_existing=False);node.image.colorspace_settings.name='sRGB' if 'basecolor'in name else'Non-Color'
for ob in bpy.context.scene.objects:ob.select_set(ob in [body,rig])
bpy.context.view_layer.objects.active=rig
# These normals were baked in OpenGL tangent space; no Meshy channel conversion applies.
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_jak1_runtime_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
info=json.loads((P/'export/export_info.json').read_text());info['triangles']=sum(len(f.vertices)-2 for f in body.data.polygons);info['reduction_step']=row['step'];info['normal_convention']='OpenGL rebake'
(P/'export/export_info.json').write_text(json.dumps(info,indent=2))
for im in bpy.data.images:
 if im.source=='FILE' and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_master.blend'))
print('REDUCED EXPORT',info,flush=True)
