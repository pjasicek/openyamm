"""Earth elemental: one enhanced stone material, fixed usage-weighted native recolor."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family

def coverage(im,config):
    a=np.array(im);y=a[:,:,:3].astype(float)@np.array([.2126,.7152,.0722])
    w=np.clip((y-2)/6,0,1)*(a[:,:,3]>0)
    return Image.fromarray(np.round(w*255).astype(np.uint8),'L')

def fit(config,inv):
    from materials import fit as palette_fit
    return palette_fit(config, inv, ROOT.parents[2])

def main():
    process_family.mask=coverage;process_family.ramps=fit;process_family.run('ert')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            a=np.array(Image.open(p).convert('RGBA'));a[:,:,:3]=np.round(a[:,:,:3].astype(float)*.75).astype(np.uint8);Image.fromarray(a).save(p)
    (ROOT/'tone.json').write_text(json.dumps(dict(rgb_gain=.75,status='fixed native tonal grade; acceptance recorded separately'),indent=2)+'\n')

if __name__=='__main__':main()
