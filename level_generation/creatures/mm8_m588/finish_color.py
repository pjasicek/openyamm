"""Fixed enhanced-art spell mask calibration; preserve stone and all alpha."""
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
from process import ROOT,queue,save,fix

def warm(c):
 return np.clip((np.minimum(c[:,:,0],c[:,:,1])-c[:,:,2]-12)/24,0,1)

def run():
 reg=json.loads((ROOT/'registration.json').read_text());tone=json.loads((ROOT/'tone_settings.json').read_text())['multiplier']
 for folder in ['final_cleaned','effect_masks']:(ROOT/folder).mkdir(exist_ok=True)
 report={}
 for n,r in reg.items():
  im=Image.open(ROOT/f'cleaned/{n}.png').convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float);mask=np.zeros(c.shape[:2])
  if n[4:6] in ['ac','ad','ae','af'] and n[-1]!='4':
   seed=(warm(c)>.15)&(a[:,:,3]>0);region=ndi.binary_fill_holes(ndi.binary_closing(seed,iterations=2));mask=np.maximum(warm(c),ndi.gaussian_filter(region.astype(float),.6))*(a[:,:,3]>0);target=c/tone;target[:,:,1]*=1.10;target=np.minimum(target,252);c=c*(1-mask[:,:,None])+target*mask[:,:,None]
   labels,count=ndi.label(a[:,:,3]>=128);sizes=np.bincount(labels.ravel());sizes[0]=0;main=int(sizes.argmax());_,nearest=ndi.distance_transform_edt(labels==0,return_indices=True);component=labels[nearest[0],nearest[1]];particles=(component!=main)&(a[:,:,3]>0)&(c[:,:,0]>c[:,:,2]+12)
   particles|=(a[:,:,3]>0)&(c[:,:,0]>c[:,:,2]+20)&(c[:,:,0]>c[:,:,1]+15)&(ndi.distance_transform_edt(a[:,:,3]>=250)<=2)
   c[:,:,1][particles]=np.maximum(c[:,:,1][particles],c[:,:,0][particles]*.99);mask[particles]=1
  a[:,:,:3]=np.round(c).clip(0,255).astype(np.uint8);out=fix(Image.fromarray(a));assert np.array_equal(np.array(out)[:,:,3],a[:,:,3]);out.save(ROOT/f'final_cleaned/{n}.png');Image.fromarray(np.round(mask*255).astype(np.uint8)).save(ROOT/f'effect_masks/{n}.png')
  scale=r['scale_to_2x'];scaled=fix(out.convert('RGBa').resize((round(out.width*scale),round(out.height*scale)),Image.Resampling.LANCZOS).convert('RGBA'));aligned=Image.new('RGBA',r['aligned_size_px']);aligned.paste(scaled,tuple(r['translation_px'][i]-r['canvas_origin_px'][i] for i in range(2)));aligned.save(ROOT/f'aligned_2x/{n}.png');report[n]={'effect_mask_pixels':int((mask>0).sum()),'alpha_unchanged':True}
 save(ROOT/'effect_settings.json',{'reason':'Reviewed attack sheets had orange/dim spell particles compared with native pale yellow-white particles. The initial red-only mask missed pale yellow core pixels, causing visible patches; the corrected mask includes yellow cores.','mask':'Enhanced-art warm chroma; smooth min(R,G)-B ramp 12..36, native flash frames ac..af views 0..3 only.','operation':{'undo_identity_tone_in_effect':tone,'green_gain':1.10,'highlight_cap':252},'stone':'Unselected cool gray/violet stone remains at fixed identity tone.','geometry_and_alpha':'unchanged'})
 save(ROOT/'review/effect_calibration.json',{'frames':report,'detached_particles':'Enhanced alpha components separate the main rock body from detached flash particles. Detached warm particles use G >= .99R to retain the native yellow particle color; alpha remains unchanged.'})
 print('95 final cleaned frames rebuilt with fixed spell-color settings.')
if __name__=='__main__':run()
