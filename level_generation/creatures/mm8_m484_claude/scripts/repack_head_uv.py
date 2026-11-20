"""Separate overlapping head triangles, repack without rotation, and retain an exact texture lookup."""
import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured_uv_original.blend'));o=bpy.data.objects['Body'];me=o.data
hd=np.array([a.value for a in me.attributes['head'].data]);me.calc_loop_triangles();uv=me.uv_layers['HeadUV'];old=np.array([x.uv[:] for x in uv.data]);tris=[t for t in me.loop_triangles if hd[t.polygon_index]]
def pixels(q,N):
 a,b,c=q*N;den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);assert abs(den)>1e-8
 lo=np.maximum(np.floor(q.min(0)*N).astype(int),0);hi=np.minimum(np.ceil(q.max(0)*N).astype(int),N-1)
 x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
 w1=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/den;w2=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/den
 m=(w1>.001)&(w2>.001)&(w1+w2<.999)
 return (y[m]-.5).astype(int),(x[m]-.5).astype(int),np.stack([1-w1[m]-w2[m],w1[m],w2[m]],-1)
owner=np.full((1024,1024),-1);split=set()
for t in tris:
 iy,ix,w=pixels(old[list(t.loops)],1024)
 if np.any(owner[iy,ix]>=0):split.add(t.polygon_index)
 else:owner[iy,ix]=t.polygon_index
for rank,i in enumerate(sorted(split)):
 for li in me.polygons[i].loop_indices:
  uv.data[li].uv.x+=2+(rank%32)*1.1;uv.data[li].uv.y+=2+(rank//32)*1.1
# Pack an isolated head with physical UV seam splits; preserve the authoritative mesh topology.
faces=[f for f in me.polygons if hd[f.index]];vertices=[];indices=[];keys={};uv_faces=[]
for face in faces:
 ids=[];values=[]
 for vi,li in zip(face.vertices,face.loop_indices):
  value=tuple(uv.data[li].uv);key=(vi,*value)
  if key not in keys:keys[key]=len(vertices);vertices.append(tuple(me.vertices[vi].co))
  ids.append(keys[key]);values.append(value)
 indices.append(ids);uv_faces.append(values)
tm=bpy.data.meshes.new('UVPacking');tm.from_pydata(vertices,[],indices);to=bpy.data.objects.new('UVPacking',tm);bpy.context.collection.objects.link(to);tu=tm.uv_layers.new(name='HeadUV')
for face,values in zip(tm.polygons,uv_faces):
 for li,value in zip(face.loop_indices,values):tu.data[li].uv=value
for ob in bpy.data.objects:ob.select_set(ob==to)
bpy.context.view_layer.objects.active=to;bpy.context.tool_settings.use_uv_select_sync=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=False,margin=.002,margin_method='FRACTION',udim_source='ACTIVE_UDIM');bpy.ops.object.mode_set(mode='OBJECT')
for face,source in zip(faces,tm.polygons):
 for li,si in zip(face.loop_indices,source.loop_indices):uv.data[li].uv=tm.uv_layers['HeadUV'].data[si].uv
bpy.data.objects.remove(to,do_unlink=True);bpy.data.meshes.remove(tm);o.select_set(True);bpy.context.view_layer.objects.active=o
uv=me.uv_layers['HeadUV'];new=np.array([x.uv[:] for x in uv.data]);print('UV_BOUNDS',new.min(0),new.max(0),old.min(0),old.max(0));me.calc_loop_triangles();N=2048
lookup=np.zeros((N,N,2),np.float32);coverage=np.zeros((N,N),bool)
for t in me.loop_triangles:
 if not hd[t.polygon_index]:continue
 ids=list(t.loops);iy,ix,w=pixels(new[ids],N);lookup[N-1-iy,ix]=w@old[ids];coverage[N-1-iy,ix]=True
np.savez_compressed(P/'work/head_uv_lookup.npz',uv=lookup,coverage=coverage)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_textured_uv.blend'))
(P/'review/head_uv_repack.json').write_text(json.dumps({'split_triangles':len(split),'rotation':False,'pixels':N,'geometry_changed':False},indent=1));print('REPACK',len(split),'triangles')
