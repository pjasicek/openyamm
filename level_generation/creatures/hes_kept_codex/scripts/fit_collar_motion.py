"""Fit the rigid control collar to the animated neck surface without changing the body's motion."""
import bpy,sys,os,json
from pathlib import Path
import numpy as np
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];path=P/'work/male/runtime_ragged.blend';bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];scene=bpy.context.scene
D=np.load(P/'texturing/kept_m_uv.npz');co=D['vertices'];pc=np.zeros(len(co),int)
for f,p in zip(D['faces'],D['piece']):pc[f]=p
ids=np.where((pc==1)&(co[:,2]>1.445)&(co[:,2]<1.48))[0];assert len(ids)>10,len(ids)
ref=co[ids];centre=ref.mean(0);rest=rig.data.bones['Kept_Collar'].matrix_local.copy();pb=rig.pose.bones['Kept_Collar'];report={}
for act in sorted(bpy.data.actions,key=lambda a:a.name):
 if not act.name.startswith('Kept_'):continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];errs=[]
 for f in np.arange(act.frame_range[0],act.frame_range[1]+.001,.5):
  scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();target=np.array([body.matrix_world@m.vertices[int(i)].co for i in ids]);ev.to_mesh_clear();tc=target.mean(0)
  U,_,V=np.linalg.svd((ref-centre).T@(target-tc));R=V.T@U.T
  if np.linalg.det(R)<0:V[-1]*=-1;R=V.T@U.T
  delta=Matrix(R.tolist()).to_4x4();delta.translation=tuple(tc-R@centre);pb.matrix=rig.matrix_world.inverted()@delta@rest;pb.rotation_mode='QUATERNION';pb.keyframe_insert('location',frame=float(f));pb.keyframe_insert('rotation_quaternion',frame=float(f))
  errs.append(float(np.linalg.norm((ref-centre)@R.T+tc-target,axis=1).max()))
 for l in act.layers:
  for s in l.strips:
   for cb in s.channelbags:
    for fc in cb.fcurves:
     if 'Kept_Collar' in fc.data_path:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[act.name]={'max_neck_fit_residual_m':max(errs),'samples':len(errs)}
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for o in bpy.data.objects:o.select_set(o in (rig,body))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_kept_m_ragged_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_extras=True,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/'review/collar_motion.json').write_text(json.dumps({'method':'rigid least-squares fit of neck skin; only the separate collar bone receives new keys','neck_vertices':ids.tolist(),'clips':report},indent=2)+'\n');print('COLLAR_MOTION',len(ids),max(r['max_neck_fit_residual_m'] for r in report.values()),flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
