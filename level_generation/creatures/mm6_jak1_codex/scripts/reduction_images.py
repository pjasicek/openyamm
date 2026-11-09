"""Material-tier images and eight-view foreground metrics for the rebake study."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter,binary_dilation
P=Path(__file__).resolve().parents[1]
def linear(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def srgb(c):return np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
def tiers(directory):
 ramps=json.loads((P/'textures/jak1_ramps.json').read_text())
 for entry in ramps['materials']:
  tag={'Jackalman_A':'body','JackalmanHead_A':'head'}[entry['base']]
  base=linear(np.asarray(Image.open(directory/f'{tag}_basecolor.png').convert('RGB'),float)/255)
  mask=np.asarray(Image.open(directory/f'{tag}_region_mask.png').convert('RGBA').resize((base.shape[1],base.shape[0])),float)/255
  lum=base@np.array([.2126,.7152,.0722])
  for variant,regions in entry['ramps'].items():
   out=base.copy()
   for k,region in enumerate(regions):
    lo,hi=region['range'];x=np.clip((lum-lo)/(hi-lo),0,1)*15;i=np.minimum(x.astype(int),14);f=(x-i)[...,None];colors=np.array(region['colors'])
    value=colors[i]*(1-f)+colors[i+1]*f;out=out*(1-mask[...,k:k+1])+value*mask[...,k:k+1]
   Image.fromarray((np.clip(srgb(out),0,1)*255+.5).astype('uint8')).save(directory/f'{tag}_{variant}.png')
def compare(a,b):
 a=np.asarray(Image.open(a).convert('RGBA'));b=np.asarray(Image.open(b).convert('RGBA'));ma=a[...,3]>=128;mb=b[...,3]>=128;union=ma|mb;assert union.any()
 yy,xx=np.where(union);crop=np.s_[max(0,yy.min()-6):yy.max()+7,max(0,xx.min()-6):xx.max()+7]
 def rgb(v):return (v[...,:3]/255*v[...,3:4]/255+.18*(1-v[...,3:4]/255))[crop]
 x,y=rgb(a),rgb(b);ux=gaussian_filter(x,(1.5,1.5,0));uy=gaussian_filter(y,(1.5,1.5,0));vx=gaussian_filter(x*x,(1.5,1.5,0))-ux*ux;vy=gaussian_filter(y*y,(1.5,1.5,0))-uy*uy;cov=gaussian_filter(x*y,(1.5,1.5,0))-ux*uy
 score=((2*ux*uy+.01**2)*(2*cov+.03**2))/((ux*ux+uy*uy+.01**2)*(vx+vy+.03**2));roi=binary_dilation(union,iterations=5)[crop]
 return {'iou':float((ma&mb).sum()/union.sum()),'ssim':float(score[roi].mean()),'intersection_pixels':int((ma&mb).sum()),'union_pixels':int(union.sum())}
if __name__=='__main__':
 if sys.argv[1]=='tiers':tiers(Path(sys.argv[2]))
 else:
  root=Path(sys.argv[2]);ref,candidate=sys.argv[3:5];rows=[]
  for tier in 'abc':
   for i in range(8):rows.append(dict(tier=tier,view=i,**compare(root/f'{ref}_{tier}_{i}.png',root/f'{candidate}_{tier}_{i}.png')))
  identity=compare(root/f'{ref}_a_0.png',root/f'{ref}_a_0.png');assert identity['iou']==1 and abs(identity['ssim']-1)<1e-8
  print(json.dumps({'views':rows,'min_iou':min(v['iou']for v in rows),'pooled_iou':sum(v['intersection_pixels']for v in rows)/sum(v['union_pixels']for v in rows),'min_ssim':min(v['ssim']for v in rows)}))
