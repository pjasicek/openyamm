"""Bake contact at 60 Hz so native 0.75-second hits have an exact endpoint."""
import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/texture_ready.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
assert scene.render.fps==30
for a in bpy.data.actions:
 end=round(a.frame_range[1]*2)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.co.x*=2;k.handle_left.x*=2;k.handle_right.x*=2;k.interpolation='LINEAR'
     fc.update()
 a.frame_start=0;a.frame_end=end
scene.render.fps=60
report={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];values=[]
 for f in range(round(a.frame_range[1])+1):
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=min(v.co.z for v in me.vertices);ev.to_mesh_clear()
  pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z-=z;pb.matrix=m;values.append((f,pb.location.copy()))
 for f,loc in values:
  rig.pose.bones['B_Pelvis'].location=loc;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f,group='B_Pelvis')
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 floor=[]
 for f in np.linspace(0,a.frame_range[1],241):
  scene.frame_set(math.floor(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  coords=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();assert np.isfinite(coords).all();floor.append(float(coords[:,2].min()))
 report[a.name]={'duration_seconds':float(a.frame_range[1]/60),'floor_min_m':min(floor),'floor_max_m':max(floor)}
 assert min(floor)>-.003 and max(floor)<(.025 if a.name=='Death' else .008),(a.name,report[a.name])
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/texture_ready.blend'))
(P/'work/final_motion_contacts.json').write_text(json.dumps(report,indent=2));print('CONTACTS',json.dumps(report))
