"""Correct demonstrated lifted native shadows with a fixed smooth native guide.

No frame histogram normalization, geometry change, alpha change, or source-mask
transfer. The guide controls coarse illumination only; generated texture stays.
"""
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
from process import ROOT,queue,save,fix
Y=np.array([.2126,.7152,.0722])
SIGMA=12
def field(c,a):
    den=ndi.gaussian_filter(a,SIGMA)
    out=np.stack([ndi.gaussian_filter(c[:,:,k]*a,SIGMA)/np.maximum(den,1e-6) for k in range(3)],axis=2)
    valid=den>.015
    ix=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True)
    out[~valid]=out[ix[0],ix[1]][~valid]
    return out
def run():
    reg=json.loads((ROOT/'registration.json').read_text())
    for d in ['final_2x','lighting_masks','review/lighting']:(ROOT/d).mkdir(parents=True,exist_ok=True)
    stats={}
    for n,r in reg.items():
        im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3]/255
        native=Image.new('RGBA',im.size);native.paste(queue.native(ROOT,n).resize((512,512),Image.Resampling.NEAREST),tuple(-v for v in r['canvas_origin_px']))
        na=np.array(native);nc=na[:,:,:3].astype(float);nf=field(nc,na[:,:,3]/255);cf=field(c,alpha)
        # Only lower demonstrated lifted shadows, never brighten a frame.
        gain=np.clip((nf@Y+3)/(cf@Y+3)*1.06,.48,1)
        # Neutral skin/flippers were warmed by generated veins. Smooth chroma
        # correction applies only to enhanced neutral/olive pixels, not shell gold.
        rr,gg,bb=c.transpose(2,0,1)
        neutral=np.clip((1.22-rr/np.maximum(gg,1))/.20,0,1)*np.clip((bb/np.maximum(gg,1)-.38)/.25,0,1)
        cy=np.maximum(cf@Y,3);ny=np.maximum(nf@Y,3)
        tint=np.clip((nf/ny[:,:,None])/(cf/cy[:,:,None]+1e-5),.72,1.30)
        corrected=c*gain[:,:,None]*(1+(tint-1)*neutral[:,:,None]*.65)
        a[:,:,:3]=np.round(corrected).clip(0,255).astype(np.uint8);out=fix(Image.fromarray(a));assert np.array_equal(np.array(out)[:,:,3],np.array(im)[:,:,3]);out.save(ROOT/f'final_2x/{n}.png')
        Image.fromarray(np.round((1-gain)*255).astype(np.uint8)).save(ROOT/f'lighting_masks/{n}.png')
        stats[n]={'minimum_gain':float(gain[alpha>0].min()),'mean_gain':float((gain*alpha).sum()/alpha.sum()),'alpha_unchanged':True}
    batches=json.loads((ROOT/'batches.json').read_text())
    for key,b in batches.items():
        names=b['frames'];contact=Image.new('RGB',(512*len(names),1650),(35,35,35));draw=ImageDraw.Draw(contact)
        for i,n in enumerate(names):
            pics=[queue.native(ROOT,n).resize((512,512),Image.Resampling.NEAREST),Image.open(ROOT/f'aligned_2x/{n}.png'),Image.open(ROOT/f'final_2x/{n}.png')]
            for row,pic in enumerate(pics):
                bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic);contact.paste(bg.convert('RGB'),(i*512,row*550+25));draw.text((i*512+5,row*550+5),n+' '+['native','before correction','corrected'][row],fill='white')
        contact.save(ROOT/f'review/lighting/{key}.png')
    save(ROOT/'lighting_settings.json',{'reason':'Native/restored contacts demonstrated lifted shadow flippers and over-warm veins in attack/fidget views; same fixed native illumination-guide operation applies across every pose for continuity.','guide':'Alpha-normalized Gaussian sigma 12 physical pixels, extend guide only where support <.015; no native pixel or mask is pasted into the artwork.','luminance_gain':'clamp((native coarse Y+3)/(art coarse Y+3)*1.06,.48,1)','chroma':'Enhanced neutral/olive soft coverage; 65% correction toward native coarse normalized chroma; per-channel ratio .72..1.30. Shell gold excluded by enhanced color coverage.','identity_tone_retained':json.loads((ROOT/'tone_settings.json').read_text()),'geometry_and_alpha_unchanged':True,'per_frame_histogram_matching':False,'status':'requires visual review','frames':stats})
    print('Prepared fixed illumination correction for',len(reg),'unique frames')
if __name__=='__main__':run()
