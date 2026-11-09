import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_reduced.blend'));me=bpy.data.objects['Body'].data
P=np.array([v.co[:] for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);print('ATTR',me.attributes['piece'].domain,flush=True)
for v in np.unique(pv):print('PIECE',v,int((pv==v).sum()),P[pv==v].min(0),P[pv==v].max(0),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uvprep.blend'));me=bpy.data.objects['Body'].data;P=np.array([v.co[:] for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);hd=np.array([x.value for x in me.attributes['head'].data]);rows={}
for f in me.polygons:
 if hd[f.index]:
  k=int(pv[f.vertices[0]]);row=rows.setdefault(k,[]);row.extend([P[i] for i in f.vertices])
for k,v in rows.items():print('HEAD',k,len(v),np.array(v).min(0),np.array(v).max(0),flush=True)
