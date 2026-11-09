"""Separate skin from overlapping feather UVs; fill only contaminated skin samples from nearby skin."""
import numpy as np,copy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from PIL import Image

def make_skin_donors(project):
 points=[];colors=[]
 for mat in range(2):
  r=np.load(project/f'work/round2_raster_0_{mat}.npz');take=r['piece']==0;im=np.array(Image.open(project/f'export/textures_lod0/body/{mat}_basecolor.png').convert('RGBA'),float)/255
  points.append(r['pos'][take][::2]);colors.append(im[take][::2,:3])
 c=np.concatenate(colors);c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
 return cKDTree(np.concatenate(points)),c

def skin_faces(co,faces):
 # UV seams duplicate vertices. Weld positions solely for component identification.
 _,ids=np.unique(np.round(co,5),axis=0,return_inverse=True);f=ids[faces];a=np.r_[f[:,0],f[:,1],f[:,2]];b=np.r_[f[:,1],f[:,2],f[:,0]];n=int(ids.max()+1)
 _,labels=connected_components(coo_matrix((np.ones(len(a)),(a,b)),shape=(n,n)),directed=False)
 tag=np.bincount(labels[ids]).argmax();return labels[f[:,0]]==tag

def repair_skin_layer(source,original,uv,faces,co,donors):
 w,h=source['size'];pos=np.zeros((h,w,3),np.float32);valid=np.zeros((h,w),bool)
 for f in faces:
  tri=uv[f]*[w,h];lo=np.maximum(0,np.floor(tri.min(0)).astype(int));hi=np.minimum([w-1,h-1],np.ceil(tri.max(0)).astype(int));xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=tri;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-12:continue
  w0=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/den;w1=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den;w2=1-w0-w1;take=(w0>=0)&(w1>=0)&(w2>=0);xx=(xs[take]-.5).astype(int);yy=(ys[take]-.5).astype(int);valid[yy,xx]=True;pos[yy,xx]=w0[take,None]*co[f[0]]+w1[take,None]*co[f[1]]+w2[take,None]*co[f[2]]
 keys=list(source['maps']);base,orm,normal,mask=keys;bad=valid&(original['maps'][mask][...,1]<254)
 tree,colors=donors
 if bad.any():
  dist,ids=tree.query(pos[bad],k=32,workers=4);weight=1/(dist+.004)**2;c=(colors[ids]*weight[...,None]).sum(1)/weight.sum(1)[:,None];c=np.where(c<=.0031308,c*12.92,1.055*c**(1/2.4)-.055)
  source['maps'][base][bad]=np.c_[np.uint8(np.clip(c*255+.5,0,255)),np.full(bad.sum(),255,np.uint8)];source['maps'][orm][bad]=[19,199,0,255];source['maps'][normal][bad]=[128,128,255,255]
 source['maps'][mask][:]=[0,255,0,255]
 return {'skin_pixels':int(valid.sum()),'overlapping_or_unclassified_pixels_repaired':int(bad.sum())}
