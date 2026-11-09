"""Ground the evaluated soles, retain a small run flight phase and hold the death endpoint."""
from pathlib import Path
import bpy,json,sys
import numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names=[g.name for g in body.vertex_groups];feet=np.array([sum(g.weight for g in v.groups if names[g.group] in ['B_L_Foot','B_R_Foot','B_L_Toe0','B_R_Toe0'])>.5 for v in body.data.vertices])
def sel(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
# Native MM8 cast acts at 1.25 s. Keep the professional release at speed after a deliberate ready lead-in.
cast=bpy.data.actions['Cast'];lead=27
for layer in cast.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    value=fc.evaluate(0)
    for key in fc.keyframe_points:key.co.x+=lead;key.handle_left.x+=lead;key.handle_right.x+=lead
    fc.keyframe_points.insert(0,value)
cast.frame_start=0;cast.frame_end=60
report={}
for name in ['Standing','Walking','Running','Attack','Hit','Cast','Fidget','Death']:
 act=bpy.data.actions[name];changes=[]
 for f in range(int(act.frame_range[1])+1):
  sel(act);sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([(body.matrix_world@v.co).z for v in m.vertices]);ev.to_mesh_clear()
  low=float(z.min() if name=='Death' else z[feet].min());target=float(np.clip(low,0,.025)) if name=='Running' else 0
  M=rig.matrix_world@rig.pose.bones['B_Pelvis'].matrix;M.translation.z+=target-low+.001
  rig.pose.bones['B_Pelvis'].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update();changes.append(rig.pose.bones['B_Pelvis'].location.copy())
 for f,loc in enumerate(changes):rig.pose.bones['B_Pelvis'].location=loc;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
 report[name]={'seconds':float(act.frame_range[1])/30}
# Exact endpoint duplication for cyclic playback.
for name in ['Standing','Walking','Running','Fidget']:
 a=bpy.data.actions[name];sel(a);sc.frame_set(0);pose={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones};end=float(a.frame_range[1])
 for n,(q,l) in pose.items():
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=end)
  if n=='B_Pelvis':b.location=l;b.keyframe_insert('location',frame=end)
sel(bpy.data.actions['Death']);sc.frame_set(int(bpy.data.actions['Death'].frame_range[1]));pose={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones};a=bpy.data.actions.new('Dead');a.use_fake_user=True;sel(a)
for n,(q,l) in pose.items():
 for f in [0,30]:
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis':b.location=l;b.keyframe_insert('location',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=30
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
sel(bpy.data.actions['Cast']);points=[]
for f in range(int(bpy.data.actions['Cast'].frame_range[1])+1):sc.frame_set(f);points.append(tuple((rig.matrix_world@rig.pose.bones['B_L_Hand'].matrix).translation))
impact=(int(np.argmax(np.linalg.norm(np.diff(np.array(points),axis=0),axis=1)))+.5)/30
r=json.loads((p/'work/clip_timing.json').read_text());r['cast_impact_s']=round(impact,4);(p/'work/clip_timing.json').write_text(json.dumps(r,indent=2))
sel(None);(p/'work/clip_manifest.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v5.blend'));print('FLOOR / TIMING',r)
