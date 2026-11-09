from pathlib import Path
import bpy,json
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot.blend'))
rig=bpy.data.objects['NightmareRig'];o=bpy.data.objects['Nightmare'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for ob in bpy.data.objects:ob.select_set(ob in (o,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/nightmare_pilot.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True)
# Texture upload is the exact retained static surface, without the armature or actions.
o.parent=None
for m in list(o.modifiers):o.modifiers.remove(m)
for ob in bpy.data.objects:ob.select_set(ob==o)
bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.gltf(filepath=str(P/'work/texture_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
