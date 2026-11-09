"""Monk extraction: protect neutral hands/rope and retain the native dark skirt weight."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent/'mm6_peasants'))
import process_family

original_mask = process_family.mask


def robe_mask(im, config):
    w = np.array(original_mask(im, config)).astype(float)/255
    hsv = np.array(im.convert('RGB').convert('HSV')).astype(float)/255
    # Generated pale grey hands have a small blue cast; they are not blue cloth.
    w *= np.clip((hsv[:,:,1]-.28)/.16,0,1)
    return Image.fromarray(np.round(w*255).astype(np.uint8),'L')


def robe_ramps(config, inv):
    repo=ROOT.parents[2]
    colors={int(p):np.frombuffer((repo/f'assets_dev/worlds/mm6/textures/pal{p}.act').read_bytes()[:768],
            np.uint8).reshape(256,3)/255 for p in inv['variants']}
    counts=np.zeros(256)
    for name in inv['sources']:
        counts+=np.bincount(np.array(Image.open(repo/f'assets_dev/engine/sprites/{name}.bmp')).ravel(),minlength=256)
    c=colors[config['base_palette']];r,g,b=c.T
    saturation=(c.max(axis=1)-c.min(axis=1))/np.maximum(c.max(axis=1),.001)
    selected=(saturation>.44)&(b>g+.02)&(b>r+.02)
    weight=counts*selected;y=c@np.array([.2126,.7152,.0722])
    return {p:(((weight*y)[:,None]*target).sum(axis=0)/(weight*y*y).sum()).tolist()
            for p,target in colors.items() if p!=config['base_palette']}


def main():
    process_family.mask = robe_mask
    process_family.ramps = robe_ramps
    process_family.run('mnk1')
    for folder in ['cleaned','aligned_2x']:
        for path in sorted((ROOT/folder).glob('*.png')):
            im=Image.open(path).convert('RGBA');a=np.array(im);mask=np.array(robe_mask(im,{'mask_kind':'blue'})).astype(float)/255
            box=im.getchannel('A').getbbox(); yy=np.indices(a.shape[:2])[0]
            relative=(yy-box[1])/max(1,box[3]-box[1])
            gain=1-.20*np.clip((relative-.42)/.12,0,1)
            color_gain=1-mask*(1-gain)
            a[:,:,:3]=np.round(a[:,:,:3]*color_gain[:,:,None]).astype(np.uint8)
            Image.fromarray(a).save(path)
    (ROOT/'tone.json').write_text(json.dumps(dict(lower_cloth_rgb_gain=.80,
        transition='normalized occupied height .42 to .54; fixed across frames',
        protected='neutral hands, rope, green spell effects and black face shadow',
        mask='enhanced blue cloth with saturation ramp .28 to .44'),indent=2)+'\n')


if __name__=='__main__':main()
