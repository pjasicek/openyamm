import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));o=bpy.data.objects['Body'];me=o.data;parts=np.array([a.value for a in me.attributes['part'].data]);co=np.array([v.co[:] for v in me.vertices]);uv=me.uv_layers.active.data
basefaces=[list(f.vertices) for f in me.polygons if all(parts[i]==0 for i in f.vertices)];tree=BVHTree.FromPolygons([v.co for v in me.vertices],basefaces)
spikes=[5,6,7,8,9,10,11,12,13,14,15,20,38];report=[];repls=[]
for part in spikes:
 ids=np.flatnonzero(parts==part);a=co[ids];dist=np.array([tree.find_nearest(Vector(x))[3] for x in a]);tip=a[dist.argmax()];near=a[np.argsort(dist)[:max(3,len(ids)//4)]];base=near.mean(0);base=base*.65+np.array(tree.find_nearest(Vector(base))[0])*.35;axis=Vector(tip-base);length=axis.length
 if length<.008:continue
 radii=[.0045,max(.003,length*.14)];radius=min(.017,max(radii));axis.normalize();u=axis.cross(Vector((1,0,0))).normalized();v=axis.cross(u).normalized();vs=[]
 for f,r in [(0,radius),(.46,radius*.65)]:
  center=Vector(base)+axis*(length*f)
  for k in range(8):vs.append(center+r*(math.cos(k*math.tau/8)*u+math.sin(k*math.tau/8)*v))
 vs.append(Vector(tip));faces=[]
 for k in range(8):
  j=(k+1)%8;faces.extend([(k,j,8+j),(k,8+j,8+k),(8+k,8+j,16)])
 faces.append(tuple(reversed(range(8))))
 oldfaces=[f for f in me.polygons if all(parts[i]==part for i in f.vertices)];uvs=np.array([uv[li].uv[:] for f in oldfaces for li in f.loop_indices]);lo=uvs.min(0);hi=uvs.max(0);centeruv=(lo+hi)/2
 weights={g.group:g.weight for g in me.vertices[ids[len(ids)//2]].groups};mat=oldfaces[0].material_index
 repls.append((part,vs,faces,lo,hi,weights,mat));report.append({'part':part,'length':length,'base':base.tolist(),'tip':tip.tolist(),'old_triangles':sum(len(f.vertices)-2 for f in oldfaces),'new_triangles':30})
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if parts[v.index] in spikes],context='VERTS');uvlayer=bm.loops.layers.uv.active;partlayer=bm.verts.layers.int.get('part');deform=bm.verts.layers.deform.verify()
for part,vs,faces,lo,hi,weights,mat in repls:
 vv=[bm.verts.new(x) for x in vs]
 for v in vv:
  v[partlayer]=part
  for g,w in weights.items():v[deform][g]=w
 for face in faces:
  f=bm.faces.new([vv[i] for i in face]);f.material_index=mat;f.smooth=True
  for loop,idx in zip(f.loops,face):
   if idx==16:tex=(lo+hi)/2
   else:angle=(idx%8)*math.tau/8;rad=.36 if idx<8 else .18;tex=(lo+hi)/2+(hi-lo)*rad*np.array([math.cos(angle),math.sin(angle)])
   loop[uvlayer].uv=tex
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();me.calc_loop_triangles();assert all(v.groups for v in me.vertices)
(P/'work/spine_repair.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print('REPAIRED',len(report),'SPINES, TOTAL',len(me.loop_triangles))
