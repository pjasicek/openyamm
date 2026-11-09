"""Eight-view silhouette IoU and foreground-window Gaussian SSIM (Wang, C1=.01², C2=.03²)."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter,binary_dilation
ref,candidate,out=map(Path,sys.argv[1:4]);rows=[]
for i in range(8):
 a=np.array(Image.open(ref/f'{i}.png').convert('RGBA'),float)/255;b=np.array(Image.open(candidate/f'{i}.png').convert('RGBA'),float)/255
 assert a.shape==b.shape
 am=a[:,:,3]>.5;bm=b[:,:,3]>.5;union=am|bm;assert union.any()
 iou=(am&bm).sum()/union.sum();soft=np.minimum(a[:,:,3],b[:,:,3]).sum()/np.maximum(a[:,:,3],b[:,:,3]).sum()
 x=a[:,:,:3]*a[:,:,3:4]+.18*(1-a[:,:,3:4]);y=b[:,:,:3]*b[:,:,3:4]+.18*(1-b[:,:,3:4]);mu1=gaussian_filter(x,(1.5,1.5,0));mu2=gaussian_filter(y,(1.5,1.5,0))
 v1=gaussian_filter(x*x,(1.5,1.5,0))-mu1*mu1;v2=gaussian_filter(y*y,(1.5,1.5,0))-mu2*mu2;cov=gaussian_filter(x*y,(1.5,1.5,0))-mu1*mu2
 sm=((2*mu1*mu2+.01**2)*(2*cov+.03**2))/((mu1*mu1+mu2*mu2+.01**2)*(v1+v2+.03**2))
 # Standard image SSIM on the tight union bounding rectangle, excluding distant background.
 # Also retain stricter foreground-only SSIM as a diagnostic, never hiding texture sensitivity.
 foreground_score=float(sm[binary_dilation(union,iterations=5)].mean());yy,xx=np.where(union);y0=max(0,yy.min()-5);y1=min(len(union),yy.max()+6);x0=max(0,xx.min()-5);x1=min(union.shape[1],xx.max()+6);score=float(sm[y0:y1,x0:x1].mean());assert np.isfinite(score)
 rows.append({'view_degrees':i*45,'iou':float(iou),'soft_iou':float(soft),'ssim':score,'foreground_ssim':foreground_score,'ssim_crop':[int(x0),int(y0),int(x1),int(y1)],'reference_foreground_pixels':int(am.sum()),'intersection_pixels':int((am&bm).sum()),'union_pixels':int(union.sum())})
r={'views':rows,'minimum_iou':min(x['iou'] for x in rows),'minimum_ssim':min(x['ssim'] for x in rows)};r['pooled_iou']=sum(x['intersection_pixels'] for x in rows)/sum(x['union_pixels'] for x in rows);r['pass']=r['minimum_iou']>=.995 and r['minimum_ssim']>=.98
out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='views'}))
