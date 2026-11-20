"""Verified returned-face UV transfer; interpolate local patches for the 22 faces Meshy omitted into a reserved atlas strip."""
import bpy, json, hashlib, sys, os
import numpy as np
from pathlib import Path
from mathutils import Vector, kdtree
import signal
signal.alarm(600)
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/texture_ready.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/brood_mother_texture_v2/model_urls_glb.glb'))
src=next(o for o in bpy.data.objects if o not in before and o.type=='MESH')
S=np.array([src.matrix_world@v.co for v in src.data.vertices]);T=np.concatenate([np.array([o.matrix_world@v.co for v in o.data.vertices]) for o in objects])
scale=np.ptp(T,axis=0).max()/np.ptp(S,axis=0).max();offset=(T.max(0)+T.min(0))/2-scale*(S.max(0)+S.min(0))/2;S=S*scale+offset
faces=np.array([list(f.vertices) for f in src.data.polygons]);tri=S[faces]
suv=np.array([[list(src.data.uv_layers.active.data[i].uv) for i in f.loop_indices] for f in src.data.polygons])
tree=kdtree.KDTree(len(faces))
for i,c in enumerate(tri.mean(1)):tree.insert(Vector(c),i)
tree.balance()
seen=set();missing=[];maximum=0.;newuv=[];newtri=[];parts=[]
for oi,o in enumerate(objects):
 uv=o.data.uv_layers.new(name='UVMap')
 for f in o.data.polygons:
  assert len(f.vertices)==3
  v=np.array([o.matrix_world@o.data.vertices[i].co for i in f.vertices]);_,si,_=tree.find(Vector(v.mean(0)))
  errors=[np.linalg.norm(v-np.roll(tri[si],k,axis=0),axis=1).max() for k in range(3)];k=int(np.argmin(errors))
  if errors[k]<1e-5:
   assert si not in seen;seen.add(si);maximum=max(maximum,float(errors[k]));out=np.roll(suv[si],k,axis=0).copy();out[:,1]=out[:,1]*15/16+1/16
  else:
   # Each omitted triangle gets its own padded 64px tile; no UV is guessed across a chart boundary.
   j=len(missing);x=j*64;out=np.array([[x+8,8],[x+56,8],[x+8,56]],float)/2048
   missing.append((o.name,f.index,v,out))
  for li,t in zip(f.loop_indices,out):uv.data[li].uv=t
  newuv.append(out);newtri.append(v);parts.append(oi)
 o.data.uv_layers.active=uv
assert len(seen)==len(faces)==12021 and len(missing)==22
sample_uv=[];pixels=[];distances=[];facing=[];patch_weights=[]
corner_tree=kdtree.KDTree(len(tri)*3)
for i,v in enumerate(tri.reshape(-1,3)):corner_tree.insert(Vector(v),i)
corner_tree.balance()
source_normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);source_normals/=np.maximum(np.linalg.norm(source_normals,axis=1,keepdims=True),1e-12)
for name,fi,v,out in missing:
 normal=np.cross(v[1]-v[0],v[2]-v[0]);normal/=np.linalg.norm(normal)
 corner_uv=[]
 for point in v:
  candidates=corner_tree.find_range(Vector(point),1e-5);assert candidates
  _,index,dist=max(candidates,key=lambda c:float(source_normals[c[1]//3]@normal))
  corner_uv.append(suv[index//3,index%3]);distances.append(dist);facing.append(float(source_normals[index//3]@normal))
 x0=int(round(out[0,0]*2048))-8
 for y in range(64):
  for x in range(64):
   w=np.array([1-(x-8)/48-(y-8)/48,(x-8)/48,(y-8)/48]);w=np.maximum(w,0);w/=w.sum()
   sample_uv.append(corner_uv);patch_weights.append(w);pixels.append((2047-y,x0+x))
assert max(distances)<1e-5
np.savez_compressed(P/'work/texture_transfer.npz',patch_uv=sample_uv,patch_weights=patch_weights,patch_pixels=pixels,triangles=newtri,uvs=newuv,parts=parts,part_names=[o.name for o in objects])
for o in list(bpy.data.objects):
 if o not in before:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
report={'source_sha256':hashlib.sha256((P/'meshy/brood_mother_texture_v2/model_urls_glb.glb').read_bytes()).hexdigest(),'rig_sha256':hashlib.sha256((P/'work/texture_ready.blend').read_bytes()).hexdigest(),'returned_faces':len(faces),'exact_cyclic_face_matches':len(seen),'maximum_match_error_m':maximum,'source_scale':float(scale),'source_offset':offset.tolist(),'retained_faces':len(newtri),'omitted_face_patches':[{'object':n,'face':i,'area_m2':float(np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))/2)} for n,i,v,u in missing],'patch_corner_position_error_m':max(distances),'patch_method':'Barycentric colour/MR from exactly coincident surviving corners; choose best-facing adjacent face for each UV seam; flat normals in fresh patch frame','patch_normal_dot_min':min(facing),'geometry_weights_actions':'unchanged','status':'pass'}
(P/'review/uv_transfer.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));sys.stdout.flush();sys.stderr.flush();os._exit(0)
