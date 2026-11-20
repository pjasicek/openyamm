import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduced_v1.blend'))
me=bpy.data.objects['Body'].data;bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece']
edges={e for e in bm.edges if e.is_boundary and all(v[pl]==1 for v in e.verts)}
while edges:
 e=edges.pop();comp={e};stack=[e]
 while stack:
  a=stack.pop()
  for v in a.verts:
   for b in v.link_edges:
    if b in edges:edges.remove(b);comp.add(b);stack.append(b)
 vs={v for e in comp for v in e.verts};c=sum((v.co for v in vs),Vector())/len(vs)
 print('FACEBOUNDARY',len(vs),list(c),[(min(v.co[i] for v in vs),max(v.co[i] for v in vs)) for i in range(3)])
