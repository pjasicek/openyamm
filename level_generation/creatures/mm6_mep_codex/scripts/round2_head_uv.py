import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];reports=[]
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round2_sash_lod{level}.blend'));b=bpy.data.objects['Body'];me=b.data
 original_uv=np.array([a.uv[:] for a in me.uv_layers['MergedUV'].data]);target=np.array([v.co[:] for v in me.vertices]);faces=[f for f in me.polygons if 'Head' in me.materials[f.material_index].name];ids=sorted({i for f in faces for i in f.vertices})
 existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy/head_retexture_round2_uv/model_urls_glb.glb'))
 src=max((o for o in bpy.data.objects if o not in existing and o.type=='MESH'),key=lambda o:len(o.data.polygons));src.data.calc_loop_triangles();sm=src.data;uv=sm.uv_layers.active.data
 points=np.array([src.matrix_world@v.co for v in sm.vertices]);sub=target[ids]
 if level==0:
  scale=np.ptp(sub,axis=0).max()/np.ptp(points,axis=0).max();shift=(sub.min(0)+sub.max(0))/2-(points.min(0)+points.max(0))*scale/2
 points=points*scale+shift;triangles=list(sm.loop_triangles);tree=kdtree.KDTree(len(triangles))
 for j,t in enumerate(triangles):tree.insert(Vector(points[list(t.vertices)].mean(0)),j)
 tree.balance();outuv=me.uv_layers['MergedUV'].data;maximum=0.
 for f in faces:
  center=Vector(target[list(f.vertices)].mean(0));_,j,dist=tree.find(center);t=triangles[j];a,bb,c=[Vector(points[i]) for i in t.vertices];tex=[Vector((*uv[i].uv,0)) for i in t.loops]
  for li,vi in zip(f.loop_indices,f.vertices):
   point=Vector(target[vi]);bary=barycentric_transform(point,a,bb,c,*tex);outuv[li].uv=bary.xy
  maximum=max(maximum,dist)
 for o in list(bpy.data.objects):
  if o not in existing:bpy.data.objects.remove(o,do_unlink=True)
 # Keep the face, ears and neck in one continuous cylindrical chart; the seam is behind the head.
 cloth_faces=set();source_uv=np.array([x.uv[:] for x in outuv]);pv=np.array([a.value for a in me.attributes['piece'].data])
 if level==0:
  cap_polys=[f for f in faces if pv[f.vertices[0]]==4];cap_points=target.copy();cap_tex=original_uv.copy();cap_tree=kdtree.KDTree(len(cap_polys));cap_indices=[list(f.vertices) for f in cap_polys];cap_loops=[list(f.loop_indices) for f in cap_polys]
  for j,ids in enumerate(cap_indices):cap_tree.insert(Vector(cap_points[ids].mean(0)),j)
  cap_tree.balance()
 for f in faces:
  part=int(pv[f.vertices[0]]);xyz=target[list(f.vertices)]
  center=xyz.mean(0);cloth=part==0 and (center[1]>.065 or (center[2]<1.49 and abs(center[0])>.055) or (center[2]<1.43 and center[1]>-.035) or (center[2]<1.60 and abs(center[0]+.004)>.073) or (center[2]<1.52 and center[1]>.035))
  if cloth:cloth_faces.add(f.index)
  if part==0 and not cloth:
   u=(np.arctan2(xyz[:,0]+.004,-(xyz[:,1]-.015))+np.pi)/(2*np.pi)
   if np.ptp(u)>.5:u[u<.5]+=1
   coords=np.column_stack([.02+.68*np.clip(u,0,1),.02+.96*np.clip((xyz[:,2]-1.29)/.325,0,1)])
  elif part==4:
   if level==0:ctex=original_uv[list(f.loop_indices)]
   else:
    _,j,_=cap_tree.find(Vector(xyz.mean(0)));a,bb,c=[Vector(cap_points[i]) for i in cap_indices[j]];tex=[Vector((*cap_tex[i],0)) for i in cap_loops[j]];ctex=np.array([barycentric_transform(Vector(point),a,bb,c,*tex).xy for point in xyz])
   source_uv[list(f.loop_indices)]=ctex;coords=np.clip(ctex,0,1)*np.array([.23,.60])+np.array([.75,.02])
  elif cloth:coords=np.clip(source_uv[list(f.loop_indices)],0,1)*np.array([.23,.16])+np.array([.75,.64])
  elif part in [12,13]:
   cx=.0196 if part==12 else -.02706;coords=np.column_stack([(.76 if part==12 else .88)+.10*np.clip((xyz[:,0]-cx)/.024+.5,0,1),.82+.16*np.clip((xyz[:,2]-1.5563)/.028+.5,0,1)])
  else:raise AssertionError(('head piece',part))
  for li,co in zip(f.loop_indices,coords):outuv[li].uv=co
 # Rasterise this exact UV layout for semantic grading and padding; geometry is unchanged.
 N=1024;piece=np.full((N,N),-1,np.int16);pos=np.zeros((N,N,3),np.float32);source_coords=np.zeros((N,N,2),np.float32);cloth_pixels=np.zeros((N,N),bool);pv=np.array([a.value for a in me.attributes['piece'].data]);me.calc_loop_triangles()
 for t in me.loop_triangles:
  if 'Head' not in me.materials[t.material_index].name:continue
  xy=np.array([outuv[i].uv[:] for i in t.loops])*N;v=target[list(t.vertices)];a,bb,c=xy;den=(bb[1]-c[1])*(a[0]-c[0])+(c[0]-bb[0])*(a[1]-c[1])
  if abs(den)<1e-9:continue
  lo=np.maximum(0,np.floor(xy.min(0)).astype(int));hi=np.minimum(N-1,np.ceil(xy.max(0)).astype(int));xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
  w0=((bb[1]-c[1])*(xs-c[0])+(c[0]-bb[0])*(ys-c[1]))/den;w1=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den;w2=1-w0-w1;m=(w0>=0)&(w1>=0)&(w2>=0);iy=(N-ys[m]-.5).astype(int);ix=(xs[m]-.5).astype(int);piece[iy,ix]=pv[t.vertices[0]];cloth_pixels[iy,ix]=t.polygon_index in cloth_faces;pos[iy,ix]=w0[m,None]*v[0]+w1[m,None]*v[1]+w2[m,None]*v[2];su=source_uv[list(t.loops)];source_coords[iy,ix]=w0[m,None]*su[0]+w1[m,None]*su[1]+w2[m,None]*su[2]
 np.savez_compressed(P/f'work/round2_head_lod{level}.npz',piece=piece,pos=pos,source_uv=source_coords,cloth=cloth_pixels)
 reports.append({'lod':level,'head_triangles':sum(len(f.vertices)-2 for f in faces),'max_face_centroid_distance_mm':maximum*1000,'coverage':float((piece>=0).mean())})
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round2_head_lod{level}.blend'))
(P/'review/round2/head_uv_transfer.json').write_text(json.dumps(reports,indent=2));print('HEAD_UV',reports)
