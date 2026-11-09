"""Measure coat deformation and identify arm influences on the torso."""
import bpy, json, sys, numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'))
b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
co=np.array([v.co[:] for v in b.data.vertices]);pc=np.array([x.value for x in b.data.attributes['piece'].data])
names={g.index:g.name for g in b.vertex_groups}
weights=[{names[e.group]:float(e.weight) for e in v.groups if e.weight>1e-5} for v in b.data.vertices]
arm=np.array([sum(w for n,w in ws.items() if any(k in n for k in ['UpperArm','Forearm','Hand','Finger'])) for ws in weights])
medial=(pc==0)&(co[:,2]>1.07)&(co[:,2]<1.34)&(abs(co[:,0]-.01)<.16)
edges=np.array([tuple(e.vertices) for e in b.data.edges]);length=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
mask=(pc[edges[:,0]]==0)&(pc[edges[:,1]]==0)&(co[edges[:,0],2]>1.03)&(co[edges[:,1],2]>1.03)&(length>.003)
edges=edges[mask];length=length[mask];report={'medial_max_arm_weight':float(arm[medial].max()),'medial_arm_vertices':int(sum(arm[medial]>.01)),'frames':{}}
for frame in [0,24,36,40,44,48,52,60,72]:
 a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=frame/48*30;sc.frame_set(int(f),subframe=f%1)
 ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();posed=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
 stretch=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1)/length
 worst=np.argsort(stretch)[-15:][::-1]
 report['frames'][frame]={'percentiles':np.percentile(stretch,[50,90,95,99,100]).tolist(),'worst':[{'ratio':float(stretch[i]),'vertices':[{'id':int(v),'rest':co[v].tolist(),'weights':weights[v]} for v in edges[i]]} for i in worst]}
(P/'review/coat_skin'/('probe_after.json' if '--after' in sys.argv else 'probe_before.json')).write_text(json.dumps(report,indent=2)+'\n')
print('COAT_PROBE',json.dumps({k:v for k,v in report.items() if k!='frames'}))
for k,v in report['frames'].items():print(k,v['percentiles'])
