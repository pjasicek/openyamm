from pathlib import Path
import bpy, bmesh, json, sys
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
report={}
for name in ['P00','P01','P02','P03','P04','P05','P16']:
 ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data)
 unseen={e for e in bm.edges if e.is_boundary};loops=[]
 while unseen:
  edge=unseen.pop();stack=list(edge.verts);vs=set(stack)
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    if e in unseen:
     unseen.remove(e);other=e.other_vert(v)
     if other not in vs:vs.add(other);stack.append(other)
  loops.append({'vertices':len(vs),'center':list(sum((v.co for v in vs),Vector())/len(vs)),
                'min':[min(v.co[k] for v in vs) for k in range(3)],'max':[max(v.co[k] for v in vs) for k in range(3)]})
 report[name]=loops;bm.free()
(p/'review/boundary_loops.json').write_text(json.dumps(report,indent=2))
common.workbench_clay(bpy.context.scene)
for obj in bpy.data.objects:
 if obj.type=='MESH':obj.hide_render=obj.name!='P16'
common.render_views(str(p/'review/skirt_backing'),0.85,0.45,views=('front','left','back'),resolution=(600,600))
for obj in bpy.data.objects:
 if obj.type=='MESH':obj.hide_render=False
common.render_views(str(p/'review/geometry_hands'),0.84,0.27,views=('front','left','back'),resolution=(500,500),target=(-0.485,-0.06))
common.render_views(str(p/'review/geometry_head'),1.55,0.40,views=('front','left','back'),resolution=(500,500))
