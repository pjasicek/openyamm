"""Extract all native bloodsucker poses and retain original dark tonal weight."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
from materials import coverage

def main():
    process_family.run('bld')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float)
            w=np.array(coverage(im))[:,:,0:1].astype(float)/255
            y=c@np.array([.2126,.7152,.0722]);c=c*(1-.18*w)+y[:,:,None]*.18*w
            a[:,:,:3]=np.round(np.clip(c*.76,0,255)).astype(np.uint8)
            im=Image.fromarray(a);im.save(p)
            if folder=='aligned_2x':coverage(im).save(ROOT/'masks_2x'/p.name)
    (ROOT/'tone.json').write_text(json.dumps({'rgb_gain':.76,'body_saturation':.82,'reason':'Fixed native dark teal/tan tonal weight; protect pale structure and mouth'},indent=2)+'\n')
if __name__=='__main__':main()
