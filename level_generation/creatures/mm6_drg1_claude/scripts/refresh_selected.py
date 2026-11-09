"""Apply the selected texture revision to the selected reduced geometry, retaining the checked actions."""
import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_repaired.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
for material in bpy.data.materials:
 if not material.use_nodes:continue
 for node in material.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image:
   file=P/'textures'/Path(node.image.filepath).name
   if file.is_file():
    space=node.image.colorspace_settings.name;node.image=bpy.data.images.load(str(file),check_existing=False);node.image.colorspace_settings.name=space;node.image.pack()
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(0)
for ob in bpy.data.objects:ob.select_set(ob.name in ['Body','Rig'])
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_drg1.blend'))
file=P/'export/mm6_drg1_runtime_lod0.glb'
bpy.ops.export_scene.gltf(filepath=str(file),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
