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
SIGMA=8
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
        # Fixed spatial color/illumination guide corrects overly dark violet
        # bodies and hot cream markings while retaining generated fine texture.
        gain=np.clip((nf+8)/(cf+8),.55,1.8)
        corrected=c*(1+(gain-1)*.85)
        a[:,:,:3]=np.round(corrected).clip(0,255).astype(np.uint8);out=fix(Image.fromarray(a));assert np.array_equal(np.array(out)[:,:,3],np.array(im)[:,:,3]);out.save(ROOT/f'final_2x/{n}.png')
        Image.fromarray(np.round(np.clip((gain-0.55)/1.25,0,1)*255).astype(np.uint8)).save(ROOT/f'lighting_masks/{n}.png')
        stats[n]={'minimum_gain':float(gain[alpha>0].min()),'mean_gain':float((gain*alpha[:,:,None]).sum()/alpha.sum()/3),'alpha_unchanged':True}
    batches=json.loads((ROOT/'batches.json').read_text())
    for key,b in batches.items():
        names=[n for n in b['frames'] if n in reg]
        if not names:continue
        contact=Image.new('RGB',(512*len(names),1650),(35,35,35));draw=ImageDraw.Draw(contact)
        for i,n in enumerate(names):
            pics=[queue.native(ROOT,n).resize((512,512),Image.Resampling.NEAREST),Image.open(ROOT/f'aligned_2x/{n}.png'),Image.open(ROOT/f'final_2x/{n}.png')]
            for row,pic in enumerate(pics):
                bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic);contact.paste(bg.convert('RGB'),(i*512,row*550+25));draw.text((i*512+5,row*550+5),n+' '+['native','before correction','corrected'][row],fill='white')
        contact.save(ROOT/f'review/lighting/{key}.png')
    save(ROOT/'lighting_settings.json',{'reason':'Identity native/restored contact showed overly dark saturated purple bodies and hot cream markings. A fixed smooth spatial color/illumination guide restores native tonal balance while retaining enhanced fine texture.','guide':'Alpha-normalized Gaussian sigma 8 physical pixels; nearest valid extension below .015 support. Native pixels and source masks are never pasted into the artwork.','operation':'Per-channel gain clamp((native coarse RGB+8)/(art coarse RGB+8),.55,1.8), applied at 85% strength.','identity_tone_retained':json.loads((ROOT/'tone_settings.json').read_text()),'geometry_and_alpha_unchanged':True,'per_frame_histogram_matching':False,'status':'requires visual review','frames':stats})
    print('Prepared fixed illumination correction for',len(reg),'unique frames')
if __name__=='__main__':run()
