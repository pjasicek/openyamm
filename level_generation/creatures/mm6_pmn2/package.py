"""Pack pmn2 base/masks, retain native playback, audit every contour, build offline review."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
from prepare import ROOT,REPO,CANVAS,native,PALETTES
from process import ALIASES,RAMPS,recolor,resize_base
ACTIONS={'sta':'standing','waa':'walk','ata':'attack','wia':'hit','fia':'fidget','dea':'death','ded':'corpse'}

def overlay(im,mask):
    a=np.array(im);w=np.array(mask)/255
    a[:,:,:3]=np.round(a[:,:,:3]*(1-.7*w[:,:,None])+np.array([255,110,0])*.7*w[:,:,None]).astype(np.uint8)
    return Image.fromarray(a)

def edge_stats(im):
    a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3]
    band=(alpha>0)&((ndimage.distance_transform_edt(alpha>=128)<=4)|(alpha<255))
    score=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1])*alpha/255*band
    y,x=np.unravel_index(np.argmax(score),score.shape)
    return {'max_score':float(score.max()),'candidates_above_16':int((score>16).sum()),'position':[int(x),int(y)]}

def export():
    sources=json.loads((ROOT/'sources.json').read_text());reg=json.loads((ROOT/'registration.json').read_text())
    assert set(sources['sources'])==set(reg),'Missing restored files'
    assert not any(r['raw_clip'] for r in reg.values()),'Review extraction boundaries'
    for d in ['atlas','trimmed_2x','trimmed_masks_2x','previews','native_variants','sheets']:(ROOT/d).mkdir(exist_ok=True)
    frames={};tiles={};masks={};aligned={};audit={}
    for name,r in reg.items():
        src=sources['sources'][name];assert hashlib.sha256((REPO/src['path']).read_bytes()).hexdigest()==src['sha256']
        im=Image.open(ROOT/f'aligned_2x/{name}.png').convert('RGBA');mask=Image.open(ROOT/f'masks_2x/{name}.png').convert('L')
        a=np.array(im);w=np.array(mask);solid=a[:,:,3]>0
        distance,idx=ndimage.distance_transform_edt(~solid,return_indices=True);ring=(distance<=3)&~solid
        a[:,:,:3][ring]=a[idx[0],idx[1],:3][ring];w[ring]=w[idx[0],idx[1]][ring]
        im=Image.fromarray(a);mask=Image.fromarray(w);im.save(ROOT/f'aligned_2x/{name}.png');mask.save(ROOT/f'masks_2x/{name}.png');aligned[name]=im
        b=im.getchannel('A').getbbox();b=(max(0,b[0]-4),max(0,b[1]-4),min(im.width,b[2]+4),min(im.height,b[3]+4))
        tile=im.crop(b);masktile=mask.crop(b);tiles[name]=tile;masks[name]=masktile
        tile.save(ROOT/f'trimmed_2x/{name}.png');masktile.save(ROOT/f'trimmed_masks_2x/{name}.png')
        restored=Image.new('RGBA',im.size);restored.paste(tile,b[:2]);assert np.array_equal(restored,im)
        origin=r['canvas_origin_px'];frames[name]={'crop_origin_px':[b[0]+origin[0],b[1]+origin[1]],'crop_in_aligned_px':b,
            'aligned_canvas_origin_px':origin,'aligned_canvas_size_px':im.size,'source':name+'.bmp','source_palette':802,
            'source_canvas':src['size'],'native_offset':src['native_offset'],'referenced':src['referenced']}
        if name in ALIASES:frames[name]['pixel_alias']=ALIASES[name]
        for pal in PALETTES:
            native(name,pal).save(ROOT/f'native_variants/{name}_{pal}.png');v=recolor(tile,masktile,pal)
            assert np.array_equal(np.array(v)[:,:,3],np.array(tile)[:,:,3]);zero=np.array(masktile)==0
            assert np.array_equal(np.array(v)[zero],np.array(tile)[zero])
            if pal==802:assert np.array_equal(v,tile)
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
        base=Image.new('RGBA',(width,height));mask=Image.new('L',(width,height));pixels+=width*height
        for name,x,y in layout:
            tile=tiles[name];base.paste(tile,(x,y));mask.paste(masks[name],(x,y));frames[name].update(page=page,atlas_xywh=[x,y,tile.width,tile.height])
        base.save(ROOT/f'atlas/base_{page}.png');mask.save(ROOT/f'atlas/mask_{page}.png')
        previews={}
        for pal in PALETTES:
            target=f'atlas/base_{page}.png' if pal==802 else f'previews/palette_{pal}_page_{page}.png'
            if pal!=802:recolor(base,mask,pal).save(ROOT/target)
            previews[str(pal)]=target
        overlay(base,mask).save(ROOT/f'previews/mask_overlay_{page}.png')
        pages.append({'base':f'atlas/base_{page}.png','mask':f'atlas/mask_{page}.png','size':[width,height],
            'base_format':'RGBA8','mask_format':'R8','variant_previews':previews,'mask_overlay':f'previews/mask_overlay_{page}.png'})
    for name,source in ALIASES.items():
        for k in ['page','atlas_xywh']:frames[name][k]=frames[source][k]
        assert np.array_equal(tiles[name],tiles[source]) and np.array_equal(masks[name],masks[source])
    for name,f in frames.items():
        x,y,w,h=f['atlas_xywh'];page=pages[f['page']]
        for key,expected in [('base',tiles[name]),('mask',masks[name])]:
            im=Image.open(ROOT/page[key]).crop((x,y,x+w,y+h));assert np.array_equal(im,expected)
            if key=='base':audit[name]['atlas_extracted']=edge_stats(im)
    animations={};bindings={}
    for group in sources['groups']:
        action=ACTIONS[group['sprite_name'][-3:]];entries=group['frames'];bindings[group['sprite_name']]=group
        if not group['sprite_name'].startswith('pmn2'):continue
        views={}
        for view in range(8):
            steps=[]
            for f in entries:
                mirror=f'Mirror{view}' in f['flags'];v=8-view if mirror else view
                name=f['texture_name'] if 'Image1' in f['flags'] else f['texture_name']+str(v)
                assert name in frames;steps.append({'frame':name,'duration_ms':f['frame_length_raw']*62.5,'mirrored':mirror})
            views[str(view)]=steps
        animations[action]={'views':views,'single_view':'Image1' in entries[0]['flags'],
            'native_length_raw':group['animation_length_raw'],'sequence_ms':sum(s['duration_ms'] for s in views['0']),
            'playback':'loop' if action in ['standing','walk'] else 'hold' if action=='corpse' else 'once',
            'next_action':'corpse' if action=='death' else 'standing' if action in ['attack','hit','fidget'] else None}
    memory={'original_all_files_rgba_one_palette':sum(s['size'][0]*s['size'][1]*4 for s in sources['sources'].values()),
        'original_indexed_bmp_disk':sum((REPO/s['path']).stat().st_size for s in sources['sources'].values()),
        'enhanced_atlas_base':pixels*4,'enhanced_atlas_mask_r8':pixels,'enhanced_shared_base_and_mask':pixels*5,
        'enhanced_tight_base_unique':sum(t.width*t.height*4 for n,t in tiles.items() if n not in ALIASES),
        'variant_previews_excluded':True}
    manifest={'schema_version':1,'schema_status':'staged asset contract; luminance recolor needs explicit engine support',
        'creature':'mm6:pmn2','installed':False,'pixels_per_logical_pixel':2,'logical_canvas':CANVAS,'logical_pivot':[165.5,272],
        'anchor':'bottom-center','native_frame_scale':.699997,'coordinate_rule':'local_x=(crop_x+u)/2-165.5; local_up=272-(crop_y+v)/2; mirror local_x and UV together',
        'pages':pages,'frames':frames,'animations':animations,'native_group_bindings':bindings,
        'variants':{'801':{'name':'Apprentice Mage / red','luminance_vector':RAMPS[801]},'802':{'name':'Journeyman Mage / green','exact_base_bypass':True},'803':{'name':'Mage / blue','luminance_vector':RAMPS[803]}},
        'regions':{'mask_r':'green cape, trousers and pouches; exclude face/hair, leather, boots/bracers, staff and rope'},
        'recolor':{'model':'masked_luminance_rgb_v1','space':'sRGB encoded RGB; mask linear coverage','operation':'Y=dot(base.rgb,[0.2126,0.7152,0.0722]); target=Y*luminance_vector; output=lerp(base,target,mask); preserve alpha; base bypass',
            'fitting':'least-squares RGB slopes against green-palette luma over changed green native palette entries; fixed across poses','reference':'process.py:recolor'},
        'filtering':{'alpha':'straight RGBA; premultiplied Lanczos resampling','crop_padding_px':4,'transparent_extrusion_px':3,'mipmaps':False},'memory_bytes':memory,
        'limitations':['AI reconstructs detail; faces and clothing microdetails vary slightly between poses.','Native-only action views and native fidget duplicates retained.','2x export is not a claim of 2x newly generated detail in every batch.','Estimated alpha from magenta; not recovered ground-truth transparency.','Not installed; current crusader shader uses another recolor operation.']}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    order=['attack','death','walk','hit','fidget','standing','corpse']
    for view in range(5):
        sheet=Image.new('RGBA',(6*704,7*592))
        for row,action in enumerate(order):
            anim=animations[action]
            if view and anim['single_view']:continue
            for col,step in enumerate(anim['views'][str(view)]):
                name=step['frame'];origin=reg[name]['canvas_origin_px'];sheet.paste(aligned[name],(col*704+21+origin[0],row*592+24+origin[1]))
        sheet.save(ROOT/f'sheets/view_{view}_all_actions_2x.png')
    for kind in ['all_base_dark','all_masks_light']:
        light='light' in kind;contact=Image.new('RGB',(8*190,((len(frames)+7)//8)*176),(230,230,227) if light else (40,43,42));d=ImageDraw.Draw(contact)
        for i,name in enumerate(frames):
            im=aligned[name]
            if light:im=overlay(im,Image.open(ROOT/f'masks_2x/{name}.png'))
            im=im.convert('RGBa').resize((round(im.width/4),round(im.height/4)),Image.Resampling.LANCZOS).convert('RGBA');origin=reg[name]['canvas_origin_px']
            x=i%8*190;y=i//8*176;contact.paste(im,(x+12+round(origin[0]/4),y+26+round(origin[1]/4)),im);d.text((x+4,y+5),name,fill='black' if light else 'white')
        contact.save(ROOT/f'review/{kind}.png')
    ranked=sorted(audit,key=lambda n:audit[n]['atlas_extracted']['max_score'],reverse=True)[:12]
    contact=Image.new('RGB',(6*280,2*190),(55,55,55));d=ImageDraw.Draw(contact)
    for i,name in enumerate(ranked):
        im=tiles[name];x,y=audit[name]['atlas_extracted']['position'];crop=im.crop((x-16,y-16,x+16,y+16)).resize((128,128),Image.Resampling.NEAREST)
        for j,bg in enumerate([(35,35,35),(240,240,240)]):
            patch=Image.new('RGBA',crop.size,(*bg,255));patch.alpha_composite(crop);contact.paste(patch.convert('RGB'),(i%6*280+j*132,i//6*190+30))
        d.text((i%6*280+2,i//6*190+8),name,fill='white')
    contact.save(ROOT/'review/edge_current.png')
    (ROOT/'review/edge_current.json').write_text(json.dumps({'matte':'magenta','band_physical_px':4,'score':'alpha-weighted max(0,min(R,B)-G)','frames':audit},indent=2)+'\n')
    validation={'source_files':len(frames),'referenced_files':58,'unique_enhanced_tiles':len(frames)-len(ALIASES),'actions':list(animations),'stored_views':5,'view_aliases':8,'palettes':3,
        'source_hashes_unchanged':True,'raw_cells_unclipped':True,'exact_crop_reconstruction':True,'exact_atlas_extraction':True,'variant_alpha_unchanged':True,'zero_mask_unchanged':True,'base_bypass_exact':True,
        'residual_candidates_above_16':sum(a['atlas_extracted']['candidates_above_16'] for a in audit.values()),'memory_bytes':memory}
    (ROOT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation))
if __name__=='__main__':export()
