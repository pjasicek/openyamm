"""Deterministic alpha-preserving alignment, atlas export and offline review for this adaptation."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
CANVAS = (768, 640)
PIVOT = (384, 540)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(mask):
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        raise ValueError('Missing expected anatomical region')
    return [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)]


def hair_region(rgba):
    rgb = rgba[..., :3].astype(float)
    mask = (rgba[..., 3] > 180) & (rgb[..., 0] > 1.45*rgb[..., 1]) & (rgb[..., 0] > 1.4*rgb[..., 2])
    labels, count = ndimage.label(mask)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    if not count:
        raise ValueError('No red hair found')
    return labels == sizes.argmax()


def edge_candidates(rgba):
    rgb = rgba[..., :3].astype(float)
    a = rgba[..., 3]
    contour = (a > 0) & ((a < 220) | (ndimage.distance_transform_edt(a > 128) <= 3))
    # Green is absent from the intended contour materials; the tiny yellow-green eyes are interior.
    score = np.maximum(0, rgb[..., 1]-np.maximum(rgb[..., 0], rgb[..., 2])) * a/255
    suspect = contour & (rgb[..., 1] > 90) & (rgb[..., 0] < .72*rgb[..., 1])
    suspect &= (rgb[..., 2] < .78*rgb[..., 1]) & (score > 12)
    return suspect, score*contour


def clean_edges(im):
    rgba = np.array(im.convert('RGBA'))
    original_alpha = rgba[..., 3].copy()
    suspect, score = edge_candidates(rgba)
    if suspect.any():
        good = (rgba[..., 3] > 220) & ~suspect
        nearest = ndimage.distance_transform_edt(~good, return_distances=False, return_indices=True)
        rgba[suspect, :3] = rgba[nearest[0][suspect], nearest[1][suspect], :3]
    assert np.array_equal(original_alpha, rgba[..., 3])
    after, remaining = edge_candidates(rgba)
    return Image.fromarray(rgba), dict(corrected_rgb_pixels=int(suspect.sum()),
        remaining_candidates=int(after.sum()), before_max=float(score.max()), after_max=float(remaining.max()))


def boot_landmark(rgba):
    rgb = rgba[..., :3].astype(float)
    opaque = rgba[..., 3] > 150
    box = bounds(opaque)
    yy = np.indices(opaque.shape)[0]
    maximum = rgb.max(axis=2); minimum = rgb.min(axis=2)
    # These particular boots are neutral charcoal; trousers are purple and club is warm brown.
    boot = opaque & (maximum-minimum < 38) & (maximum < 180) & (yy > box[1]+.64*(box[3]-box[1]))
    labels, count = ndimage.label(boot)
    if not count:
        raise ValueError('Missing boots')
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    ranked = sorted(range(1, count+1), key=lambda i: sizes[i], reverse=True)
    selected = ranked[:2] if len(ranked)>1 and sizes[ranked[1]]>.16*sizes[ranked[0]] else ranked[:1]
    chosen = np.isin(labels, selected)
    y, x = np.nonzero(chosen)
    ground = int(np.quantile(y, .998))+1
    centers = []
    for label in selected:
        ly, lx = np.nonzero(labels == label)
        # A stable whole-boot center avoids selecting toe highlights or a single antialias pixel.
        centers.append(float(np.median(lx)))
    return [float(np.mean(centers)), ground]


def pelvis_x(rgba):
    """Authored fall root follows the ochre waist rope, not the changing prone silhouette bounds."""
    rgb=rgba[..., :3].astype(float)
    red,green,blue=rgb[...,0],rgb[...,1],rgb[...,2]
    hue=60*(green-blue)/np.maximum(red-blue,1)
    rope=(rgba[...,3]>150)&(red>green)&(green>blue)&(red>90)&(hue>38)&(hue<62)
    yy,xx=np.nonzero(rope)
    if len(xx)<10:
        raise ValueError('Missing waist-rope landmark in falling pose')
    return float(np.median(xx))


def vest_mask(im):
    rgba = np.array(im)
    rgb = rgba[..., :3].astype(float)/255
    maximum = rgb.max(axis=2); minimum = rgb.min(axis=2)
    delta = maximum-minimum
    hue = np.zeros_like(maximum)
    valid = delta > .0001
    blue = valid & (maximum == rgb[..., 2])
    hue[blue] = (rgb[..., 0][blue]-rgb[..., 1][blue])/delta[blue]+4
    hue *= 60
    # Soft blue-only material coverage. Purple trousers and teal skin are protected.
    weight = np.clip((hue-208)/12, 0, 1)*np.clip((269-hue)/15, 0, 1)
    weight *= blue*np.clip(delta/.10, 0, 1)*(rgba[..., 3] > 0)
    return Image.fromarray(np.rint(weight*255).astype(np.uint8), 'L')


def composite(im, color=(45, 47, 50)):
    bg = Image.new('RGBA', im.size, (*color,255)); bg.alpha_composite(im)
    return bg.convert('RGB')


def extract_cells(raw, columns, rows, count):
    """Partition separated figures without cutting art at an approximate AI grid boundary."""
    rgba = np.array(raw)
    # The supplied alpha has faint (<=8/255) background dust far outside the actual silhouettes.
    # Remove only that demonstrated exterior noise; retain soft alpha within eight pixels of the art.
    exterior = (rgba[..., 3] <= 8) & (ndimage.distance_transform_edt(rgba[..., 3] <= 32) > 8)
    rgba[exterior] = 0
    labels, _ = ndimage.label(rgba[..., 3] > 32)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    major = np.argsort(sizes)[-count:]
    if min(sizes[major]) < 1000:
        raise ValueError('Missing a complete figure in the raw sheet')
    mapping = {}
    for label in major:
        yy, xx = np.nonzero(labels == label)
        col = min(columns-1, int(np.median(xx)*columns/raw.width))
        row = min(rows-1, int(np.median(yy)*rows/raw.height))
        index = row*columns+col
        if index in mapping or index >= count:
            raise ValueError(f'Ambiguous figure ownership in cell {index}')
        mapping[index] = label
    seeds = np.isin(labels, major)
    nearest = ndimage.distance_transform_edt(~seeds, return_distances=False, return_indices=True)
    owners = labels[nearest[0], nearest[1]]
    # Assign every faint/isolated visible pixel to its closest complete figure; do not erase thin details.
    reconstructed_alpha = np.zeros_like(rgba[..., 3], dtype=np.uint16)
    cells = []; rectangles = []
    for i in range(count):
        selected = owners == mapping[i]
        reconstructed_alpha += np.where(selected, rgba[..., 3], 0).astype(np.uint16)
        isolated = rgba.copy(); isolated[~selected] = 0
        rectangle = [round(i%columns*raw.width/columns)-256, round(i//columns*raw.height/rows)-256,
                     round((i%columns+1)*raw.width/columns)+256,
                     round((i//columns+1)*raw.height/rows)+256]
        im = Image.fromarray(isolated)
        box = im.getbbox()
        if not (rectangle[0] <= box[0] and rectangle[1] <= box[1]
                and rectangle[2] >= box[2] and rectangle[3] >= box[3]):
            raise ValueError('Raw figure escapes padded extraction cell')
        cells.append(im.crop(rectangle)); rectangles.append(rectangle)
    assert np.array_equal(reconstructed_alpha, rgba[..., 3])
    return cells, rectangles


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()
    for folder in ['aligned', 'masks', 'atlas', 'review', 'cleaned']:
        (HERE/folder).mkdir(exist_ok=True)
    jobs = json.loads((HERE/'jobs.json').read_text())
    source = json.loads((HERE/'sources.json').read_text())
    settings_path = HERE/'registration.json'
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    selected_identity = settings.get('identity', 'identity_v2')
    identity = Image.open(HERE/f'raw/{selected_identity}.png').convert('RGBA')
    identity_cells = [identity.crop((i%3*512,i//3*512,(i%3+1)*512,(i//3+1)*512)) for i in range(5)]
    identity_hair = [int(hair_region(np.array(im)).sum()) for im in identity_cells]
    # One authored logical scale: reference standing hair-to-sole ~432 px becomes 320 physical px.
    identity_scale = settings.get('identity_scale', .74)
    batches = {'identity': dict(frames=[f'm476sa{v}' for v in range(5)], columns=3, rows=2,
                               action='s', view=None), **jobs}
    masters = {}; masks = {}; frames = {}; audits = {}; registration = {}; missing = []; override_cache={}
    for job_id, job in batches.items():
        selected_sheet=settings.get('sheets', {}).get(job_id, selected_identity if job_id=='identity' else job_id)
        raw_path = HERE/f'raw/{selected_sheet}.png'
        if not raw_path.exists():
            missing.append(job_id); continue
        raw = Image.open(raw_path).convert('RGBA')
        cols, rows = job['columns'], job['rows']
        try:
            cells, rects = extract_cells(raw, cols, rows, len(job['frames']))
        except ValueError as error:
            raise ValueError(f'{job_id}: {error}') from error
        if job_id=='identity':
            scale=identity_scale
        else:
            # One common anatomical scale for a complete sequence. No per-frame silhouette fitting.
            count=2 if job['action']=='d' else len(cells)
            area=np.median([hair_region(np.array(im)).sum() for im in cells[:count]])
            scale=identity_scale*math.sqrt(identity_hair[job['view']]/area)
        scale=settings.get('scales', {}).get(job_id, scale)
        registration[job_id]=dict(raw=str(raw_path.relative_to(HERE)), sha256=digest(raw_path),
            actual_size=list(raw.size), cell_rectangles=rects, uniform_scale_to_2x=scale,
            generated_pixels_per_authored_logical_pixel=2/scale,
            scale_method='single batch scale from median red-hair area against same-view identity; overrides recorded')
        for i, (name, cell) in enumerate(zip(job['frames'],cells)):
            frame_scale=scale
            replacement=settings.get('frame_overrides', {}).get(name)
            if replacement:
                replacement_path=HERE/f'raw/{replacement["sheet"]}.png'
                if replacement['sheet'] not in override_cache:
                    replacement_raw=Image.open(replacement_path).convert('RGBA')
                    override_cache[replacement['sheet']]=extract_cells(replacement_raw,
                        replacement['columns'],replacement['rows'],replacement['count'])
                replacement_cells,replacement_rects=override_cache[replacement['sheet']]
                cell=replacement_cells[replacement['index']]
                predecessor=(np.array(cells[replacement['reference_cell']]) if 'reference_cell' in replacement
                    else np.array(Image.open(HERE/f'cleaned/{replacement["scale_reference"]}.png')))
                # Match a comparable head orientation in the accepted neighboring pose.
                frame_scale=scale*math.sqrt(hair_region(predecessor).sum()/hair_region(np.array(cell)).sum())
                frame_scale=replacement.get('scale',frame_scale)
                registration[name]=dict(raw=str(replacement_path.relative_to(HERE)),sha256=digest(replacement_path),
                    cell_rectangles=[replacement_rects[replacement['index']]],uniform_scale_to_2x=frame_scale,
                    generated_pixels_per_authored_logical_pixel=2/frame_scale,
                    scale_method='corrective raw pose registered to comparable head in accepted neighboring frame')
            cleaned, audit=clean_edges(cell); cleaned.save(HERE/f'cleaned/{name}.png')
            a=np.array(cleaned)[...,3]
            audit['raw_cell_border_pixels_gt32']=int((np.r_[a[0],a[-1],a[:,0],a[:,-1]]>32).sum())
            # Premultiplied filtering, then straight RGBA storage; never key a resized image.
            scaled=cleaned.convert('RGBa').resize((round(cell.width*frame_scale),round(cell.height*frame_scale)),
                                                Image.Resampling.LANCZOS).convert('RGBA')
            scaled, resize_audit=clean_edges(scaled)
            if job['action']=='d':
                # Collapse motion stays in the shared sheet coordinate system. Use the first falling
                # pose's feet as the sequence contact reference; never bottom-center each prone silhouette.
                if i==0:
                    death_anchor=boot_landmark(np.array(scaled))
                # Original fall poses keep their bottom contact at native y=255/256, while the AI
                # rows drift. Use the visible lowest body contact and preserve that native delta.
                body_bottom=bounds(np.array(scaled)[...,3]>150)[3]
                native_bottom=source['motion_sources'][name]['original_bounds'][3]
                landmark=[pelvis_x(np.array(scaled)),body_bottom-(native_bottom-256)*2]
            else:
                landmark=boot_landmark(np.array(scaled))
            shift=[round(PIVOT[0]-landmark[0]),round(PIVOT[1]-landmark[1])]
            extra=settings.get('translations', {}).get(name, [0,0])
            shift=[shift[0]+extra[0],shift[1]+extra[1]]
            box=scaled.getbbox()
            if box[0]+shift[0]<0 or box[1]+shift[1]<0 or box[2]+shift[0]>CANVAS[0] or box[3]+shift[1]>CANVAS[1]:
                raise ValueError(f'Clipping {name}: {box}, shift {shift}; use recorded canvas/crop correction')
            aligned=Image.new('RGBA',CANVAS); aligned.paste(scaled,tuple(shift))
            assert np.array_equal(np.array(aligned.crop((box[0]+shift[0],box[1]+shift[1],
                box[2]+shift[0],box[3]+shift[1]))),np.array(scaled.crop(box)))
            mask=vest_mask(aligned)
            aligned.save(HERE/f'aligned/{name}.png');mask.save(HERE/f'masks/{name}.png')
            masters[name]=aligned;masks[name]=mask
            frames[name]=dict(batch=job_id, raw_cell=i, source_kind='new authored MM5 adaptation',
                motion_reference=name, registration_scale=frame_scale, registration_translation_px=shift,
                contact_landmark_before_translation=landmark, crop_origin_px=list(aligned.getbbox()[:2]))
            audit['post_resize']=resize_audit; audits[name]=audit
    write_json(HERE/'review/registration_audit.json', registration)
    write_json(HERE/'review/cleaned_edge_audit.json', audits)
    if missing and not args.partial:
        raise ValueError(f'Missing {len(missing)} batches: {missing}')
    if not missing:
        assert set(frames)==set(source['motion_sources']), 'Frame coverage differs from the explicit MM8 template'
    # Deterministic height-sorted shelf packing, 8px gutters; base and R8 mask use identical rectangles.
    pages=[]; packed={}; page_images=[]; mask_images=[]
    candidates=sorted(masters, key=lambda n: (-(masters[n].getbbox()[3]-masters[n].getbbox()[1]),n))
    placements=[]; page=0;x=y=rowh=0;limit=2048;pad=8
    for name in candidates:
        box=masters[name].getbbox();w=box[2]-box[0];h=box[3]-box[1]
        if x+w+2*pad>limit:
            y+=rowh;x=0;rowh=0
        if y+h+2*pad>limit:
            page+=1;x=y=rowh=0
        placements.append((name,page,x+pad,y+pad,w,h,box));x+=w+2*pad;rowh=max(rowh,h+2*pad)
    for page_id in range(page+1):
        selected=[p for p in placements if p[1]==page_id]
        w=max(p[2]+p[4]+pad for p in selected);h=max(p[3]+p[5]+pad for p in selected)
        base=Image.new('RGBA',(w,h));mask=Image.new('L',(w,h));
        for name,_,px,py,fw,fh,box in selected:
            crop=masters[name].crop(box);mcrop=masks[name].crop(box)
            base.paste(crop,(px,py));mask.paste(mcrop,(px,py))
            # Transparent padding stores nearest foreground RGB; opacity and semantic mask remain zero.
            arr=np.array(crop);valid=arr[...,3]>0
            nearest=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True)
            arr[~valid,:3]=arr[nearest[0][~valid],nearest[1][~valid],:3]
            padded=np.pad(arr,((pad,pad),(pad,pad),(0,0)),mode='edge')
            padded[:pad,:,3]=0;padded[-pad:,:,3]=0;padded[:,:pad,3]=0;padded[:,-pad:,3]=0
            base.paste(Image.fromarray(padded),(px-pad,py-pad))
            base.paste(crop,(px,py))
            frames[name].update(page=page_id,atlas_xywh=[px,py,fw,fh],crop_origin_px=list(box[:2]))
        base.save(HERE/f'atlas/base_{page_id}.png');mask.save(HERE/f'atlas/mask_{page_id}.png')
        page_images.append(base);mask_images.append(mask)
        pages.append(dict(base=f'atlas/base_{page_id}.png',mask=f'atlas/mask_{page_id}.png',size=[w,h],
                          base_format='RGBA8 sRGB',mask_format='R8 linear',decoded_bytes=w*h*5))
    final_audit={}
    for name, frame in frames.items():
        px,py,w,h=frame['atlas_xywh'];box=masters[name].getbbox();pi=frame['page']
        extracted=page_images[pi].crop((px,py,px+w,py+h))
        assert np.array_equal(np.array(extracted),np.array(masters[name].crop(box)))
        assert np.array_equal(np.array(mask_images[pi].crop((px,py,px+w,py+h))),np.array(masks[name].crop(box)))
        rebuilt=Image.new('RGBA',CANVAS);rebuilt.paste(extracted,tuple(frame['crop_origin_px']))
        assert np.array_equal(np.array(rebuilt),np.array(masters[name]))
        suspect,score=edge_candidates(np.array(extracted))
        final_audit[name]=dict(candidates=int(suspect.sum()),max_score=float(score.max()))
    write_json(HERE/'review/atlas_edge_audit.json',final_audit)
    animations={}
    for action,record in source['motion_animations'].items():
        views={}
        for view, entries in record['views'].items():
            views[view]=[dict(frame=e['frame'],duration_ms=e['duration_ms'],mirrored=e['mirrored']) for e in entries]
        animations[action]=dict(views=views,playback=record['playback'],
                                adapted_from_group=record['native_group'])
    manifest=dict(schema_version=1,creature='mm5:troll_grunt',installed=False,
        schema_status='staged authored adaptation; offline contract, not a runtime registration',
        pixels_per_logical_pixel=2,logical_canvas=[v/2 for v in CANVAS],logical_pivot=[v/2 for v in PIVOT],
        coordinate_rule='x=(crop_x+u)/2-pivot_x; up=pivot_y-(crop_y+v)/2',
        direction_labels=['front','front-left','left','rear-left','back','rear-right (mirrored)',
                          'right (mirrored)','front-right (mirrored)'],
        pages=pages,frames=frames,animations=animations,
        masks=[dict(channel='R',region='blue vest',operation='soft coverage; base preset is exact bypass')],
        variants={'base':dict(operation='exact bypass',label='Troll Grunt / shared native appearance')},
        decoded_memory_bytes=sum(p['decoded_bytes'] for p in pages),atlas_padding_px=pad,
        mipmaps='not generated; offline review pages use base level',
        coverage=dict(expected=160,exported=len(frames),missing_batches=missing),
        limitations=['MM5 hidden views and motion are newly authored, not native recovered frames.',
                    'Mirror aliases use the MM7/MM8 convention and reflect equipment handedness.',
                    'Single decoded MM5 appearance; no unsupported native palette variants invented.'])
    write_json(HERE/'manifest.json',manifest)
    # All-frame contacts and semantic-mask overlays, organized by action/view, never independently fitted.
    names=list(frames)
    for start in range(0,len(names),40):
        chunk=names[start:start+40];sheet=Image.new('RGB',(1280,math.ceil(len(chunk)/8)*156),(44,46,49))
        overlay=sheet.copy();draw=ImageDraw.Draw(sheet);odraw=ImageDraw.Draw(overlay)
        for i,name in enumerate(chunk):
            im=masters[name].resize((144,120),Image.Resampling.LANCZOS)
            px=i%8*160+8;py=i//8*156
            sheet.paste(composite(im),(px,py+20));draw.text((px,py+142),name,fill='white')
            marked=masters[name].copy();tint=Image.new('RGBA',CANVAS,(255,190,35,0));tint.putalpha(masks[name].point(lambda a:int(a*.65)))
            marked.alpha_composite(tint);overlay.paste(composite(marked.resize((144,120))),(px,py+20))
            odraw.text((px,py+142),name,fill='white')
        sheet.save(HERE/f'review/contact_{start//40}.jpg',quality=93)
        overlay.save(HERE/f'review/masks_{start//40}.jpg',quality=93)
    worst=sorted(final_audit,key=lambda n:final_audit[n]['max_score'],reverse=True)[:8]
    edge=Image.new('RGB',(1024,512),(60,60,60));ed=ImageDraw.Draw(edge)
    for i,name in enumerate(worst):
        arr=np.array(masters[name]);_,score=edge_candidates(arr);yy,xx=np.unravel_index(score.argmax(),score.shape)
        crop=masters[name].crop((xx-24,yy-24,xx+24,yy+24)).resize((128,128),Image.Resampling.NEAREST)
        x=i%4*256;y=i//4*256
        edge.paste(composite(crop,(240,240,240)),(x,y+25));edge.paste(composite(crop,(15,15,15)),(x+128,y+25))
        ed.text((x,y+5),name,fill='white')
    edge.save(HERE/'review/edge_closeups.png')
    write_json(HERE/'review/checks.json',dict(frames=len(frames),expected=160,missing=missing,
        atlas_reconstruction='exact RGBA',mask_coordinates='exact',base_variant='exact bypass',
        minimum_generated_sampling=min(r['generated_pixels_per_authored_logical_pixel'] for r in registration.values()),
        contour_candidates=sum(a['candidates'] for a in final_audit.values()),
        cell_boundary_candidates=sum(a['raw_cell_border_pixels_gt32'] for a in audits.values()),
        decoded_mib=manifest['decoded_memory_bytes']/1048576,visual_acceptance='pending human/agent review'))
    print(json.dumps(dict(frames=len(frames),missing=missing,pages=len(pages),
                         decoded_mib=manifest['decoded_memory_bytes']/1048576),indent=2))


if __name__=='__main__':
    main()
