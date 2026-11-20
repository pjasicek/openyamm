from pathlib import Path
import bpy,bmesh,json,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import common
p=Path(common.PROJECT)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
scene=bpy.context.scene;common.workbench_clay(scene)
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=o.name!='P03'
common.render_views(str(p/'review/legs'),.54,1.2,views=('front','left'),resolution=(600,800))
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=o.name not in ('P01','P09','P10')
common.render_views(str(p/'review/face'),1.53,.3,views=('front','three_quarter'),resolution=(700,700))
for side,part,x in [('L','P05',.48),('R','P06',-.48)]:
 for o in bpy.data.objects:
  if o.type=='MESH':o.hide_render=o.name!=part
 common.render_views(str(p/f'review/hand_{side}'),1.04,.22,views=('front','back'),resolution=(700,500),target=(x,-.10))
reports=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 boundary=[e for e in bm.edges if e.is_boundary];remaining=set(boundary);loops=[]
 while remaining:
  queue=[next(iter(remaining))];component=set()
  while queue:
   e=queue.pop()
   if e not in remaining:continue
   remaining.remove(e);component.add(e)
   queue.extend(q for v in e.verts for q in v.link_edges if q in remaining)
  pts=np.array([tuple(v.co) for e in component for v in e.verts])
  loops.append({'edges':len(component),'centre':pts.mean(0).tolist(),'lo':pts.min(0).tolist(),'hi':pts.max(0).tolist()})
 reports.append({'part':o.name,'volume':bm.calc_volume(signed=True),'boundary_loops':loops})
 bm.free()
(p/'work/geometry_boundaries.json').write_text(json.dumps(reports,indent=2)+'\n')
