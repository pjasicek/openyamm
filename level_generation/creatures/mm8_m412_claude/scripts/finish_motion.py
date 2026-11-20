"""Keep Standard Run's authored legs and foot trajectories; reuse the calibrated carrying arm pose."""
import bpy,json,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_equipped.blend'))
rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
# Runtime supports four influences. Make the authoring checkpoint use exactly those same weights.
for v in o.data.vertices:
 weights=sorted([(g.group,g.weight) for g in v.groups],key=lambda a:a[1],reverse=True)
 keep=weights[:4];total=sum(w for _,w in keep)
 assert total>0
 for g,_ in weights:o.vertex_groups[g].remove([v.index])
 for g,w in keep:o.vertex_groups[g].add([v.index],w/total,'REPLACE')
old=bpy.data.actions['Running'];rig.animation_data.action=old;rig.animation_data.action_slot=old.slots[0]
times=np.arange(0,22.001,.25);upper=[]
for f in times:
 sc.frame_set(int(f),subframe=float(f%1));upper.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones if not any(k in b.name for k in ('Pelvis','Thigh','Calf','Foot','Toe'))})
with bpy.data.libraries.load(str(P/'work/rig_v2t.blend'),link=False) as (_,d):d.actions=['Running']
a=d.actions[0];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];legs=[]
for f in times:
 sc.frame_set(int(f),subframe=float(f%1));legs.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones if b.name=='B_Pelvis' or any(k in b.name for k in ('Thigh','Calf','Foot','Toe'))})
bpy.data.actions.remove(old);bpy.data.actions.remove(a);a=bpy.data.actions.new('Running');a.use_fake_user=True;rig.animation_data.action=a
for f,up,leg in zip(times,upper,legs):
 pose={**up,**leg}
 for n,(q,loc) in pose.items():
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=loc;b.keyframe_insert('rotation_quaternion',frame=float(f))
  if n=='B_Pelvis':b.keyframe_insert('location',frame=float(f))
a.use_frame_range=True;a.frame_start=0;a.frame_end=22
# Loop correction is a gradual quaternion/position drift removal, retaining the original source trajectories.
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
pv=np.array([a.value for a in o.data.attributes['piece'].data]);feet=np.isin(pv,[5,6]);report={}
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];ts=np.arange(0,float(a.frame_range[1])+.001,.25);rows=[]
 for f in ts:
  sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();z=np.array([v.co.z for v in em.vertices]);ev.to_mesh_clear();low=z.min() if name=='Death' else z[feet].min()
  dz=max(0,.002-low) if name=='Running' else .002-low
  rows.append((rig.pose.bones['B_Pelvis'].location.copy(),dz,float(low)))
 inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
 for f,(loc,dz,low) in zip(ts,rows):
  rig.pose.bones['B_Pelvis'].location=loc+inv@Vector((0,0,float(dz)));rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=float(f))
 report[name]={'lowest_before_m':[min(r[2] for r in rows),max(r[2] for r in rows)],'correction_m':[min(r[1] for r in rows),max(r[1] for r in rows)]}
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_finished.blend'))
(P/'work/final_floor_fit.json').write_text(json.dumps(report,indent=2));print('FINAL_FLOOR',report)
