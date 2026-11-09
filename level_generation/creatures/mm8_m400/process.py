"""Offline m400 cleanup and registration; reviewed settings are family-specific."""
from pathlib import Path
import json
import hashlib
import importlib.util
import argparse
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
HERE=ROOT.parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

queue=module('mm8_queue',HERE/'mm8_restore_queue.py')
matte=module('native_matte',HERE/'mm6_goblin/direct_ai_attack/clean_edges.py')

def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n')

def spill(im):
    a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3]
    band=(alpha>0)&((ndimage.distance_transform_edt(alpha>=250)<=4)|(alpha<255))
    score=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1])*alpha/255*band
    y,x=np.unravel_index(np.argmax(score),score.shape)
    return dict(max_score=float(score.max()),candidates_above_12=int((score>12).sum()),position=[int(x),int(y)],band_px=4,matte=[255,0,255])

def fix(im):
    a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3]
    band=(alpha>0)&((ndimage.distance_transform_edt(alpha>=250)<=4)|(alpha<255))
    excess=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-8)*band
    c[:,:,0]-=excess;c[:,:,2]-=excess
    a[:,:,:3]=np.round(np.clip(c,0,255)).astype(np.uint8)
    a[alpha==0]=0
    return Image.fromarray(a)

def composite(im,color):
    out=Image.new('RGBA',im.size,(*color,255));out.alpha_composite(im);return out.convert('RGB')

def process(batch,raw_name,prompt_name,identity=None):
    batches=json.loads((ROOT/'batches.json').read_text());b=batches[batch]
    inv=json.loads((ROOT/'sources.json').read_text())
    raw_path=ROOT/'raw'/raw_name
    raw=Image.open(raw_path).convert('RGB')
    for d in ('cleaned','aligned_2x','review','checkpoints'):(ROOT/d).mkdir(exist_ok=True)
    config_path=ROOT/'processing.json'
    config=json.loads(config_path.read_text()) if config_path.exists() else {}
    rectangles=[]
    if batch=='identity':
        # The generated top feet extend below nominal row 512; empty row 527 is the safe split.
        rectangles=[[i%3*512,0 if i<3 else 528,(i%3+1)*512,528 if i<3 else 1024] for i in range(5)]
    else:
        cols,rows=b['columns'],b['rows']
        rectangles=[[round(i%cols*raw.width/cols),round(i//cols*raw.height/rows),
                     round((i%cols+1)*raw.width/cols),round((i//cols+1)*raw.height/rows)] for i in range(len(b['frames']))]
    rectangles=config.get('batch_rectangles',{}).get(batch,rectangles)
    extracted=[]
    ratios=[]
    for n,rect in zip(b['frames'],rectangles):
        rgba,stats=matte.extract(raw.crop(rect));rgba=fix(rgba)
        bounds=rgba.getchannel('A').getbbox()
        if not bounds:raise ValueError('Empty cell '+n)
        if bounds[0]<=0 or bounds[1]<=0 or bounds[2]>=rgba.width or bounds[3]>=rgba.height:
            raise ValueError('Extraction edge touched: '+n+' '+str(bounds))
        source=queue.native(ROOT,n)
        sb=source.getchannel('A').getbbox()
        ratios.append((sb[3]-sb[1])*2/(bounds[3]-bounds[1]))
        extracted.append((n,rgba,bounds,source,sb,stats,rect))
    if batch=='identity':
        # Standing body heights establish one global anatomical scale, frozen for this sheet.
        ratio=float(np.median(ratios))
        ng=[];gg=[]
        for n,im,bb,source,sb,stats,rect in extracted:
            na=np.asarray(source);ga=np.asarray(im)
            ng.extend((na[:,:,:3][na[:,:,3]>128]@np.array([.2126,.7152,.0722])).tolist())
            gg.extend((ga[:,:,:3][ga[:,:,3]>128]@np.array([.2126,.7152,.0722])).tolist())
        exposure=float(np.median(ng)/np.median(gg))
        config.update(identity_generated_to_2x=ratio,tone_multiplier=exposure,
                      tone_method='One standing-sheet median luminance ratio, fixed for the family; no per-frame histogram changes.',
                      matte='magenta absent from base materials',edge_limit=8,premultiplied_resize='Lanczos',
                      identity_rectangles=rectangles)
        save(config_path,config)
    else:
        # This unarmed family has no raised weapon confounding full-body calibration.
        # One shared scale per sheet, with every native pose paired; review verifies prone-body mass.
        ratio=config.get('batch_scales',{}).get(batch,float(np.median(ratios)))
    registration=json.loads((ROOT/'registration.json').read_text()) if (ROOT/'registration.json').exists() else {}
    review=Image.new('RGB',(len(extracted)*320,700),(40,40,40));draw=ImageDraw.Draw(review)
    edge=Image.new('RGB',(len(extracted)*200,420),(40,40,40))
    for i,(n,im,bb,source,sb,stats,rect) in enumerate(extracted):
        a=np.array(im);a[:,:,:3]=np.round(a[:,:,:3]*config['tone_multiplier']).clip(0,255).astype(np.uint8)
        im=Image.fromarray(a);im.save(ROOT/f'cleaned/{n}.png')
        scaled=fix(im.convert('RGBa').resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS).convert('RGBA'))
        dest=Image.new('RGBA',(source.width*2,source.height*2))
        # Reviewed standing anatomical registration: native feet and torso center, common sheet scale.
        native_a=np.asarray(source)[:,:,3]>128
        restored_a=np.asarray(im)[:,:,3]>128
        ny0=round(sb[1]+.25*(sb[3]-sb[1]));ny1=round(sb[1]+.62*(sb[3]-sb[1]))
        gy0=round(bb[1]+.25*(bb[3]-bb[1]));gy1=round(bb[1]+.62*(bb[3]-bb[1]))
        nx=float(np.median(np.where(native_a[ny0:ny1])[1]));gx=float(np.median(np.where(restored_a[gy0:gy1])[1]))
        offset=[round(nx*2-gx*ratio),round(sb[3]*2-bb[3]*ratio)]
        # Keep the full aligned support, including filter padding beyond native canvas.
        bounds=scaled.getchannel('A').getbbox()
        origin=[min(0,offset[0]+bounds[0]-4),min(0,offset[1]+bounds[1]-4)]
        size=[max(dest.width,offset[0]+bounds[2]+4)-origin[0],max(dest.height,offset[1]+bounds[3]+4)-origin[1]]
        aligned=Image.new('RGBA',size);aligned.paste(scaled,(offset[0]-origin[0],offset[1]-origin[1]))
        aligned.save(ROOT/f'aligned_2x/{n}.png')
        record=dict(batch=batch,raw=raw_name,extraction_xyxy=rect,scale_to_2x=ratio,translation_px=offset,
                    canvas_origin_px=origin,aligned_size_px=size,logical_size=list(source.size),
                    source_sha256=inv['sources'][n]['sha256'],raw_clip=False,
                    generated_visible_height=bb[3]-bb[1],native_visible_height=sb[3]-sb[1],
                    edge_cleaned=spill(im),edge_export=spill(aligned))
        registration[n]=record
        for row,pic in enumerate((source.resize((source.width*2,source.height*2),Image.Resampling.NEAREST),aligned)):
            show=composite(pic,(40,40,40));show.thumbnail((310,320),Image.Resampling.LANCZOS)
            review.paste(show,(i*320+(320-show.width)//2,row*350+30))
        draw.text((i*320+5,5),n+' native',fill='white');draw.text((i*320+5,355),'restored 2x',fill='white')
        x,y=record['edge_export']['position'];patch=aligned.crop((x-20,y-20,x+20,y+20))
        for j,bg in enumerate(((25,25,25),(235,235,235))):
            edge.paste(composite(patch,bg).resize((200,200),Image.Resampling.NEAREST),(i*200,j*210))
    review.save(ROOT/f'review/{batch}_native_restored.png');edge.save(ROOT/f'review/{batch}_edges.png')
    save(ROOT/'registration.json',registration)
    generation=json.loads((ROOT/'generation.json').read_text()) if (ROOT/'generation.json').exists() else {'tool':'built-in image_gen','batches':{}}
    refs=[ROOT/'raw/identity_v1.png'] if batch=='identity' else [ROOT/f'references/{batch}_matte.png']
    if identity:refs.append(ROOT/identity)
    generation['batches'][batch]=dict(raw={'path':str(raw_path.relative_to(ROOT)),'sha256':queue.sha(raw_path)},
       prompt={'path':'prompts/'+prompt_name,'sha256':queue.sha(ROOT/'prompts'/prompt_name)},
       references=[dict(path=str(p.relative_to(ROOT)),sha256=queue.sha(p)) for p in refs],
       dimensions=list(raw.size),status='processed_unreviewed')
    save(ROOT/'generation.json',generation)
    batches[batch]['state']='processed_unreviewed'
    batches[batch]['selected_raw']=raw_name
    save(ROOT/'batches.json',batches)
    ledger=json.loads((HERE/'mm8_remaining/progress.json').read_text())
    ledger['families']['m400']['status']='partial'
    ledger['families']['m400']['processed_frames']=len(registration)
    ledger['families']['m400']['resume']='Review mm8_m400/review/identity_native_restored.png and identity_edges.png; accept identity before dependent batches. Full family remains incomplete.'
    ledger['summary']={s:sum(r['status']==s for r in ledger['families'].values()) for s in ('pending','partial','validated','blocked')}
    save(HERE/'mm8_remaining/progress.json',ledger)
    print(json.dumps({'batch':batch,'frames':len(extracted),'settings':config,'reviewed':False},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('raw');p.add_argument('prompt');p.add_argument('--identity')
    a=p.parse_args();process(a.batch,a.raw,a.prompt,a.identity)
