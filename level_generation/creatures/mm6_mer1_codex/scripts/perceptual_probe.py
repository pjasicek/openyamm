"""Supplemental multiscale structural similarity for the batch's perceptual-review alternative."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import gaussian_filter,binary_dilation
P=Path(__file__).resolve().parents[1]
def score(ref,cur):
 a=np.asarray(Image.open(ref).convert('RGBA'),float)/255;b=np.asarray(Image.open(cur).convert('RGBA'),float)/255;x=a[...,:3]*a[...,3:]+.32*(1-a[...,3:]);y=b[...,:3]*b[...,3:]+.32*(1-b[...,3:]);mask=(a[...,3]>.5)|(b[...,3]>.5);weights=[.0448,.2856,.3001,.2363,.1333];product=1.;values=[]
 for level,w in enumerate(weights):
  m=binary_dilation(mask,iterations=max(1,5//(2**level)));ux=gaussian_filter(x,(1.5,1.5,0));uy=gaussian_filter(y,(1.5,1.5,0));vx=gaussian_filter(x*x,(1.5,1.5,0))-ux*ux;vy=gaussian_filter(y*y,(1.5,1.5,0))-uy*uy;cov=gaussian_filter(x*y,(1.5,1.5,0))-ux*uy;cs=(2*cov+.03**2)/(vx+vy+.03**2);lum=(2*ux*uy+.01**2)/(ux*ux+uy*uy+.01**2);v=float((cs*lum if level==4 else cs)[m].mean());values.append(v);product*=max(v,0)**w
  h=x.shape[0]//2*2;wi=x.shape[1]//2*2;x=x[:h,:wi].reshape(h//2,2,wi//2,2,3).mean((1,3));y=y[:h,:wi].reshape(h//2,2,wi//2,2,3).mean((1,3));mask=mask[:h,:wi].reshape(h//2,2,wi//2,2).any((1,3))
 return {'ms_ssim':float(product),'scale_cs_and_final_ssim':values}
if __name__=='__main__':
 ref,cur=map(Path,sys.argv[1:]);rows={f.name:score(ref/f.name,f)for f in sorted(cur.glob('*.png'))};report={'views':rows,'min_ms_ssim':min(v['ms_ssim']for v in rows.values())};first=next(cur.glob('*.png'));assert abs(score(first,first)['ms_ssim']-1)<1e-12;print(json.dumps(report))
