"""Deterministic extraction/registration for this goal, with reviewed per-family material settings."""
import argparse, json, importlib.util, shutil
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from prepare_family import HERE, REPO, load, native

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
matte=module('peasant_matte',HERE.parent/'mm6_goblin/direct_ai_attack/clean_edges.py')

def fix_contour(im,matte_color):
    a=np.array(im);rgb=a[:,:,:3].astype(np.int16);alpha=a[:,:,3]
    order=[0,1,2] if matte_color=='magenta' else [1,0,2]
    c=rgb[:,:,order];edge=(alpha>0)&((ndimage.distance_transform_edt(alpha>=128)<=4)|(alpha<255))
    excess=np.where(edge,np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-10),0)
    c[:,:,0]-=excess;c[:,:,2]-=excess;a[:,:,:3]=c[:,:,order].astype(np.uint8)
    return Image.fromarray(a)

def resize_base(im,size,config):
    return fix_contour(im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA'),config['matte'])

def mask(im,config):
    if config.get('material_module'):
        return module('family_materials',HERE.parent/('mm6_'+config['family'])/config['material_module']).coverage(im)
    if config['mask_kind']=='gua_regions':
        return module('guard_materials',HERE.parent/'mm6_gua/materials.py').coverage(im)
    if config['mask_kind']=='mep_regions':
        from mep_materials import coverage
        return coverage(im)
    a=np.array(im);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    kind=config['mask_kind']
    if kind=='green':strength=np.maximum(0,g-np.maximum(r,b));dominant=g
    elif kind=='blue':strength=np.maximum(0,b-np.maximum(r,g));dominant=b
    elif kind=='olive':
        # NATF's armor is yellow-green, while skin/leather/gold are warmer.
        # Hue range excludes neutral blade/feather highlights and brown skin.
        hsv=np.array(im.convert('RGB').convert('HSV')).astype(float)
        hue=hsv[:,:,0]*360/255;saturation=hsv[:,:,1]/255
        upper=config.get('olive_hue_upper',95)
        w=np.clip((hue-38)/7,0,1)*np.clip((upper-hue)/10,0,1)*np.clip((saturation-.32)/.16,0,1)
        # Keep coherent olive materials, excluding small warm specks on neutral gear.
        labels,count=ndimage.label(w>.5)
        sizes=np.bincount(labels.ravel());accepted=sizes>=32;accepted[0]=False
        core=accepted[labels]
        w*=ndimage.binary_dilation(core,iterations=2)
        # Low-saturation highlights inside armor retain its palette; a thin blade
        # outside that material does not become a recolorable specular stripe.
        holes=ndimage.binary_fill_holes(core)&~core
        candidate=np.clip((hue-38)/7,0,1)*np.clip((upper-hue)/10,0,1)*np.clip((saturation-.08)/.08,0,1)
        w[holes]=np.maximum(w[holes],candidate[holes])
    else:raise ValueError('This family needs explicit reviewed mask logic: '+kind)
    if kind!='olive':
        w=np.clip((strength-.002)/.014,0,1)*np.clip((strength/np.maximum(dominant,.01)-.015)/.075,0,1)
    hue_range=config.get('material_mask_hue_range')
    if hue_range is not None:
        # Some restored cloth is muted yellow-green rather than green-dominant.
        # A reviewed hue window covers that material without selecting warm leather.
        lower,upper=hue_range
        transition=config.get('material_mask_hue_transition',6)
        saturation_floor=config.get('material_mask_hue_saturation_floor',.08)
        assert 0 <= lower < upper <= 360 and transition > 0
        assert 0 <= saturation_floor < 1
        hsv=np.array(im.convert('RGB').convert('HSV')).astype(float)
        hue=hsv[:,:,0]*360/255;saturation=hsv[:,:,1]/255
        hue_coverage=np.clip((hue-lower)/transition,0,1)*np.clip((upper-hue)/transition,0,1)
        hue_coverage*=np.clip((saturation-saturation_floor)/.08,0,1)
        w=np.maximum(w,hue_coverage)
    minimum_saturation=config.get('material_mask_minimum_saturation')
    if minimum_saturation is not None:
        transition=config.get('material_mask_saturation_transition',.08)
        assert 0 <= minimum_saturation < 1 and transition > 0
        saturation=(c.max(axis=2)-c.min(axis=2))/np.maximum(c.max(axis=2),.01)
        w*=np.clip((saturation-minimum_saturation)/transition,0,1)
    # Matte unmixing can introduce slight green into otherwise neutral contour pixels.
    # Carry nearby interior material coverage to this narrow fringe, not its altered hue.
    depth=ndimage.distance_transform_edt(a[:,:,3]>=250)
    interior=depth>3
    if interior.any():
        dist,idx=ndimage.distance_transform_edt(~interior,return_indices=True)
        fringe=(a[:,:,3]>0)&~interior&(dist<=5)
        w[fringe]=w[idx[0],idx[1]][fringe]
    w[a[:,:,3]==0]=0
    return Image.fromarray(np.round(w*255).astype(np.uint8),'L')

def ramps(config,inv):
    if config.get('material_module'):
        return module('family_materials',HERE.parent/('mm6_'+config['family'])/config['material_module']).fit(config,inv,REPO)
    if config['mask_kind']=='gua_regions':
        return module('guard_materials',HERE.parent/'mm6_gua/materials.py').fit(config,inv,REPO)
    if config['mask_kind']=='mep_regions':
        from mep_materials import fit
        return fit(config,inv,REPO)
    base=config['base_palette'];colors={int(p):np.frombuffer((REPO/f'assets_dev/worlds/mm6/textures/pal{p}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for p in inv['variants']}
    r,g,b=colors[base].T
    selected=(g>r+.015)&(g>b+.015) if config['mask_kind']=='green' else (b>r+.02)&(b>g+.02)
    if config['mask_kind']=='olive':selected=(g>r*.80)&(g>b*1.15)
    # Only native-used indices participate; fixed fit, no per-frame histograms.
    used=np.zeros(256,bool)
    for name in inv['sources']:used[np.unique(np.array(Image.open(REPO/f'assets_dev/engine/sprites/{name}.bmp')))]=True
    changed=np.zeros(256,bool)
    for pal,c in colors.items():
        if pal!=base:changed |= np.max(np.abs(c-colors[base]),axis=1)>.03
    selected &= used & changed;assert selected.sum()>3
    y=colors[base][selected]@np.array([.2126,.7152,.0722])
    return {p:((y[:,None]*c[selected]).sum(axis=0)/(y*y).sum()).tolist() for p,c in colors.items() if p!=base}

def recolor(im,coverage,palette,config,vectors):
    if config.get('material_module'):
        return module('family_materials',HERE.parent/('mm6_'+config['family'])/config['material_module']).recolor(im,coverage,palette,config,vectors)
    if config['mask_kind']=='gua_regions':
        return module('guard_materials',HERE.parent/'mm6_gua/materials.py').recolor(im,coverage,palette,config,vectors)
    if config['mask_kind']=='mep_regions':
        from mep_materials import recolor as material_recolor
        return material_recolor(im,coverage,palette,config,vectors)
    if palette==config['base_palette']:return im.copy()
    a=np.array(im);c=a[:,:,:3].astype(float)/255;w=np.array(coverage).astype(float)/255
    y=c@np.array([.2126,.7152,.0722]);target=y[:,:,None]*np.array(vectors[palette])
    a[:,:,:3]=np.round(np.clip(c*(1-w[:,:,None])+target*w[:,:,None],0,1)*255).astype(np.uint8)
    return Image.fromarray(a)

def bounds(im):return Image.fromarray((np.array(im)[:,:,3]>96).astype(np.uint8)*255).getbbox()
def body_x(im):
    b=bounds(im);a=np.array(im)[:,:,3]>128;y0=round(b[1]+(b[3]-b[1])*.3);y1=round(b[1]+(b[3]-b[1])*.85)
    return float(np.median(np.where(a[y0:y1])[1]))

def gutters(occupied,count):
    size=len(occupied);cuts=[0]
    for i in range(1,count):
        center=size*i/count;radius=size/count*.24;start=max(0,round(center-radius));end=min(size,round(center+radius))
        labels,n=ndimage.label(~occupied[start:end]);gaps=[np.where(labels==v)[0]+start for v in range(1,n+1)]
        assert gaps,'No verified empty gutter: inspect source rather than clip it'
        gap=max(gaps,key=len);cuts.append(int((gap[0]+gap[-1])//2))
    return cuts+[size]

def run(family):
    root,config,inv=load(family);canvas=inv['logical_canvas'];batches=json.loads((root/'batches.json').read_text());records={}
    for d in ['cleaned','aligned_2x','masks_2x','review']:(root/d).mkdir(exist_ok=True)
    for key,b in batches.items():
        path=root/f'raw/{key}.png'
        if not path.exists():continue
        sheet=Image.open(path);rgb=np.array(sheet.convert('RGB')).astype(float)/255
        if config['matte']=='cyan':rgb=rgb[:,:,[1,0,2]]
        fg=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]<.55
        if sheet.mode=='RGBA' and sheet.getchannel('A').getextrema()[0]<255:fg=np.array(sheet.getchannel('A'))>0
        yc=gutters(fg.any(axis=1),b['rows']);entries=[]
        for i,name in enumerate(b['frames']):
            row=i//b['columns'];col=i%b['columns'];xc=gutters(fg[yc[row]:yc[row+1]].any(axis=0),b['columns'])
            rect=config.get('raw_cell_rect_overrides',{}).get(name,[xc[col],yc[row],xc[col+1],yc[row+1]])
            cell=sheet.crop(rect)
            original=native(name,config['base_palette'],canvas,inv)
            if name in config.get('native_particle_endpoints', []) or original.getbbox() is None:
                # Explicit sparse-decay policy, or a genuinely empty native image: no invented replacement mass.
                count=int((np.array(original)[:,:,3]>0).sum())
                assert count<=300, (name,count)
                preserved=original.resize((canvas[0]*2,canvas[1]*2),Image.Resampling.NEAREST)
                preserved.save(root/f'cleaned/{name}.png')
                preserved.save(root/f'aligned_2x/{name}.png')
                mask(preserved,config).save(root/f'masks_2x/{name}.png')
                records[name]=dict(batch=key,raw_size=sheet.size,raw_rect=rect,scale=2,
                    translate=[0,0],canvas_origin_px=[0,0],native_bounds=original.getbbox(),raw_clip=False,
                    matte={'method':'exact native sparse/empty endpoint; generated cell rejected',
                           'native_visible_pixels':count})
                continue
            # Reviewed nonrectangular ownership where neighboring loose equipment
            # overlaps in X but occupies a different Y band. Only erase foreign art.
            for exclusion in config.get('raw_cell_foreign_rects',{}).get(name,[]):
                box=[exclusion[0]-rect[0],exclusion[1]-rect[1],exclusion[2]-rect[0],exclusion[3]-rect[1]]
                fill=(255,0,255) if config['matte']=='magenta' else (0,255,255)
                if cell.mode=='RGBA':fill=(*fill,0)
                ImageDraw.Draw(cell).rectangle(box,fill=fill)
            if cell.mode=='RGBA' and cell.getchannel('A').getextrema()[0]<255:clean=cell;stats={'method':'supplied alpha'}
            else:
                c=np.array(cell.convert('RGB'))
                if config['matte']=='cyan':c=c[:,:,[1,0,2]]
                clean,stats=matte.extract(Image.fromarray(c))
                if config['matte']=='cyan':c=np.array(clean);c[:,:,:3]=c[:,:,[1,0,2]];clean=Image.fromarray(c)
            clean=fix_contour(clean,config['matte']);clean.save(root/f'cleaned/{name}.png')
            original=native(name,config['base_palette'],canvas,inv);nb,gb=bounds(original),bounds(clean);assert gb,name
            entries.append((name,clean,original,nb,gb,rect,stats))
        scale=float(np.median([2*(nb[3]-nb[1])/(gb[3]-gb[1]) for _,_,_,nb,gb,_,_ in entries])) if entries else 1.0
        for name,clean,original,nb,gb,rect,stats in entries:
            factor=scale
            if key=='death_corpse':factor=2*(nb[2]-nb[0])/(gb[2]-gb[0]) if nb[2]-nb[0]>nb[3]-nb[1] else 2*(nb[3]-nb[1])/(gb[3]-gb[1])
            im=resize_base(clean,(round(clean.width*factor),round(clean.height*factor)),config);rb=bounds(im)
            tx=round(body_x(original)*2-body_x(im));ty=nb[3]*2-rb[3];box=im.getbbox()
            left=min(0,tx+box[0]-4);top=min(0,ty+box[1]-4);right=max(canvas[0]*2,tx+box[2]+4);bottom=max(canvas[1]*2,ty+box[3]+4)
            aligned=Image.new('RGBA',(right-left,bottom-top));aligned.paste(im,(tx-left,ty-top))
            polygon=config.get('neutral_material_polygons',{}).get(name)
            repair=None
            if polygon:
                repair=Image.new('L',aligned.size);ImageDraw.Draw(repair).polygon([tuple(p) for p in polygon],fill=255)
                a=np.array(aligned);selected=(np.array(repair)>0)&(a[:,:,3]>0)&(a[:,:,1]>=a[:,:,0])
                grey=np.round(a[:,:,:3]@np.array([.2126,.7152,.0722])).astype(np.uint8)
                a[:,:,:3][selected]=grey[selected,None];aligned=Image.fromarray(a)
            coverage=mask(aligned,config)
            if repair is not None:
                w=np.array(coverage);w[np.array(repair)>0]=0;coverage=Image.fromarray(w)
            aligned.save(root/f'aligned_2x/{name}.png');coverage.save(root/f'masks_2x/{name}.png')
            records[name]={'batch':key,'raw_size':sheet.size,'raw_rect':rect,'scale':factor,'translate':[tx,ty],
                'canvas_origin_px':[left,top],'native_bounds':nb,'matte':stats,
                'raw_clip':gb[0]<=0 or gb[1]<=0 or gb[2]>=clean.width or gb[3]>=clean.height}
    for name,canonical in inv['pixel_aliases'].items():
        if canonical not in records:continue
        for d in ['cleaned','aligned_2x','masks_2x']:shutil.copy2(root/d/f'{canonical}.png',root/d/f'{name}.png')
        records[name]=dict(records[canonical],pixel_alias=canonical)
    (root/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
    for key,b in batches.items():
        names=[n for n in b['frames'] if n in records]
        if not names:continue
        cw=max(canvas[0]+16,240);ch=canvas[1]+34;contact=Image.new('RGB',(len(names)*cw,2*ch),(43,45,43));d=ImageDraw.Draw(contact)
        for i,name in enumerate(names):
            src=native(name,config['base_palette'],canvas,inv);im=Image.open(root/f'aligned_2x/{name}.png');im=resize_base(im,(round(im.width/2),round(im.height/2)),config)
            origin=records[name]['canvas_origin_px'];contact.paste(src,(i*cw+8,28),src);contact.paste(im,(i*cw+8+round(origin[0]/2),ch+28+round(origin[1]/2)),im)
            d.text((i*cw+4,6),name+' native / restored',fill='white')
        contact.save(root/f'review/{key}_comparison.png')
    (root/'recolor_vectors.json').write_text(json.dumps(ramps(config,inv),indent=2)+'\n')
    print(json.dumps({'family':family,'processed':len(records),'clipped':[n for n,r in records.items() if r['raw_clip']]}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family');run(p.parse_args().family)
