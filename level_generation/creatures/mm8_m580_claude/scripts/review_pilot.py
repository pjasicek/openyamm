"""Review fixed-camera pilot poses and export the current clay animation for playback."""
from pathlib import Path
import bpy,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from review_studio import render_views
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));rig=bpy.data.objects['Turtle_Rig'];mesh=bpy.data.objects['Turtle'];sc=bpy.context.scene
for role,times in [('Swim',[0,.25,.5,.75]),('Bite',[.55,.75]),('Death',[.875])]:
 for t in times:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(t*48),subframe=t*48-int(t*48))
  render_views(mesh,P/'review'/f'pilot_{role}_{t:.3f}',views=['side'],bounds=((-0.65,-.85,0),(.65,.85,.85)))
for obj in bpy.data.objects:obj.select_set(obj in [rig,mesh])
bpy.context.view_layer.objects.active=rig;rig.animation_data.action=bpy.data.actions['Swim'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
(P/'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P/'export/m580_pilot.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=False,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
