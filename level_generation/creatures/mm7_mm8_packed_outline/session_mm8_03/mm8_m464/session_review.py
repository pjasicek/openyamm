"""One MM8 staging adapter for shared placement/detail review and exported native palette contacts."""
import argparse
import copy
import contextlib
import io
import math
import sys

import numpy as np
from PIL import Image, ImageDraw

from session_prepare import REPO, CREATURES, STAGE, read, save, native_2x
from session_finish import sha

sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
from review_complete_sheets import contacts
from review_detail_and_alpha import review as detail_review
sys.path.insert(0, str(CREATURES / 'mm8_remaining'))
import native_materials as materials
from process_detail import edge_candidates


def centroid(image, weights):
    a = np.asarray(image)[:, :, 3].astype(float) / 255
    w = np.asarray(weights).astype(float) * a
    if w.sum() < 20:
        return None
    yy, xx = np.indices(w.shape)
    return [float((xx*w).sum()/w.sum()), float((yy*w).sum()/w.sum())]


def diagnostic_weights(image, settings):
    if settings['regions']:
        return materials.masks(image, settings)
    # Dragon has one fixed palette. Warm scales are a diagnostic material feature only.
    a = np.asarray(image); r, g, b = np.moveaxis(a[:, :, :3].astype(float), -1, 0)
    return ((r > b*1.4) & (g > b*1.2) & (a[:, :, 3] >= 128)).astype(np.uint8)*255


def run(stem):
    root = STAGE / f'mm8_m{stem}'; out = root / 'redo_2x'
    sources = read(root / 'sources.json'); manifest = read(out / 'draft_manifest.json')
    records = read(out / 'registration.json'); settings = read(out / 'material_settings.json')
    policy=read(out/'processing.json')
    for name, canonical in sources['pixel_aliases'].items():
        if canonical in records:
            records[name] = copy.deepcopy(records[canonical])
    # Material center is independent unless a visually reviewed translation explicitly uses it.
    for name, record in records.items():
        native = native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
        restored = Image.open(out / 'aligned_2x' / (name+'.png')).convert('RGBA')
        n = centroid(native, diagnostic_weights(native, settings))
        r = centroid(restored, diagnostic_weights(restored, settings))
        if n and r:
            fitted='material_region_center' in policy.get('frame_translation_calibration',{}).get(name,{}).get('landmark','')
            label='fitted_material_region_center' if fitted else 'independent_material_region_center'
            record.setdefault('review_landmarks', {}).pop('independent_material_region_center',None)
            record['review_landmarks'][label] = dict(
                native=[v/2 for v in n], restored_before_translation=[
                    r[i]+record['canvas_origin_px'][i]-record['translate'][i] for i in [0,1]],
                role=('Explicitly used for reviewed whole-pose translation; cannot certify independent anatomy.' if fitted else
                    'Diagnostic corresponding palette-changing garment/skin, or fixed Dragon warm scales; not used by the transform. Check the marked material and independent limbs/equipment visually.'))
            if fitted:
                points=[]
                for im in [native,restored]:
                    yy,xx=np.where(np.asarray(im)[:,:,3]>=128);bottom=int(yy.max())
                    band=yy>=bottom-2;points.append([float(np.median(xx[band])),float(np.median(yy[band]))])
                record['review_landmarks']['independent_lowest_solid_contour']=dict(
                    native=[v/2 for v in points[0]],restored_before_translation=[
                        points[1][i]+record['canvas_origin_px'][i]-record['translate'][i] for i in [0,1]],
                    role='Diagnostic lowest solid contour; it can mark a foot, hand or other part in falling poses. Never used for translation or scale. Identify the marked part visually and inspect independent head, limbs and equipment.')
    save(out / 'registration.json', records)
    with contextlib.redirect_stdout(io.StringIO()):
        contacts(str(root.relative_to(REPO))); detail_review(str(root.relative_to(REPO)))
    # Existing exact aliases are included; no native source is substituted for restored art.
    panels=[]; palettes=list(manifest['native_palettes']); evidence=[]
    for name, frame in manifest['frames'].items():
        record=records[name]; origin=record['canvas_origin_px']
        native=Image.open(out/'native_variants'/f'{name}_{sources["base_palette"]}.png').convert('RGBA')
        restored=Image.open(out/'previews'/f'{name}_{sources["base_palette"]}.png').convert('RGBA')
        nb=native.getbbox(); rb=restored.getbbox()
        assert native.size == tuple(sources['sources'][name]['size'])
        crop=[math.floor(min(nb[0],(rb[0]+origin[0])/2))-4,
              math.floor(min(nb[1],(rb[1]+origin[1])/2))-4,
              math.ceil(max(nb[2],(rb[2]+origin[0])/2))+4,
              math.ceil(max(nb[3],(rb[3]+origin[1])/2))+4]
        w,h=crop[2]-crop[0],crop[3]-crop[1]
        labels=[]; images=[]
        for palette in palettes:
            for kind,folder in [('N','native_variants'),('R','previews')]:
                im=Image.open(out/folder/f'{name}_{palette}.png').convert('RGBA')
                rect=tuple(crop) if kind=='N' else tuple(crop[i]*2-origin[i%2] for i in range(4))
                patch=im.crop(rect)
                patch=(patch.resize((w,h),Image.Resampling.NEAREST) if kind=='N' else
                    patch.convert('RGBa').resize((w,h),Image.Resampling.LANCZOS).convert('RGBA'))
                images.append(patch);labels.append(f'{kind} {palette}')
        mask=Image.open(out/'runtime_masks_2x'/(name+'.png')).convert('L')
        mask=mask.crop(tuple(crop[i]*2-origin[i%2] for i in range(4))).resize((w,h),Image.Resampling.BILINEAR)
        base=images[1].copy(); overlay=Image.new('RGBA',(w,h),(255,30,220,0));overlay.putalpha(mask.point(lambda v:round(v*.5)))
        base.alpha_composite(overlay);images.append(base);labels.append('R8 mask overlay')
        panel=Image.new('RGB',((w+4)*len(images),h+44),'#2a2d2b');d=ImageDraw.Draw(panel)
        d.text((3,3),name+' | each palette: native / restored; mask magenta',fill='white')
        for i,(im,label) in enumerate(zip(images,labels)):
            panel.paste(im,(i*(w+4),40),im);d.text((i*(w+4)+2,22),label,fill='white')
        panels.append((name,panel));evidence.append(name)
    pages=[];page=Image.new('RGB',(1800,1800),'#2a2d2b');x=y=rowh=0
    for name,panel in panels:
        if panel.width>1800 or panel.height>1800:
            path=out/'review'/f'{name}_palette_masks.png';panel.save(path);pages.append(str(path.relative_to(out)));continue
        if x+panel.width>1800:x=0;y+=rowh;rowh=0
        if y+panel.height>1800:
            path=out/'review'/f'all_palette_masks_{len(pages):02d}.png';page.crop((0,0,1800,y+rowh)).save(path);pages.append(str(path.relative_to(out)))
            page=Image.new('RGB',(1800,1800),'#2a2d2b');x=y=rowh=0
        page.paste(panel,(x,y));x+=panel.width;rowh=max(rowh,panel.height)
    if x or y:
        path=out/'review'/f'all_palette_masks_{len(pages):02d}.png';page.crop((0,0,1800,y+rowh)).save(path);pages.append(str(path.relative_to(out)))
    scan=[];samples=[];atlas_images={}
    for name,record in records.items():
        if name not in manifest['frames']:continue
        frame=manifest['frames'][name]
        if 'pixel_alias_of' in frame:continue
        clean=REPO/record['clean_path']
        for kind,path in [('cleaned',clean),('atlas',out/manifest['pages'][frame['page']]['base'])]:
            if kind=='cleaned':im=Image.open(path).convert('RGBA')
            else:
                if path not in atlas_images:atlas_images[path]=Image.open(path).convert('RGBA')
                x0,y0,w,h=frame['atlas_xywh'];im=atlas_images[path].crop((x0,y0,x0+w,y0+h))
            score,_=edge_candidates(im);cy,cx=np.unravel_index(score.argmax(),score.shape)
            maximum=float(score.max());scan.append(dict(frame=name,kind=kind,sha256=sha(path),max_score=maximum,pixels_over_80=int((score>80).sum())))
            samples.append((maximum,name+' '+kind,im,[int(cx),int(cy)]))
    worst=sorted(samples,key=lambda item:item[0],reverse=True)[:16]
    page=Image.new('RGB',(1072,154*math.ceil(len(worst)/4)),'#353535');d=ImageDraw.Draw(page)
    for i,(score,label,im,(cx,cy)) in enumerate(worst):
        x=(i%4)*268;y=(i//4)*154;d.text((x+2,y+2),label+f' {score:.1f}',fill='white')
        patch=im.crop((cx-64,cy-64,cx+64,cy+64))
        for j,color in enumerate(['#262a28','#eee9df']):
            bg=Image.new('RGBA',patch.size,color);bg.alpha_composite(patch);page.paste(bg,(x+j*134,y+22))
    edge_path=out/'review/worst_final_edges_100pct.png';page.save(edge_path)
    checks=read(out/'review/export_checks.json');checks['residual_spill_scan']=dict(method='Shared nearest-opaque-core chroma diagnostic on every cleaned physical pose and final atlas extraction. Scores flag intended colours too; visual light/dark review is required.',frames=scan,contact=str(edge_path.relative_to(out)),visual_review_complete=False)
    checks['palette_mask_review']=dict(frames=evidence,palettes=palettes,pages=pages,native_logical_pixel_scale=1,status='pending_visual_review')
    save(out/'review/export_checks.json',checks)
    print(stem,'placement pages',len(read(out/'review/complete_placement.json')['pages']),'palette/mask pages',len(pages),'edge samples',len(worst),'review pending')


def reused_contacts(stem):
    """Expose every later returned occurrence whose native bitmap has a canonical master."""
    root=STAGE/f'mm8_m{stem}';out=root/'redo_2x';run=read(out/'run.json')
    owners={};tiles=[];entries=[]
    for job in run['jobs']:
        if not job.get('selected_raw'):continue
        path=out/'review'/(job['id']+'_actual_return_registered.png')
        for i,name in enumerate(job['frames']):
            if name in owners and path.exists():
                source=Image.open(path).convert('RGB')
                tile=source.crop((i*256,0,(i+1)*256,source.height))
                canvas=Image.new('RGB',(256,tile.height+22),'#292d2e')
                ImageDraw.Draw(canvas).text((3,3),job['id']+' | '+name,fill='white')
                canvas.paste(tile,(0,22));tiles.append(canvas)
                entries.append(dict(job=job['id'],frame=name,actual_return=str(path.relative_to(out)),sha256=sha(path)))
            owners.setdefault(name,job['id'])
    pages=[]
    for start in range(0,len(tiles),12):
        group=tiles[start:start+12];height=max(t.height for t in group)
        page=Image.new('RGB',(1024,height*math.ceil(len(group)/4)),'#292d2e')
        for i,tile in enumerate(group):page.paste(tile,((i%4)*256,(i//4)*height))
        path=out/'review'/f'actual_reused_poses_{start//12:02d}.png';page.save(path);pages.append(str(path.relative_to(out)))
    save(out/'review/actual_reused_poses.json',dict(occurrences=entries,pages=pages,status='pending_visual_review'))
    print(stem,'later returned reused poses',len(entries),'pages',len(pages))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stems',nargs='+',type=int)
    for stem in parser.parse_args().stems:
        try:run(stem)
        except Exception as e:print(stem,'review preparation failed:',type(e).__name__,str(e))
