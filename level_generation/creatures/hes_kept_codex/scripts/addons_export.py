"""Export the chosen overhead swing, repaired Enforcer body and skinned plate at 60 Hz."""
import bpy,sys,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/addons_v2/equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];plate=bpy.data.objects['hes_kept_plate'];sc=bpy.context.scene
for a in list(bpy.data.actions):
 if a.name in ('Kept_ClubR2','Kept_ClubSword1'):bpy.data.actions.remove(a)
bpy.data.actions['Kept_ClubR1'].name='Kept_ClubAttack'
# Preserve the 30 Hz authoring master, including half-frame fit keys.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/addons_v2/final.blend'))
for a in bpy.data.actions:
 for l in a.layers:
  for s in l.strips:
   for cb in s.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.co.x*=2;k.handle_left.x*=2;k.handle_right.x*=2
     fc.update()
 a.frame_start*=2;a.frame_end*=2
sc.render.fps=60;r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
plate.name=plate.data.name='KeptPlate'
# The same repaired male core is used for all three collared tiers; only C embeds its fitted skinned shell.
for stem,extra in [('hes_kept_m_ragged',[]),('hes_kept_m_enforcer',[plate])]:
 for o in bpy.data.objects:o.select_set(o in (r,b,*extra))
 bpy.context.view_layer.objects.active=r
 bpy.ops.export_scene.gltf(filepath=str(P/'export'/f'{stem}_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_extras=True,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
