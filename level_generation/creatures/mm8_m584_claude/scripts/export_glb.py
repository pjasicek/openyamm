import bpy,sys
from pathlib import Path
from mathutils import Matrix
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
sc=bpy.context.scene;rig=bpy.data.objects['Rig']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
# The deformation/contact gate runs at half frames; retain those samples in glTF.
for action in bpy.data.actions:
 end=action.frame_range[1]
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:
      key.co.x*=2;key.handle_left.x*=2;key.handle_right.x*=2
     curve.update()
 action.use_frame_range=True;action.frame_start=0;action.frame_end=end*2
sc.render.fps=60;sc.render.fps_base=1
bpy.context.view_layer.update()
for ob in bpy.data.objects:ob.select_set(ob.type in ('MESH','ARMATURE','EMPTY'))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,
 export_anim_slide_to_zero=True,export_optimize_animation_size=False)
