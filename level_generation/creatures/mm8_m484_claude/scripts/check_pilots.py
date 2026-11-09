import os
import bpy,sys,json,runpy
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/os.environ.get('CHECK_BLEND','work/pilots.blend')));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene
co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in b.vertex_groups];W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
E=np.array([e.vertices[:] for e in me.edges]);length=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);report={}
for nm in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];out={}
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.1,.5):
  sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();pts=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(pts[E[:,0]]-pts[E[:,1]],axis=1)/np.maximum(length,1e-8)
  for sd in 'RL':
   for label,keys in [('arm',['UpperArm','Forearm']),('hand',['Hand','Finger'])]:
    weights=W[:,[i for i,n in enumerate(names) if n.startswith(f'B_{sd}_') and any(k in n for k in keys)]].sum(1);mask=(weights[E[:,0]]>.3)&(weights[E[:,1]]>.3)&(pv[E[:,0]]==0)&(length>.00001);ids=np.where(mask)[0];vals=ratio[ids];v=float(np.percentile(vals,99)) if label=='arm' else float(vals.max());key=sd+'_'+label
    if v>out.get(key,{}).get('value',0):j=ids[np.argmax(vals)];out[key]={'value':v,'max':float(vals.max()),'frame':float(f),'edge':E[j].tolist(),'rest_points':co[E[j]].tolist(),'weights':[{names[k]:round(float(W[i,k]),3) for k in np.where(W[i]>.01)[0]} for i in E[j]]}
 report[nm]=out;print('GATES',nm,{k:(round(v['value'],3),v['frame'],v['edge']) for k,v in out.items()},flush=True)
(P/'review'/(os.environ.get('CHECK_PREFIX','pilot')+'_'+'stretch'+'.json')).write_text(json.dumps(report,indent=2))
