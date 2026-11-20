"""Purple-safe extraction, fixed native tonal correction and fixed-palette corpse protection."""
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
    process_family.run('wdm')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float)
            # Preserve native effect brightness; reduce generated body/bone highlights.
            fx=np.clip((c[:,:,2]-c[:,:,0]-8)/30,0,1)
            if p.stem.startswith('wdmdth'):
                fx=np.maximum(fx,np.clip((np.minimum(c[:,:,0],c[:,:,1])-90)/35,0,1)*np.clip((c[:,:,2]-c[:,:,0]+20)/20,0,1))
            gain=.78+.22*fx
            if p.stem.startswith('m496x'):gain=.42
            c[:,:,1]=np.minimum(c[:,:,1],np.maximum(c[:,:,0],c[:,:,2])+1)
            c*=np.asarray(gain)[...,None] if np.ndim(gain) else gain
            # Original base horns are cool ivory, not yellow.
            warm=np.clip((np.minimum(c[:,:,0],c[:,:,1])-c[:,:,2]-2)/10,0,1)*np.clip((c[:,:,0]-50)/35,0,1)
            y=c@np.array([.2126,.7152,.0722]);c=c*(1-.7*warm[:,:,None])+y[:,:,None]*.7*warm[:,:,None]
            a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8);im=Image.fromarray(a);im.save(p)
            if folder=='aligned_2x':
                m=coverage(im)
                if p.stem.startswith('wdmdth'):
                    w=np.array(m).astype(float)/255
                    e=np.maximum(np.clip((c[:,:,2]-c[:,:,0]-5)/15,0,1),np.clip((np.minimum(c[:,:,0],c[:,:,1])-90)/35,0,1)*np.clip((c[:,:,2]-c[:,:,0]+20)/20,0,1))
                    w[:,:,:3]*=1-e[:,:,None];w[:,:,3]=np.maximum(w[:,:,3],e)
                    w/=np.maximum(1,w.sum(axis=2,keepdims=True));w[a[:,:,3]==0]=0
                    m=Image.fromarray(np.floor(w*255).astype(np.uint8),'RGBA')
                if p.stem.startswith('m496x'):m=Image.new('RGBA',im.size)
                m.save(ROOT/'masks_2x'/p.name)
    (ROOT/'tone.json').write_text(json.dumps({'rgb_gain':.78,'blue_effect_gain':1.,'corpse_gain':.42,'warm_ivory_desaturation':.7,'reason':'Preserve native dark body, near-black corpse and cool pale claws; retain blue disintegration'},indent=2)+'\n')
if __name__=='__main__':main()
