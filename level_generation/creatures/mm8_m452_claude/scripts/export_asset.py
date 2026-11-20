"""Export the visually selected weighted reduction with all eight clips."""
import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
tag=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction.blend'))
rig=bpy.data.objects['Rat_Rig'];mesh=bpy.data.objects['Rat_'+tag]
for obj in list(bpy.data.objects):
    if obj not in (rig,mesh):bpy.data.objects.remove(obj,do_unlink=True)
mesh.name=mesh.data.name='Rat';mesh.hide_render=False
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
for obj in bpy.data.objects:obj.select_set(obj in (rig,mesh))
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rat_final.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m452_lod0.glb'),use_selection=True,
 export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',
 export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,
 export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,
 export_anim_slide_to_zero=True)
(P/'work/selected_reduction.json').write_text(json.dumps({'selected':tag,'triangles':sum(len(f.vertices)-2 for f in mesh.data.polygons)},indent=2)+'\n')
