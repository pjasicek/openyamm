from pathlib import Path
import bpy,bmesh,json
import numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
rows=[]
for file,name in [('st_v1_parts.blend','P00'),('head_v1_parts.blend','H00')]:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/file));o=bpy.data.objects[name]
 for q in [1.53,1.55,1.57,1.59,1.61]:
  bm=bmesh.new();bm.from_mesh(o.data)
  if name=='H00':
   for v in bm.verts:v.co+=Vector((-.0035,.04,-.014))
  res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,q),plane_no=(0,-.5,1))
  edges={e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge)};loops=[]
  while edges:
   pending=[edges.pop()];es=set(pending)
   while pending:
    e=pending.pop()
    for v in e.verts:
     for e2 in v.link_edges:
      if e2 in edges:edges.remove(e2);es.add(e2);pending.append(e2)
   co=np.array([tuple(v.co) for v in set(v for e in es for v in e.verts)])
   loops.append({'n':len(co),'lo':co.min(0).round(3).tolist(),'hi':co.max(0).round(3).tolist(),'center':co.mean(0).round(3).tolist()})
  rows.append({'object':name,'q':q,'loops':loops});bm.free()
(p/'work/neck_sections.json').write_text(json.dumps(rows,indent=2))
for row in rows:print('CUT',row)
