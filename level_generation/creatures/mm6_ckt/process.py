"""Cockatrice extraction, fixed tone and native wing coverage."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
from materials import coverage

def main():
    process_family.run('ckt')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im)
            a[:,:,:3]=np.round(a[:,:,:3].astype(float)*.90).astype(np.uint8)
            im=Image.fromarray(a);im.save(p)
            if folder=='aligned_2x':coverage(im).save(ROOT/'masks_2x'/p.name)
    (ROOT/'tone.json').write_text(json.dumps({'rgb_gain':.90,'reason':'Retain native dark brown body and mottled turquoise wing weight','alpha':'unchanged'},indent=2)+'\n')
if __name__=='__main__':main()
