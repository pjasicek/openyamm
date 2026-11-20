import bpy,numpy as np,json
from pathlib import Path
from collections import Counter
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));m=bpy.data.objects['Body'].data;co=[v.co.copy()for v in m.vertices];pv=[x.value for x in m.attributes['piece'].data];f=[tuple(p.vertices)for p in m.polygons if Counter(pv[i]for i in p.vertices).most_common(1)[0][0]==12];tree=BVHTree.FromPolygons(co,f);ids=sorted(set(i for fc in f for i in fc));print('HIGH BELT',np.array(co)[ids].min(0),np.array(co)[ids].max(0),len(f),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction/body_lod1_18.blend'));m=bpy.data.objects['Body'].data;pv=[x.value for x in m.attributes['piece'].data];rows=[]
for f in m.polygons:
 if Counter(pv[i]for i in f.vertices).most_common(1)[0][0]!=12:continue
 for i in f.vertices:
  p=m.vertices[i].co;loc,n,fi,d=tree.find_nearest(p);rows.append([d,i,p[:],loc[:],tuple(pv[j]for j in f.vertices)])
print('LOW BELT WORST',sorted(rows,reverse=True)[:15],flush=True)
