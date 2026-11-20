"""Extract qfi sources and retain native tone, including disintegration."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
from materials import coverage

def main():
    process_family.run('qfi')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float)
            gain=0.9
            c*=np.asarray(gain)[...,None] if np.ndim(gain) else gain
            a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8);im=Image.fromarray(a);im.save(p)
            if folder=='aligned_2x':
                w=np.array(coverage(im))
                Image.fromarray(w,'L').save(ROOT/'masks_2x'/p.name)
    # The composite rock alcove visibly collapses in the native corpse frame.
    # Correct the generated alcove's excessive height to that specific native extent,
    # without giving all creature poses equal silhouette bounds.
    reg=json.loads((ROOT/'registration.json').read_text());name='qdef0';record=reg[name]
    clean=Image.open(ROOT/'cleaned'/f'{name}.png').convert('RGBA');gb=process_family.bounds(clean)
    nb=record['native_bounds'];size=(2*(nb[2]-nb[0]),2*(nb[3]-nb[1]))
    tile=process_family.resize_base(clean.crop(gb),size,{'matte':'magenta'})
    old=Image.open(ROOT/'aligned_2x'/f'{name}.png');out=Image.new('RGBA',old.size)
    origin=record['canvas_origin_px'];out.paste(tile,(2*nb[0]-origin[0],2*nb[1]-origin[1]))
    out.save(ROOT/'aligned_2x'/f'{name}.png');coverage(out).save(ROOT/'masks_2x'/f'{name}.png')
    record['native_corpse_alcove_extent_correction']={'source_crop':gb,'target_size':size,'reason':'Generated composite alcove too tall against native corpse'}
    (ROOT/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
    (ROOT/'tone.json').write_text(json.dumps({'body_gain':0.9,'armor_gain':0.9},indent=2)+'\n')
if __name__=='__main__':main()
