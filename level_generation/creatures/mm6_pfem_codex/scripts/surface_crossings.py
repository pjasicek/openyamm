"""Locate actual triangle-edge crossings, avoiding ambiguous signed distances on an open, pleated dress."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene;m=o.data
pv=np.array([x.value for x in m.attributes['piece'].data]);R=np.array([tuple(v.co) for v in m.vertices])
faces={n:[tuple(f.vertices) for f in m.polygons if all(pv[i] in parts for i in f.vertices)] for n,parts in [('cloth',[100]),('neck',[1])]}
edges={n:[tuple(e.vertices) for e in m.edges if all(pv[i] in parts for i in e.vertices) and (n!='braid' or all(R[i,2]<1.445 for i in e.vertices))] for n,parts in [('arms',[3,4,9,11]),('braid',[19])]}
report={}
for name in ('Standing','Walking','Hit','Death','Fidget'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];out={}
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();V=[v.co.copy() for v in mm.vertices];ev.to_mesh_clear()
  for part,target in [('arms','cloth'),('braid','neck')]:
   tree=BVHTree.FromPolygons(V,faces[target]);hits=[]
   for i,j in edges[part]:
    d=V[j]-V[i];length=d.length
    if length<.001:continue
    d.normalize();loc,n,fi,dist=tree.ray_cast(V[i]+d*.0003,d,length-.0006)
    if loc is not None:hits.append({'edge':[i,j],'position':list(loc)})
   if hits and (part not in out or len(hits)>out[part]['crossings']):out[part]={'frame':float(f),'crossings':len(hits),'hits':hits[:10]}
 report[name]=out;print(name,out)
(p/'work/surface_crossings.json').write_text(json.dumps(report,indent=2))
