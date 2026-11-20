"""Promote the three selected library clips; retain the approved rig, appearance and other actions."""
from pathlib import Path
import bpy, json, shutil
p=Path(__file__).resolve().parents[1];out=p/'revision_03';old=out/'previous';old.mkdir(exist_ok=True)
source=p/'export/mm6_ogr.blend'
if not (old/'mm6_ogr.blend').exists():shutil.copy2(source,old/source.name)
bpy.ops.wm.open_mainfile(filepath=str(old/'mm6_ogr.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Ogre'];sc=bpy.context.scene
assert sc.render.fps==30 and sc.render.fps_base==1
selected={'Running_Weighted':'Running','Attack_Downward':'Attack','Fidget_NeckStretch':'Fidget'}
for name in selected.values():bpy.data.actions.remove(bpy.data.actions[name])
with bpy.data.libraries.load(str(p/'review/motion_options/ogre_motion_options.blend'),link=False) as (src,dst):
 dst.actions=list(selected)
for a in dst.actions:a.name=selected[a.name];a.use_fake_user=True
# The source run differs by at most 0.51 degrees at its seam; close only its last three frames.
a=bpy.data.actions['Running'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
sc.frame_set(0);first={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
sc.frame_set(25);last={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
for f in range(23,26):
 sc.frame_set(f);w=(f-22)/3
 for b in rig.pose.bones:
  q0,l0=first[b.name];q1,l1=last[b.name]
  correction=q1.rotation_difference(q0)
  b.rotation_quaternion=b.rotation_quaternion @ correction.__class__().slerp(correction,w)
  b.location+=(l0-l1)*w
  b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
sc.frame_set(0)
for b in rig.pose.bones:b.scale=(1,1,1)
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'selected_motion.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'selected_motion.glb'),use_selection=True,export_format='GLB',
 export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
 export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,
 export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
assert {a.name for a in bpy.data.actions}=={'Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'}
print('SELECTED',[(a.name,tuple(a.frame_range)) for a in bpy.data.actions])
