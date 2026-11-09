import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pre_final_ground.blend'));rig=bpy.data.objects['Rig'];root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();body=bpy.data.objects['Body'];part=np.array([v.value for v in body.data.attributes['piece'].data]);rest=np.array([tuple(v.co)for v in body.data.vertices]);foot=np.where((part==1)&(rest[:,2]<.025))[0];objects=[bpy.data.objects[n]for n in ['Body','ForearmBlade','LeafShield']];sc=bpy.context.scene;report={}
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];samples=[]
 for f in np.arange(0,a.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));low=100;sole=100
  for ob in objects:
   ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(v.co)for v in me.vertices]);low=min(low,float(co[:,2].min()))
   if ob==body:sole=float(co[foot,2].min())
   ev.to_mesh_clear()
  dz=min(0,.006-sole)if name=='Running'else 0;dz=max(dz,.002-low);samples.append((float(f),root.location.copy()+inv@Vector((0,0,dz)),dz))
 for f,loc,dz in samples:root.location=loc;root.keyframe_insert('location',frame=f)
 report[name]={'root_shift_min_m':min(s[2]for s in samples),'root_shift_max_m':max(s[2]for s in samples)}
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
(P/'review/final/ground_correction.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/accepted_master.blend'))
