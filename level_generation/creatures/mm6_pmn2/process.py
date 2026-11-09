"""Deterministic pmn2 matting, native registration, and selective cloth recoloring."""
from pathlib import Path
import importlib.util,json,shutil
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
from prepare import ROOT, native, CANVAS
spec=importlib.util.spec_from_file_location('matte',ROOT.parent/'mm6_goblin/direct_ai_attack/clean_edges.py')
matte=importlib.util.module_from_spec(spec);spec.loader.exec_module(matte)
ALIASES={'pmn2fid0':'pmn2fic0','pmn2fie0':'pmn2fib0','pmn2fif0':'pmn2fia0'}
RAMPS={801:[1.20082748,.32973674,.35848369],803:[.71988815,.86409279,1.09847968]}

def contour_fix(im):
    a=np.array(im);c=a[:,:,:3].astype(np.int16);alpha=a[:,:,3]
    edge=(alpha>0)&((ndimage.distance_transform_edt(alpha>=128)<=4)|(alpha<255))
    excess=np.where(edge,np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-10),0)
    c[:,:,0]-=excess;c[:,:,2]-=excess;a[:,:,:3]=c.astype(np.uint8)
    return Image.fromarray(a)

def resize_base(im,size):
    return contour_fix(im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA'))

def mask(im):
    a=np.array(im);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    strength=np.maximum(0,g-np.maximum(r,b))
    w=np.clip((strength-.006)/.048,0,1)*np.clip((strength/np.maximum(g,.01)-.035)/.15,0,1)
    w[a[:,:,3]==0]=0
    return Image.fromarray(np.round(w*255).astype(np.uint8),'L')

def recolor(im,coverage,palette):
    if palette==802:return im.copy()
    a=np.array(im);c=a[:,:,:3].astype(float)/255;w=np.array(coverage)/255
    luminance=c@np.array([.2126,.7152,.0722]);target=luminance[:,:,None]*np.array(RAMPS[palette])
    out=a.copy();out[:,:,:3]=np.round(np.clip(c*(1-w[:,:,None])+target*w[:,:,None],0,1)*255).astype(np.uint8)
    return Image.fromarray(out)

def bounds(im):return Image.fromarray((np.array(im)[:,:,3]>96).astype(np.uint8)*255).getbbox()
def body_x(im):
    a=np.array(im)[:,:,3]>128;b=bounds(im);y0=round(b[1]+(b[3]-b[1])*.35);y1=round(b[1]+(b[3]-b[1])*.9)
    return float(np.median(np.where(a[y0:y1])[1]))

def run():
    batches=json.loads((ROOT/'batches.json').read_text());records={}
    for d in ['cleaned','aligned_2x','masks_2x','review']:(ROOT/d).mkdir(exist_ok=True)
    for key,b in batches.items():
        path=ROOT/f'raw/{key}.png'
        if not path.exists():continue
        sheet=Image.open(path);entries=[];cols=b['columns'];rows=b['rows']
        for i,name in enumerate(b['frames']):
            if name in ALIASES:continue
            rect=(round(i%cols*sheet.width/cols),round(i//cols*sheet.height/rows),round((i%cols+1)*sheet.width/cols),round((i//cols+1)*sheet.height/rows))
            if key=='death_corpse':
                # Reviewed empty gutters: top-row boots pass the nominal halfway split;
                # falling pose c's staff extends a little left of its column.
                edges=[0,512,992,sheet.width]
                rect=(edges[i%3],0 if i<3 else 568,edges[i%3+1],568 if i<3 else sheet.height)
            cell=sheet.crop(rect)
            if cell.mode=='RGBA' and cell.getchannel('A').getextrema()[0]<255:clean=cell;stats={'method':'native alpha'}
            else:clean,stats=matte.extract(cell.convert('RGB'))
            clean=contour_fix(clean);clean.save(ROOT/f'cleaned/{name}.png');original=native(name)
            nb,gb=bounds(original),bounds(clean);assert gb,name
            ratio=2*(nb[3]-nb[1])/(gb[3]-gb[1]);entries.append((name,clean,original,nb,gb,rect,stats,ratio))
        common=float(np.median([e[-1] for e in entries]))
        for name,clean,original,nb,gb,rect,stats,ratio in entries:
            factor=common
            if key=='death_corpse':
                factor=2*(nb[2]-nb[0])/(gb[2]-gb[0]) if nb[2]-nb[0]>nb[3]-nb[1] else ratio
            scaled=resize_base(clean,(round(clean.width*factor),round(clean.height*factor)));rb=bounds(scaled)
            tx=round(body_x(original)*2-body_x(scaled));ty=nb[3]*2-rb[3];box=scaled.getchannel('A').getbbox()
            left=min(0,tx+box[0]-4);top=min(0,ty+box[1]-4);right=max(CANVAS[0]*2,tx+box[2]+4);bottom=max(CANVAS[1]*2,ty+box[3]+4)
            aligned=Image.new('RGBA',(right-left,bottom-top));aligned.paste(scaled,(tx-left,ty-top))
            aligned.save(ROOT/f'aligned_2x/{name}.png');mask(aligned).save(ROOT/f'masks_2x/{name}.png')
            records[name]={'batch':key,'raw_size':list(sheet.size),'raw_rect':rect,'scale':factor,'translate':[tx,ty],
                'canvas_origin_px':[left,top],'native_bounds':list(nb),'matte':stats,
                'raw_clip':gb[0]<=0 or gb[1]<=0 or gb[2]>=clean.width or gb[3]>=clean.height}
    for name,source in ALIASES.items():
        if source not in records:continue
        for d in ['cleaned','aligned_2x','masks_2x']:shutil.copy2(ROOT/d/f'{source}.png',ROOT/d/f'{name}.png')
        records[name]=dict(records[source],pixel_alias=source)
    (ROOT/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
    for key,b in batches.items():
        names=[n for n in b['frames'] if n in records]
        if not names:continue
        contact=Image.new('RGB',(len(names)*350,610),(42,44,43));d=ImageDraw.Draw(contact)
        for i,n in enumerate(names):
            original=native(n);restored=Image.open(ROOT/f'aligned_2x/{n}.png')
            restored=resize_base(restored,(round(restored.width/2),round(restored.height/2)))
            origin=records[n]['canvas_origin_px']
            contact.paste(original,(i*350+9,30),original)
            contact.paste(restored,(i*350+9+round(origin[0]/2),335+round(origin[1]/2)),restored)
            d.text((i*350+5,6),n,fill='white')
        contact.save(ROOT/f'review/{key}_comparison.png')
    print(json.dumps({'processed':len(records),'clipped':[n for n,r in records.items() if r['raw_clip']]}))
if __name__=='__main__':run()
