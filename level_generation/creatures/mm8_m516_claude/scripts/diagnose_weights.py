import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];a=np.load(P/'work/rig_weights.npz');c=a['co'];edges=a['edges'];w=a['weights'];names=a['names'];rest=np.linalg.norm(c[edges[:,0]]-c[edges[:,1]],axis=1);out={}
for role,frames in [('Walking',range(1,26)),('Attack',[13,25]),('Death',range(1,26))]:
 worst=[];rig.animation_data.action=bpy.data.actions[role]
 for frame in frames:
  bpy.context.scene.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)/np.maximum(rest,1e-6);ratio[rest<.002]=0
  for k in np.argsort(ratio)[-8:]:
   ii=edges[k];worst.append({'frame':frame,'ratio':float(ratio[k]),'rest':c[ii].tolist(),'edge':ii.tolist(),'weights':[{str(names[j]):round(float(w[v,j]),3) for j in np.where(w[v]>.001)[0]} for v in ii]})
 out[role]=sorted(worst,key=lambda v:-v['ratio'])[:10]
(P/'work/weight_diagnostic.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
