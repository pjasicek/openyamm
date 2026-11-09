import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));m=bpy.data.objects['Turtle'];bm=bmesh.new();bm.from_mesh(m.data)
remaining={e for e in bm.edges if e.is_boundary};loops=[]
while remaining:
 todo=[remaining.pop()];edges=[]
 while todo:
  e=todo.pop();edges.append(e)
  for v in e.verts:
   for j in v.link_edges:
    if j in remaining:remaining.remove(j);todo.append(j)
 vs={v for e in edges for v in e.verts};center=sum((v.co for v in vs),Vector())/len(vs);loops.append({'edges':len(edges),'center':list(center),'lo':[min(v.co[i] for v in vs) for i in range(3)],'hi':[max(v.co[i] for v in vs) for i in range(3)]})
print('BOUNDARY_LOOPS',json.dumps(loops),flush=True)
