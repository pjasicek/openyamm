"""Inspect and stage the wingless humanoid for independent rig estimates."""
from pathlib import Path
import bpy,bmesh,json,sys
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
report=[]
for name in ('P00','P01','P02','P20','P21'):
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
 edges=[e for e in bm.edges if e.is_boundary];adj={}
 for e in edges:
  for v in e.verts:adj.setdefault(v,set()).update(e.verts)
 seen=set()
 for v in adj:
  if v in seen:continue
  stack=[v];comp=[]
  while stack:
   x=stack.pop()
   if x in seen:continue
   seen.add(x);comp.append(x);stack.extend(adj[x])
  co=np.array([tuple(v.co) for v in comp]);report.append({'part':name,'boundary_vertices':len(comp),'lo':co.min(0).tolist(),'hi':co.max(0).tolist()})
 bm.free()
(P/'work/boundaries.json').write_text(json.dumps(report,indent=2)+'\n')
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/head_detail'),1.63,.6,views=('front','left','back'),resolution=(700,700))
