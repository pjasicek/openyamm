"""Extract air elemental sources and retain native tone, including disintegration."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
from materials import coverage,LUMA

def main():
    process_family.run('aie1')
    warm_curve=np.array(json.loads((ROOT/'recolor_vectors.json').read_text())['198'][1])
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float)
            weight=np.array(coverage(im))[:,:,1].astype(float)/255
            levels=np.clip(np.round((c/255@LUMA)*255),0,255).astype(int)
            c=c*(1-weight[:,:,None])+warm_curve[levels]*255*weight[:,:,None]
            gain=.84
            c*=np.asarray(gain)[...,None] if np.ndim(gain) else gain
            a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8);im=Image.fromarray(a);im.save(p)
            if folder=='aligned_2x':
                w=np.array(coverage(im))
                Image.fromarray(w,'RGBA').save(ROOT/'masks_2x'/p.name)
    opacity={}
    for p in (ROOT/'aligned_2x').glob('*.png'):
        if not p.stem.startswith(('aie1wi','aie1de')):continue
        a=np.array(Image.open(p));native_alpha=np.array(Image.open(ROOT/'native'/p.name))[:,:,3]
        gain=min(1.0,float(native_alpha.sum())*4/float(a[:,:,3].sum()))
        opacity[p.stem]=gain
        for folder in ['cleaned','aligned_2x']:
            target=ROOT/folder/p.name;b=np.array(Image.open(target));b[:,:,3]=np.round(b[:,:,3].astype(float)*gain).astype(np.uint8)
            Image.fromarray(b).save(target)
    (ROOT/'opacity.json').write_text(json.dumps({'method':'Native occupied alpha area matched for hit/disappearance; shape and RGB preserved','gains':opacity},indent=2)+'\n')
    (ROOT/'tone.json').write_text(json.dumps({'body_gain':.84,'dust_correction':'native palette 198 warm-region luminance curve before gain'},indent=2)+'\n')
if __name__=='__main__':main()
