"""Package the complete staged Human Male Cleric restoration with matching RGB8 staff/hair coverage atlases."""
import copy
import json
import math
import shutil
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
from process import ROOT, queue, save, spill
from materials import PALETTES

def run(partial=False):
    sources = json.loads((ROOT/'sources.json').read_text())
    registration = json.loads((ROOT/'calibration_registration.json').read_text())
    aliases = sources['pixel_aliases']
    missing = sorted(set(sources['sources']) - (set(registration) | set(aliases)))
    assert partial or not missing, missing
    assert set(registration) | set(aliases) <= set(sources['sources'])
    assert not set(registration) & set(aliases)
    settings = json.loads((ROOT/'material_settings.json').read_text())
    for folder in ['atlas','runtime_aligned_2x','runtime_masks_2x','trimmed_2x','trimmed_masks_2x']:
        (ROOT/folder).mkdir(exist_ok=True)
    frames, tiles, masks, edges = {}, {}, {}, {}
    for name, source in sources['sources'].items():
        assert queue.sha(queue.REPO/source['path']) == source['sha256']
        if name in missing:
            for palette in PALETTES:
                queue.native(ROOT,name,palette).save(ROOT/f'native_variants/{name}_{palette}.png')
            continue
        if name in aliases:
            canonical = sources['sources'][aliases[name]]
            assert source['pixel_hash'] == canonical['pixel_hash']
            assert source['size'] == canonical['size']
            for palette in PALETTES:
                assert np.array_equal(queue.native(ROOT,name,palette),queue.native(ROOT,aliases[name],palette))
            continue
        r = registration[name]
        im = Image.open(ROOT/f'toned_2x/{name}.png').convert('RGBA')
        a = np.array(im)
        mask = np.array(Image.open(ROOT/f'masks_2x/{name}.png'))
        assert mask.shape == a.shape[:2] + (3,)
        solid = a[:,:,3]>0
        dist, ix = ndi.distance_transform_edt(~solid,return_indices=True)
        ring = (dist<=3)&~solid
        a[:,:,:3][~solid] = 0
        a[:,:,:3][ring] = a[ix[0],ix[1],:3][ring]
        mask[~solid] = 0
        mask[ring] = mask[ix[0],ix[1]][ring]
        im, maskIm = Image.fromarray(a), Image.fromarray(mask)
        im.save(ROOT/f'runtime_aligned_2x/{name}.png')
        maskIm.save(ROOT/f'runtime_masks_2x/{name}.png')
        box = im.getchannel('A').getbbox()
        box = [max(0,box[0]-4),max(0,box[1]-4),min(im.width,box[2]+4),min(im.height,box[3]+4)]
        tiles[name], masks[name] = im.crop(box), maskIm.crop(box)
        for tile, original, folder in [(tiles[name],im,'trimmed_2x'),(masks[name],maskIm,'trimmed_masks_2x')]:
            reconstructed=Image.new(original.mode,original.size)
            reconstructed.paste(tile,box[:2])
            assert np.array_equal(reconstructed,original)
            tile.save(ROOT/f'{folder}/{name}.png')
        for palette in PALETTES:
            variant=np.asarray(Image.open(ROOT/f'previews/{name}_{palette}.png'))
            assert np.array_equal(variant[:,:,3],a[:,:,3])
            if palette==461:assert np.array_equal(variant[solid],a[solid])
        frames[name] = {'source':name+'.bmp','logical_size':source['size'],
            'crop_origin_px':[box[0]+r['canvas_origin_px'][0],box[1]+r['canvas_origin_px'][1]],
            'crop_in_aligned_px':box,'aligned_canvas_origin_px':r['canvas_origin_px'],
            'aligned_canvas_size_px':r['aligned_size_px'],'referenced':source['referenced']}
        edges[name]={'cleaned':spill(Image.open(ROOT/f'cleaned/{name}.png'),name),'aligned':spill(im,name)}
    layouts, current = [], []
    x=y=rowHeight=0
    for name, tile in sorted(tiles.items(),key=lambda pair:(-pair[1].height,pair[0])):
        width=math.ceil((tile.width+32)/16)*16; height=math.ceil((tile.height+32)/16)*16
        assert max(width,height)<=2048
        if x+width>2048:x=0;y+=rowHeight;rowHeight=0
        if y+height>2048:layouts.append(current);current=[];x=y=rowHeight=0
        current.append((name,x,y,width,height));x+=width;rowHeight=max(rowHeight,height)
    if current:layouts.append(current)
    pages=[]
    for pageId,layout in enumerate(layouts):
        size=(max(x+w for n,x,y,w,h in layout),max(y+h for n,x,y,w,h in layout))
        base=Image.new('RGBA',size);mask=Image.new('RGB',size)
        for name,x,y,w,h in layout:
            tile=tiles[name];rect=[x+16,y+16,tile.width,tile.height]
            base.paste(tile,rect[:2]);mask.paste(masks[name],rect[:2])
            frames[name].update(page=pageId,atlas_xywh=rect)
        bp=f'atlas/base_{pageId}.png';mp=f'atlas/mask_{pageId}.png'
        base.save(ROOT/bp);mask.save(ROOT/mp)
        pages.append({'base':bp,'mask':mp,'size':list(size),'base_format':'RGBA8','mask_format':'RGB8',
                      'base_color_space':'sRGB','mask_color_space':'linear coverage','gutter_px':16,'mipmaps':False})
        for name,x,y,w,h in layout:
            xx,yy,ww,hh=frames[name]['atlas_xywh'];box=(xx,yy,xx+ww,yy+hh)
            assert np.array_equal(base.crop(box),tiles[name])
            assert np.array_equal(mask.crop(box),masks[name])
            edges[name]['atlas_extracted']=spill(base.crop(box),name)
    for name, canonical in aliases.items():
        frames[name] = {**copy.deepcopy(frames[canonical]), 'source':name+'.bmp',
                        'referenced':sources['sources'][name]['referenced'], 'pixel_alias_of':canonical}
        edges[name] = copy.deepcopy(edges[canonical])
        for folder in ['runtime_aligned_2x','runtime_masks_2x']:
            shutil.copy2(ROOT/f'{folder}/{canonical}.png',ROOT/f'{folder}/{name}.png')
        for palette in PALETTES:
            shutil.copy2(ROOT/f'previews/{canonical}_{palette}.png',ROOT/f'previews/{name}_{palette}.png')
            queue.native(ROOT,name,palette).save(ROOT/f'native_variants/{name}_{palette}.png')
    animations=copy.deepcopy(sources['bindings'])
    for actor in animations.values():
        for action in actor['actions'].values():
            for steps in action['views'].values():
                for step in steps:
                    if step['frame']:assert step['frame'] in frames or (partial and step['frame'] in missing)
    manifest={'schema_version':1,'creature':'mm8:m460','status':'partial' if missing else 'awaiting_visual_acceptance',
        'pixels_per_logical_pixel':2,'frames':frames,'pages':pages,'animations':animations,
        'regions':settings['regions'],'variants':settings,'missing_frames':missing,
        'pivot_rule':'Native per-step Center/bottom-center flag and logical 256x256 canvas; mirror around native pivot.',
        'filter_policy':'Premultiplied-alpha Lanczos extraction, shared batch anatomical scale/translation with premultiplied bicubic; 3px hidden color/coverage bleed; 16px aligned gutters; no mipmaps.',
        'source_manifest':'sources.json','viewer':'viewer.html','installed':False,
        'pixel_aliases':aliases,
        'runtime_support':'Staged offline staff palette deltas and hair ramps with RGB8 enhanced coverage masks; runtime integration is outside this package.'}
    save(ROOT/'draft_manifest.json',manifest)
    pixels=sum(p['size'][0]*p['size'][1] for p in pages)
    tight=sum(im.width*im.height*7 for im in tiles.values())
    checks={'source_files':len(frames),'unique_frames':len(tiles),'full_coverage':not missing, 'missing_frames':missing,
        'pixel_aliases_verified':aliases,
        'source_hashes_unchanged':True,'exact_crop_reconstruction':True,'exact_atlas_extraction':True,
        'base_mask_placement_identical':True,'variant_alpha_unchanged':True,'base_bypass_exact':True,
        'visual_review_complete':False,'animation_review_complete':False,
        'memory_bytes':{'base_rgba8':pixels*4,'mask_rgb8':pixels*3,'total_base_mask_packing':pixels*7,
                        'tight_rgba_plus_mask':tight,'packing_overhead':pixels*7-tight}}
    save(ROOT/'review/export_checks.json',checks);save(ROOT/'review/edge_audit.json',edges)
    template=(ROOT/'viewer_template.html').read_text()
    (ROOT/'viewer.html').write_text(template.replace('__DATA__',json.dumps({'manifest':manifest,'sources':sources['sources']})).replace('__COVERAGE__',f'{len(frames)}/{len(sources["sources"])} native poses restored. '+(f'{len(missing)} poses pending restoration.' if missing else 'All native poses included.')))
    print(json.dumps({'frames':len(frames),'pages':len(pages),'memory_bytes':checks['memory_bytes']}))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true')
    run(partial=parser.parse_args().partial)
