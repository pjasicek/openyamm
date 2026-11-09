"""Nearest-surface material transfer, restricted to the same garment/anatomy piece."""
from pathlib import Path
import json,numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt, binary_erosion
from PIL import Image
p=Path(__file__).resolve().parents[1];out=p/'textures/round4'
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-20)
def nearest(points,triangles):
 a,b,c=np.moveaxis(triangles,-2,0);ab=b-a;ac=c-a;ap=points-a;d00=(ab*ab).sum(-1);d01=(ab*ac).sum(-1);d11=(ac*ac).sum(-1);d20=(ap*ab).sum(-1);d21=(ap*ac).sum(-1);det=np.maximum(d00*d11-d01*d01,1e-24);u=(d11*d20-d01*d21)/det;v=(d00*d21-d01*d20)/det
 weights=np.stack([1-u-v,u,v],-1);q=(triangles*weights[...,None]).sum(-2);dist=((q-points)**2).sum(-1);dist=np.where((weights>=0).all(-1),dist,np.inf)
 for j,k in [(0,1),(1,2),(2,0)]:
  x=triangles[...,j,:];edge=triangles[...,k,:]-x;t=np.clip(((points-x)*edge).sum(-1)/np.maximum((edge*edge).sum(-1),1e-24),0,1);qq=x+edge*t[...,None];dd=((qq-points)**2).sum(-1);take=dd<dist;w=np.zeros_like(weights);w[...,j]=1-t;w[...,k]=t;weights=np.where(take[...,None],w,weights);dist=np.minimum(dist,dd)
 return weights,dist
# Projection self-checks include a point outside an edge and above the triangle interior.
test=np.array([[[0.,0,0],[1,0,0],[0,1,0]]]*2);w,d=nearest(np.array([[.2,.3,1],[2,0,0]]),test);assert np.allclose(w,[[.5,.2,.3],[0,1,0]]) and np.allclose(d,[1,1])
def normals(v,f):
 n=np.zeros_like(v);x=v[f];cross=np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0])
 for k in range(3):np.add.at(n,f[:,k],cross)
 return unit(n)
def frame(tri,uv,n):
 ab=tri[:,1]-tri[:,0];ac=tri[:,2]-tri[:,0];du=uv[:,1]-uv[:,0];dv=uv[:,2]-uv[:,0];det=du[:,0]*dv[:,1]-du[:,1]*dv[:,0];safe=np.where(abs(det)>1e-12,det,1)
 t=(ab*dv[:,1,None]-ac*du[:,1,None])/safe[:,None];b=(ac*du[:,0,None]-ab*dv[:,0,None])/safe[:,None];t=unit(t-n*(n*t).sum(-1,keepdims=True));cross=unit(np.cross(n,t));sign=np.where((cross*b).sum(-1)<0,-1,1);return t,cross*sign[:,None],n
def main():
 hi=np.load(p/'work/uv_accepted_r4.npz');lo=np.load(p/'work/atlas_uv_r4.npz');r=np.load(p/'work/atlas_raster_r4.npz');owner=r['owner'];face=r['face'];bary=r['bary'];H,W=owner.shape
 hv,hf,hu,hp=[hi[k] for k in ['vertices','faces','uv','part']];lv,lf,lu,lp=[lo[k] for k in ['vertices','faces','uv','part']];hn=normals(hv,hf);ln=normals(lv,lf);hpart=hp[hf[:,0]]
 textures={}
 for material,prefix in [(0,''),(1,'head_')]:
  maps={}
  for channel,suffix in [('basecolor','basecolor_1k'),('normal','normal_1k'),('orm','metal_rough_1k')]:
   a=np.asarray(Image.open(p/'textures'/f'sor1_{prefix}{suffix}.png').convert('RGB'),float)/255
   if channel=='normal':a[:,:,1]=1-a[:,:,1]
   maps[channel]=a[::-1].copy()
  maps['mask']=np.asarray(Image.open(p/'textures/sor1_region_mask.png').convert('RGBA'),float)[::-1]/255 if material==0 else np.zeros((1024,1024,4))
  textures[material]=maps
 
 # Restrict source filtering to the interior of its own UV chart. The old atlas has
 # foreign colours at some island borders; ordinary bilinear lookup transfers those flecks.
 parent=list(range(len(hf)));edges={}
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,(source_face,uv) in enumerate(zip(hf,hu)):
  for k in range(3):
   a,b=sorted([(int(source_face[k]),*np.round(uv[k],5)),(int(source_face[(k+1)%3]),*np.round(uv[(k+1)%3],5))]);key=(int(hi['material'][i]),tuple(a),tuple(b))
   if key in edges:parent[root(i)]=root(edges[key])
   else:edges[key]=i
 chart=np.array([root(i) for i in range(len(hf))]);lookup={}
 for c in np.unique(chart):
  ids=np.where(chart==c)[0];q=hu[ids]*1024;lower=np.maximum(np.floor(q.min((0,1))).astype(int)-2,0);upper=np.minimum(np.ceil(q.max((0,1))).astype(int)+2,1023);width,height=upper-lower+1;coverage=np.zeros((height,width),bool)
  for tri in q-lower:
   low=np.maximum(np.floor(tri.min(0)).astype(int),0);high=np.minimum(np.ceil(tri.max(0)).astype(int),[width-1,height-1]);xx,yy=np.meshgrid(np.arange(low[0],high[0]+1)+.5,np.arange(low[1],high[1]+1)+.5);de=np.stack([xx,yy],-1)-tri[0];ab=tri[1]-tri[0];ac=tri[2]-tri[0];det=ab[0]*ac[1]-ab[1]*ac[0]
   if abs(det)<1e-12:continue
   bb=(de[...,0]*ac[1]-de[...,1]*ac[0])/det;cc=(ab[0]*de[...,1]-ab[1]*de[...,0])/det;coverage[low[1]:high[1]+1,low[0]:high[0]+1]|=(bb>=0)&(cc>=0)&(bb+cc<=1)
  safe=binary_erosion(coverage,iterations=1)
  # Sub-texel islands cannot supply an interior; use their own covered pixels where possible.
  if not safe.any():safe=coverage
  if safe.any():
   nearest_safe=distance_transform_edt(~safe,return_distances=False,return_indices=True);lookup[int(c)]=(lower,nearest_safe)
 def sample(im,uv,source_faces):
  h,w=im.shape[:2];q=np.clip(uv*[w,h]-.5,[0,0],[w-1.00001,h-1.00001]);i=np.floor(q).astype(int);t=q-i;x,y=i.T;tx=t[:,0,None];ty=t[:,1,None];cs=chart[source_faces]
  def corner(dx,dy):
   xx=x+dx;yy=y+dy
   for c in np.unique(cs):
    if int(c) not in lookup:continue
    sel=cs==c;lower,near=lookup[int(c)];lx=np.clip(xx[sel]-lower[0],0,near.shape[2]-1);ly=np.clip(yy[sel]-lower[1],0,near.shape[1]-1);xx[sel]=near[1,ly,lx]+lower[0];yy[sel]=near[0,ly,lx]+lower[1]
   return im[yy,xx]
  return (corner(0,0)*(1-tx)+corner(1,0)*tx)*(1-ty)+(corner(0,1)*(1-tx)+corner(1,1)*tx)*ty
 images={k:np.zeros((H,W,4 if k=='mask' else 3),np.float32) for k in ['basecolor','normal','orm','mask']};maxdist={};yy,xx=np.where(owner>=0);lowfaces=face[yy,xx];parts=lp[lf[lowfaces,0]]
 for pt in sorted(set(parts)):
  selected=np.where(parts==pt)[0];hs=np.where(hpart==pt)[0];tri=hv[hf[hs]];tree=cKDTree(tri.mean(1));maxdistance=0
  for start in range(0,len(selected),8000):
   ids=selected[start:start+8000];y,x=yy[ids],xx[ids];fi=lowfaces[ids];lw=bary[y,x];points=(lv[lf[fi]]*lw[:,:,None]).sum(1);_,near=tree.query(points,k=min(24,len(hs)));near=np.asarray(near).reshape(len(ids),-1);candidate=tri[near];hw,dist=nearest(points[:,None,:],candidate);pick=dist.argmin(1);hw=hw[np.arange(len(ids)),pick];hfi=hs[near[np.arange(len(ids)),pick]];maxdistance=max(maxdistance,float(np.sqrt(dist.min(1).max())));uv=(hu[hfi]*hw[:,:,None]).sum(1)
   materials=hi['material'][hfi]
   for material in set(materials):
    sel=materials==material;maps=textures[int(material)]
    for channel in ['basecolor','orm','mask']:images[channel][y[sel],x[sel]]=sample(maps[channel],uv[sel],hfi[sel])
    tangent_normal=unit(sample(maps['normal'],uv[sel],hfi[sel])*2-1);ns=unit((hn[hf[hfi[sel]]]*hw[sel,:,None]).sum(1));ts,bs,ns=frame(hv[hf[hfi[sel]]],hu[hfi[sel]],ns);world=unit(ts*tangent_normal[:,0,None]+bs*tangent_normal[:,1,None]+ns*tangent_normal[:,2,None]);nl=unit((ln[lf[fi[sel]]]*lw[sel,:,None]).sum(1));tl,bl,nl=frame(lv[lf[fi[sel]]],lu[fi[sel]],nl);n=np.stack([(world*tl).sum(1),(world*bl).sum(1),(world*nl).sum(1)],-1);images['normal'][y[sel],x[sel]]=unit(n)*.5+.5
  maxdist[int(pt)]=maxdistance*1000;print('TRANSFER',int(pt),len(selected),'texels',round(maxdistance*1000,3),'mm',flush=True)
 # Each island has an 18-pixel reserved margin. Fill the entire unused atlas by nearest covered texel,
 # including the mask, so neither bilinear sampling nor the 4x mip footprint can see black/foreign texels.
 nearest_index=distance_transform_edt(owner<0,return_distances=False,return_indices=True)
 for channel,a in images.items():
  a=a[tuple(nearest_index)];pixels=np.clip(np.rint(a[::-1]*255),0,255).astype(np.uint8);Image.fromarray(pixels).save(out/f'sor1_{channel}.png')
 (p/'review/round4/material_transfer.json').write_text(json.dumps({'method':'same-piece nearest original triangle; barycentric source UV lookup and tangent-frame normal transfer','source':'round2 accepted original maps; bilinear samples restricted to one-pixel-eroded source chart interiors','maximum_projection_mm_per_part':maxdist,'dilation':'18-pixel reserved chart margins; nearest coverage extended through all unused texels; mask padded identically','images':4,'dimensions':[W,H]},indent=2))
 print('BAKED FOUR SHARED MAPS',flush=True)

if __name__=='__main__':main()
