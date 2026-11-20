"""Connected tunic edge stretch on the coarser runtime LODs; no dense sole-patch assumption."""
import bpy,json,numpy as np,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;me=body.data
rest=np.array([tuple(body.matrix_world@v.co)for v in me.vertices]);parts=np.array([a.value for a in me.attributes['piece'].data])
edges=np.array([tuple(e.vertices)for e in me.edges]);edges=edges[(parts[edges[:,0]]==2)&(parts[edges[:,1]]==2)]
lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);edges=edges[lengths>1e-5];lengths=lengths[lengths>1e-5];assert len(edges)>3;report={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];p99=0;maximum=0
 for t in np.arange(0,float(a.frame_range[1])/scene.render.fps+1e-6,1/48):
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co)for v in m.vertices]);ev.to_mesh_clear()
  stretch=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/lengths;p99=max(p99,float(np.percentile(stretch,99)));maximum=max(maximum,float(stretch.max()))
 report[name]={'p99_edge_stretch':p99,'max_edge_stretch':maximum,'pass':p99<2 and maximum<2.5}
out={'runtime_sha256':hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest(),'sample_hz':48,'clips':report,'pass':all(x['pass']for x in report.values())}
(P/'review/round3/flap_stretch_gate.json').write_text(json.dumps(out,indent=2)+'\n');assert out['pass']

