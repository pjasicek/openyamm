"""Separate the specific self-overlapping skull UV faces, then validate before retexturing."""
import bpy,bmesh,json,runpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));o=bpy.data.objects['Body'];me=o.data;receipt=[]
def overlaps():
 owner=np.full((1024,1024),-1,np.int32);bad=set();uv=me.uv_layers.active.data
 for f in me.polygons:
  if f.material_index!=1:continue
  p=np.array([uv[i].uv[:] for i in f.loop_indices])*1024;lo=np.maximum(0,np.floor(p.min(0)).astype(int));hi=np.minimum(1023,np.ceil(p.max(0)).astype(int));xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);q=np.stack([xx,yy],-1)-p[0];m=np.column_stack([p[1]-p[0],p[2]-p[0]])
  if abs(np.linalg.det(m))<1e-9:continue
  w=q@np.linalg.inv(m).T;inside=(w[...,0]>1e-4)&(w[...,1]>1e-4)&(w.sum(-1)<.9999);block=owner[lo[1]:hi[1]+1,lo[0]:hi[0]+1];hits=block[inside&(block>=0)]
  if len(hits):bad.add(f.index);bad.update(int(x) for x in hits)
  block[inside]=f.index
 return bad
for attempt in range(4):
 bad=overlaps();print('OVERLAPPING HEAD FACES',len(bad),flush=True)
 if not bad:break
 receipt.append(sorted(bad));uv=me.uv_layers.active.data;world=0.;area=0.
 for f in me.polygons:
  if f.material_index!=1:continue
  a,b,c=[me.vertices[v].co for v in f.vertices];u,v,w=[Vector(uv[i].uv) for i in f.loop_indices];world+=(b-a).cross(c-a).length/2;area+=abs((v-u).cross(w-u))/2
 scale=(area/world)**.5
 for i,fi in enumerate(sorted(bad)):
  f=me.polygons[fi];a,b,c=[me.vertices[v].co for v in f.vertices];u=(b-a).normalized();v=(b-a).cross(c-a).normalized().cross(u);points=[(0,0),((b-a).length*scale,0),((c-a).dot(u)*scale,(c-a).dot(v)*scale)]
  for li,p in zip(f.loop_indices,points):uv[li].uv=(10+i+p[0],10+p[1])
 for ob in bpy.context.scene.objects:ob.select_set(ob==o)
 bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(me)
 for f in bm.faces:f.select_set(f.material_index==1)
 bmesh.update_edit_mesh(me);bpy.ops.uv.pack_islands(margin=.004,rotate=True,shape_method='CONVEX');bpy.ops.object.mode_set(mode='OBJECT')
assert not overlaps(),'Unresolved head UV overlap'
(P/'work/head_uv_detach_receipt.json').write_text(json.dumps({'detached_faces_by_pass':receipt},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
for script in ['uv_gate.py','uv_raster.py','export_head_v2.py']:runpy.run_path(str(P/'scripts'/script),run_name='__main__')
