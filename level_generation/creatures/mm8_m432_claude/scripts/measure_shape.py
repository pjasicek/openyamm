import bpy,bmesh,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_clean.blend'))
o=bpy.data.objects['Body']; c=np.array([v.co[:] for v in o.data.vertices]); pv=np.array([x.value for x in o.data.attributes['piece'].data])
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
r={}
for side,part in [('R',5),('L',6)]:
    ids=[v.index for v in bm.verts if pv[v.index]==part and any(e.is_boundary for e in v.link_edges)]
    r[side]={'wrist_boundary_count':len(ids),'wrist_center':c[ids].mean(0).tolist(),'bounds':[c[ids].min(0).tolist(),c[ids].max(0).tolist()]}
ids=np.where((pv==1)&(c[:,0]>.066)&(c[:,2]>1.72))[0]
r['left_ear_candidates']=[{'id':int(i),'co':c[i].tolist()} for i in ids]
(P/'work/shape_measurements.json').write_text(json.dumps(r,indent=1))
print(json.dumps(r))
