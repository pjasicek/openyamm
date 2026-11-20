"""Keep the complete equipped collapse above the floor, preserving every relative pose and grip."""
import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];path=P/'work/male/runtime_ragged.blend';bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];scene=bpy.context.scene;report={}
def points(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=np.array([o.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear();return p
for name in ('Kept_Death','Kept_ArmedDeath'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];objects=[body,bpy.data.objects['hes_kept_collar']]+([bpy.data.objects['hes_kept_'+n] for n in ('pick','club','plate')] if 'Armed' in name else []);times=np.arange(a.frame_range[0],a.frame_range[1]+.001,.5);before=[];poses=[];needed=[];pb=rig.pose.bones['B_Pelvis']
 for f in times:
  scene.frame_set(int(f),subframe=float(f%1));p=np.concatenate([points(o) for o in objects]);before.append(p);needed.append(max(0,.001-p[:,2].min()));poses.append(pb.matrix.copy())
 # Smooth, compact bumps cover each penetrating sample without changing the first/last poses.
 lift=np.array([max(n*(.5+.5*math.cos(math.pi*min(1,abs(t-f)/4.5))) for f,n in zip(times,needed)) for t in times]);assert max(lift)<.08
 for f,M,dz in zip(times,poses,lift):
  scene.frame_set(int(f),subframe=float(f%1));M.translation.z+=float(dz);pb.matrix=M;pb.keyframe_insert('location',frame=float(f))
 for l in a.layers:
  for strip in l.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     if fc.data_path=='pose.bones["B_Pelvis"].location':
      for k in fc.keyframe_points:k.interpolation='LINEAR'
 worst=1e9;err=0
 for f,old,dz in zip(times,before,lift):
  scene.frame_set(int(f),subframe=float(f%1));new=np.concatenate([points(o) for o in objects]);err=max(err,float(np.abs(new-old-np.array([0,0,dz])).max()));worst=min(worst,float(new[:,2].min()))
 assert err<2e-6 and worst>=-.0001,(err,worst)
 report[name]={'max_world_lift_m':float(max(lift)),'min_before_m':float(min(p[:,2].min() for p in before)),'min_after_m':worst,'relative_pose_error_m':err,'half_frame_samples':len(times),'world_lift_by_frame':[[float(f),float(d)] for f,d in zip(times,lift)]}
bpy.ops.wm.save_as_mainfile(filepath=str(path))
for a in bpy.data.actions:
 for l in a.layers:
  for strip in l.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.co.x*=2;k.handle_left.x*=2;k.handle_right.x*=2
     fc.update()
 a.frame_start*=2;a.frame_end*=2
scene.render.fps=60;rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for obj in bpy.data.objects:obj.select_set(obj in (rig,body))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_kept_m_ragged_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_extras=True,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'review/equipped_death_floor.json').write_text(json.dumps({'pass':True,'clips':report},indent=2)+'\n');print('EQUIPPED_FLOOR',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
