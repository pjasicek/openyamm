import sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import bpy,bmesh
from common import render_views,workbench_clay
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
workbench_clay(bpy.context.scene)
render_views(str(p/'review/geometry_full'),.85,2.0,views=('front','three_quarter','left','back'),resolution=(1000,1000))
render_views(str(p/'review/geometry_right_hand'),.878,.25,views=('front','back'),resolution=(900,900),target=(-.546,-.073))
render_views(str(p/'review/geometry_head'),1.56,.37,views=('front','left'),resolution=(800,800))
report={}
for name in ['P00','P04','P05']:
 ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
 edges={e for e in bm.edges if e.is_boundary};loops=[]
 while edges:
  todo=[edges.pop()];group=set(todo)
  while todo:
   e=todo.pop()
   for v in e.verts:
    for n in v.link_edges:
     if n in edges:edges.remove(n);group.add(n);todo.append(n)
  vs={v for e in group for v in e.verts}
  loops.append({'edges':len(group),'lo':[min(v.co[i] for v in vs) for i in range(3)],'hi':[max(v.co[i] for v in vs) for i in range(3)]})
 report[name]=loops;bm.free()
(p/'work/boundaries.json').write_text(json.dumps(report,indent=2))
print(report)
