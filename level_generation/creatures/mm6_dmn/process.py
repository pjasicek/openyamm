"""Extract demon animation, grade native tone and protect its enhanced belly material."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
from materials import coverage

def main():
    process_family.run('dmn')
    reg=json.loads((ROOT/'registration.json').read_text())
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float)
            effect=np.clip((c[:,:,0]-c[:,:,1]-10)/20,0,1) if p.stem.startswith('dmndth') else np.zeros(c.shape[:2])
            gain=.86+.14*effect
            if p.stem.startswith('m496x'):gain=.42
            c*=np.asarray(gain)[...,None] if np.ndim(gain) else gain
            a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8);im=Image.fromarray(a);im.save(p)
            if folder!='aligned_2x':continue
            w=np.array(coverage(im)).astype(float)/255
            # Coarse anatomy locates the chest; actual coverage follows neutral enhanced paint.
            # Front and oblique belly appears below the harness, above the thighs. Back views have none.
            name=p.stem;batch=reg[name]['batch'];view=int(name[-1]) if name[-1].isdigit() else 0
            r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
            if name.startswith('dmndth'):
                # The death plume has warmer peach highlights than the red eyes.
                # Include those enhanced pixels rather than treating them as gray skin.
                fx=np.clip((r-g-3)/10,0,1)*np.clip((r-b-3)/10,0,1)
                w[:,:,:3]*=1-fx[:,:,None]
                w[:,:,3]=np.maximum(w[:,:,3],fx)
            elif not name.startswith('m496x'):
                ys,xs=np.where(a[:,:,3]>128);yy,xx=np.indices(r.shape)
                head=yy<ys.min()+.24*(ys.max()-ys.min())
                eyes=head*np.clip((r-g-12)/20,0,1)*np.clip((r-b-18)/20,0,1)
                w[:,:,:3]*=1-eyes[:,:,None]
                w[:,:,3]=np.maximum(w[:,:,3],eyes)
            if not name.startswith('m496x') and view in [0,1,2]:
                alpha=a[:,:,3]>128;ys,xs=np.where(alpha);x0,x1=xs.min(),xs.max();y0,y1=ys.min(),ys.max();bw=x1-x0;bh=y1-y0
                yy,xx=np.indices(alpha.shape);cx=(x0+x1)/2
                if view==0:left,right=cx-.145*bw,cx+.145*bw
                elif view==1:left,right=cx-.11*bw,cx+.16*bw
                else:left,right=cx+.06*bw,cx+.30*bw
                roi=(xx>=left)&(xx<=right)&(yy>y0+.25*bh)&(yy<y0+.58*bh)
                neutral=np.clip((16-(np.max(c,axis=2)-np.min(c,axis=2)))/10,0,1)*np.clip((np.min(c,axis=2)-35)/15,0,1)
                # Edge softness belongs to enhanced paint; do not resize a native pixel mask.
                protect=ndimage.gaussian_filter((roi*neutral).astype(float),.7)
                w[:,:,0]*=1-protect
            if name.startswith('m496x'):w[:]=0
            w/=np.maximum(1,w.sum(axis=2,keepdims=True));w[a[:,:,3]==0]=0
            Image.fromarray(np.floor(w*255).astype(np.uint8),'RGBA').save(ROOT/'masks_2x'/p.name)
    (ROOT/'tone.json').write_text(json.dumps({'body_gain':.86,'death_effect_gain':1.,'shared_ash_gain':.42,'belly_mask':'coarse reviewed anatomical region intersected with neutral enhanced paint, sigma .7 feather'},indent=2)+'\n')
if __name__=='__main__':main()
