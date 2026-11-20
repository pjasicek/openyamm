import bpy,json
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01');s=bpy.data.scenes['Goblin - Upright Rig Review'];bpy.context.window.scene=s;arm=next(o for o in s.objects if o.type=='ARMATURE');mesh=next(o for o in s.objects if o.type=='MESH');a=bpy.data.actions['Goblin_Upright_restpose'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0]
for f in [0,1,2]:
 s.frame_set(f)
 for pb in arm.pose.bones:
  pb.location=(0,0,0);pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
  for channel in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=channel,frame=f,group=pb.name)
for layer in a.layers:
 for strip in layer.strips:
  bag=strip.channelbag(a.slots[0])
  if bag:
   for fc in bag.fcurves:
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
a=bpy.data.actions['Goblin_Upright_Walking'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_start=1;s.frame_end=26;s.frame_set(7)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(OUT/'mm6_goblin_10577_rig_upright_v2.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=False,export_force_sampling=True,export_tangents=True)
bpy.data.libraries.write(str(OUT/'mm6_goblin_rig_upright_v2.blend'),{s},fake_user=True,compress=True);print('Explicit rest transforms saved; five clips exported.')
