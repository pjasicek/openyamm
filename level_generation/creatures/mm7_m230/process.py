"""Deterministic m230 matte extraction, selective recoloring, and native registration."""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('matte',ROOT.parent/'mm6_goblin/direct_ai_attack/clean_edges.py')
matte=importlib.util.module_from_spec(spec); spec.loader.exec_module(matte)
spec=importlib.util.spec_from_file_location('pose_tools',ROOT.parent/'mm7_m514/process.py')
pose_tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(pose_tools)

def extract_detail(image,*args):
    if image.mode=='RGBA' and image.getchannel('A').getextrema()[0]<255:
        rgba=np.array(image);alpha=rgba[:,:,3]
        labels,count=ndimage.label(alpha>0)
        maxima=ndimage.maximum(alpha,labels,np.arange(count+1))
        # Discard detached 1/255-opacity gutter noise, preserving full connected soft edges.
        rgba[(alpha>0)&(maxima[labels]<=1)]=0
        return Image.fromarray(rgba)
    return matte.extract(image.convert('RGB'))[0]

pose_tools.extract=extract_detail

def resize_base(im, size):
    """Preserve alpha filtering; constrain resampling-created magenta only at base contours.

    This green m230 base has no purple material. Its cleaned foreground permits at most
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
    rgb=np.array(im)[:,:,:3].astype(float)/255
    r,g,b=rgb.transpose(2,0,1)
    # Forest-green textile is distinct from neutral steel/white, warm gold, and brown leather.
    strength=np.maximum(0,g-np.maximum(r,b))
    weight=np.clip((strength-.009)/.07,0,1)*np.clip((strength/np.maximum(g,.015)-.07)/.26,0,1)
    weight[np.array(im)[:,:,3]==0]=0
    return Image.fromarray(np.round(weight*255).astype(np.uint8),'L')

def recolor(im,coverage,palette):
    if palette==54:
        return im.copy()
    rgb=np.array(im).astype(float)/255
    c=rgb[:,:,:3]; w=np.array(coverage).astype(float)/255
    # Preserve green-region tone and achromatic detail; move only its green chromatic component.
    neutral=np.minimum(c[:,:,0],c[:,:,2])
    chroma=np.maximum(0,c[:,:,1]-neutral)
    ramp={55:np.array([.20,.18,1.0]),233:np.array([1.0,.12,.27])}[palette]
    target=neutral[:,:,None]+chroma[:,:,None]*ramp
    rgb[:,:,:3]=c*(1-w[:,:,None])+target*w[:,:,None]
    result=np.round(np.clip(rgb,0,1)*255).astype(np.uint8)
    result[:,:,3]=np.array(im)[:,:,3]
    return Image.fromarray(result)

def bounds(im):
    return Image.fromarray((np.array(im)[:,:,3]>96).astype(np.uint8)*255).getbbox()

def body_x(im):
    a=np.array(im)[:,:,3]>128; box=bounds(im)
    y0=round(box[1]+(box[3]-box[1])*.35);y1=round(box[1]+(box[3]-box[1])*.9)
    xs=np.where(a[y0:y1])[1]
    return float(np.median(xs))

def run():
    batches=json.loads((ROOT/'batches.json').read_text());records={}
    generation=json.loads((ROOT/'generation.json').read_text())['batches']
    for directory in ['cleaned','aligned_2x','masks_2x','review']:
        (ROOT/directory).mkdir(exist_ok=True)
    for key,batch in batches.items():
        if not generation.get(key,{}).get('selected'):continue
        raw=ROOT/generation[key]['selected']
        sheet=Image.open(raw)
        if key=='hit_3_detail_0' and raw.name=='hit_3_detail_0_v1.png':
            # Reviewed all three bottom-row boots: alpha>1 ends by row 1015.
            # Attached 1/255-alpha tails continue into the bottom gutter.
            # Keep two extra edge rows; remove only that demonstrated noise.
            pixels=np.array(sheet)
            gutter=pixels[1018:,:]
            gutter[gutter[:,:,3]==1]=0
            sheet=Image.fromarray(pixels)
        if key=='walk_0_detail_0' and raw.name=='walk_0_detail_0_v1.png':
            # All alpha>1 ends at y=1244; only attached 1/255 gutter noise remains.
            pixels=np.array(sheet)
            gutter=pixels[1248:,:]
            gutter[gutter[:,:,3]==1]=0
            sheet=Image.fromarray(pixels)
        cols,rows=batch['columns'],batch['rows']; entries=[]
        cells=pose_tools.connected_pose_cells(sheet,batch,8) if 'native_window' in batch else None
        for i,name in enumerate(batch['frames']):
            rect=(round((i%cols)*sheet.width/cols),round((i//cols)*sheet.height/rows),
                  round((i%cols+1)*sheet.width/cols),round((i//cols+1)*sheet.height/rows))
            if key=='walk_0':
                # The first-row planted boot extends past the nominal half-height divider.
                divider=round(sheet.height*.55)
                rect=(rect[0],0 if i<cols else divider,rect[2],divider if i<cols else sheet.height)
            # Reviewed empty gap between death-d and corpse: preserve the corpse's leftward sword tip.
            if key=='death_corpse' and i in (3,4):
                boundary=round(sheet.width*.313)
                rect=(rect[0],rect[1],boundary,rect[3]) if i==3 else (boundary,rect[1],rect[2],rect[3])
            if cells:
                clean,rect=cells[i]
                stats={'method':'connected full-pose extraction; supplied RGBA retained or legacy matte unmixed'}
            else:
                cell=sheet.crop(rect)
                if cell.mode=='RGBA' and cell.getchannel('A').getextrema()[0]<255:
                    clean=cell; stats={'method':'native alpha'}
                else:
                    clean,stats=matte.extract(cell.convert('RGB'))
            native=Image.open(ROOT/f'native/{name}.png')
            nb,gb=bounds(native),bounds(clean)
            ratio=(nb[3]-nb[1])*2/(gb[3]-gb[1])
            entries.append((name,clean,native,nb,gb,rect,stats,ratio))
        common=float(np.median([e[-1] for e in entries]))
        # Ordered walk review demonstrated coherent row-wise generator zoom drift.
        # Calibrate each three-pose row against the same native poses, retaining
        # one uniform transform per row and native differences within the row.
        row_calibration=key in ('walk_0_detail_0','walk_1_detail_0','walk_3_detail_0')
        row_scales={}
        if row_calibration:
            for row in range(rows):
                row_scales[row]=float(np.median([e[-1] for e in entries[row*cols:(row+1)*cols]]))
        for name,clean,native,nb,gb,rect,stats,ratio in entries:
            if name in batch.get('reference_only_frames',[]):continue
            clean.save(ROOT/f'cleaned/{name}.png')
            # Falling/prone poses require their own anatomical reference, measured by width when horizontal.
            factor=common
            if row_calibration:
                factor=row_scales[batch['frames'].index(name)//cols]
            if key.startswith('death_corpse'):
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
                'matte':stats}
            if row_calibration:
                records[name]['registration']='shared three-pose row scale correcting demonstrated generator row zoom + native lower-body median x and alpha baseline'
    (ROOT/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
    settings={'tone_rgb_multiplier':1.0,'export_scale':2,'masks':'R8 linear',
        'raw_selection':'generation.json selects immutable legacy and replacement outputs',
        'native_alpha':'Preserve supplied RGBA; remove only disconnected components with maximum opacity 1/255.',
        'local_alpha_cleanup':{'walk_0_detail_0_v1.png':'Clear alpha exactly 1 only at y>=1248; reviewed gutter noise, alpha>1 ends at1244.','hit_3_detail_0_v1.png':'Clear alpha exactly 1 only at y>=1018; reviewed attached gutter noise below intact nd3/ne3/nf3 boots, alpha>1 ends by row 1015.'},
        'opaque_extraction':'Retained original magenta matte helper for opaque legacy sheets.',
        'registration':'Common batch height scale and native lower-body median x / alpha baseline. Horizontal collapse poses use native width.',
        'row_scale_corrections':{'batches':['walk_0_detail_0','walk_1_detail_0','walk_3_detail_0'],
            'method':'Shared median native/raw height ratio per three-pose row; preserve relative pose differences within each row.',
            'evidence':'Ordered native/2x walk contacts showed row-wise scale jumps. Original front-oblique raw/native ratios 3.030-3.081 in row 0 vs 2.790-2.838 in row 1.'},
        'resize':'Premultiplied-alpha Lanczos with retained base contour magenta limit 10/255.',
        'recolor':'Retained selective green chroma transfer in normalized sRGB; palette 54 exact bypass, 55 blue, 233 red.'}
    (ROOT/'processing_settings.json').write_text(json.dumps(settings,indent=2)+'\n')
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
    if 'm230sa0' in records:
        contact=Image.new('RGB',(5*256,4*280),(48,48,48));draw=ImageDraw.Draw(contact)
        for view in range(5):
            name=f'm230sa{view}';base=Image.open(ROOT/f'aligned_2x/{name}.png');coverage=Image.open(ROOT/f'masks_2x/{name}.png')
            for row,palette in enumerate([54,55,233,0]):
                if palette: im=recolor(base,coverage,palette)
                else:
                    a=np.array(base);w=np.array(coverage)/255;a[:,:,:3]=np.round(a[:,:,:3]*(1-.7*w[:,:,None])+np.array([255,110,0])*.7*w[:,:,None]).astype(np.uint8);im=Image.fromarray(a)
                im=im.convert('RGBa').resize((256,256),Image.Resampling.LANCZOS).convert('RGBA')
                contact.paste(im,(view*256,row*280+24),im);draw.text((view*256+5,row*280+5),f'{palette or "Mask overlay"}, view {view}',fill='white')
        contact.save(ROOT/'review/standing_variants.png')
    print(json.dumps({'processed':len(records),'raw_clipped':[n for n,v in records.items() if v['raw_clip']]}))

if __name__=='__main__': run()
