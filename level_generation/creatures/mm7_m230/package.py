"""Pack staged base/mask atlases and deterministic palette previews. No runtime installation."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from process import ROOT, recolor, resize_base
from prepare import native, REPO

ACTIONS={'s':'standing','w':'walk','a':'attack','n':'hit','f':'fidget','d':'death','x':'corpse'}
PALETTES=[54,55,233]

def pad_colors(im):
    a=np.array(im); solid=a[:,:,3]>0
    distance,indices=ndimage.distance_transform_edt(~solid,return_indices=True)
    ring=(distance<=3)&~solid
    a[:,:,:3][ring]=a[indices[0],indices[1],:3][ring]
    return Image.fromarray(a)

def export():
    sources=json.loads((ROOT/'sources.json').read_text())
    registration=json.loads((ROOT/'registration.json').read_text())
    assert set(sources['sources'])==set(registration),'Missing restored frames'
    assert not any(r['raw_clip'] for r in registration.values()),'Raw cell clips remain'
    minimum_sampling=min(2/r['scale'] for r in registration.values())
    assert minimum_sampling>=2-1e-6,'Actual generated detail below 2x; resume sampling repair'
    for d in ['atlas','trimmed_2x','trimmed_masks_2x','previews','native_variants','sheets']:
        (ROOT/d).mkdir(exist_ok=True)
    frames={}; tiles={}; masks={}; aligned={}
    for name,record in registration.items():
        source=REPO/sources['sources'][name]['path']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==sources['sources'][name]['sha256']
        im=pad_colors(Image.open(ROOT/f'aligned_2x/{name}.png').convert('RGBA'))
        # The master includes the same transparent edge RGB as its exact packed crop.
        im.save(ROOT/f'aligned_2x/{name}.png');aligned[name]=im
        coverage=Image.open(ROOT/f'masks_2x/{name}.png').convert('L')
        assert im.size==coverage.size
        # Match transparent RGB extrusion with mask extrusion, avoiding green padding in blue/red variants.
        solid=np.array(im)[:,:,3]>0
        distance,indices=ndimage.distance_transform_edt(~solid,return_indices=True)
        weights=np.array(coverage);ring=(distance<=3)&~solid
        weights[ring]=weights[indices[0],indices[1]][ring]
        coverage=Image.fromarray(weights);coverage.save(ROOT/f'masks_2x/{name}.png')
        box=im.getchannel('A').getbbox()
        box=(max(0,box[0]-4),max(0,box[1]-4),min(im.width,box[2]+4),min(im.height,box[3]+4))
        tile=im.crop(box); mask=coverage.crop(box)
        tile.save(ROOT/f'trimmed_2x/{name}.png');mask.save(ROOT/f'trimmed_masks_2x/{name}.png')
        reconstruction=Image.new('RGBA',im.size);reconstruction.paste(tile,box[:2])
        assert np.array_equal(np.array(reconstruction),np.array(im)),name
        tiles[name]=tile;masks[name]=mask
        origin=record['canvas_origin_px']
        frames[name]={'crop_origin_px':[box[0]+origin[0],box[1]+origin[1]],'aligned_canvas_origin_px':origin,
            'aligned_canvas_size_px':list(im.size),'crop_in_aligned_px':list(box),
            'source':name+'.bmp','source_palette':54,'anchor':'Center'}
        for palette in PALETTES:
            native(name,palette).save(ROOT/f'native_variants/{name}_{palette}.png')
        for palette in PALETTES:
            variant=recolor(tile,mask,palette)
            assert np.array_equal(np.array(variant)[:,:,3],np.array(tile)[:,:,3])
            unchanged=np.array(mask)==0
            assert np.array_equal(np.array(variant)[unchanged],np.array(tile)[unchanged])
            if palette==54: assert np.array_equal(np.array(variant),np.array(tile))
    # Deterministic height-sorted shelves with a maximum 2048px edge. No unnecessary square padding.
    layouts=[];current=[];x=2;y=2;row_h=0;used_w=0
    for name in sorted(tiles,key=lambda n:(-tiles[n].height,-tiles[n].width,n)):
        w,h=tiles[name].size
        assert w+4<=2048 and h+4<=2048
        if x+w+2>2048: x=2;y+=row_h+4;row_h=0
        if y+h+2>2048:
            used_h=max(py+tiles[n].height+2 for n,px,py in current)
            layouts.append((current,used_w,used_h));current=[];x=2;y=2;row_h=0;used_w=0
        current.append((name,x,y));x+=w+4;row_h=max(row_h,h);used_w=max(used_w,x)
    if current:layouts.append((current,used_w,y+row_h+2))
    pages=[];atlas_pixels=0
    for index,(layout,width,height) in enumerate(layouts):
        base=Image.new('RGBA',(width,height));mask=Image.new('L',(width,height));atlas_pixels+=width*height
        for name,x,y in layout:
            tile=tiles[name];base.paste(tile,(x,y));mask.paste(masks[name],(x,y))
            frames[name].update(page=index,atlas_xywh=[x,y,tile.width,tile.height])
        base.save(ROOT/f'atlas/base_{index}.png');mask.save(ROOT/f'atlas/mask_{index}.png')
        variants={}
        for palette in PALETTES:
            filename=f'atlas/base_{index}.png' if palette==54 else f'previews/palette_{palette}_page_{index}.png'
            if palette!=54:recolor(base,mask,palette).save(ROOT/filename)
            variants[str(palette)]=filename
        overlay=np.array(base);weight=np.array(mask)/255
        overlay[:,:,:3]=np.round(overlay[:,:,:3]*(1-.7*weight[:,:,None])+np.array([255,110,0])*.7*weight[:,:,None]).astype(np.uint8)
        Image.fromarray(overlay).save(ROOT/f'previews/mask_overlay_{index}.png')
        pages.append({'base':f'atlas/base_{index}.png','mask':f'atlas/mask_{index}.png','size':[width,height],
                      'base_format':'RGBA8','mask_format':'R8','variant_previews':variants,
                      'mask_overlay':f'previews/mask_overlay_{index}.png'})
    for name,f in frames.items():
        x,y,w,h=f['atlas_xywh'];page=pages[f['page']]
        for path,expected in [(page['base'],tiles[name]),(page['mask'],masks[name])]:
            with Image.open(ROOT/path) as im:
                assert np.array_equal(np.array(im.crop((x,y,x+w,y+h))),np.array(expected))
    animations={};group_bindings={}
    for group in sources['groups']['m231']['sprites']:
        code=group['sprite_name'][-1]; action=ACTIONS[code]; entries=group['frames'];views={}
        for view in range(8):
            steps=[]
            for e in entries:
                mirror=f'Mirror{view}' in e['flags'];source_view=8-view if mirror else view
                name=e['texture_name'] if 'Image1' in e['flags'] else e['texture_name']+str(source_view)
                assert name in frames
                steps.append({'frame':name,'duration_ms':e['frame_length_raw']*62.5,'mirrored':mirror})
            views[str(view)]=steps
        animations[action]={'views':views,'single_view':'Image1' in entries[0]['flags'],
            'native_length_raw':group['animation_length_raw'], 'sequence_ms':sum(x['duration_ms'] for x in views['0']),
            'playback':'loop' if action in ['standing','walk'] else 'hold' if action=='corpse' else 'once',
            'next_action':'corpse' if action=='death' else 'standing' if action in ['hit','attack','fidget'] else None}
    for variant,groups in sources['groups'].items():
        group_bindings[variant]={g['sprite_name']:{'action':ACTIONS[g['sprite_name'][-1]],'sprite_id':g['sprite_id'],
            'palette_id':g['frames'][0]['palette_id'],'scale':g['frames'][0]['scale'],'flags':g['frames'][0]['flags']}
            for g in groups['sprites']}
    variants={'54':{'name':'Initiate of the Sword / green','exact_base_bypass':True},
              '55':{'name':'Champion of the Sword / blue','chroma_vector':[.20,.18,1.]},
              '233':{'name':'Master of the Sword / red','chroma_vector':[1.,.12,.27]}}
    manifest={'schema_version':1,'schema_status':'staged asset contract; not an engine-supported loader schema',
        'creature':'mm7:creature/m230','installed':False,'pixels_per_logical_pixel':2,
        'logical_canvas':[256,256],'logical_pivot':[128,128],'anchor':'Center','native_frame_scale':.899994,
        'coordinate_rule':'local_x=(crop_origin_x+u)/2-128; local_up=128-(crop_origin_y+v)/2; mirror local_x and UV together',
        'pages':pages,'frames':frames,'animations':animations,'native_group_bindings':group_bindings,'variants':variants,
        'regions':{'mask_r':'soft green textile/plume coverage; excludes neutral heraldry, metals and warm leather'},
        'recolor':{'color_space':'sRGB encoded RGB normalized 0..1; mask is linear coverage',
            'operation':'n=min(R,B); c=max(0,G-n); target=n+c*chroma_vector; output=lerp(base,target,mask); alpha unchanged',
            'shading':'fixed chromatic ramp over retained neutral component; no per-frame normalization',
            'reference_implementation':'process.py:recolor'},
        'filtering':{'alpha':'straight RGBA PNG; premultiply for resampling','transparent_color_extrusion_px':3,
            'crop_padding_px':4,'atlas_gutter_px':2,'mipmaps':False,'mask_color_space':'linear'},
        'memory_bytes':{'original_all_frames_rgba_one_palette':114*256*256*4,
            'enhanced_tight_base':sum(im.width*im.height*4 for im in tiles.values()),
            'enhanced_atlas_base':atlas_pixels*4,'enhanced_atlas_mask_r8':atlas_pixels,
            'enhanced_shared_base_and_mask':atlas_pixels*5,
            'baked_variant_preview_pages_excluded':True},
        'limits':['AI artwork interprets low-resolution detail; microdetails may vary across poses.',
            'Masks and ramps approximate native palette appearances on new artwork, not indexed-pixel identity.',
            '2x is the export tier; raw batches have differing per-pose detail. No renderer integration in this package.']}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # A full-action sheet per stored view for review, separate from runtime atlas allocation.
    order=['attack','death','walk','hit','fidget','standing','corpse']
    for view in range(5):
        sheet=Image.new('RGBA',(8*544,len(order)*544))
        for row,action in enumerate(order):
            anim=animations[action]
            if view and anim['single_view']:continue
            for col,step in enumerate(anim['views'][str(view)]):
                name=step['frame'];im=aligned[name];origin=registration[name]['canvas_origin_px']
                sheet.paste(im,(col*544+16+origin[0],row*544+16+origin[1]))
        sheet.save(ROOT/f'sheets/view_{view}_all_actions_2x.png')
    # Native-timed APNG, five stored views side by side. Default viewer handles all eight aliases.
    for action,anim in animations.items():
        seq=anim['views']['0'];playback=[]
        for frame_index in range(len(seq)):
            canvas=Image.new('RGBA',(5*280,280))
            for view in range(1 if anim['single_view'] else 5):
                name=anim['views'][str(view)][frame_index]['frame'];im=aligned[name];origin=registration[name]['canvas_origin_px']
                im=resize_base(im,(round(im.width/2),round(im.height/2)))
                canvas.paste(im,(view*280+12+round(origin[0]/2),12+round(origin[1]/2)))
            playback.append(canvas)
        playback[0].save(ROOT/f'previews/{action}.png',save_all=len(playback)>1,append_images=playback[1:],
                        duration=[int(x['duration_ms']) for x in seq],loop=0,disposal=0,blend=0)
    validation={'frames':len(frames),'stored_views':5,'runtime_view_aliases':8,'palette_variants':3,
        'minimum_actual_generated_sampling':minimum_sampling,'actual_generated_detail_at_least_2x':True,
        'all_sources_unchanged':True,'all_raw_cells_unclipped':True,'exact_crop_reconstruction':True,
        'exact_atlas_extraction':True,'all_variant_alpha_unchanged':True,'zero_mask_pixels_unchanged':True,
        'base_variant_exact_bypass':True,'memory_bytes':manifest['memory_bytes']}
    (ROOT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    from edge_audit import audit
    audit()
    print(json.dumps(validation))

if __name__=='__main__':export()
