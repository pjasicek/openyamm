"""Register master-A sources to native MM8 scale and export the staged sprite family."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
CANVAS = (640, 640)
PIVOT = (320, 576)
# Reuse the established lossless cell partition and color-only contour correction.
spec = importlib.util.spec_from_file_location('troll_processing', HERE.parent/'export.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def read(name):
    return json.loads((HERE/name).read_text())


def write(name, data):
    (HERE/name).write_text(json.dumps(data, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hair(im):
    rgba = np.array(im)
    red, green, blue = [rgba[...,i].astype(float) for i in range(3)]
    delta = np.maximum(red-np.minimum(green,blue),1)
    hue = 60*(green-blue)/delta
    selected = (rgba[...,3]>160)&(red>35)&(red>green)&(red>blue)&(hue>=-3)&(hue<24)
    selected &= delta/np.maximum(red,1)>.28
    # Fine auburn strands form many disconnected islands; keep the complete hair cluster.
    joined = ndimage.binary_closing(selected,iterations=5)
    labels, count = ndimage.label(ndimage.binary_dilation(joined,iterations=3))
    sizes = np.bincount(labels.ravel());sizes[0]=0
    if not count:
        raise ValueError('Missing auburn hair landmark')
    return selected & (labels==sizes.argmax())


def ground(im):
    """Lowest opaque contact; foot lifts remain within the same actor's common ground plane."""
    a = np.array(im)
    opaque = a[..., 3] > 160
    yy, xx = np.nonzero(opaque)
    bottom = int(yy.max())+1
    # Lowest boot bands, excluding the torso/cloth, establish stance midpoint.
    band = opaque & (np.indices(opaque.shape)[0] > bottom-.10*(bottom-yy.min()))
    labels, n = ndimage.label(band)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    ranked = sorted(range(1, n+1), key=lambda i: sizes[i], reverse=True)
    selected = ranked[:2] if len(ranked)>1 and sizes[ranked[1]]>.12*sizes[ranked[0]] else ranked[:1]
    centers = [float(np.median(np.nonzero(labels == k)[1])) for k in selected]
    return [float(np.mean(centers)), bottom]


def pelvis(im):
    rgba = np.array(im)
    red, green, blue = [rgba[...,i].astype(float) for i in range(3)]
    gold = (rgba[...,3]>160)&(red>80)&(red>green*1.08)&(green>blue*1.7)&(blue>10)
    labels, count = ndimage.label(ndimage.binary_closing(gold,iterations=2))
    sizes = np.bincount(labels.ravel());sizes[0]=0
    if not count or sizes.max()<8:
        raise ValueError('Missing ochre waist rope for actor-root registration')
    yy,xx=np.nonzero(gold&(labels==sizes.argmax()))
    return float(np.median(xx))


def walking_anatomy_height(im):
    rgba=np.array(im)
    red,green,blue=[rgba[...,i].astype(float) for i in range(3)]
    skin=(rgba[...,3]>160)&(green>red*1.12)&(blue>red*1.12)&(blue<green*1.35)&(green>30)
    yy,_=np.nonzero(skin)
    if len(yy)<20:
        raise ValueError('Missing teal head/shoulder landmark')
    return ground(im)[1]-int(yy.min())


def identity_records():
    records = {}
    for v in range(5):
        im = Image.open(HERE/f'references/identity_{v}.png').convert('RGBA')
        head = hair(im); y, x = np.nonzero(head)
        contact = ground(im)
        # The original standing troll's head-to-ground extent is 148 native pixels.
        scale = 296/(contact[1]-int(y.min()))
        records[v] = dict(image=im, hair_area=int(head.sum()), scale=scale,
                          ground=contact, generated_head_to_ground=contact[1]-int(y.min()))
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()
    for folder in ['source_cells', 'aligned_2x', 'masks_2x', 'atlas', 'review']:
        (HERE/folder).mkdir(exist_ok=True)
    jobs = read('jobs.json'); source = read('sources.json')
    settings = read('registration.json') if (HERE/'registration.json').exists() else {}
    identities = identity_records()
    masters = {}; masks = {}; frames = {}; audits = {}; measured = {}; missing = []; overlaps = {}
    # Standing uses the exact selected A source and newly authored matching directions.
    work = {}
    for v, info in identities.items():
        work[f's{v}'] = dict(action='s', view=v, frames=[f'm476sa{v}'], cells=[info['image']],
            rectangles=[[0,0,*info['image'].size]], scale=info['scale'], raw=f'references/identity_{v}.png')
    for job_id, job in jobs.items():
        selected = settings.get('sheets', {}).get(job_id, job_id)
        path = HERE/f'raw/{selected}.png'
        if not path.exists():
            missing.append(job_id); continue
        raw = Image.open(path).convert('RGBA')
        alpha=np.array(raw)[...,3]
        outer_border=int(sum((edge>32).sum() for edge in [alpha[0],alpha[-1],alpha[:,0],alpha[:,-1]]))
        if outer_border:
            raise ValueError(f'Raw image boundary requires clipping review: {job_id}, {outer_border} pixels')
        cells, rectangles = helpers.extract_cells(raw, job['columns'], job['rows'], len(job['frames']))
        ref = identities[job['view']]
        count = 2 if job['action']=='d' else len(cells)
        area = float(np.median([int(hair(im).sum()) for im in cells[:count]]))
        scale = ref['scale']*math.sqrt(ref['hair_area']/area)
        if job['action']=='w':
            scale = ref['scale']*walking_anatomy_height(ref['image'])/float(np.median(
                [walking_anatomy_height(im) for im in cells]))
        if job['part'] and f"{job['action']}{job['view']}_0" in work:
            prev = work[f"{job['action']}{job['view']}_0"]
            if job['action']=='w':
                scale = prev['scale']*walking_anatomy_height(prev['cells'][-1])/walking_anatomy_height(cells[0])
            else:
                pair=settings.get('scale_reference_cells',{}).get(job_id,{'previous':-1,'current':0})
                scale = prev['scale']*math.sqrt(hair(prev['cells'][pair['previous']]).sum()/hair(cells[pair['current']]).sum())
        scale = settings.get('scales', {}).get(job_id, scale)
        work[job_id] = dict(job, cells=cells, rectangles=rectangles, scale=scale, raw=f'raw/{selected}.png')
    override_cache = {}
    for job_id, job in work.items():
        scale = job['scale']; v = job['view']
        measured[job_id] = dict(raw=job['raw'], sha256=sha(HERE/job['raw']), scale_to_2x=scale,
            actual_size=list(Image.open(HERE/job['raw']).size), raw_rectangles=job['rectangles'],
            generated_pixels_per_native_pixel=2/scale)
        for i, (name, cell) in enumerate(zip(job['frames'], job['cells'])):
            if name in frames:
                overlaps[name] = dict(retained_batch=frames[name]['batch'], comparison_batch=job_id,
                    previous_scale=frames[name]['registration_scale'], comparison_scale=scale)
                continue
            frame_scale = scale
            override = settings.get('frame_overrides', {}).get(name)
            if override:
                key = override['sheet']
                if key not in override_cache:
                    override_cache[key] = helpers.extract_cells(Image.open(HERE/f'raw/{key}.png').convert('RGBA'),
                        override['columns'], override['rows'], override['count'])[0]
                cell = override_cache[key][override['index']]
                frame_scale = override['scale']
            clean, audit = helpers.clean_edges(cell)
            clean.save(HERE/f'source_cells/{name}.png')
            a = np.array(clean)[...,3]
            audit['cell_boundary_alpha_gt32'] = int((np.r_[a[0],a[-1],a[:,0],a[:,-1]]>32).sum())
            scaled = clean.convert('RGBa').resize((round(clean.width*frame_scale),round(clean.height*frame_scale)),
                Image.Resampling.LANCZOS).convert('RGBA')
            scaled, post = helpers.clean_edges(scaled); audit['post_resize'] = post
            contact = ground(scaled)
            # Register the actor's waist root, not whichever walking foot is lowest in this frame.
            contact[0] = pelvis(scaled)
            native_bottom = source['motion_sources'][name]['original_bounds'][3]
            delta = 2*(native_bottom-256)
            shift = [round(PIVOT[0]-contact[0]), round(PIVOT[1]+delta-contact[1])]
            extra = settings.get('translations', {}).get(name, [0,0])
            shift = [shift[k]+extra[k] for k in range(2)]
            box = scaled.getbbox()
            if box[0]+shift[0]<0 or box[1]+shift[1]<0 or box[2]+shift[0]>CANVAS[0] or box[3]+shift[1]>CANVAS[1]:
                raise ValueError(f'Clipping {name}: scale {frame_scale}, bounds {box}, shift {shift}')
            aligned = Image.new('RGBA', CANVAS); aligned.paste(scaled,tuple(shift))
            mask = helpers.vest_mask(aligned)
            aligned.save(HERE/f'aligned_2x/{name}.png'); mask.save(HERE/f'masks_2x/{name}.png')
            masters[name] = aligned; masks[name] = mask; audits[name] = audit
            frames[name] = dict(batch=job_id, raw_cell=i, registration_scale=frame_scale,
                generated_pixels_per_native_pixel=2/frame_scale, translation_px=shift,
                source_cell=f'source_cells/{name}.png', source_cell_size=list(clean.size),
                source_foreground_bounds=list(clean.getbbox()))
    if missing and not args.partial:
        raise ValueError(f'Missing generation batches: {missing}')
    if not missing:
        assert set(frames)==set(source['motion_sources'])
        assert min(f['generated_pixels_per_native_pixel'] for f in frames.values())>=2, 'Insufficient raw detail'
    pages = []; base_pages = []; mask_pages = []; placements = []
    x=y=row_height=page=0; pad=8; limit=2048
    for name in sorted(masters, key=lambda n: (-(masters[n].getbbox()[3]-masters[n].getbbox()[1]), n)):
        box=masters[name].getbbox(); w=box[2]-box[0]; h=box[3]-box[1]
        if x+w+pad*2>limit:
            y+=row_height; x=0; row_height=0
        if y+h+pad*2>limit:
            page+=1; x=y=row_height=0
        placements.append((name,page,x+pad,y+pad,w,h,box)); x+=w+pad*2; row_height=max(row_height,h+pad*2)
    for page_id in range(page+1):
        members=[r for r in placements if r[1]==page_id]
        width=max(r[2]+r[4]+pad for r in members); height=max(r[3]+r[5]+pad for r in members)
        base=Image.new('RGBA',(width,height)); mask=Image.new('L',(width,height))
        for name,_,px,py,w,h,box in members:
            crop=masters[name].crop(box); arr=np.array(crop); valid=arr[...,3]>0
            near=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True)
            arr[~valid,:3]=arr[near[0][~valid],near[1][~valid],:3]
            padded=np.pad(arr,((pad,pad),(pad,pad),(0,0)),mode='edge')
            padded[:pad,:,3]=0;padded[-pad:,:,3]=0;padded[:,:pad,3]=0;padded[:,-pad:,3]=0
            base.paste(Image.fromarray(padded),(px-pad,py-pad));base.paste(crop,(px,py))
            mask.paste(masks[name].crop(box),(px,py))
            frames[name].update(page=page_id,atlas_xywh=[px,py,w,h],crop_origin_px=list(box[:2]))
        base.save(HERE/f'atlas/base_{page_id}.png'); mask.save(HERE/f'atlas/mask_{page_id}.png')
        base_pages.append(base);mask_pages.append(mask)
        pages.append(dict(base=f'atlas/base_{page_id}.png',mask=f'atlas/mask_{page_id}.png',size=[width,height],
            base_format='RGBA8 sRGB',mask_format='R8 linear',decoded_bytes=width*height*5))
    final_edges={}
    for name,f in frames.items():
        px,py,w,h=f['atlas_xywh']; box=(px,py,px+w,py+h)
        extracted=base_pages[f['page']].crop(box)
        rebuilt=Image.new('RGBA',CANVAS);rebuilt.paste(extracted,tuple(f['crop_origin_px']))
        assert np.array_equal(np.array(rebuilt),np.array(masters[name]))
        assert np.array_equal(np.array(mask_pages[f['page']].crop(box)),np.array(masks[name].crop(masters[name].getbbox())))
        candidates,score=helpers.edge_candidates(np.array(extracted))
        final_edges[name]=dict(candidates=int(candidates.sum()),maximum=float(score.max()))
    animations={k:dict(views={v:[dict(frame=e['frame'],duration_ms=e['duration_ms'],mirrored=e['mirrored'])
        for e in entries] for v,entries in r['views'].items()},playback=r['playback'])
        for k,r in source['motion_animations'].items()}
    manifest=dict(schema_version=2,creature='mm5:troll_grunt',revision='selected-master-a',installed=False,
        identity='../style_front_v2/A_faithful_render.png',identity_sha256=sha(HERE.parent/'style_front_v2/A_faithful_render.png'),
        pixels_per_logical_pixel=2,logical_canvas=[320,320],logical_pivot=[160,288],
        native_reference_canvas=[256,256],native_padding_each_side=32,
        coordinate_rule='x=(crop_x+u)/2-160; up=288-(crop_y+v)/2',
        direction_labels=VIEWS+['rear-right (mirrored)','right (mirrored)','front-right (mirrored)'],
        pages=pages,frames=frames,animations=animations,
        variants={'base':{'operation':'exact bypass','label':'Troll Grunt native appearance'}},
        masks=[dict(channel='R',region='blue vest',operation='soft material coverage independent of alpha')],
        decoded_memory_bytes=sum(p['decoded_bytes'] for p in pages),atlas_padding_px=pad,mipmaps=False,
        coverage=dict(expected=160,exported=len(frames),missing_batches=missing),
        limitations=['Additional views and motion authored from selected A, using MM8 topology.',
                    'Mirrored views also mirror weapon handedness; native five-view convention.'])
    write('manifest.json',manifest);write('review/registration.json',measured)
    write('review/overlaps.json',overlaps);write('review/cleaned_edges.json',audits);write('review/atlas_edges.json',final_edges)
    names=sorted(frames)
    for start in range(0,len(names),40):
        sheet=Image.new('RGB',(1280,800),(45,47,51)); overlay=sheet.copy()
        draw=ImageDraw.Draw(sheet);odraw=ImageDraw.Draw(overlay)
        for i,name in enumerate(names[start:start+40]):
            px=i%8*160;py=i//8*160
            im=masters[name].resize((150,150),Image.Resampling.LANCZOS)
            sheet.paste(helpers.composite(im),(px,py));draw.text((px+4,py+146),name,fill='white')
            marked=masters[name].copy();tint=Image.new('RGBA',CANVAS,(255,190,40,0));tint.putalpha(masks[name].point(lambda a:int(a*.65)))
            marked.alpha_composite(tint);overlay.paste(helpers.composite(marked.resize((150,150))),(px,py))
            odraw.text((px+4,py+146),name,fill='white')
        sheet.save(HERE/f'review/contact_{start//40}.jpg',quality=94)
        overlay.save(HERE/f'review/masks_{start//40}.jpg',quality=94)
    write('review/checks.json',dict(frames=len(frames),expected=160,missing=missing,
        exact_atlas_reconstruction=True,exact_mask_placement=True,
        minimum_generated_sampling=min(f['generated_pixels_per_native_pixel'] for f in frames.values()),
        cell_boundary_candidates=sum(r['cell_boundary_alpha_gt32'] for r in audits.values()),
        contour_candidates=sum(r['candidates'] for r in final_edges.values()),
        decoded_mib=manifest['decoded_memory_bytes']/1048576,visual_acceptance='pending visual review'))
    print(json.dumps(read('review/checks.json'),indent=2))


VIEWS = ['front','front-left','left','rear-left','back']
if __name__ == '__main__':
    main()
