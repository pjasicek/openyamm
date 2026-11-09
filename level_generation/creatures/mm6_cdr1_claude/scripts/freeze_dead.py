import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_cdr1.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Death'];sc.frame_set(36);bpy.context.view_layer.update()
pose={b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones}
old=bpy.data.actions['Dead'];rig.animation_data.action=None;bpy.data.actions.remove(old);a=bpy.data.actions.new('Dead');a.use_fake_user=True;rig.animation_data.action=a
for f in [0,24]:
 for b in rig.pose.bones:
  b.location,b.rotation_quaternion,b.scale=pose[b.name]
  for key in ['location','rotation_quaternion','scale']:b.keyframe_insert(key,frame=f)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_cdr1.blend'))
bpy.ops.object.select_all(action='DESELECT')
for name in ['Rig','Body']:bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_cdr1_selected.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True,export_all_influences=False,export_attributes=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
