"""Re-extract complete subjects and repair contour spill on explicitly scoped review copies."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage
from inspect_sources import HERE,OUT,foreground,read


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resize_rgba(im,size):return im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA')


def fit_native(subject,native):
    # Ignore almost-transparent tool residue when measuring the sprite's actual extent.
    opacity=np.asarray(subject.getchannel('A'))
    box=Image.fromarray((opacity>32).astype('uint8')*255).getbbox();dest=native.getbbox()
    result=Image.new('RGBA',(native.width*2,native.height*2))
    if not box or not dest:return result
    x,y,X,Y=[v*2 for v in dest]
    result.alpha_composite(resize_rgba(subject.crop(box),(X-x,Y-y)),(x,y))
    return result


def clean_spill(image,native,magenta=True,green=True):
    a=np.asarray(image.convert('RGBA')).copy();rgb=a[:,:,:3].astype(float);alpha=a[:,:,3]
    n=np.asarray(native.resize(image.size,Image.Resampling.NEAREST).convert('RGBA')).astype(float)
    visible=alpha>8;distance=ndimage.distance_transform_edt(np.pad(visible,1))[1:-1,1:-1]
    r,g,b=rgb.transpose(2,0,1);nr,ng,nb=n[:,:,:3].transpose(2,0,1)
    native_purple=(np.minimum(nr,nb)-ng>22)&(n[:,:,3]>96)
    protected=ndimage.binary_dilation(native_purple,iterations=3)
    pink=visible&(distance<=4)&(np.minimum(r,b)-g>20)&(r>40)&(b>35)&~protected if magenta else np.zeros_like(visible)
    # Muted purple metal must not protect a saturated fuchsia fringe beside it.
    native_chroma=ndimage.maximum_filter(np.where(n[:,:,3]>96,np.minimum(nr,nb)-ng,0),size=7)
    if magenta:
        pink|=visible&(np.minimum(r,b)-g>65)&(np.minimum(r,b)-g>native_chroma+45)
        pink|=visible&(np.minimum(r,b)-g>110)&(np.minimum(r,b)>150)&(n[:,:,3]<32)
    green_bad=visible&(g-np.maximum(r,b)>12)&((distance<=4)|(alpha<240)) if green else np.zeros_like(visible)
    bad=pink|green_bad
    holes=pink&(np.minimum(r,b)-g>110)&(np.minimum(r,b)>150)&(n[:,:,3]<32)
    color_key=(np.minimum(r,b)-g>65)&(np.minimum(r,b)-g>native_chroma+45)
    good=visible&~bad&~color_key&(alpha>=220)
    if good.any() and bad.any():
        indices=ndimage.distance_transform_edt(~good,return_indices=True)[1]
        rgb[bad]=rgb[indices[0],indices[1]][bad]
    # Matte islands in native-transparent gaps should be holes, not opaque recolored specks.
    alpha=alpha.copy();alpha[holes]=0
    opaque=(alpha>=250)&~bad&~color_key
    if opaque.any():
        indices=ndimage.distance_transform_edt(~opaque,return_indices=True)[1]
        edge=(alpha>0)&(alpha<250)
        rgb[edge]=rgb[indices[0],indices[1]][edge]
    # A sampled purple detail can be legitimate at its origin but a spill at a different contour.
    # Bound only excessive fuchsia saturation after edge extension, preserving material luminance.
    chroma=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]
    fringe=(alpha>0)&(distance<=4)&(chroma>65)&(chroma>native_chroma+45) if magenta else np.zeros_like(visible)
    rgb[:,:,1][fringe]=np.minimum(rgb[:,:,0],rgb[:,:,2])[fringe]-np.maximum(20,native_chroma[fringe]+30)
    a[:,:,:3]=np.clip(np.rint(rgb),0,255).astype('uint8');a[:,:,3]=alpha;a[alpha==0,:3]=0
    return Image.fromarray(a),{'magenta_pixels_recolored':int(pink.sum()),'green_pixels_recolored':int(green_bad.sum()),'matte_hole_pixels_removed':int(holes.sum())}


def native_openings(image,native):
    # Only the native-empty portion of the generated silhouette can expose the mannequin back wall.
    guide=native.getchannel('A').resize(image.size,Image.Resampling.LANCZOS)
    mask=np.asarray(guide).astype(float)/255
    a=np.asarray(image).copy();old=a[:,:,3].copy()
    a[:,:,3]=np.minimum(a[:,:,3],np.rint(mask*255)).astype('uint8')
    a[a[:,:,3]==0,:3]=0
    return Image.fromarray(a),int((old>a[:,:,3]).sum())


def narrow_to_native(image,native):
    guide=np.asarray(native.resize(image.size,Image.Resampling.NEAREST))[:,:,3]>96
    source=np.asarray(image).copy();result=np.zeros_like(source)
    widths=np.ones(image.height);centers=np.zeros(image.height);native_centers=np.zeros(image.height)
    for y in range(image.height):
        xs=np.where(source[y,:,3]>32)[0];ns=np.where(guide[y])[0]
        if not len(xs) or not len(ns):continue
        centers[y]=(xs[0]+xs[-1])/2;native_centers[y]=(ns[0]+ns[-1])/2
        widths[y]=min(1,(ns[-1]-ns[0]+1)/(xs[-1]-xs[0]+1))
    # Smooth the warp along the weapon so the native pixel staircase cannot notch the grip.
    widths=ndimage.gaussian_filter1d(widths,3)
    centers=ndimage.gaussian_filter1d(centers,3);native_centers=ndimage.gaussian_filter1d(native_centers,3)
    yy,xx=np.indices(guide.shape,dtype=float)
    blend=np.clip((np.arange(image.height)/image.height-.45)/.15,0,1)
    blend=blend*blend*(3-2*blend)
    blend*=np.clip((1-widths)/.12,0,1)
    for y in range(image.height):
        scale=1-(1-widths[y])*blend[y]
        center=centers[y]+(native_centers[y]-centers[y])*blend[y]
        xx[y]=(xx[y]-center)/max(scale,.25)+centers[y]
    premult=np.asarray(image.convert('RGBa')).astype(float)
    for channel in range(4):result[:,:,channel]=ndimage.map_coordinates(premult[:,:,channel],[yy,xx],order=1,mode='constant',cval=0)
    return Image.fromarray(result,'RGBa').convert('RGBA')


def extract_piece(raw,component,labels=None):
    if labels is None:labels,_=ndimage.label(foreground(raw))
    target=labels==component['label'];target=ndimage.binary_dilation(target,iterations=2)
    a=np.asarray(raw).copy();a[~target,3]=0;a[a[:,:,3]==0,:3]=0
    im=Image.fromarray(a);return im.crop(im.getbbox())


def isolate_generated_slot(image):
    pixels=np.asarray(image).copy();labels,count=ndimage.label(pixels[:,:,3]>32)
    if not count:return image
    sizes=np.bincount(labels.ravel());sizes[0]=0
    keep=ndimage.binary_dilation(labels==int(sizes.argmax()),iterations=3)
    pixels[~keep]=0
    return Image.fromarray(pixels)


def generation_outputs(assets):
    manifest=read(OUT/'generated/batches.json');outputs={}
    for batch in manifest['batches']:
        path=OUT/'generated'/batch['name']/'raw.png'
        if not path.exists():continue
        with Image.open(path) as opened:raw=opened.convert('RGBA')
        if batch['name']=='large_quality_01':
            # User identified the generated sleeve back wall; preserve the gold rim, open its interior.
            ImageDraw.Draw(raw).polygon([(765,1098),(767,1095),(774,1090),(788,1083),(800,1080),
                (807,1079),(808,1082),(805,1086),(797,1091),(785,1096),(774,1099),(767,1100)], fill=(0,0,0,0))
        sx,sy=raw.width/batch['size'][0],raw.height/batch['size'][1]
        for cell in batch['cells']:
            x,y,w,h=cell['slot'];box=[round(x*sx),round(y*sy),round((x+w)*sx),round((y+h)*sy)]
            native=Image.open(HERE/unquote(assets[cell['target']]['native'])).convert('RGBA')
            cut=raw.crop(box)
            # A generation slot may contain faint color-key residue from the row above.
            # The meaningful alpha bounds drive fitting, not invisible RGB/near-zero alpha.
            pixels=np.asarray(cut).copy();pixels[pixels[:,:,3]<16]=0;cut=Image.fromarray(pixels)
            # The slot contains only this requested target. Transparent outside frame stays transparent.
            outputs[cell['target']]=(fit_native(isolate_generated_slot(cut),native),{'master':str(path),'raw_crop':box,'method':'imagegen_native_reference_repair',
                                                           'master_sha256':digest(path),'prompt':str(path.parent/'prompt.txt'),
                                                           'sleeve_interior_removed':cell['name']=='7item235v2a'})
    for target,donor in manifest['exact_native_duplicates'].items():
        if donor in outputs:outputs[target]=(outputs[donor][0].copy(),{**outputs[donor][1],'exact_native_donor':donor})
    sword=OUT/'generated/7item221-master.png'
    if sword.exists():
        target='engine--icons--7item221.bmp';native=Image.open(HERE/unquote(assets[target]['native'])).convert('RGBA')
        with Image.open(sword) as im:outputs[target]=(fit_native(isolate_generated_slot(im.convert('RGBA')),native),{'master':str(sword),'master_sha256':digest(sword),'method':'imagegen_explicit_sword_regeneration'})
    return outputs


def main():
    data=json.loads((OUT/'catalog.original.js').read_text().removeprefix('window.PAPERDOLL_REVIEW_DATA = ').removesuffix(';\n'))
    assets={a['id']:a for a in data['assets'].values()};source=read(OUT/'source_audit.json');crop=read(OUT/'crop_audit.json');queue=read(OUT/'repair_queue.json');stage=read(OUT/'stage_manifest.json')
    generated=generation_outputs(assets);results={};raw_cache={};label_cache={};(OUT/'repaired').mkdir(exist_ok=True)
    for target,info in source['assets'].items():
        a=assets[target];native=Image.open(HERE/unquote(a['native'])).convert('RGBA')
        original=Image.open(HERE/unquote(info['reviewed_path'])).convert('RGBA');image=original.copy()
        rec=queue.get(target,{});cats=rec.get('categories',[]);audit=crop['targets'][target];operations=[];unresolved=[]
        # Include previously approved extractions when their known extraction cuts a raw component.
        crop_suspect=audit['status']=='crop_repair' and info.get('known_extraction_rect')
        needs_crop='crop' in cats or crop_suspect
        if needs_crop and audit.get('component'):
            raw_path=audit['raw']
            if raw_path not in raw_cache:
                with Image.open(raw_path) as opened:raw_cache[raw_path]=opened.convert('RGBA')
            if raw_path not in label_cache:label_cache[raw_path]=ndimage.label(foreground(raw_cache[raw_path]))[0]
            component=audit['component']
            if audit.get('raw_canvas_clipped'):
                donor=next((key for key,piece in crop['sheets'][raw_path].items() if key!=target and
                            assets.get(key,{}).get('sourceHash')==a['sourceHash'] and piece['box'][0]>0 and piece['box'][2]<raw_cache[raw_path].width),None)
                if donor:
                    component=crop['sheets'][raw_path][donor];operations.append({'method':'exact_native_raw_donor','donor':donor})
                else:unresolved.append('raw_subject_itself_touches_canvas_edge')
            image=fit_native(extract_piece(raw_cache[raw_path],component,label_cache[raw_path]),native)
            operations.append({'method':'complete_raw_subject_reextraction','raw':raw_path,'component':component,
                               'destination_native_bounds':list(native.getbbox()),'old_crop':audit['old_crop']})
        elif needs_crop:
            unresolved.append('crop_requires_manual_raw_region')
        if a['name'] in ['item133v2','item133v4']:
            # Boot pairs have two disconnected pieces: use the complete inspected quadrant.
            raw_path=HERE/'new_returns/raw/item133.png'
            with Image.open(raw_path) as bootraw:
                box=(627,0,1254,627) if a['name']=='item133v2' else (0,627,627,1254)
                image=fit_native(bootraw.convert('RGBA').crop(box),native)
            operations.append({'method':'inspected_complete_boot_pair','raw':str(raw_path),'raw_crop':box})
            unresolved=[]
        if target in generated:
            image,operation=generated[target];image=image.copy();operations.append(operation)
            unresolved=[x for x in unresolved if 'crop' not in x and 'raw_subject' not in x]
        if 'handle' in cats:
            image=narrow_to_native(image,native);operations.append({'method':'native_row_width_handle_correction'})
        if 'openings' in cats:
            image,count=native_openings(image,native);operations.append({'method':'native_transparent_openings','changed_alpha_pixels':count})
        if rec or operations:
            image,stats=clean_spill(image,native,magenta=True,green='green' in cats)
            operations.append({'method':'native_guided_contour_decontamination',**stats})
        if ('identity' in cats or 'quality' in cats) and target not in generated:
            unresolved.append('requested_detail_or_identity_repair_pending')
        if not rec and not operations:continue
        polygons=read(OUT/'manual_openings.json')['polygons'].get(a['name'],[])
        if polygons:
            cut=Image.new('L',(image.width*4,image.height*4));pen=ImageDraw.Draw(cut)
            for polygon in polygons:pen.polygon([(round(x*4),round(y*4)) for x,y in polygon],fill=255)
            erase=np.asarray(cut.resize(image.size,Image.Resampling.LANCZOS)).astype(float)/255
            pixels=np.asarray(image).copy();pixels[:,:,3]=np.rint(pixels[:,:,3]*(1-erase)).astype('uint8')
            pixels[pixels[:,:,3]==0,:3]=0;image=Image.fromarray(pixels)
            operations.append({'method':'inspected_interior_polygons','polygons':polygons})
        changed=not np.array_equal(np.asarray(image),np.asarray(original))
        destination=OUT/'repaired'/(target+'.png')
        image.save(destination)
        results[target]={'target':target,'name':a['name'],'path':str(destination.relative_to(HERE)),
            'sha256':digest(destination),'source_hash':a['sourceHash'],'old_sha256':digest(HERE/unquote(info['reviewed_path'])),
            'old_path':info['reviewed_path'],'note':rec.get('note',''),'categories':cats,'operations':operations,
            'changed':changed,'unresolved':unresolved,'status':'repair_candidate_needs_review',
            'previously_approved':stage['records'].get(target,{}).get('decision',{}).get('decision')=='approve'}
    report={'schema':'paperdoll-repairs-v1','results':results,'summary':{'outputs':len(results),
        'changed':sum(x['changed'] for x in results.values()),'previously_approved':sum(x['previously_approved'] for x in results.values()),
        'unresolved':dict(Counter(issue for r in results.values() for issue in r['unresolved']))}}
    (OUT/'repairs.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))

if __name__=='__main__':main()
