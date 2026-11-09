"""Nearest-surface texture rebake; avoids ray cages leaking across the layered feather trim."""
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def project(target,source,tags,N):
 src=source.data;dst=target.data;src.calc_loop_triangles();dst.calc_loop_triangles();S=np.array([tuple(v.co)for v in src.vertices]);D=np.array([tuple(v.co)for v in dst.vertices]);su=src.uv_layers.active.data;du=dst.uv_layers.active.data;results={}
 for mat,tag in enumerate(tags):
  tris=[t for t in src.loop_triangles if t.material_index==mat];ids=np.array([t.vertices[:]for t in tris]);uv=np.array([[tuple(su[l].uv)for l in t.loops]for t in tris]);tree=BVHTree.FromPolygons([Vector(v)for v in S],ids.tolist(),all_triangles=True);positions=np.zeros((N,N,3),np.float32);valid=np.zeros((N,N),bool);piece_image=np.zeros((N,N),np.int32);srcpieces=np.array([a.value for a in src.attributes['piece'].data])if 'piece'in src.attributes else np.zeros(len(src.vertices),int);dstpieces=np.array([a.value for a in dst.attributes['piece'].data])if 'piece'in dst.attributes else np.zeros(len(dst.vertices),int);tri_parts=srcpieces[ids[:,0]];part_faces={int(k):np.where(tri_parts==k)[0]for k in np.unique(tri_parts)};trees={k:BVHTree.FromPolygons([Vector(v)for v in S],ids[ix].tolist(),all_triangles=True)for k,ix in part_faces.items()}
  for t in dst.loop_triangles:
   if t.material_index!=mat:continue
   q=np.array([tuple(du[l].uv)for l in t.loops])*N;lo=np.maximum(0,np.floor(q.min(0)).astype(int));hi=np.minimum(N-1,np.ceil(q.max(0)).astype(int))
   if (lo>hi).any():continue
   xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=q;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
   if abs(den)<1e-10:continue
   u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v;m=(u>=0)&(v>=0)&(w>=0);x=(xx[m]-.5).astype(int);y=(yy[m]-.5).astype(int);pos=u[m,None]*D[t.vertices[0]]+v[m,None]*D[t.vertices[1]]+w[m,None]*D[t.vertices[2]];positions[y,x]=pos;valid[y,x]=True;piece_image[y,x]=dstpieces[t.vertices[0]]
  yy,xx=np.where(valid);hits=[]
  for pos,pp in zip(positions[yy,xx],piece_image[yy,xx]):
   assert int(pp)in trees,pp
   hit,n,idx,dist=trees[int(pp)].find_nearest(Vector(pos));hits.append((hit,n,int(part_faces[int(pp)][idx]),dist))
  points=np.array([h[0]for h in hits]);face=np.array([h[2]for h in hits]);abc=S[ids[face]];v0=abc[:,1]-abc[:,0];v1=abc[:,2]-abc[:,0];v2=points-abc[:,0];dot=lambda a,b:np.einsum('ij,ij->i',a,b);d00=dot(v0,v0);d01=dot(v0,v1);d11=dot(v1,v1);d20=dot(v2,v0);d21=dot(v2,v1);den=np.maximum(d00*d11-d01*d01,1e-20);v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;coords=(1-v-w)[:,None]*uv[face,0]+v[:,None]*uv[face,1]+w[:,None]*uv[face,2]
  # Dilation is performed on the newly unwrapped atlas, without borrowing colours across source layers.
  lookup=np.zeros((N,N,2),np.float32);lookup[yy,xx]=coords;mask=valid.copy()
  for _ in range(8):
   old=mask.copy()
   for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
    adj=np.roll(old,(dy,dx),(0,1));fill=adj&~mask;lookup[fill]=np.roll(lookup,(dy,dx),(0,1))[fill];mask[fill]=True
  oy,ox=np.where(mask);coords=lookup[oy,ox];maps={}
  for channel in ['basecolor','metal_rough','region_mask']:
   path=P/f'textures/{tag}_{channel}{"_1k"if channel!="region_mask"else""}.png';out=np.zeros((N,N,4),np.float32);out[:,:,3]=1
   if path.exists():
    im=bpy.data.images.load(str(path),check_existing=True);im.colorspace_settings.name='sRGB'if channel=='basecolor'else'Non-Color';im.alpha_mode='CHANNEL_PACKED';width,height=im.size;a=np.empty(width*height*4,np.float32);im.pixels.foreach_get(a);a=a.reshape(height,width,4);xy=np.clip(coords,0,1)*[width,height]-.5;x0=np.floor(xy[:,0]).astype(int);y0=np.floor(xy[:,1]).astype(int);fx=xy[:,0]-x0;fy=xy[:,1]-y0;x1=np.clip(x0+1,0,width-1);y1=np.clip(y0+1,0,height-1);x0=np.clip(x0,0,width-1);y0=np.clip(y0,0,height-1);col=a[y0,x0]*(1-fx[:,None])*(1-fy[:,None])+a[y0,x1]*fx[:,None]*(1-fy[:,None])+a[y1,x0]*(1-fx[:,None])*fy[:,None]+a[y1,x1]*fx[:,None]*fy[:,None];out[oy,ox,:3]=col[:,:3]
   maps[channel]=out
  results[mat]=maps;assert valid.sum()>100;print('PROJECT',tag,'texels',int(valid.sum()),'max distance',max(h[3]for h in hits),flush=True)
 return results
