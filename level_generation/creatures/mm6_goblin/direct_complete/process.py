"""Clean missing views, preserve accepted front placement, and author selective goblin masks."""
import importlib.util
import json
import hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from prepare import ROOT, REPO, PREVIOUS, CANVAS, PALETTES, native

def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
matte=module('goblin_matte',ROOT.parent/'direct_ai_attack/clean_edges.py')
helpers=module('behemoth_geometry',ROOT.parent.parent/'mm7_m162/process.py')
ALIASES={'gobdyf0':'gobdyd0'}

def resize_base(im,size):
    return helpers.resize_base(im,size)

def mask(im):
    a=np.array(im);rgb=a[:,:,:3].astype(float)/255;r,g,b=rgb.transpose(2,0,1)
    # Olive skin and yellow-green/gold details; suppress neutral steel and leather brown.
    color=np.clip((np.minimum(r,g)-b-.012)/.07,0,1)
    skin=color*np.clip((1.37-r/np.maximum(g,.01))/.20,0,1)
    # Brown leather, warm blade faces and copper/gold accents have a distinct red/green ratio.
    warm=np.clip((r-g-.012)/.05,0,1)*np.clip((g-b+.005)/.045,0,1)
    warm*=1-skin
    weights=np.stack([skin,warm,np.zeros_like(skin)],axis=2)
    weights[a[:,:,3]==0]=0
    return Image.fromarray(np.round(weights*255).astype(np.uint8),'RGB')

def ramps():
    c={p:np.frombuffer((REPO/f'assets_dev/worlds/mm6/textures/pal{p}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for p in PALETTES}
    r,g,b=c[745].T
    regions=[(np.minimum(r,g)-b>.04)&(r<g*1.25), (r>g*1.3)&(g>b*1.15)&(r-g>.025)]
    # Weight skin fitting by actual native face/torso pixels, avoiding unused palette/gold entries
    # pulling the Goblin King's red skin toward brown. Regions remain fixed for the entire family.
    indices=np.array(Image.open(REPO/'assets_dev/engine/sprites/gobsta0.bmp'))
    selected_pixels=np.zeros(indices.shape,bool)
    selected_pixels[38:88,155:201]=True
    selected_pixels[102:151,162:200]=True
    selected_pixels &= regions[0][indices]
    weights=np.bincount(indices[selected_pixels],minlength=256).astype(float)
    result={}
    for p in [746,747]:
        vectors=[]
        for region,selected in enumerate(regions):
            y=c[745][selected]@np.array([.2126,.7152,.0722])
            w=weights[selected] if region==0 else np.ones_like(y)
            vectors.append((w[:,None]*y[:,None]*c[p][selected]).sum(axis=0)/(w*y*y).sum())
        result[p]=np.array(vectors)
    return result
RAMPS=ramps()

def recolor(im,coverage,palette):
    if palette==745:return im.copy()
    a=np.array(im);rgb=a[:,:,:3].astype(float)/255;w=np.array(coverage).astype(float)[:,:,:2]/255
    y=rgb@np.array([.2126,.7152,.0722])
    targets=y[:,:,None,None]*RAMPS[palette][None,None,:,:]
    rgb=rgb*(1-w.sum(axis=2))[:,:,None]+(targets*w[:,:,:,None]).sum(axis=2)
    a[:,:,:3]=np.round(np.clip(rgb,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)

def head_x(im):
    a=np.array(im);rgb=a[:,:,:3].astype(float)/255;r,g,b=rgb.transpose(2,0,1)
    skin=(a[:,:,3]>128)&(np.minimum(r,g)>b+.025)&(r<g*1.35)
    labels,n=ndimage.label(skin);sizes=np.bincount(labels.ravel());skin&=sizes[labels]>max(5,im.width*im.height*.0001)
    ys,xs=np.where(skin);assert len(xs),'No olive head landmark'
    top=ys.min();bottom=im.getbbox()[3];band=skin.copy();band[:top+round((bottom-top)*.025)]=False;band[top+round((bottom-top)*.14):]=False
    xs=np.where(band)[1];assert len(xs)
    return float(np.median(xs))

def restore_front(sources, records):
    for name in sources['reused']:
        canonical=ALIASES.get(name,name)
        source=sources['reused'][canonical]
        path=REPO/source['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
        accepted=Image.open(path).convert('RGBA');im=resize_base(accepted,accepted.size)
        assert np.array_equal(np.array(accepted)[:,:,3],np.array(im)[:,:,3])
        original=native(canonical)
        native_bottom=Image.fromarray((np.array(original)[:,:,3]>=128).astype(np.uint8)).getbbox()[3]
        restored_bottom=Image.fromarray((np.array(im)[:,:,3]>=128).astype(np.uint8)).getbbox()[3]
        dy=native_bottom*2-restored_bottom
        assert 0<=dy<=5, (name,dy)
        aligned=Image.new('RGBA',(im.width,im.height+dy))
        aligned.paste(im,(0,dy))
        assert np.array_equal(np.array(aligned)[dy:],np.array(im))
        im.save(ROOT/f'cleaned/{name}.png');aligned.save(ROOT/f'aligned_2x/{name}.png')
        mask(aligned).save(ROOT/f'masks_2x/{name}.png')
        records[name]={'batch':'accepted_front','canvas_origin_px':[0,0],'raw_clip':False,
            'translate':[0,dy], 'registration':'Accepted front art; integer vertical correction to native alpha>=128 baseline',
            'source_checkpoint':source,'canonical_pixel_frame':canonical}

def run(front_only=False):
    for d in ['cleaned','aligned_2x','masks_2x','review']:(ROOT/d).mkdir(exist_ok=True)
    sources=json.loads((ROOT/'sources.json').read_text())
    records=json.loads((ROOT/'registration.json').read_text()) if front_only else {}
    restore_front(sources,records)
    if front_only:
        (ROOT/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
        return
    for key,batch in json.loads((ROOT/'batches.json').read_text()).items():
        path=ROOT/f'raw/{key}.png'
        if not path.exists():continue
        sheet=Image.open(path).convert('RGB');rgb=np.array(sheet).astype(float)/255
        fg=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]<.55
        yc=helpers.gutter_cuts(fg.any(axis=1),2);entries=[]
        for i,name in enumerate(batch['frames']):
            row=i//batch['columns'];col=i%batch['columns'];xc=helpers.gutter_cuts(fg[yc[row]:yc[row+1]].any(axis=0),batch['columns'])
            rect=[xc[col],yc[row],xc[col+1],yc[row+1]];clean,stats=matte.extract(sheet.crop(rect))
            clean=resize_base(clean,clean.size);clean.save(ROOT/f'cleaned/{name}.png')
            src=native(name);nb=helpers.bounds(src);gb=helpers.bounds(clean)
            entries.append((name,clean,src,nb,gb,rect,stats))
        scale=float(np.median([2*(nb[3]-nb[1])/(gb[3]-gb[1]) for _,_,_,nb,gb,_,_ in entries]))
        for name,clean,src,nb,gb,rect,stats in entries:
            resized=resize_base(clean,(round(clean.width*scale),round(clean.height*scale)))
            rb=helpers.bounds(resized);tx=round(head_x(src)*2-head_x(resized));ty=nb[3]*2-rb[3]
            true=resized.getbbox();left=min(0,tx+true[0]-4);top=min(0,ty+true[1]-4)
            right=max(CANVAS[0]*2,tx+true[2]+4);bottom=max(CANVAS[1]*2,ty+true[3]+4)
            aligned=Image.new('RGBA',(right-left,bottom-top));aligned.paste(resized,(tx-left,ty-top))
            aligned.save(ROOT/f'aligned_2x/{name}.png');mask(aligned).save(ROOT/f'masks_2x/{name}.png')
            records[name]={'batch':key,'scale':scale,'translate':[tx,ty],'raw_rect':rect,'raw_size':sheet.size,
                'canvas_origin_px':[left,top],'raw_clip':gb[0]<=0 or gb[1]<=0 or gb[2]>=clean.width or gb[3]>=clean.height,
                'registration':'Shared sheet scale, native olive head x and native silhouette baseline','matte':stats,
                'tone':'Generated against accepted toned reference; no extra grade'}
    (ROOT/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
    for key in sorted({r['batch'] for r in records.values()}):
        names=[n for n,r in records.items() if r['batch']==key]
        if key=='accepted_front':continue
        contact=Image.new('RGB',(len(names)*355,2*315),(45,45,45));d=ImageDraw.Draw(contact)
        for i,name in enumerate(names):
            for row,im in enumerate([native(name),Image.open(ROOT/f'aligned_2x/{name}.png')]):
                if row:im=im.convert('RGBa').resize((round(im.width/2),round(im.height/2)),Image.Resampling.LANCZOS).convert('RGBA')
                origin=records[name]['canvas_origin_px'] if row else [0,0]
                contact.paste(im,(i*355+round(origin[0]/2),row*315+24+round(origin[1]/2)),im)
                d.text((i*355+4,row*315+4),name+(' restored' if row else ' native'),fill='white')
        contact.save(ROOT/f'review/{key}_comparison.png')
    print(json.dumps({'processed':len(records),'clipped':[n for n,r in records.items() if r['raw_clip']]}))

def head_landmark(im):
    """Locate the olive crown, excluding neutral blades and small gold fittings."""
    a = np.array(im)
    r, g, b = a[:, :, :3].astype(float).transpose(2, 0, 1)
    skin = (a[:, :, 3] >= 128) & (np.minimum(r, g) > b + 6) & (r < g * 1.37)
    bounds = im.getbbox()
    skin[round(bounds[1] + (bounds[3] - bounds[1]) * .40):] = False
    # A warm blade may connect to the skin through its guard. Require a broad horizontal
    # skin run, so the narrow blade and pointed ear tips cannot become a crown landmark.
    width = max(3, round((bounds[3]-bounds[1]) * .055))
    broad = ndimage.binary_opening(skin, structure=np.ones((1, width), dtype=bool))
    ys, xs = np.where(broad)
    assert len(xs), 'Missing olive crown landmark'
    top = int(ys.min())
    cap = xs[ys <= top + max(2, round((bounds[3]-bounds[1]) * .045))]
    return [float(np.median(cap)), top]


def run_redo():
    """Register the shared redo extractor's outputs without changing the historical package."""
    import shutil
    out = ROOT / 'redo_2x'
    run_record = json.loads((out / 'run.json').read_text())
    policy = json.loads((out / 'processing.json').read_text())
    records, calibration, generation = {}, {}, {}
    for folder in ['aligned_2x', 'masks_2x']:
        (out / folder).mkdir(exist_ok=True)
    for job in run_record['jobs']:
        report = json.loads((out / 'review' / (job['id'] + '_extraction.json')).read_text())
        assert report['raw'] == job['selected_raw'], job['id']
        entries = report['frames']
        first = entries[0]
        clean = Image.open(REPO / first['clean_path']).convert('RGBA')
        source = native(first['frame'])
        nb, gb = source.getbbox(), clean.getbbox()
        if 'death_corpse_redo_02' in job['id']:
            # Transfer the preceding sheet's anatomical scale through the common prone endpoint.
            previous = records[first['frame']]
            previous_clean = Image.open(REPO / previous['clean_path']).convert('RGBA')
            pb = previous_clean.getbbox()
            sampling = (gb[2]-gb[0]) / (pb[2]-pb[0]) * (2 / previous['scale'])
            method = 'Prone overlap width transfers preceding upright anatomical calibration'
        else:
            nh, gh = head_landmark(source), head_landmark(clean)
            sampling = (gb[3]-gh[1]) / (nb[3]-nh[1])
            method = 'First-pose olive crown to sole; common uniform scale for the complete batch'
        factor = 2 / sampling
        assert sampling > 2, (job['id'], sampling)
        calibration[job['id']] = dict(frame=first['frame'], generated_sampling=sampling,
                                      raw_sha256=report['raw_sha256'], method=method)
        attempt = next(a for a in job['attempts'] if a['raw'] == job['selected_raw'])
        generation[job['id']] = attempt
        for entry in entries:
            name = entry['frame']
            if policy.get('selected_batches', {}).get(name, job['id']) != job['id']:
                continue
            if name in records or name in ALIASES:
                continue
            clean = Image.open(REPO / entry['clean_path']).convert('RGBA')
            source = native(name)
            im = resize_base(clean, (round(clean.width*factor), round(clean.height*factor)))
            nb, rb = source.getbbox(), im.getbbox()
            prone = name in ['gobdyd0', 'gobdye0', 'gobdyf0']
            if prone:
                nx, rx = (nb[0]+nb[2])/2, (rb[0]+rb[2])/2
            else:
                nx, rx = head_landmark(source)[0], head_landmark(im)[0]
            tx, ty = round(nx*2-rx), nb[3]*2-rb[3]
            origin = [min(0, tx+rb[0]-4), min(0, ty+rb[1]-4)]
            end = [max(CANVAS[0]*2, tx+rb[2]+4), max(CANVAS[1]*2, ty+rb[3]+4)]
            aligned = Image.new('RGBA', (end[0]-origin[0], end[1]-origin[1]))
            aligned.paste(im, (tx-origin[0], ty-origin[1]))
            aligned.save(out / 'aligned_2x' / (name+'.png'))
            mask(aligned).save(out / 'masks_2x' / (name+'.png'))
            shutil.copy2(REPO / entry['clean_path'], out / 'cleaned' / (name+'.png'))
            effective = [2*clean.width/im.width, 2*clean.height/im.height]
            assert min(effective) > 2, name
            records[name] = dict(batch=job['id'], clean_path=entry['clean_path'], raw_path=report['raw'],
                raw_sha256=report['raw_sha256'], raw_size=report['raw_size'], raw_rect=entry['raw_rect'],
                native_crop=report['native_crop'], scale=factor, effective_sampling_xy=effective,
                translate=[tx,ty], canvas_origin_px=origin,
                raw_clip=(entry['clean_bounds'][0] <= 0 or entry['clean_bounds'][1] <= 0
                          or entry['clean_bounds'][2] >= clean.width or entry['clean_bounds'][3] >= clean.height),
                placement_landmarks=dict(native_x=nx, resized_x=rx, native_bottom=nb[3], resized_bottom=rb[3],
                    physical_residual=[rx+tx-nx*2, rb[3]+ty-nb[3]*2]),
                registration='Common batch anatomical scale; per-native-pose crown X and sole Y; prone bounds center X',
                matte=entry['matte'], review_status='pending_sequence_review')
    old = json.loads((ROOT / 'registration.json').read_text())
    # The front standing image already met 2x; preserve its exact approved pixels and provenance.
    for name in set(old)-set(records)-set(ALIASES):
        assert name == 'gobsta0', name
        for folder in ['aligned_2x', 'masks_2x', 'cleaned']:
            shutil.copy2(ROOT/folder/(name+'.png'), out/folder/(name+'.png'))
        provenance = dict(project=str(ROOT.relative_to(REPO)),
            registration_sha256=hashlib.sha256((ROOT/'registration.json').read_bytes()).hexdigest(),
            assets={f'{folder}/{name}.png': hashlib.sha256((ROOT/folder/(name+'.png')).read_bytes()).hexdigest()
                    for folder in ['aligned_2x', 'masks_2x', 'cleaned']})
        records[name] = dict(old[name], retained_from=provenance,
                             effective_sampling_xy=[2,2], review_status='retained_adequate_checkpoint')
    for name, canonical in ALIASES.items():
        for folder in ['aligned_2x', 'masks_2x', 'cleaned']:
            shutil.copy2(out/folder/(canonical+'.png'), out/folder/(name+'.png'))
        records[name] = dict(records[canonical], canonical_pixel_frame=canonical)
    assert set(records) == set(old)
    shutil.copy2(ROOT/'sources.json', out/'sources.json')
    shutil.copy2(ROOT/'config.json', out/'config.json')
    for name, value in [('registration.json', records), ('calibration.json', calibration),
                        ('generation.json', dict(batches=generation))]:
        (out/name).write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(dict(frames=len(records), replacement_minimum=min(
        min(r['effective_sampling_xy']) for r in records.values() if 'retained_from' not in r),
        retained=['gobsta0'], status='registered_pending_visual_review')))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--front-only',action='store_true')
    parser.add_argument('--redo', action='store_true')
    args = parser.parse_args()
    run_redo() if args.redo else run(args.front_only)
