"""Project simplified surfaces back onto the corresponding original piece before evaluating a distance LOD."""
import bpy,numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1]
AXES=[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
def project(obj,minimum=1e-6):
 with bpy.data.libraries.load(str(P/'work/reduction_master.blend'),link=False)as(src,dst):dst.objects=[obj.name]
 high=dst.objects[0];m=high.data;m.calc_loop_triangles();co=[v.co.copy()for v in m.vertices];part=[x.value for x in m.attributes['piece'].data]if 'piece'in m.attributes else[0]*len(co);groups={g.index:g.name for g in high.vertex_groups};weights=[{groups[g.group]:g.weight for g in v.groups if groups[g.group]in bpy.data.objects['Rig'].data.bones}for v in m.vertices];lowpart=[x.value for x in obj.data.attributes['piece'].data]if 'piece'in obj.data.attributes else[0]*len(obj.data.vertices);trees={}
 for pid in set(lowpart):
  ts=[t for t in m.loop_triangles if Counter(part[i]for i in t.vertices).most_common(1)[0][0]==pid];assert ts,pid;trees[pid]=(BVHTree.FromPolygons(co,[tuple(t.vertices)for t in ts],all_triangles=True),ts)
 worst=0.
 for v,pid in zip(obj.data.vertices,lowpart):
  tree,ts=trees[pid];loc,n,fi,d=tree.find_nearest(v.co);assert loc is not None;worst=max(worst,d)
  if d<minimum:continue
  t=ts[fi];w=barycentric_transform(loc,*[co[i]for i in t.vertices],*AXES);skin={}
  for i,q in zip(t.vertices,w):
   for name,value in weights[i].items():skin[name]=skin.get(name,0)+max(0,q)*value
  skin=sorted(skin.items(),key=lambda kv:-kv[1])[:4];total=sum(x[1]for x in skin);assert total>0
  for g in list(v.groups):
   if obj.vertex_groups[g.group].name!='_reduction_protect':obj.vertex_groups[g.group].remove([v.index])
  for name,value in skin:(obj.vertex_groups.get(name)or obj.vertex_groups.new(name=name)).add([v.index],value/total,'REPLACE')
  v.co=loc
 obj.data.update();bpy.data.objects.remove(high,do_unlink=True);return worst
