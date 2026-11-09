"""m400 enhanced-pixel material masks and fixed native-palette color fits."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
Y=np.array([.2126,.7152,.0722])

def masks(im,name=None):
    a=np.array(im);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    green=np.clip((g-r-.008)/.04,0,1)*np.clip((g-b-.008)/.04,0,1)
    # Pale claw/fringe highlights can have a weak green cast after matte unmixing.
    if name and name[4] in ('d','x'):green*=np.clip((.55-c@Y)/.15,0,1)
    # Enhanced-art semantic support: preserve detached claws, head fins and fringe.
    # Upright garment extent is authored on the enhanced body, never from a resized native mask.
    if name and name[4] not in ('d','x'):
        yy,xx=np.where(a[:,:,3]>128); top,bottom=int(yy.min()),int(yy.max())+1
        seed=np.zeros(a.shape[:2],bool)
        seed[round(top+.30*(bottom-top)):round(top+.70*(bottom-top)),:]=True
        lab,count=ndimage.label(ndimage.binary_closing(green>.35,iterations=2))
        votes=np.bincount(lab[seed].ravel(),minlength=count+1);votes[0]=0
        support=ndimage.binary_dilation((votes>=100)[lab],iterations=3)
        support[round(top+.71*(bottom-top)):,:]=False
        green*=support
    elif name and name[4:6] not in ('de','df','dg'):
        # For prone/inverted clothed poses, retain connected garment islands only.
        lab,count=ndimage.label(ndimage.binary_closing(green>.35,iterations=2))
        areas=np.bincount(lab.ravel());areas[0]=0
        keep=areas>=max(220,float(areas.max())*.10)
        support=ndimage.binary_dilation(keep[lab],iterations=3)
        green*=support
    brown=np.clip((r-g-.008)/.05,0,1)*np.clip((g-b-.008)/.04,0,1)
    # Demonstrated identity-contact leakage: fins, claws, cuffs and arm bands
    # share warm pixels with leather. Only garment-adjacent brown trim is recolorable.
    near_garment=ndimage.distance_transform_edt(green<.5)
    brown*=np.clip((14-near_garment)/5,0,1)
    brown*=np.clip((r/np.maximum(g,.005)-1.18)/.18,0,1)
    # Keep original pale teeth/fringe and bright silver/gold highlights.
    brown*=np.clip((.62-c@Y)/.20,0,1)
    w=np.dstack([green,brown])
    core=ndimage.distance_transform_edt(a[:,:,3]>=250)>3
    if core.any():
        dist,ix=ndimage.distance_transform_edt(~core,return_indices=True)
        edge=(a[:,:,3]>0)&~core&(dist<=4)
        w[edge]=w[ix[0],ix[1]][edge]
    w[a[:,:,3]==0]=0
    w/=np.maximum(1,w.sum(axis=2,keepdims=True))
    return np.round(w*255).astype(np.uint8)

def fit():
    inv=json.loads((ROOT/'sources.json').read_text())
    palettes={int(k):np.frombuffer((REPO/v['path']).read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in inv['palette_sources'].items()}
    base=palettes[401];r,g,b=base.T
    changed=np.max(np.abs(base-palettes[402]),axis=1)>.08
    groups=[(g-r>.02)&(g-b>.02)&changed,(r-g>.025)&(g-b>.025)&changed]
    settings={'schema_version':1,'color_space':'sRGB normalized RGB, fixed luminance projection; masks are linear coverage',
              'base_palette':401,'base_exact_bypass':True,'regions':['green garment panels','warm trim, belt and apron bands'],
              'mask_method':'Enhanced-pixel hue/material selection with local interior coverage extended to contours; no resized native masks.',
              'protected':'teal skin, pale teeth/fringe, bright metallic highlights',
              'support_settings':{'upright_seed_body_y':[.30,.70],'minimum_seed_pixels':100,'prone_green_highlight_fade_luminance':[.40,.55],'enhanced_green_component_closing_px':2,'support_dilation_px':3,'lower_body_cutoff':.71,'prone_minimum_area':220,'prone_minimum_largest_fraction':.10,'legacy_de_df_dg':'full native palette regions across mottled scales'},
              'palettes':{}}
    for pal,col in palettes.items():
        coeff=[]
        for selected in groups:
            y=base[selected]@Y
            x=np.column_stack((y,np.ones_like(y)))
            coeff.append(np.linalg.lstsq(x,col[selected],rcond=None)[0].tolist())
        settings['palettes'][str(pal)]=coeff
    return settings

def recolor(im,w,pal,settings):
    if pal==401:return im.copy()
    a=np.array(im);c=a[:,:,:3].astype(float)/255;y=c@Y;weights=w.astype(float)/255
    out=c*(1-weights.sum(axis=2,keepdims=True))
    for k,coeff in enumerate(settings['palettes'][str(pal)]):
        slope,intercept=np.array(coeff)
        target=np.clip(y[:,:,None]*slope+intercept,0,1)
        out+=target*weights[:,:,k,None]
    a[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)

def run(batch=None):
    settings=fit();(ROOT/'material_settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    for d in ('masks_2x','previews'):(ROOT/d).mkdir(exist_ok=True)
    records=json.loads((ROOT/'registration.json').read_text())
    names=[n for n,r in records.items() if batch is None or r['batch']==batch]
    contact=Image.new('RGB',(320*len(names),4*340),(42,42,42));draw=ImageDraw.Draw(contact)
    for i,n in enumerate(names):
        im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');w=masks(im,n)
        Image.fromarray(np.dstack([w,np.zeros(w.shape[:2],np.uint8)]),'RGB').save(ROOT/f'masks_2x/{n}.png')
        pics=[recolor(im,w,pal,settings) for pal in (401,402,403)]
        alpha=np.asarray(im)[:,:,3]
        for pal,pic in zip((401,402,403),pics):
            assert np.array_equal(np.asarray(pic)[:,:,3],alpha)
            if pal==401:assert np.array_equal(pic,im)
            pic.save(ROOT/f'previews/{n}_{pal}.png')
        over=np.array(im);weights=w.astype(float)/255*.7
        over[:,:,:3]=np.round(over[:,:,:3]*(1-weights.sum(axis=2,keepdims=True))+weights[:,:,0,None]*[255,80,0]+weights[:,:,1,None]*[80,80,255]).astype(np.uint8)
        pics.append(Image.fromarray(over))
        for row,pic in enumerate(pics):
            bg=Image.new('RGBA',pic.size,(42,42,42,255));bg.alpha_composite(pic);bg.thumbnail((310,310),Image.Resampling.LANCZOS)
            contact.paste(bg.convert('RGB'),(i*320+(320-bg.width)//2,row*340+25));draw.text((i*320+4,row*340+5),n+' '+str([401,402,403,'mask overlay'][row]),fill='white')
    contact.save(ROOT/f'review/{batch or "all"}_variants_masks.png')
    print(len(names),'frames: variant alpha, exact base bypass verified; masks require visual review')

if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else None)
