import bpy,bmesh,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_master.blend'));me=bpy.data.objects['Body'].data;bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();edges=[e for e in bm.edges if e.is_boundary];todo=set(edges);rows=[]
while todo:
 es={todo.pop()};vs=set(es.copy().pop().verts);last=0
 while last!=len(vs):
  last=len(vs);more={e for e in todo if any(v in vs for v in e.verts)};es|=more;todo-=more;vs|={v for e in more for v in e.verts}
 co=np.array([tuple(v.co)for v in vs]);rows.append({'edges':len(es),'centre':co.mean(0).tolist(),'min':co.min(0).tolist(),'max':co.max(0).tolist(),'piece':me.attributes['piece'].data[next(iter(vs)).index].value})
print('BOUNDARIES',rows,flush=True);(P/'work/boundaries.json').write_text(json.dumps(rows,indent=2))
