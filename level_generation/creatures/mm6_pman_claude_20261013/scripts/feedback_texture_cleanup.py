"""Remove projected hair/cuff pigment from skin using nearby samples on the same anatomical surface."""
import numpy as np
from scipy.spatial import cKDTree

def clean(part,base,piece,pos,coverage):
 out=base.copy();normal_mask=np.zeros_like(coverage);report={}
 def replace(name,bad,good,weight=None,offset_z=0.):
  bad=bad&coverage;good=good&coverage
  if not bad.any():return
  assert good.sum()>100,(name,int(good.sum()))
  tree=cKDTree(pos[good]);query=pos[bad].copy();query[:,2]+=offset_z;_,idx=tree.query(query,k=4)
  colors=np.mean(base[good][idx],axis=1)
  w=np.ones(bad.sum()) if weight is None else weight[bad]
  out[bad]=out[bad]*(1-w[:,None])+colors*w[:,None];normal_mask[bad]=True;report[name]=int(bad.sum())
 x,y,z=pos[...,0],pos[...,1],pos[...,2]
 if part=='head':
  forehead=(piece==1)&(y<-.025)&(abs(x)<.077)
  replace('forehead_hair_spill',forehead&(z>1.612),forehead&(z>1.593)&(z<1.61)&(base[...,0]>.72),np.clip((z-1.612)/.009,0,1))
 else:
  from scipy.ndimage import gaussian_filter
  # Remove stretched cuff/skin bands from the old collapsed triangles. Retain a restrained fine skin residual.
  fine=base-gaussian_filter(base,sigma=(3,3,0))
  for p in [4,5]:
   skin=(piece==p)&coverage;bad=skin&(z>.915);good=skin&(z>.855)&(z<.92)&(base[...,0]>.65)&(base[...,1]>.40)
   assert good.sum()>30
   colour=np.median(base[good],axis=0);target=colour+np.clip(fine,-.02,.02)*.3
   w=np.clip((z[bad]-.915)/.065,0,1)
   out[bad]=base[bad]*(1-w[:,None])+target[bad]*w[:,None]
   normal_mask[skin&(z>.93)]=True;report['forearm_projection_bands_'+str(p)]=int(bad.sum())
 return out,normal_mask,report
