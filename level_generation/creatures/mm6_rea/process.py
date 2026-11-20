"""Extract rea sources and retain native tone, including disintegration."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'mm6_peasants'))
import process_family
from materials import coverage

def main():
    process_family.run('rea')
    for folder in ['cleaned','aligned_2x']:
        for p in (ROOT/folder).glob('*.png'):
            im=Image.open(p).convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float)
            gain=0.96
            c*=np.asarray(gain)[...,None] if np.ndim(gain) else gain
            a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8);im=Image.fromarray(a);im.save(p)
            if folder=='aligned_2x':
                w=np.array(coverage(im))
                Image.fromarray(w,'L').save(ROOT/'masks_2x'/p.name)
    # Match native control-panel lamp on/off states on the enhanced artwork.
    lamp_states={}
    for p in (ROOT/'aligned_2x').glob('*.png'):
        native=np.array(Image.open(ROOT/'native'/p.name));ys,xs=np.where(native[:,:,3]>128)
        x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
        panel=native[round(y0+(y1-y0)*.71):round(y0+(y1-y0)*.88),round(x0+(x1-x0)*.30):round(x0+(x1-x0)*.65),:3].astype(float)
        states=[]
        a=np.array(Image.open(p));ys,xs=np.where(a[:,:,3]>128);x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
        ya,yb=round(y0+(y1-y0)*.71),round(y0+(y1-y0)*.88);xa,xb=round(x0+(x1-x0)*.30),round(x0+(x1-x0)*.65)
        color=a[ya:yb,xa:xb,:3].astype(float)
        for channel in [0,1]:
            other=[i for i in range(3) if i!=channel];other_native=np.max(panel[:,:,other],2)
            on=bool(((panel[:,:,channel]>80)&(panel[:,:,channel]>other_native*1.7)).sum()>2);states.append(on)
            if not on:
                remaining=np.max(color[:,:,other],2)
                lamp_weight=np.clip((color[:,:,channel]-remaining-10)/30,0,1)
                lamp_weight*=np.clip((color[:,:,channel]-80)/50,0,1)
                neutral=remaining*.6
                color=color*(1-lamp_weight[:,:,None])+neutral[:,:,None]*lamp_weight[:,:,None]
        a[ya:yb,xa:xb,:3]=np.round(np.clip(color,0,255)).astype(np.uint8)
        if p.stem=='reaat05':
            # Native first charging flash is weaker than the next full-white flash.
            rgb=a[:,:,:3].astype(float);neutral=1-np.clip((rgb.max(2)-rgb.min(2))/80,0,1)
            a[:,:,:3]=np.round(np.clip(rgb*(1+.45*neutral[:,:,None]),0,255)).astype(np.uint8)
        Image.fromarray(a).save(p);lamp_states[p.stem]={'red_on':states[0],'green_on':states[1]}
    (ROOT/'native_lamp_states.json').write_text(json.dumps(lamp_states,indent=2)+'\n')
    (ROOT/'tone.json').write_text(json.dumps({'body_gain':0.96,'armor_gain':0.96},indent=2)+'\n')
if __name__=='__main__':main()
