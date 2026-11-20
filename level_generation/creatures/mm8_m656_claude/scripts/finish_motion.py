"""Final influence cap and support-ground fit at 120 Hz, retaining source flight in Running."""
import bpy,numpy as np,json
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];W=P/'work'
bpy.ops.wm.open_mainfile(filepath=str(W/'rig_v6t.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
for v in body.data.vertices:
 ws=sorted([(e.group,e.weight) for e in v.groups],key=lambda x:-x[1]);keep=ws[:4];total=sum(w for _,w in keep);assert total>0
 for i,_ in ws:body.vertex_groups[i].remove([v.index])
 for i,w in keep:body.vertex_groups[i].add([v.index],w/total,'REPLACE')
pv=np.array([x.value for x in body.data.attributes['piece'].data]);feet=np.isin(pv,[6,7]);report={}
inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
 for f in np.arange(0,float(act.frame_range[1])+.001,.25):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=np.array([(body.matrix_world@v.co).z for v in me.vertices]);ev.to_mesh_clear()
  low=z.min() if name=='Death' else z[feet].min();dz=max(0,.002-low) if name=='Running' else .002-low
  rows.append((float(f),rig.pose.bones['B_Pelvis'].location.copy()+inv@Vector((0,0,float(dz))),float(dz)))
 for f,loc,dz in rows:rig.pose.bones['B_Pelvis'].location=loc;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'duration_s':float(act.frame_range[1])/30,'root_correction_cm':[min(x[2] for x in rows)*100,max(x[2] for x in rows)*100]}
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(W/'motion_grounded.blend'));(W/'motion_report.json').write_text(json.dumps(report,indent=2));print('MOTION',report)
