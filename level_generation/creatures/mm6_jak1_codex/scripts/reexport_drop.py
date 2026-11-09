"""Re-export a prop-only correction using the already fitted body timing."""
import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from retime_acceleration import warp
from staff_drop import bake_staff_drop
T=json.loads((P/'work/action_timing.json').read_text());source=P/'work/drop_unretimed.blend'
def curves(action):
 return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
if not source.exists():
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));fps=bpy.context.scene.render.fps
 for action in bpy.data.actions:
  row=T[action.name];old=np.arange(round(row['source_duration_s']*fps)+1)/fps;mapped=warp(old,row['bumps'])
  for curve in curves(action):
   seen=set()
   for key in list(curve.keyframe_points):
    frame=round(float(np.interp(key.co.x/fps,mapped,old))*fps)
    if frame in seen:curve.keyframe_points.remove(key,fast=True);continue
    seen.add(frame);key.co.x=frame;key.interpolation='LINEAR'
   curve.update()
  action.use_frame_range=True;action.frame_start=0;action.frame_end=old[-1]*fps
 bpy.ops.wm.save_as_mainfile(filepath=str(source))
else:bpy.ops.wm.open_mainfile(filepath=str(source))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Jackalman'];fps=bpy.context.scene.render.fps
bake_staff_drop(rig,body,P)
for action in bpy.data.actions:
 row=T[action.name]
 for curve in curves(action):
  for key in curve.keyframe_points:key.co.x=float(warp(key.co.x/fps,row['bumps']))*fps;key.interpolation='LINEAR'
  curve.update();end=row['duration_s']*fps;value=curve.evaluate(end);curve.keyframe_points.insert(end,value,options={'FAST'});curve.update()
 action.use_frame_range=True;action.frame_start=0;action.frame_end=row['duration_s']*fps
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_jak1_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_master.blend'))
drop=json.loads((P/'work/staff_drop.json').read_text());drop['source_phase_seconds']={k:drop[k]for k in ['release_seconds','first_floor_contact_seconds','settled_seconds']}
for k,v in drop['source_phase_seconds'].items():
 if v is not None:drop[k]=float(warp(v,T['Death']['bumps']))
(P/'work/staff_drop.json').write_text(json.dumps(drop,indent=2))
