"""Package the complete staged fish restoration with matching R8 coverage atlases."""
import copy
import json
import math
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
from process import ROOT, queue, save, spill
from materials import PALETTES

def run():
    sources = json.loads((ROOT/'sources.json').read_text())
    registration = json.loads((ROOT/'registration.json').read_text())
    assert set(sources['sources']) == set(registration)
    assert not sources['pixel_aliases']
    settings = json.loads((ROOT/'material_settings.json').read_text())
    for folder in ['atlas','runtime_aligned_2x','runtime_masks_2x','trimmed_2x','trimmed_masks_2x']:
        (ROOT/folder).mkdir(exist_ok=True)
    frames, tiles, masks, edges = {}, {}, {}, {}
    for name, source in sources['sources'].items():
        assert queue.sha(queue.REPO/source['path']) == source['sha256']
        r = registration[name]
        im = Image.open(ROOT/f'toned_2x/{name}.png').convert('RGBA')
        a = np.array(im)
        mask = np.array(Image.open(ROOT/f'masks_2x/{name}.png'))
        assert mask.shape == a.shape[:2]
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
            if palette==637:assert np.array_equal(variant[solid],a[solid])
        frames[name] = {'source':name+'.bmp','source_canvas':source['size'],
            'crop_origin_px':[box[0]+r['canvas_origin_px'][0],box[1]+r['canvas_origin_px'][1]],
            'crop_in_aligned_px':box,'aligned_canvas_origin_px':r['canvas_origin_px'],
            'aligned_canvas_size_px':r['aligned_size_px'],'referenced':source['referenced']}
        edges[name]={'cleaned':spill(Image.open(ROOT/f'cleaned/{name}.png')),'aligned':spill(im)}
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
        base=Image.new('RGBA',size);mask=Image.new('L',size)
        for name,x,y,w,h in layout:
            tile=tiles[name];rect=[x+16,y+16,tile.width,tile.height]
            base.paste(tile,rect[:2]);mask.paste(masks[name],rect[:2])
            frames[name].update(page=pageId,atlas_xywh=rect)
        bp=f'atlas/base_{pageId}.png';mp=f'atlas/mask_{pageId}.png'
        base.save(ROOT/bp);mask.save(ROOT/mp)
        pages.append({'base':bp,'mask':mp,'size':list(size),'base_format':'RGBA8','mask_format':'R8',
                      'base_color_space':'sRGB','mask_color_space':'linear coverage','gutter_px':16,'mipmaps':False})
        for name,x,y,w,h in layout:
            xx,yy,ww,hh=frames[name]['atlas_xywh'];box=(xx,yy,xx+ww,yy+hh)
            assert np.array_equal(base.crop(box),tiles[name])
            assert np.array_equal(mask.crop(box),masks[name])
            edges[name]['atlas_extracted']=spill(base.crop(box))
    animations=copy.deepcopy(sources['bindings'])
    for actor in animations.values():
        for action in actor['actions'].values():
            for steps in action['views'].values():
                for step in steps:
                    if step['frame']:assert step['frame'] in frames
    manifest={'schema_version':1,'creature':'mm8:m636','status':'awaiting_visual_acceptance',
        'pixels_per_logical_pixel':2,'frames':frames,'pages':pages,'animations':animations,
        'regions':settings['regions'],'variants':settings,'missing_frames':[],
        'pivot_rule':'Native per-step Center/bottom-center flag and logical 256x256 canvas; mirror around native pivot.',
        'filter_policy':'Premultiplied-alpha Lanczos; 3px hidden color/coverage bleed; 16px aligned gutters; no mipmaps.',
        'source_manifest':'sources.json','viewer':'viewer.html','installed':False,
        'runtime_support':'Staged offline palette-delta operation; runtime integration not part of this package.'}
    save(ROOT/'draft_manifest.json',manifest)
    pixels=sum(p['size'][0]*p['size'][1] for p in pages)
    tight=sum(im.width*im.height*5 for im in tiles.values())
    checks={'source_files':len(frames),'unique_frames':len(tiles),'full_coverage':True,
        'source_hashes_unchanged':True,'exact_crop_reconstruction':True,'exact_atlas_extraction':True,
        'base_mask_placement_identical':True,'variant_alpha_unchanged':True,'base_bypass_exact':True,
        'visual_review_complete':False,'animation_review_complete':False,
        'memory_bytes':{'base_rgba8':pixels*4,'mask_r8':pixels,'total_base_mask_packing':pixels*5,
                        'tight_rgba_plus_mask':tight,'packing_overhead':pixels*5-tight}}
    save(ROOT/'review/export_checks.json',checks);save(ROOT/'review/edge_audit.json',edges)
    template=(ROOT/'viewer_template.html').read_text()
    (ROOT/'viewer.html').write_text(template.replace('__DATA__',json.dumps({'manifest':manifest,'sources':sources['sources']})))
    print(json.dumps({'frames':len(frames),'pages':len(pages),'memory_bytes':checks['memory_bytes']}))

if __name__=='__main__':
    run()
