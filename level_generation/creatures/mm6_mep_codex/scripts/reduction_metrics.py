"""Eight-view binary silhouette IoU and foreground-crop RGB SSIM, no background dilution."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import gaussian_filter,binary_dilation

def compare(a,b):
 a=np.array(Image.open(a).convert('RGBA'));b=np.array(Image.open(b).convert('RGBA'));ma=a[...,3]>=128;mb=b[...,3]>=128;union=ma|mb;assert union.any()
 iou=float((ma&mb).sum()/union.sum());yy,xx=np.where(union);crop=np.s_[max(0,yy.min()-6):yy.max()+7,max(0,xx.min()-6):xx.max()+7]
 # Composite both on the same mid-grey; alpha remains authoritative for silhouette.
 def rgb(x):return (x[...,:3]/255*x[...,3:4]/255+.18*(1-x[...,3:4]/255))[crop]
 x,y=rgb(a),rgb(b);ux=gaussian_filter(x,(1.5,1.5,0));uy=gaussian_filter(y,(1.5,1.5,0));vx=gaussian_filter(x*x,(1.5,1.5,0))-ux*ux;vy=gaussian_filter(y*y,(1.5,1.5,0))-uy*uy;cov=gaussian_filter(x*y,(1.5,1.5,0))-ux*uy
 s=((2*ux*uy+.01**2)*(2*cov+.03**2))/((ux*ux+uy*uy+.01**2)*(vx+vy+.03**2));mask=binary_dilation(union,iterations=5)[crop];ssim=float(s[mask].mean());return {'iou':iou,'ssim':ssim,'intersection':int((ma&mb).sum()),'union':int(union.sum())}
if __name__=='__main__':
 root=Path(sys.argv[1]);ref,cand=sys.argv[2:4];rows=[compare(root/f'{ref}_{i}.png',root/f'{cand}_{i}.png')for i in range(8)];r={'views':rows,'min_iou':min(v['iou']for v in rows),'min_ssim':min(v['ssim']for v in rows)};r['pooled_iou']=sum(v['intersection'] for v in rows)/sum(v['union'] for v in rows);r['pass']=r['min_iou']>=.99 and r['min_ssim']>=.95;print(json.dumps(r))
