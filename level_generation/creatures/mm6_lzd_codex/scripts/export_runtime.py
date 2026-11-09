"""Final source-frame export; up to eight normalized skin influences, linear continuous quaternion keys."""
import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master.blend'))
scene=bpy.context.scene;scene.render.fps=30;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
before=max(len([g for g in v.groups if g.weight>1e-8])for v in body.data.vertices)
bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
assert all(len([g for g in v.groups if g.weight>1e-8])<=8 for v in body.data.vertices)
assert max(abs(sum(g.weight for g in v.groups)-1)for v in body.data.vertices)<1e-5
for act in bpy.data.actions:
 curves=[fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves];groups={}
 for fc in curves:
  for key in fc.keyframe_points:key.interpolation='LINEAR'
  if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
 for cs in groups.values():
  if len(cs)!=4:continue
  keys=[cs[i].keyframe_points for i in range(4)];prev=None
  for j in range(min(map(len,keys))):
   q=np.array([k[j].co.y for k in keys]);q=q/np.linalg.norm(q)
   if prev is not None and np.dot(q,prev)<0:q=-q
   for i in range(4):keys[i][j].co.y=q[i]
   prev=q
  for fc in cs.values():fc.update()
# Save the exact export input for repeatable full geometry probes.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_export.blend'))
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pv=np.array([a.value for a in body.data.attributes['piece'].data]);co=np.array([tuple(body.matrix_world@v.co)for v in me.vertices]);ev.to_mesh_clear();bodyco=co[pv<201];height=float(np.ptp(bodyco[:,2]));native=256*.699997
walk=bpy.data.actions['Walking'];rig.animation_data.action=walk;rig.animation_data.action_slot=walk.slots[0];feet=[]
for f in np.linspace(*walk.frame_range,97):
 scene.frame_set(int(f),subframe=float(f%1));feet.append([tuple(rig.pose.bones[f'B_{s}_Foot'].head)for s in 'LR'])
feet=np.array(feet);stride=float(np.mean(np.ptp(feet[:,:,1],axis=0))*2)
info={'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'bones':len(rig.data.bones),'influences_before_limit':before,'max_influences':8,'standing_body_height_m':height,'native_height_units':native,'scale':native/height,'stride_length_m':stride,'stride_method':'twice mean fore-aft foot excursion in Walking','clips':{a.name:float((a.frame_range[1]-a.frame_range[0])/30)for a in bpy.data.actions},'impact_seconds':.734375}
body.name=body.data.name='Lizard'
for name in ['piece','finger','head','orig_co']:
 if name in body.data.attributes:body.data.attributes.remove(body.data.attributes[name])
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
for o in bpy.data.objects:o.select_set(o in (rig,body))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_lzd_raw.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'export/export_info.json').write_text(json.dumps(info,indent=2));print('EXPORT_INFO',info)
