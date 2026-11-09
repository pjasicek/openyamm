"""Enhanced-art soft material masks and frozen native palette color transforms."""
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
from process import ROOT,queue,save
Y=np.array([.2126,.7152,.0722])
def masks(im):
 a=np.array(im);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
 green=np.clip((g-r-.003)/np.maximum(g*.16,.015),0,1)*np.clip((g-b-.003)/np.maximum(g*.14,.015),0,1)
 saturated=np.clip((.60-b/np.maximum(g,.01))/.30,0,1)*np.clip((g/np.maximum(r,.01)-1.12)/.45,0,1)
 shell=green*saturated;skin=green*(1-saturated)
 neutral=np.clip((b/np.maximum(g,.01)-.40)/.25,0,1)*np.clip((r/np.maximum(g,.01)-.58)/.22,0,1)*np.clip((1.25-r/np.maximum(g,.01))/.25,0,1)*np.clip((.78-c@Y)/.20,0,1)
 neutral*=1-green
 w=np.dstack([shell,skin,neutral]);core=ndi.distance_transform_edt(a[:,:,3]>=250)>3
 if core.any():
  dist,ix=ndi.distance_transform_edt(~core,return_indices=True);edge=(a[:,:,3]>0)&~core&(dist<=4);w[edge]=w[ix[0],ix[1]][edge]
 w[a[:,:,3]==0]=0;w/=np.maximum(1,w.sum(axis=2,keepdims=True));return np.round(w*255).astype(np.uint8)
def fit():
 s=json.loads((ROOT/'sources.json').read_text());p={int(k):np.frombuffer((queue.REPO/v['path']).read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in s['palette_sources'].items()};base=p[581]
 r,g,b=base.T; changed=np.max(np.abs(base-p[583]),axis=1)>0; changed[0]=False
 groups=[np.where(changed&(g>r*1.2)&(b<g*.45))[0].tolist(),np.where(changed&(g>r*1.05)&(b>=g*.45)&(b<g*.95))[0].tolist(),np.where(changed&(g<=r*1.05)&(r<g*1.25)&(b>g*.5))[0].tolist()]
 settings={'base_palette':581,'base_exact_bypass':True,'operation':'native_material_linear_rgb_transform','color_space':'sRGB normalized RGB; linear mask coverage','regions':['saturated green shell markings','desaturated green underside and skin','neutral gray/olive native palette details'],'protected':'unchanged ochre shell patches, warm face, eye and bright cream highlights; thin alpha preserved','mask_method':'Enhanced RGB material coverage with local enhanced-interior contour extension. No native mask transfer.','neutral_delta_limit_rgb8':4,'native_palette_groups':groups,'palettes':{}}
 for pal,target in p.items():
  ramps=[]
  for ids in groups:
   x=base[ids];matrix=np.linalg.lstsq(x,target[ids],rcond=None)[0];ramps.append(matrix.tolist())
  settings['palettes'][str(pal)]=ramps
 return settings
def recolor(im,w,pal,settings):
 if int(pal)==581:return im.copy()
 a=np.array(im);c=a[:,:,:3].astype(float)/255;out=c*(1-w.astype(float).sum(axis=2,keepdims=True)/255)
 for k,coeff in enumerate(settings['palettes'][str(pal)]):
  target=(c@np.array(coeff)).clip(0,1)
  if k==2:target=c+np.clip(target-c,-4/255,4/255)
  out+=target*w[:,:,k,None]/255
 a[:,:,:3]=np.round(out.clip(0,1)*255).astype(np.uint8);return Image.fromarray(a)
def run(batch=None):
 settings=fit();save(ROOT/'material_settings.json',settings)
 for d in ['masks_2x','previews','native_variants','review/variants']:(ROOT/d).mkdir(parents=True,exist_ok=True)
 batches=json.loads((ROOT/'batches.json').read_text());names=[n for k,b in batches.items() if batch is None or batch==k for n in b['frames']]
 for n in names:
  im=Image.open(ROOT/f'final_2x/{n}.png').convert('RGBA');w=masks(im);assert np.max(w.astype(int).sum(axis=2))<=255;assert not w[np.array(im)[:,:,3]==0].any();Image.fromarray(w).save(ROOT/f'masks_2x/{n}.png')
  for pal in [581,582,583]:
   out=recolor(im,w,pal,settings);assert np.array_equal(np.array(out)[:,:,3],np.array(im)[:,:,3]);assert pal!=581 or np.array_equal(out,im);out.save(ROOT/f'previews/{n}_{pal}.png');queue.native(ROOT,n,pal).save(ROOT/f'native_variants/{n}_{pal}.png')
 for key,b in batches.items():
  if batch is not None and key!=batch:continue
  contact=Image.new('RGB',(400*len(b['frames']),1680),(35,35,35));draw=ImageDraw.Draw(contact)
  for i,n in enumerate(b['frames']):
   im=Image.open(ROOT/f'final_2x/{n}.png');w=np.array(Image.open(ROOT/f'masks_2x/{n}.png'));over=np.array(im);ww=w.astype(float)/255*.65;over[:,:,:3]=np.round(over[:,:,:3]*(1-ww.sum(axis=2,keepdims=True))+ww@np.array([[255,65,40],[50,150,255],[255,40,240]])).clip(0,255).astype(np.uint8)
   pics=[Image.open(ROOT/f'previews/{n}_{p}.png') for p in [581,582,583]]+[Image.fromarray(over)]
   for j,pic in enumerate(pics):
    bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic);bg.thumbnail((395,395),Image.Resampling.LANCZOS);contact.paste(bg.convert('RGB'),(i*400,j*420+25));draw.text((i*400+5,j*420+5),n+' '+str([581,582,583,'mask overlay'][j]),fill='white')
  contact.save(ROOT/f'review/variants/{key}.png')
 print('Derived',len(names),'frames × 3 native palettes; alpha and base bypass checked')
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else None)
