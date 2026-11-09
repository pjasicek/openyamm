import bpy,json,numpy as np
from pathlib import Path
from collections import defaultdict
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];groups=defaultdict(list)
for v in body.data.vertices:groups[tuple(round(x,5) for x in v.co)].append(v.index)
groups=[g for g in groups.values() if len(g)>1];rig.animation_data.action=bpy.data.actions['Attack'];bpy.context.scene.frame_set(24);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();C=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();r=[]
for g in groups:
 error=float(np.linalg.norm(C[g]-C[g[0]],axis=1).max())
 if error>.00005:r.append({'vertices':g,'error':error,'rest':list(body.data.vertices[g[0]].co)})
print('SEAMS',json.dumps(sorted(r,key=lambda x:-x['error'])[:15]));print('COUNT',len(groups),len(r));(P/'work/seam_audit.json').write_text(json.dumps(r,indent=2))
