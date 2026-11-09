"""Use mesh soles for grounded clips; preserve the run's aerial phase and let the death settle on the floor."""
import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_body.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
pv=np.array([d.value for d in body.data.attributes['piece'].data]);boot=np.where(np.isin(pv,[13,14]))[0];report={}
for nm in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']:
 ac=bpy.data.actions[nm];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];rows=[]
 for f in range(int(ac.frame_range[1])+1):
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();ids=range(len(me.vertices)) if nm=='Death' else boot;z=min((body.matrix_world@me.vertices[i].co).z for i in ids);ev.to_mesh_clear();rows.append((f,rig.pose.bones['B_Pelvis'].matrix.copy(),z))
 base=min(z for _,_,z in rows)
 for f,M,z in rows:
  scene.frame_set(f);M.translation.z-=base if nm=='Running' else z;pb=rig.pose.bones['B_Pelvis'];pb.matrix=M;bpy.context.view_layer.update();pb.keyframe_insert('location',frame=f)
 report[nm]={'min_correction_m':min(z for _,_,z in rows),'max_correction_m':max(z for _,_,z in rows),'mode':'constant lift, run flight retained' if nm=='Running' else 'actual lowest sole/body point'}
(P/'work/floor_corrections.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_body.blend'))
