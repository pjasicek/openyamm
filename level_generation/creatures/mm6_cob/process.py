"""Cobra extraction and fixed native-dark tonal treatment, with separate scale ramps."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family

def main():
    process_family.run('cob')
    import materials
    selections={}
    for path in (ROOT/'aligned_2x').glob('*.png'):
        native=np.array(Image.open(ROOT.parents[2]/'assets_dev/engine/sprites'/f'{path.stem}.bmp'))
        yy=np.indices(native.shape)[0]
        count=int(((native>=86)&(native<102)&(yy<native.shape[0]*.72)).sum())
        allow=count>200
        # Native presence determines whether this view exposes back markings;
        # actual coverage comes from enhanced colors, never resized native pixels.
        materials.coverage(Image.open(path).convert('RGBA'),allow).save(ROOT/'masks_2x'/path.name)
        selections[path.stem]=dict(native_back_ring_pixels=count,back_ring_region_enabled=allow)
    (ROOT/'back_ring_views.json').write_text(json.dumps(selections,indent=2)+'\n')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            a=np.array(Image.open(p).convert('RGBA'));a[:,:,:3]=np.round(a[:,:,:3].astype(float)*.84).astype(np.uint8);Image.fromarray(a).save(p)
    (ROOT/'tone.json').write_text(json.dumps(dict(rgb_gain=.84,mask='enhanced color/material regions; native palette usage weighted fit',native_aliases='six exact pixel aliases reused with native timelines'),indent=2)+'\n')

if __name__=='__main__':main()
