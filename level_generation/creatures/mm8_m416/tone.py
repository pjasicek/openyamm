"""Restore native low-frequency clothing, skin and equipment colors while retaining generated fine surface detail."""
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

def run(batch_keys=None):
    reg=json.loads((ROOT/'calibration_registration.json').read_text())
    (ROOT/'toned_2x').mkdir(exist_ok=True)
    for name,record in reg.items():
        if batch_keys and record['batch'] not in batch_keys:continue
        im=Image.open(ROOT/f'registered_2x/{name}.png').convert('RGBA')
        a=np.array(im);rgb=a[:,:,:3].astype(float);alpha=a[:,:,3]/255
        native=Image.new('RGBA',im.size)
        native.paste(queue.native(ROOT,name).resize((512,512),Image.Resampling.NEAREST),(32,32))
        n=np.asarray(native)
        corrected=field(n[:,:,:3].astype(float),n[:,:,3]/255)+.7*(rgb-field(rgb,alpha))
        a[:,:,:3]=np.round(corrected).clip(0,255).astype(np.uint8)
        out=im.copy() if record['batch'] in ['native_n_v1','native_n_v4'] else fix(Image.fromarray(a),name);assert np.array_equal(np.asarray(out)[:,:,3],np.asarray(im)[:,:,3])
        out.save(ROOT/f'toned_2x/{name}.png')
    save(ROOT/'tone_refinement.json',{'operation':'native coarse RGB + 0.7*(generated RGB - generated coarse RGB)',
         'reason':'Restore native coarse gray trousers, tan skin, brown leather and teal bandanna/vest RGB while retaining enhanced fine detail; no alpha or mask transfer.',
         'filter':'Alpha-normalized Gaussian sigma 7 physical pixels, nearest supported extension.',
         'material_boundary_correction':{'batches':['native_n_v1','native_n_v4'],'method':'Accepted identity-frozen luminance multiplier is retained without spatial tone transfer where native colors crossed enhanced hair and clothing boundaries.','settings':'tone_settings.json'},'fixed_across_all_frames':False,'alpha_and_geometry_unchanged':True,'frames':len(reg),
         'input':'registered_2x','output':'toned_2x'})
    print('Restored native coarse tone for',len(reg),'frames')

if __name__=='__main__':run()
