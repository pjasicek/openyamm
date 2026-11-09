"""Restore native low-frequency plumage color while retaining generated fine feather detail."""
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
from process import ROOT,queue,save,fix

def field(rgb,alpha):
    den=ndi.gaussian_filter(alpha,7)
    out=np.stack([ndi.gaussian_filter(rgb[:,:,k]*alpha,7)/np.maximum(den,1e-6)
                  for k in range(3)],axis=2)
    valid=den>.015
    ix=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True)
    out[~valid]=out[ix[0],ix[1]][~valid]
    return out

def run():
    reg=json.loads((ROOT/'calibration_registration.json').read_text())
    (ROOT/'toned_2x').mkdir(exist_ok=True)
    (ROOT/'accent_masks_2x').mkdir(exist_ok=True)
    for name,record in reg.items():
        im=Image.open(ROOT/f'registered_2x/{name}.png').convert('RGBA')
        a=np.array(im);rgb=a[:,:,:3].astype(float);alpha=a[:,:,3]/255
        native=Image.new('RGBA',im.size)
        native.paste(queue.native(ROOT,name).resize((512,512),Image.Resampling.NEAREST),(32,32))
        n=np.asarray(native)
        corrected=field(n[:,:,:3].astype(float),n[:,:,3]/255)+.7*(rgb-field(rgb,alpha))
        # Enhanced-art chroma coverage protects gold claws and red beaks from the coarse plumage transfer.
        red,green,blue=np.moveaxis(rgb,-1,0)
        accent=np.clip((red-green-12)/18,0,1)*np.clip((red-blue-50)/35,0,1)*np.clip((red-85)/40,0,1)
        accent[alpha==0]=0
        corrected=corrected*(1-accent[:,:,None])+rgb*accent[:,:,None]
        Image.fromarray(np.round(accent*255).astype(np.uint8)).save(ROOT/f'accent_masks_2x/{name}.png')
        a[:,:,:3]=np.round(corrected).clip(0,255).astype(np.uint8)
        out=fix(Image.fromarray(a));assert np.array_equal(np.asarray(out)[:,:,3],np.asarray(im)[:,:,3])
        out.save(ROOT/f'toned_2x/{name}.png')
    save(ROOT/'tone_refinement.json',{'operation':'native coarse RGB + 0.7*(generated RGB - generated coarse RGB)',
         'accent_protection':'Enhanced RGB soft chroma coverage: clamp((R-G-12)/18)*clamp((R-B-50)/35)*clamp((R-85)/40); retain registered generated color at gold talons and red beaks. Masks retained in accent_masks_2x.',
         'reason':'Generated feather highlights and warm body markings drift in contrast and color across batches.',
         'filter':'Alpha-normalized Gaussian sigma 7 physical pixels, nearest supported extension.',
         'fixed_across_all_frames':True,'alpha_and_geometry_unchanged':True,'frames':len(reg),
         'input':'registered_2x','output':'toned_2x'})
    print('Restored native coarse tone for',len(reg),'frames')

if __name__=='__main__':run()
