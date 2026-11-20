"""Purple-safe beholder extraction and fixed native tone."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
from materials import coverage
purple=process_family.module('purple_matte',ROOT.parent/'mm6_sor1/process.py')

def main():
    process_family.matte.extract=purple.extract;process_family.fix_contour=purple.contour
    process_family.run('bh')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im);w=np.array(coverage(im)).astype(float)/255
            gains=np.array([.94,1.,1.07]);grade=.80*(1-w[:,:,1,None]+w[:,:,1,None]*gains)
            a[:,:,:3]=np.round(np.clip(a[:,:,:3].astype(float)*grade,0,255)).astype(np.uint8)
            im=Image.fromarray(a);im.save(p)
            if folder=='aligned_2x':coverage(im).save(ROOT/'masks_2x'/p.name)
    from refine import refine
    refine()
    (ROOT/'tone.json').write_text(json.dumps({'rgb_gain':.80,'neutral_temperature_rgb':[.94,1.,1.07],'reason':'Reduce generated highlights and warm neutral cast; preserve purple eye and baked shading'},indent=2)+'\n')

if __name__=='__main__':main()
