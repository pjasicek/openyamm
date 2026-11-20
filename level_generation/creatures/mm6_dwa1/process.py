"""Extract dwarf art, grade consistently, and split enhanced clothing at reviewed hem boundaries."""
import json
from pathlib import Path
import sys
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent/'mm6_peasants'))
import process_family


def main():
    process_family.run('dwa1')
    reg = json.loads((ROOT/'registration.json').read_text())
    boundaries = {}
    overrides_path = ROOT/'hem_overrides.json'
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    contact = Image.new('RGB', (8*200,8*250), (45,45,45))
    draw = ImageDraw.Draw(contact)
    for i, name in enumerate(reg):
        for folder in ['cleaned', 'aligned_2x']:
            path = ROOT/folder/f'{name}.png'
            a = np.array(Image.open(path))
            a[:,:,:3] = np.round(a[:,:,:3].astype(float)*.90).astype(np.uint8)
            Image.fromarray(a).save(path)
        im = Image.open(ROOT/'aligned_2x'/f'{name}.png')
        w = np.array(Image.open(ROOT/'masks_2x'/f'{name}.png'))
        profile = ndimage.gaussian_filter1d(w[:,:,0].sum(axis=1).astype(float),2)
        start,end = (395,445) if name=='dwa1dye0' else (345,400)
        boundary = int(np.argmin(np.diff(profile)[start:end])+start+2)
        boundary = overrides.get(name,boundary)
        if name=='dwa1dyf0':boundary=im.height
        torso_y, torso_x = np.where(w[max(0,boundary-65):max(1,boundary-25),:,0]>128)
        center = float(np.median(torso_x))
        radius = max(30.,float(np.percentile(torso_x,95)-np.percentile(torso_x,5))/2)
        yy,xx = np.indices(w.shape[:2])
        hem = boundary-8*np.minimum(1,((xx-center)/radius)**2)
        trousers = np.clip((yy-hem+1)/2,0,1)
        if name=='dwa1dyf0':trousers[:]=0
        w[(xx>np.percentile(torso_x,95)+45)&(yy>boundary),:] = 0
        w[:,:,1] = np.floor(w[:,:,0]*trousers).astype(np.uint8)
        w[:,:,0] -= w[:,:,1]
        Image.fromarray(w,'RGBA').save(ROOT/'masks_2x'/f'{name}.png')
        boundaries[name]=boundary
        a=np.array(im);weights=w.astype(float)/255
        colors=np.array([[255,80,0],[0,160,255],[0,0,0],[0,0,0]])
        a[:,:,:3]=np.round(a[:,:,:3]*(1-weights.sum(axis=2,keepdims=True)*.65)+np.einsum('hwk,kc->hwc',weights,colors)*.65).astype(np.uint8)
        preview=Image.fromarray(a);preview.thumbnail((196,220));x=i%8*200;y=i//8*250
        contact.paste(preview,(x,y+20),preview);draw.text((x,y),f'{name} hem={boundary}',fill='white')
    contact.save(ROOT/'review/two_material_masks.png')
    (ROOT/'hem_boundaries.json').write_text(json.dumps(boundaries,indent=2)+'\n')
    (ROOT/'tone.json').write_text(json.dumps(dict(rgb_gain=.90,scope='fixed family-wide',
        reason='Reduce generated leather/metal brightness toward native tonal weight; alpha unchanged'),indent=2)+'\n')


if __name__=='__main__':
    main()
