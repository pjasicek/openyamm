import json,numpy as np
from scipy import ndimage as ndi
from PIL import Image
from process import ROOT,queue
def core(im,quiet=False):
 rgba=np.asarray(im);a=rgba[:,:,3]>128
 if quiet:
  c=rgba[:,:,:3].astype(float);a&=(c@np.array([.2126,.7152,.0722])<150)&(c[:,:,1]+c[:,:,2]>1.8*c[:,:,0]);a=ndi.binary_fill_holes(a)
 y,x=np.ogrid[-6:7,-6:7];m=ndi.binary_opening(a,structure=x*x+y*y<=36);l,c=ndi.label(m)
 if not c:return None
 sizes=np.bincount(l.ravel());sizes[0]=0;ys,xs=np.where(l==sizes.argmax())
 if len(xs)<400:return None
 return np.array([xs.min(),ys.min(),xs.max()+1,ys.max()+1])
reg=json.loads((ROOT/'registration.json').read_text());batches=json.loads((ROOT/'batches.json').read_text())
out={}
for key,b in batches.items():
 rows=[]
 for n in b['frames']:
  if n.startswith('m528d') and n[5]>'c':continue
  quiet=n.startswith('m528w') or n in ['m528aa0','m528ab0','m528da0','m528db0'] or n.startswith('m528a') and n[5]>='m'
  a=core(queue.native(ROOT,n).resize((256,256),Image.Resampling.NEAREST),quiet);b=core(Image.open(ROOT/f'aligned_2x/{n}.png'),quiet)
  if a is None or b is None:continue
  rows.append({'frame':n,'native':a.tolist(),'enhanced':b.tolist(),'ratio':float(np.sqrt(np.prod(a[2:]-a[:2])/np.prod(b[2:]-b[:2]))),'center_delta':((a[:2]+a[2:]-b[:2]-b[2:])/2).tolist()})
 if rows:out[key]={'median_scale':float(np.median([r['ratio'] for r in rows])),'median_offset':np.median([r['center_delta'] for r in rows],axis=0).tolist(),'frames':rows}
(ROOT/'review/core_registration_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='frames'} for k,v in out.items()},indent=2))
