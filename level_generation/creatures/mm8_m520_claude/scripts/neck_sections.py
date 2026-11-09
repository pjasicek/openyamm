from pathlib import Path
import bpy,bmesh,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/body_clean.blend'))
rows=[]
for tilt in [0,-.4]:
 for z in [1.98,2,2.02,2.04,2.06,2.08,2.10]:
  bm=bmesh.new();bm.from_mesh(bpy.data.objects['P00'].data);res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,z),plane_no=(0,tilt,1));edges=[e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge)];todo={v for e in edges for v in e.verts};comps=[]
  while todo:
   v=todo.pop();stack=[v];comp=[v]
   while stack:
    v=stack.pop()
    for e in v.link_edges:
     if e not in edges:continue
     n=e.other_vert(v)
     if n in todo:todo.remove(n);stack.append(n);comp.append(n)
   comps.append(comp)
  row={'tilt':tilt,'cut':z,'loops':[{'vertices':len(c),'lo':[round(min(v.co[k] for v in c),3) for k in range(3)],'hi':[round(max(v.co[k] for v in c),3) for k in range(3)]} for c in sorted(comps,key=len,reverse=True)]};rows.append(row);print('SECTION',json.dumps(row),flush=True);bm.free()
(p/'work/neck_sections.json').write_text(json.dumps(rows,indent=2))
