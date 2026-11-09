import bpy, numpy as np, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
pieces=np.array([x.value for x in o.data.attributes['piece'].data])
print('BRAID',[(i,tuple(o.data.vertices[i].co),[(o.vertex_groups[g.group].name,round(g.weight,3)) for g in o.data.vertices[i].groups]) for i in np.flatnonzero(pieces==19)[::35]])
faces=[tuple(f.vertices) for f in o.data.polygons if all(pieces[i]==1 for i in f.vertices)]
for name,f in [('Standing',0),('Death',71)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(f)
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();V=np.array([tuple(v.co) for v in m.vertices]);tree=BVHTree.FromPolygons(V.tolist(),faces);bad=[]
 for i in np.flatnonzero(pieces==19):
  co,n,_,d=tree.find_nearest(Vector(V[i]));signed=(Vector(V[i])-co).dot(n)
  if signed<0:bad.append([int(i),round(signed,4),d,tuple(o.data.vertices[i].co)])
 print(name,'BRAID INTERNAL',len(bad),sorted(bad,key=lambda x:x[1])[:8])
 ev.to_mesh_clear()
