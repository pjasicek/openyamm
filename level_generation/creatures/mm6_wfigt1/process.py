"""Extract wfigt1 sources and retain native tone, including disintegration."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
from materials import coverage

def main():
    process_family.run('wfigt1')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float)
            gain=0.86
            c*=np.asarray(gain)[...,None] if np.ndim(gain) else gain
            a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8);im=Image.fromarray(a);im.save(p)
            if folder=='aligned_2x':
                w=np.array(coverage(im))
                Image.fromarray(w,'RGBA').save(ROOT/'masks_2x'/p.name)
    (ROOT/'tone.json').write_text(json.dumps({'body_gain':0.86,'armor_gain':0.86},indent=2)+'\n')
if __name__=='__main__':main()
