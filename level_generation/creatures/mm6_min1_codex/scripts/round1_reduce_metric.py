"""Compare matching 8-view RGBA renders; object crop avoids rewarding empty background."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
def compare(a,b):
 aa=a[:,:,3]/255;bb=b[:,:,3]/255;union=(aa>.5)|(bb>.5);inter=(aa>.5)&(bb>.5)
 assert 10<union.sum()<union.size*.8,'Expected a transparent, framed object render'
 iou=float(inter.sum()/max(1,union.sum()))
 yy,xx=np.where(union);sl=np.s_[max(0,yy.min()-8):yy.max()+9,max(0,xx.min()-8):xx.max()+9]
 a=a[:,:,:3]/255*aa[:,:,None]+.35*(1-aa[:,:,None]);b=b[:,:,:3]/255*bb[:,:,None]+.35*(1-bb[:,:,None]);a=a[sl];b=b[sl]
 def g(v):return gaussian_filter(v,(1.5,1.5,0),truncate=3.333333)
 ma=g(a);mb=g(b);va=g(a*a)-ma*ma;vb=g(b*b)-mb*mb;cov=g(a*b)-ma*mb
 ssim=float(np.mean(((2*ma*mb+.01**2)*(2*cov+.03**2))/((ma*ma+mb*mb+.01**2)*(va+vb+.03**2))))
 return {'iou':iou,'ssim':ssim,'intersection':int(inter.sum()),'union':int(union.sum())}
a=np.zeros((32,32,4));a[8:24,8:24]=255;assert compare(a,a)['iou']==compare(a,a)['ssim']==1.0
if __name__=='__main__':
 reference,candidate,output=map(Path,sys.argv[1:]);out={}
 for f in sorted(reference.glob('*.png')):
  if (candidate/f.name).exists():out[f.name]=compare(np.array(Image.open(f).convert('RGBA'),float),np.array(Image.open(candidate/f.name).convert('RGBA'),float))
 assert len(out)>=8
 result={'views':out,'min_iou':min(v['iou'] for v in out.values()),'min_ssim':min(v['ssim'] for v in out.values())}
 result['pooled_iou']=sum(x['intersection'] for x in out.values())/sum(x['union'] for x in out.values())
 result['pass']=result['min_iou']>=.99 and result['min_ssim']>=.95;output.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='views'}))
