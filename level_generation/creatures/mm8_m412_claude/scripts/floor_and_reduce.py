import bpy,sys,runpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];w=p/'work'
bpy.ops.wm.open_mainfile(filepath=str(w/'motion_polished.blend'));rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene
pv=np.array([a.value for a in o.data.attributes['piece'].data]);feet=np.isin(pv,[5,6]);report={}
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];ts=np.arange(0,float(a.frame_range[1])+.001,.25);rows=[]
 for f in ts:
  sc.frame_set(int(f),subframe=float(f-int(f)));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();z=np.array([(o.matrix_world@v.co).z for v in em.vertices]);ev.to_mesh_clear()
  low=z.min() if name=='Death' else z[feet].min();dz=max(0,.002-low) if name=='Running' else .002-low
  rows.append((rig.pose.bones['B_Pelvis'].location.copy(),dz,low))
 # Linear quarter-frame root samples retain the measured contact surface through the source interpolation.
 rot=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
 for f,(loc,dz,low) in zip(ts,rows):
  rig.pose.bones['B_Pelvis'].location=loc+rot@Vector((0,0,float(dz)));rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=float(f))
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if fc.data_path.endswith('.location'):
      for key in fc.keyframe_points:key.interpolation='LINEAR'
 report[name]={'correction_cm':[float(min(r[1] for r in rows)*100),float(max(r[1] for r in rows)*100)],'sample_hz':120}
 a['export_substeps']=4
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(w/'motion_grounded.blend'))
(p/'work/floor_fit.json').write_text(json.dumps(report,indent=2));print('FLOOR FIT',report)
sys.argv=['reduce_rigged.py','--',str(w/'motion_grounded.blend'),str(w/'master_rig.blend')]
runpy.run_path(str(p/'scripts/reduce_rigged.py'),run_name='__main__')
