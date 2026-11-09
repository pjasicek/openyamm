from pathlib import Path
import bpy,json,numpy as np
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm8_m604.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['EtherKnight'];sc=bpy.context.scene;out={}
for n in ['Standing','Walking','Running','Dead']:
 a=bpy.data.actions[n];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];points=[]
 for f in a.frame_range:
  sc.frame_set(int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();points.append(np.array([v.co[:] for v in m.vertices]));ev.to_mesh_clear()
 delta=np.linalg.norm(points[1]-points[0],axis=1);out[n]={'max_surface_delta_mm':float(delta.max()*1000),'p99_mm':float(np.percentile(delta,99)*1000)}
(p/'work/loop_endpoints.json').write_text(json.dumps(out,indent=2));print('LOOPS',out)
