"""Repair collapsed UV triangles from the small shoulder-boundary projection without changing geometry."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];report={}
for file in ['rig_uv','rig_complete','animated']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{file}.blend'));count=0
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.data.uv_layers.active]:
  me=o.data;uv=me.uv_layers.active.data
  def area(f):
   a,b,c=[uv[i].uv for i in f.loop_indices];return abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))
  good=[f for f in me.polygons if len(f.vertices)==3 and area(f)>1e-10]
  for f in me.polygons:
   if len(f.vertices)!=3 or area(f)>1e-10:continue
   center=sum((me.vertices[i].co for i in f.vertices),Vector())/3
   candidates=[g for g in good if g.material_index==f.material_index]
   nearest=min(candidates,key=lambda g:(sum((me.vertices[i].co for i in g.vertices),Vector())/3-center).length_squared)
   for li,sl in zip(f.loop_indices,nearest.loop_indices):uv[li].uv=uv[sl].uv
   assert area(f)>1e-10;count+=1
 report[file]=count;bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{file}.blend'))
(P/'work/uv_projection_repair.json').write_text(json.dumps(report,indent=2));print('UV_REPAIR',report,flush=True)
