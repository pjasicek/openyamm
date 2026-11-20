import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v2new.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
for o in bpy.data.objects:o.select_set(o in [rig,body])
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'work/source_motion_reference.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_anim_slide_to_zero=True)
