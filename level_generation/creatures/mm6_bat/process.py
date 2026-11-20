"""Purple-safe bat extraction and fixed base tonal restoration."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
purple=process_family.module('purple_matte',ROOT.parent/'mm6_sor1/process.py')


def pale_cleanup(im, clean_outer=True):
    a=np.array(im);c=a[:,:,:3].astype(float);r,g,b=c.transpose(2,0,1)
    ivory=(a[:,:,3]>128)&(np.min(c,axis=2)>100)&((np.max(c,axis=2)-np.min(c,axis=2))<40)
    if ivory.any():
        near=ndimage.distance_transform_edt(~ivory)<=5
        pale=near&(r+b>200)&(b>r*.65)&(b<r*1.2)&(a[:,:,3]>0)
        excess=np.maximum(0,np.minimum(r,b)-g-3)*pale
        c[:,:,0]-=excess;c[:,:,2]-=excess
        a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8)
    if not clean_outer:return Image.fromarray(a)
    # Thin ivory details have no interior core. Limit excess chroma only on their outer two pixels.
    c=a[:,:,:3].astype(float);edge=(a[:,:,3]>0)&(ndimage.distance_transform_edt(a[:,:,3]>=250)<=2)
    excess=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-16)*edge
    c[:,:,0]-=excess;c[:,:,2]-=excess
    a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8)
    return Image.fromarray(a)


def main():
    process_family.matte.extract=purple.extract
    process_family.fix_contour=purple.contour
    process_family.run('bat')
    config=json.loads((ROOT/'config.json').read_text())
    for folder in ('cleaned','aligned_2x'):
        for p in (ROOT/folder).glob('*.png'):
            a=np.array(Image.open(p).convert('RGBA'))
            weights=np.array(process_family.mask(Image.fromarray(a),config)).astype(float)/255
            gains=(1.,1.)
            n=p.stem
            if n.startswith('batwa'):
                pose=n[5];view=int(n[-1])
                if view==0:
                    gains={'a':(.32,1.),'b':(.40,1.),'c':(.40,1.),'d':(1.,.30),'e':(.65,.90),'f':(.60,.85)}[pose]
                elif view==3:gains=(.48,.48)
                elif view==4:
                    gains={'a':(.28,.35),'b':(.32,.40),'c':(.30,.60),'d':(.30,1.),'e':(.70,.70),'f':(.65,.65)}[pose]
            elif n.startswith('batat'):gains=(.38,.95)
            elif n.startswith('batwi'):
                gains={'a':(.32,1.),'b':(1.,.55),'c':(1.05,.75),'d':(.4,1.),'e':(1.,.45),'f':(.55,.35)}[n[5]]
            box=Image.fromarray(a).getbbox();middle=(box[0]+box[2])/2
            x=np.arange(a.shape[1]);blend=np.clip((x-middle)/16+.5,0,1)
            wing_gain=gains[0]*(1-blend)+gains[1]*blend
            gain=.82*(1-weights+weights*wing_gain[None,:])
            a[:,:,:3]=np.round(np.clip(a[:,:,:3].astype(float)*gain[:,:,None],0,255)).astype(np.uint8)
            im=pale_cleanup(pale_cleanup(Image.fromarray(a), clean_outer=False));im.save(p)
            if folder=='aligned_2x':process_family.mask(im,config).save(ROOT/'masks_2x'/p.name)
    (ROOT/'tone.json').write_text(json.dumps({'rgb_gain':.82,'matte':'Purple-safe local foreground projection; preserve intentional purple body and pink ears','wing_shadows':'Explicit native pose/view gains in process.py, applied through enhanced wing coverage; soft 16-pixel center blend. No per-frame histogram normalization.'},indent=2)+'\n')

if __name__=='__main__':main()
