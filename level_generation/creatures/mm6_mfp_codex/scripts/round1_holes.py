import bpy,bmesh,json,numpy as np,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1/lod0.blend'));b=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(b.data);pv=bm.verts.layers.int['piece'];edges=[e for e in bm.edges if e.is_boundary and all(v[pv] in [4,5]for v in e.verts)];remaining=set(edges);loops=[]
while remaining:
 edge=remaining.pop();group={edge};verts=set(edge.verts)
 while True:
  more={e for e in remaining if set(e.verts)&verts}
  if not more:break
  remaining-=more;group|=more
  for e in more:verts.update(e.verts)
 loops.append({'edges':len(group),'vertices':[[v.index,list(v.co)]for v in verts]})
print('ARM_BOUNDARIES',json.dumps(loops));(P/'review/round1/arm_holes.json').write_text(json.dumps(loops,indent=2));print('UV_ACTIVE',b.data.uv_layers.active.name)
