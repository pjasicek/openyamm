import bpy,bmesh,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/"work/texture_master.blend"))
b=bpy.data.objects["Body"];bm=bmesh.new();bm.from_mesh(b.data);pl=bm.verts.layers.int["piece"]
for piece in [0,60]:
 es=[e for e in bm.edges if e.is_boundary and e.verts[0][pl]==piece]; unseen=set(v for e in es for v in e.verts); rows=[]
 while unseen:
  stack=[unseen.pop()];vs=[]
  while stack:
   v=stack.pop();vs.append(v)
   for e in v.link_edges:
    if e.is_boundary and e.other_vert(v) in unseen:unseen.remove(e.other_vert(v));stack.append(e.other_vert(v))
  rows.append({"count":len(vs),"center":[sum(v.co[k] for v in vs)/len(vs) for k in range(3)],"span":[max(v.co[k] for v in vs)-min(v.co[k] for v in vs) for k in range(3)]})
 print("BOUNDARIES",piece,json.dumps(rows))
