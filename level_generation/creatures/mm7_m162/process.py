"""Deterministic m162 matte extraction, selective recoloring, and native registration."""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT=Path(__file__).resolve().parent
ALIASES={}
spec=importlib.util.spec_from_file_location('matte',ROOT.parent/'mm6_goblin/direct_ai_attack/clean_edges.py')
matte=importlib.util.module_from_spec(spec); spec.loader.exec_module(matte)

def tone(im):
    """One fixed hue-preserving curve restores the source's dark tonal weight across all poses."""
    a=np.array(im);rgb=a[:,:,:3].astype(float)/255
    luminance=rgb@np.array([.2126,.7152,.0722])
    a[:,:,:3]=np.round(rgb*luminance[:,:,None]**.10*255).astype(np.uint8)
    return Image.fromarray(a)

def resize_base(im, size):
    """Preserve alpha filtering; constrain resampling-created magenta only at base contours.

    This green-mane base has no intended purple materials. Its cleaned foreground permits at most
    10/255 magenta excess (8/255 core tolerance plus 2/255 unmix allowance). Filtering
    warm/cool neighbors can exceed that bound even after the source matte is clean.
    Do not use this creature-specific correction on recolored variants or mask overlays.
    """
    resized=im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA')
    rgba=np.array(resized); rgb=rgba[:,:,:3].astype(np.int16); alpha=rgba[:,:,3]
    contour=(alpha>0)&((ndimage.distance_transform_edt(alpha>=128)<=4)|(alpha<255))
    excess=np.where(contour,np.maximum(0,np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]-10),0)
    rgb[:,:,0]-=excess;rgb[:,:,2]-=excess
    rgba[:,:,:3]=rgb.astype(np.uint8)
    return Image.fromarray(rgba)

def mask(im):
    a=np.array(im);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    strength=np.maximum(0,g-np.maximum(r,b))
    # Green mane/beard only. Beige hide, ivory claws, warm tips and amber eyes have R>=G.
    weight=np.clip((strength-.003)/.035,0,1)*np.clip((strength/np.maximum(g,.015)-.025)/.12,0,1)
    weight[a[:,:,3]==0]=0
    return Image.fromarray(np.round(weight*255).astype(np.uint8),'L')

def ramps():
    root=ROOT.parents[2]/'assets_dev/worlds/mm7/textures'
    colors={p:np.frombuffer((root/f'pal{p}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for p in [163,164,165]}
    base=colors[163];r,g,b=base.T
    selected=(g>r+.02)&(g>b+.01)&(np.max(abs(colors[164]-base),axis=1)>.035)
    y=base[selected]@np.array([.2126,.7152,.0722])
    return {p:(y[:,None]*colors[p][selected]).sum(axis=0)/(y*y).sum() for p in [164,165]}
RAMPS=ramps()

def recolor(im,coverage,palette):
    if palette==163:return im.copy()
    a=np.array(im);rgb=a[:,:,:3].astype(float)/255;weight=np.array(coverage)/255
    target=(rgb@np.array([.2126,.7152,.0722]))[:,:,None]*RAMPS[palette]
    a[:,:,:3]=np.round(np.clip(rgb*(1-weight[:,:,None])+target*weight[:,:,None],0,1)*255).astype(np.uint8)
    return Image.fromarray(a)

def bounds(im):
    return Image.fromarray((np.array(im)[:,:,3]>96).astype(np.uint8)*255).getbbox()

def body_x(im):
    a=np.array(im)[:,:,3]>128; box=bounds(im)
    y0=round(box[1]+(box[3]-box[1])*.35);y1=round(box[1]+(box[3]-box[1])*.9)
    xs=np.where(a[y0:y1])[1]
    return float(np.median(xs))

def gutter_cuts(occupied, count):
    """Move nominal grid boundaries through verified empty gutters, preserving extended tips/feet."""
    size=len(occupied);cuts=[0]
    for i in range(1,count):
        center=size*i/count;radius=size/count*.24
        start=max(0,round(center-radius));end=min(size,round(center+radius))
        labels,n=ndimage.label(~occupied[start:end])
        gaps=[np.where(labels==label)[0]+start for label in range(1,n+1)]
        assert gaps,'No empty extraction gutter; inspect this sheet'
        best=max(gaps,key=lambda g:len(g))
        cuts.append(int((best[0]+best[-1])//2))
    return cuts+[size]

def run():
    batches=json.loads((ROOT/'batches.json').read_text());records={}
    generation=json.loads((ROOT/'generation.json').read_text())['batches']
    for directory in ['cleaned','aligned_2x','masks_2x','review']:
        (ROOT/directory).mkdir(exist_ok=True)
    for key,batch in batches.items():
        record=generation.get(key,{})
        selected=record.get('selected') or record.get('raw',{}).get('path')
        if not selected: continue
        raw=ROOT/selected
        if not raw.exists(): continue
        sheet=Image.open(raw)
        cols,rows=batch['columns'],batch['rows']; entries=[]
        rgb=np.array(sheet.convert('RGB')).astype(float)/255
        foreground=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]<.55
        yc=gutter_cuts(foreground.any(axis=1),rows)
        for i,name in enumerate(batch['frames']):
            if name in batch.get('reference_only_frames',[]): continue
            row=i//cols;col=i%cols
            xc=gutter_cuts(foreground[yc[row]:yc[row+1]].any(axis=0),cols)
            rect=(xc[col],yc[row],xc[col+1],yc[row+1])
            cell=sheet.crop(rect)
            if cell.mode=='RGBA' and cell.getchannel('A').getextrema()[0]<255:
                clean=cell; stats={'method':'native alpha'}
            else:
                clean,stats=matte.extract(cell.convert('RGB'))
            clean=resize_base(tone(clean),clean.size)
            clean.save(ROOT/f'cleaned/{name}.png')
            native=Image.open(ROOT/f'native/{name}.png')
            nb,gb=bounds(native),bounds(clean)
            ratio=(nb[3]-nb[1])*2/(gb[3]-gb[1])
            entries.append((name,clean,native,nb,gb,rect,stats,ratio))
        common=float(np.median([e[-1] for e in entries]))
        for name,clean,native,nb,gb,rect,stats,ratio in entries:
            # Falling/prone poses require their own anatomical reference, measured by width when horizontal.
            factor=common
            if key=='death_corpse':
                factor=2*(nb[2]-nb[0])/(gb[2]-gb[0]) if nb[2]-nb[0]>nb[3]-nb[1] else ratio
            size=(round(clean.width*factor),round(clean.height*factor))
            resized=resize_base(clean,size)
            rb=bounds(resized)
            tx=round(body_x(native)*2-body_x(resized));ty=nb[3]*2-rb[3]
            # Keep full extended canvas if AI silhouette exceeds the native canvas; never silently clip it.
            true=resized.getchannel('A').getbbox()
            left=min(0,tx+true[0]-4);top=min(0,ty+true[1]-4)
            right=max(512,tx+true[2]+4);bottom=max(512,ty+true[3]+4)
            aligned=Image.new('RGBA',(right-left,bottom-top));aligned.paste(resized,(tx-left,ty-top))
            aligned.save(ROOT/f'aligned_2x/{name}.png'); coverage=mask(aligned)
            coverage.save(ROOT/f'masks_2x/{name}.png')
            records[name]={'batch':key,'raw_size':list(sheet.size),'raw_rect':rect,'source_bounds':list(gb),
                'scale':factor,'translate':[tx,ty],'canvas_origin_px':[left,top], 'native_bounds':list(nb),
                'raw_clip':gb[0]<=0 or gb[1]<=0 or gb[2]>=clean.width or gb[3]>=clean.height,
                'registration':'shared batch scale + native lower-body median x and alpha baseline; falling/prone separately measured',
                'tone':'encoded RGB multiplied by encoded luminance**0.10; same curve for every pose',
                'matte':stats}
    (ROOT/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
    keys=list(records)
    for batchname in sorted({v['batch'] for v in records.values()}):
        names=[n for n in keys if records[n]['batch']==batchname]
        contact=Image.new('RGB',(len(names)*256,2*280),(48,48,48));draw=ImageDraw.Draw(contact)
        for i,name in enumerate(names):
            for row,directory in enumerate(['native','aligned_2x']):
                im=Image.open(ROOT/directory/f'{name}.png').convert('RGBA')
                if row: im=resize_base(im,(round(im.width/2),round(im.height/2)))
                x=i*256;y=row*280+24
                contact.paste(im,(x,y),im);draw.text((x+3,y-20),name+(' native' if row==0 else ' restored'),fill='white')
        contact.save(ROOT/f'review/{batchname}_comparison.png')
    if 'm162sa0' in records:
        contact=Image.new('RGB',(5*256,4*280),(48,48,48));draw=ImageDraw.Draw(contact)
        for view in range(5):
            name=f'm162sa{view}';base=Image.open(ROOT/f'aligned_2x/{name}.png');coverage=Image.open(ROOT/f'masks_2x/{name}.png')
            for row,palette in enumerate([163,164,165,0]):
                if palette: im=recolor(base,coverage,palette)
                else:
                    a=np.array(base);w=np.array(coverage)/255;a[:,:,:3]=np.round(a[:,:,:3]*(1-.7*w[:,:,None])+np.array([255,110,0])*.7*w[:,:,None]).astype(np.uint8);im=Image.fromarray(a)
                im=im.convert('RGBa').resize((256,256),Image.Resampling.LANCZOS).convert('RGBA')
                contact.paste(im,(view*256,row*280+24),im);draw.text((view*256+5,row*280+5),f'{palette or "Mask overlay"}, view {view}',fill='white')
        contact.save(ROOT/'review/standing_variants.png')
    print(json.dumps({'processed':len(records),'raw_clipped':[n for n,v in records.items() if v['raw_clip']]}))

if __name__=='__main__': run()
