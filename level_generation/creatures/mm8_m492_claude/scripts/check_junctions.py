import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
a=np.array([v.co[:] for v in o.data.vertices]);e=np.array([ed.vertices[:] for ed in o.data.edges]);length=np.linalg.norm(a[e[:,0]]-a[e[:,1]],axis=1);pa=np.array([v.value for v in o.data.attributes['part'].data]);names={g.index:g.name for g in o.vertex_groups}
report={}
for clip,frame in [('Standing',0),('Standing',16),('Attack',30),('Death',24),('Dead',0)]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();b=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(b[e[:,0]]-b[e[:,1]],axis=1)/np.maximum(length,1e-9);ix=np.argsort(ratio)[-20:][::-1]
 report[clip+str(frame)]=[{'ratio':float(ratio[j]),'rest_length':float(length[j]),'vertices':[{'index':int(v),'part':int(pa[v]),'rest':a[v].tolist(),'posed':b[v].tolist(),'weights':{names[g.group]:g.weight for g in o.data.vertices[v].groups}} for v in e[j]]} for j in ix]
(P/'review/junction_stretch.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v[:4] for k,v in report.items()},indent=2))
