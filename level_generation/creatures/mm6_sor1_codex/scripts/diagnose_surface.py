import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/robe_v5.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;pv=np.array([a.value for a in me.attributes['piece'].data])
for piece in [2,5,101,102]:
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if pv[v.index]!=piece],context='VERTS')
 print('PIECE',piece,'volume',bm.calc_volume(signed=True),'boundary_edges',sum(e.is_boundary for e in bm.edges))
 adj={}
 for e in bm.edges:
  if e.is_boundary:
   a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 seen=set()
 for v in adj:
  if v in seen:continue
  stack=[v];group=[]
  while stack:
   a=stack.pop()
   if a in seen:continue
   seen.add(a);group.append(a);stack+=adj[a]
  co=np.array([v.co[:] for v in group]);print('BOUNDARY',piece,len(group),'lo',co.min(0).tolist(),'hi',co.max(0).tolist())
 bm.free()
for role,f,vi in [('Standing',0,2226),('Cast',12,2226),('Death',2,2221)]:
 a=bpy.data.actions[role];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 bpy.context.scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();V=[v.co.copy() for v in em.vertices];faces=[tuple(x.vertices) for x in em.polygons if all(pv[i] in [101,102] for i in x.vertices)];tree=BVHTree.FromPolygons(V,faces);loc,n,fi,d=tree.find_nearest(V[vi]);print('CONTACT',role,f,'clothvi',vi,'rest',me.vertices[vi].co[:],'posed',V[vi][:],'hit',loc[:],'normal',n[:],'dist',d,'shoevi',faces[fi])
 # Independent parity rays determine whether this point is actually inside either closed shoe.
 from mathutils import Vector
 for ray in [Vector((1,.071,.032)).normalized(),Vector((.033,1,.082)).normalized()]:
  hits=0;start=V[vi].copy()
  for _ in range(20):
   q,nn,ii,dd=tree.ray_cast(start,ray,2)
   if q is None:break
   hits+=1;start=q+ray*.00001
  print('PARITY',hits)
 ev.to_mesh_clear()
