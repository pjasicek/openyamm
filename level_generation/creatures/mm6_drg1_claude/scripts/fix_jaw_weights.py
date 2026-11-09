import bpy,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/graft_uv.blend'));o=bpy.data.objects['Body'];me=o.data;co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);ids=sorted({i for f in me.polygons if f.material_index==1 for i in f.vertices});weights={}
for i in ids:
 x,y,z=(co[i]-np.array([0,-.35,.52]))/.35
 jaw=y<-.08 and .23<z<.58+.55*y
 h=float(np.clip((z-.07)/.35,0,1));weights[i]={'Jaw':1.} if jaw else {'Neck3':1-h,'Head':h}
main=[i for i in ids if pa[i]==100];tree=kdtree.KDTree(len(main))
for i in main:tree.insert(Vector(co[i]),i)
tree.balance()
for part in sorted(set(pa[ids])):
 if part==100:continue
 group=[i for i in ids if pa[i]==part];anchor=min((tree.find(Vector(co[i])) for i in group),key=lambda q:q[2])[1]
 for i in group:weights[i]={'Jaw':1.} if part==101 else weights[anchor]
for g in o.vertex_groups:g.remove(ids)
for i,w in weights.items():
 for n,v in w.items():
  if v>1e-6:o.vertex_groups[n].add([i],v,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/graft_uv.blend'))
