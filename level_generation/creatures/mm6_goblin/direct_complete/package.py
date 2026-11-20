"""Export shared goblin base/masks, exact native playback and compact review artifacts."""
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from prepare import ROOT, REPO, CANVAS, PALETTES, ACTIONS, native
from process import recolor, RAMPS, ALIASES

def overlay(im, mask):
    a=np.array(im);w=np.array(mask).astype(float)[:,:,:2]/255
    colors=np.array([[255,130,0],[0,190,255]])
    a[:,:,:3]=np.round(a[:,:,:3]*(1-.7*w.sum(axis=2))[:,:,None]+.7*w@colors).astype(np.uint8)
    return Image.fromarray(a)

def edge_stats(im):
    a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3]
    band=(alpha>0)&((ndimage.distance_transform_edt(alpha>=128)<=4)|(alpha<255))
    score=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1])*alpha/255*band
    y,x=np.unravel_index(np.argmax(score),score.shape)
    return {'max_score':float(score.max()),'candidates_above_16':int((score>16).sum()),'position':[int(x),int(y)]}

def playback(groups):
    bindings={g['sprite_name']:g for g in groups};by_palette={}
    for g in groups:
        entries=g['frames'];first=entries[0];name=first['texture_name']
        action='corpse' if name=='gobdyf0' else ACTIONS[name[3:5]]
        views={}
        for v in range(8):
            steps=[]
            for f in entries:
                mirror=f'Mirror{v}' in f['flags'];stored=8-v if mirror else v
                name=f['texture_name'] if 'Image1' in f['flags'] else f['texture_name']+str(stored)
                steps.append({'frame':name,'duration_ms':f['frame_length_raw']*62.5,'mirrored':mirror})
            views[str(v)]=steps
        by_palette.setdefault(str(first['palette_id']),{})[action]={'views':views,'single_view':'Image1' in first['flags'],
            'native_group':g['sprite_name'],'native_frame_scale':first['scale'],'native_length_raw':g['animation_length_raw'],
            'sequence_ms':sum(s['duration_ms'] for s in views['0']),
            'playback':'loop' if action in ['standing','walk'] else 'hold' if action=='corpse' else 'once',
            'next_action':'corpse' if action=='death' else 'standing' if action in ['attack','hit','fidget'] else None}
    return by_palette,bindings

def export():
    sources=json.loads((ROOT/'sources.json').read_text());reg=json.loads((ROOT/'registration.json').read_text())
    assert set(sources['sources'])==set(reg);assert not any(r['raw_clip'] for r in reg.values())
    for d in ['atlas','trimmed_2x','trimmed_masks_2x','previews','native_variants','sheets']:(ROOT/d).mkdir(exist_ok=True)
    frames={};tiles={};masks={};aligned={};audit={}
    for name in sorted(reg):
        r=reg[name];src=sources['sources'][name]
        assert hashlib.sha256((REPO/src['path']).read_bytes()).hexdigest()==src['sha256']
        im=Image.open(ROOT/f'aligned_2x/{name}.png').convert('RGBA');coverage=Image.open(ROOT/f'masks_2x/{name}.png').convert('RGB')
        a=np.array(im);w=np.array(coverage);solid=a[:,:,3]>0
        assert np.max(w.astype(int).sum(axis=2))<=255
        distance,idx=ndimage.distance_transform_edt(~solid,return_indices=True);ring=(distance<=3)&~solid
        a[:,:,:3][ring]=a[idx[0],idx[1],:3][ring];w[ring]=w[idx[0],idx[1]][ring]
        im=Image.fromarray(a);coverage=Image.fromarray(w)
        im.save(ROOT/f'aligned_2x/{name}.png');coverage.save(ROOT/f'masks_2x/{name}.png');aligned[name]=im
        b=im.getbbox();b=[max(0,b[0]-4),max(0,b[1]-4),min(im.width,b[2]+4),min(im.height,b[3]+4)]
        tile=im.crop(b);mask=coverage.crop(b);tiles[name]=tile;masks[name]=mask
        tile.save(ROOT/f'trimmed_2x/{name}.png');mask.save(ROOT/f'trimmed_masks_2x/{name}.png')
        rebuilt=Image.new('RGBA',im.size);rebuilt.paste(tile,b[:2]);assert np.array_equal(rebuilt,im)
        origin=r['canvas_origin_px'];frames[name]={'crop_origin_px':[b[0]+origin[0],b[1]+origin[1]],'crop_in_aligned_px':b,
            'aligned_canvas_origin_px':origin,'aligned_canvas_size_px':im.size,'source':name+'.bmp','source_palette':745,
            'source_canvas':src['size'],'native_offset':[0,0],'referenced':True}
        for p in PALETTES:
            native(name,p).save(ROOT/f'native_variants/{name}_{p}.png');v=recolor(tile,mask,p)
            assert np.array_equal(np.array(v)[:,:,3],np.array(tile)[:,:,3]);zero=np.array(mask).sum(axis=2)==0
            assert np.array_equal(np.array(v)[zero],np.array(tile)[zero])
            if p==745:assert np.array_equal(v,tile)
        audit[name]={'cleaned':edge_stats(Image.open(ROOT/f'cleaned/{name}.png')),'exported':edge_stats(tile)}
    layouts=[];current=[];x=y=2;rh=uw=0
    for name in sorted((n for n in tiles if n not in ALIASES),key=lambda n:(-tiles[n].height,-tiles[n].width,n)):
        w,h=tiles[name].size;assert max(w,h)+4<=2048
        if x+w+2>2048:x=2;y+=rh+4;rh=0
        if y+h+2>2048:layouts.append((current,uw,y+rh+2));current=[];x=y=2;rh=uw=0
        current.append((name,x,y));x+=w+4;rh=max(rh,h);uw=max(uw,x)
    if current:layouts.append((current,uw,y+rh+2))
    pages=[];pixels=0
    for page,(layout,width,height) in enumerate(layouts):
        base=Image.new('RGBA',(width,height));mask=Image.new('RGB',(width,height));pixels+=width*height
        for name,x,y in layout:
            tile=tiles[name];base.paste(tile,(x,y));mask.paste(masks[name],(x,y))
            frames[name].update(page=page,atlas_xywh=[x,y,tile.width,tile.height])
        base.save(ROOT/f'atlas/base_{page}.png');mask.save(ROOT/f'atlas/mask_{page}.png');previews={}
        for p in PALETTES:
            path=f'atlas/base_{page}.png' if p==745 else f'previews/palette_{p}_page_{page}.png'
            if p!=745:recolor(base,mask,p).save(ROOT/path)
            previews[str(p)]=path
        overlay(base,mask).save(ROOT/f'previews/mask_overlay_{page}.png')
        pages.append({'base':f'atlas/base_{page}.png','mask':f'atlas/mask_{page}.png','size':[width,height],
            'base_format':'RGBA8','mask_file_format':'RGB8','mask_runtime_format':'RG8 proposed; B unused',
            'variant_previews':previews,'mask_overlay':f'previews/mask_overlay_{page}.png'})
        for name,x,y in layout:
            f=frames[name];_,_,w,h=f['atlas_xywh'];box=[x,y,x+w,y+h]
            assert np.array_equal(base.crop(box),tiles[name]);assert np.array_equal(mask.crop(box),masks[name])
            audit[name]['atlas_extracted']=edge_stats(base.crop(box))
    for name,canonical in ALIASES.items():
        assert np.array_equal(native(name),native(canonical)), 'Native pixel alias changed'
        assert np.array_equal(tiles[name],tiles[canonical]) and np.array_equal(masks[name],masks[canonical])
        frames[name].update(page=frames[canonical]['page'],atlas_xywh=frames[canonical]['atlas_xywh'],pixel_alias=canonical)
        audit[name]['atlas_extracted']=audit[canonical]['atlas_extracted']
    animations,bindings=playback(sources['groups']['goblin']['sprites'])
    for actions in animations.values():
        for a in actions.values():
            for steps in a['views'].values():
                for s in steps:assert s['frame'] in frames
    memory={'original_all_files_rgba_one_palette':sum(s['size'][0]*s['size'][1]*4 for s in sources['sources'].values()),
        'original_indexed_bmp_disk':sum((REPO/s['path']).stat().st_size for s in sources['sources'].values()),
        'enhanced_base_rgba8':pixels*4,'enhanced_mask_rgb8_file_decode':pixels*3,
        'enhanced_base_plus_rgb8_mask':pixels*7,'enhanced_base_plus_rg8_mask_if_supported':pixels*6,
        'enhanced_base_plus_rgba8_mask_upload':pixels*8,'variant_previews_excluded':True}
    variants={str(p):{'name':{745:'Goblin / green',746:'Goblin Shaman / blue',747:'Goblin King / red'}[p],
        'native_frame_scale':sources['variant_scales'][str(p)][0],
        **({'exact_base_bypass':True} if p==745 else {'region_luminance_vectors':RAMPS[p].tolist()})} for p in PALETTES}
    manifest={'schema_version':2,'creature':'mm6:goblin','installed':False,
        'schema_status':'Staged two-region recolor extension; current runtime single-region shader cannot consume this unchanged',
        'pixels_per_logical_pixel':2,'logical_canvas':CANVAS,'logical_pivot':[177.5,289],'anchor':'bottom-center',
        'native_center_flag':False,'pages':pages,'frames':frames,'animations':animations['745'],
        'animations_by_palette':animations,'native_group_bindings':bindings,'variants':variants,
        'regions':{'R':'olive skin and yellow/gold accents','G':'brown leather and warm equipment/blade accents','B':'unused'},
        'recolor':{'model':'masked_regions_luminance_rgb_v1','space':'encoded sRGB RGB; linear mask coverage',
            'operation':'Y=dot(base,[.2126,.7152,.0722]); output=base*(1-R-G)+Y*(R*skinVector+G*equipmentVector); preserve alpha; base exact bypass',
            'fitting':'fixed least-squares target RGB versus base luma over classified native palette entries','reference':'process.py:mask,ramps,recolor'},
        'filtering':{'alpha':'straight RGBA, premultiplied Lanczos','crop_padding_px':4,'transparent_extrusion_px':3,'mipmaps':False},
        'memory_bytes':memory,'limitations':['Skin/equipment masks approximate continuous materials; native subtle palette changes are not reproduced exactly.',
            'Original accepted front art retained; AI surface detail, sword notches and armor perspective vary slightly between views.',
            '2x export does not imply 2x generated detail. Alpha is estimated from magenta.',
            'Only standing and walking have stored side/back views in native data. Other actions use native front reuse.']}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    order=['attack','death','walk','hit','fidget','standing','corpse']
    for v in range(5):
        sheet=Image.new('RGBA',(6*768,7*640))
        for row,action in enumerate(order):
            a=animations['745'][action]
            if v and a['single_view']:continue
            for col,s in enumerate(a['views'][str(v)]):
                name=s['frame'];origin=reg[name]['canvas_origin_px'];sheet.paste(aligned[name],(col*768+29+origin[0],row*640+31+origin[1]))
        sheet.save(ROOT/f'sheets/view_{v}_all_actions_2x.png')
    for masked in [False,True]:
        contact=Image.new('RGB',(6*260,10*245),(230,230,227) if masked else (40,43,42));d=ImageDraw.Draw(contact)
        for i,name in enumerate(frames):
            im=aligned[name]
            if masked:im=overlay(im,Image.open(ROOT/f'masks_2x/{name}.png'))
            im=im.convert('RGBa').resize((round(im.width/3),round(im.height/3)),Image.Resampling.LANCZOS).convert('RGBA')
            origin=reg[name]['canvas_origin_px'];x=i%6*260;y=i//6*245
            contact.paste(im,(x+8+round(origin[0]/3),y+24+round(origin[1]/3)),im)
            d.text((x+4,y+4),name,fill='black' if masked else 'white')
        contact.save(ROOT/f'review/{"all_masks_light" if masked else "all_base_dark"}.png')
    contact=Image.new('RGB',(5*355,3*315),(45,45,45));d=ImageDraw.Draw(contact)
    for row,p in enumerate(PALETTES):
        for v in range(5):
            name=f'gobsta{v}';im=recolor(aligned[name],Image.open(ROOT/f'masks_2x/{name}.png'),p)
            im=im.convert('RGBa').resize((round(im.width/2),round(im.height/2)),Image.Resampling.LANCZOS).convert('RGBA')
            contact.paste(im,(v*355,row*315+24),im);d.text((v*355+4,row*315+4),f'{p}: view {v}',fill='white')
    contact.save(ROOT/'review/standing_variants.png')
    ranked=sorted(audit,key=lambda n:audit[n]['atlas_extracted']['max_score'],reverse=True)[:12]
    contact=Image.new('RGB',(6*280,2*190),(55,55,55));d=ImageDraw.Draw(contact)
    for i,name in enumerate(ranked):
        x,y=audit[name]['atlas_extracted']['position'];crop=tiles[name].crop((x-16,y-16,x+16,y+16)).resize((128,128),Image.Resampling.NEAREST)
        for j,bg in enumerate([(35,35,35),(240,240,240)]):
            patch=Image.new('RGBA',crop.size,(*bg,255));patch.alpha_composite(crop);contact.paste(patch.convert('RGB'),(i%6*280+j*132,i//6*190+30))
        d.text((i%6*280+2,i//6*190+8),name,fill='white')
    contact.save(ROOT/'review/edge_current.png')
    (ROOT/'review/edge_current.json').write_text(json.dumps({'matte':'magenta','band_physical_px':4,'frames':audit},indent=2)+'\n')
    validation={'source_files':59,'unique_enhanced_tiles':58,'pixel_aliases':ALIASES,'reused_front':31,'new_direction_frames':28,'source_hashes_unchanged':True,
        'raw_cells_unclipped':True,'exact_crop_reconstruction':True,'exact_atlas_extraction':True,'mask_weight_sum_valid':True,
        'variant_alpha_unchanged':True,'zero_mask_unchanged':True,'base_bypass_exact':True,
        'native_palette_timing_preserved':True,'residual_candidates_above_16':sum(a[s]['candidates_above_16'] for a in audit.values() for s in ['cleaned','atlas_extracted']),
        'memory_bytes':memory}
    (ROOT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation))

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--redo', action='store_true')
    args = parser.parse_args()
    if args.redo:
        ROOT = ROOT / 'redo_2x'
    export()
    if args.redo:
        path = ROOT / 'manifest.json'
        manifest = json.loads(path.read_text())
        records = json.loads((ROOT / 'registration.json').read_text())
        manifest['schema_status'] = 'Staged RG8 two-region package; not installed'
        manifest['generated_detail'] = dict(
            measured_minimum=min(min(r['effective_sampling_xy']) for r in records.values()),
            replacement_minimum=min(min(r['effective_sampling_xy']) for r in records.values()
                                    if 'retained_from' not in r),
            retained_adequate_frames=[n for n,r in records.items() if 'retained_from' in r],
            registration='registration.json', calibration='calibration.json')
        manifest['quality_status'] = 'pending_full_animation_and_variant_review'
        for folder, channels in [('aligned_2x',4), ('masks_2x',3), ('cleaned',4)]:
            manifest['memory_bytes'][folder+'_decoded'] = sum(
                Image.open(ROOT/folder/(name+'.png')).width * Image.open(ROOT/folder/(name+'.png')).height * channels
                for name in records)
        manifest['limitations'] = [
            'Selective masks approximate continuous materials and subtle native palette changes.',
            'AI surface detail and armor/sword perspective vary slightly between frames.',
            'Front standing retains the adequate historical 2x checkpoint; replacement art uses supplied alpha.',
            'Only standing and walking have native side/back views; other actions reuse the front view.']
        for page in manifest['pages']:
            page['mask_runtime_format'] = 'RG8; B unused'
        path.write_text(json.dumps(manifest, indent=2)+'\n')
        path = ROOT / 'validation.json'
        validation = json.loads(path.read_text())
        validation.pop('reused_front', None)
        validation.pop('new_direction_frames', None)
        validation['retained_adequate_frames'] = ['gobsta0']
        validation['replacement_frame_names'] = len(records)-1
        validation['memory_bytes'] = manifest['memory_bytes']
        generation = json.loads((ROOT/'generation.json').read_text())['batches']
        for attempt in generation.values():
            assert hashlib.sha256((REPO/attempt['raw']).read_bytes()).hexdigest() == attempt['sha256']
            assert hashlib.sha256((REPO/attempt['prompt']).read_bytes()).hexdigest() == attempt['prompt_sha256']
            for reference in attempt['references']:
                assert hashlib.sha256((REPO/reference['path']).read_bytes()).hexdigest() == reference['sha256']
        original = json.loads((ROOT.parent/'manifest.json').read_text())
        for key in ['animations', 'animations_by_palette', 'logical_canvas', 'logical_pivot']:
            assert manifest[key] == original[key], key
        validation['generation_provenance_hashes_verified'] = True
        validation['per_palette_native_sequences_preserved'] = True
        path.write_text(json.dumps(validation, indent=2)+'\n')
