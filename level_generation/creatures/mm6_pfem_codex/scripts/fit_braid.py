"""Let the braid follow the neck/back below its head attachment."""
import bpy,sys,runpy
from pathlib import Path
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
o=bpy.data.objects['Body'];m=o.data
pieces=[x.value for x in m.attributes['piece'].data]
faces=[tuple(f.vertices) for f in m.polygons if all(pieces[i] in (0,1) for i in f.vertices)]
tree=BVHTree.FromPolygons([v.co for v in m.vertices],faces)
head=o.vertex_groups['B_Head']
for v in m.vertices:
 if pieces[v.index]!=19:continue
 t=max(0.,min(1.,(1.45-v.co.z)/.065));t=t*t*(3-2*t)
 loc,no,fi,d=tree.find_nearest(v.co)
 tri=faces[fi];weights={}
 for i in tri:
  for g in m.vertices[i].groups:weights[g.group]=weights.get(g.group,0.)+g.weight*t/len(tri)
 weights[head.index]=weights.get(head.index,0.)+1-t
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 weights=dict(sorted(weights.items(),key=lambda x:-x[1])[:4]);total=sum(weights.values())
 for g,w in weights.items():
  if w>1e-6:o.vertex_groups[g].add([v.index],w/total,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured_uv.blend'))
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
