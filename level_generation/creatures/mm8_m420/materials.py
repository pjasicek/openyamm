"""Soft coverage on enhanced Pirate Mage Male pixels and frozen native palette color interpolation."""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from process import ROOT, queue, save

PALETTES = [421, 422, 423, 649, 650, 651]

def feature(rgb):
    r, g, b = np.moveaxis(np.asarray(rgb, dtype=float), -1, 0)
    return np.stack((r-g, b-g, .5*(.2126*r+.7152*g+.0722*b)), axis=-1)

def settings():
    source = json.loads((ROOT/'sources.json').read_text())
    palettes = {key: np.frombuffer((queue.REPO/rec['path']).read_bytes()[:768], np.uint8)
                .reshape(256,3).astype(float) for key,rec in source['palette_sources'].items()}
    base = palettes['421']
    changed = np.max(np.stack([np.max(abs(v-base),axis=1) for v in palettes.values()]),axis=0) >= 10
    changed[0] = False
    return {'base_palette':421, 'base_exact_bypass':True,
            'operation':'soft_native_palette_delta_knn_v1',
            'color_space':'sRGB RGB8, linear coverage',
            'regions':['native palette-changing coat, hair and beard'],
            'protected':'Native unchanged highlights remain protected; palette-changing coat, hair and beard follow original native palette deltas. No spatial native mask transfer.',
            'mask_method':'Eight nearest native palette color samples classify enhanced RGB pixels; inverse fourth-power distance weights. Reviewed enhanced-art rectangles protect unchanged waist cloth, wood and other warm details from hair recoloring: identity rectangles have zero coverage; action rectangles attenuate coverage by 1-clip((R-G)/8,0,1), preserving adjacent green coat.',
            'feature':'(R-G, B-G, 0.5*luma709), RGB8', 'neighbors':8, 'distance_floor':2,
            'base_samples':base[1:].tolist(),
            'changed_samples':changed[1:].astype(int).tolist(),
            'palette_deltas':{k:(v-base)[1:].tolist() for k,v in palettes.items()}}

def lookup(rgb, config):
    points = np.asarray(config['base_samples'])
    unique, inverse = np.unique(np.asarray(rgb).reshape(-1,3), axis=0, return_inverse=True)
    distances, indices = cKDTree(feature(points)).query(feature(unique), k=config['neighbors'])
    dist, ids = distances[inverse], indices[inverse]
    weights = 1/np.maximum(dist,config['distance_floor'])**4
    weights /= weights.sum(axis=1,keepdims=True)
    changed = np.asarray(config['changed_samples'])[ids]
    selected = weights*changed
    coverage = selected.sum(axis=1)
    return ids, selected/np.maximum(coverage[:,None],1e-12), coverage.reshape(rgb.shape[:-1])

def masks(im, config):
    a = np.asarray(im)
    _, _, coverage = lookup(a[:,:,:3],config)
    coverage[a[:,:,3]==0] = 0
    return np.round(coverage*255).astype(np.uint8)

def recolor(im, mask, palette, config, samples=None):
    if int(palette)==421:
        return im.copy()
    a = np.array(im)
    rgb = a[:,:,:3].astype(float)
    ids, weights, _ = samples if samples is not None else lookup(rgb,config)
    deltas = np.asarray(config['palette_deltas'][str(palette)])
    delta = (deltas[ids]*weights[:,:,None]).sum(axis=1).reshape(rgb.shape)
    a[:,:,:3] = np.round(rgb+delta*np.asarray(mask)[:,:,None]/255).clip(0,255).astype(np.uint8)
    return Image.fromarray(a)

def run(batch_keys=None):
    config = settings()
    hair_regions_path = ROOT/'enhanced_hair_regions.json'
    hair_regions = json.loads(hair_regions_path.read_text()) if hair_regions_path.exists() else None
    skin_regions_path = ROOT/'enhanced_skin_regions.json'
    skin_regions = json.loads(skin_regions_path.read_text()) if skin_regions_path.exists() else {}
    if hair_regions is not None:
        config['mask_method'] = ('Eight nearest native palette samples classify enhanced RGB pixels; inverse '
            'fourth-power distance weights. Outside reviewed enhanced-art hair/beard rectangles, warm pixels '
            'are protected by 1-clip((R-G)/8,0,1), retaining coat coverage. Rectangles use aligned physical '
            'pixels and are recorded in enhanced_hair_regions.json; no native mask transfer.')
        config['enhanced_hair_regions'] = 'enhanced_hair_regions.json'
    if skin_regions:
        config['enhanced_skin_regions'] = 'enhanced_skin_regions.json'
        config['mask_method'] += ' Reviewed enhanced-art hand polygons exclude fingers overlapping the beard region.'
    save(ROOT/'material_settings.json',config)
    for folder in ['masks_2x','previews','native_variants','review/variants']:
        (ROOT/folder).mkdir(exist_ok=True,parents=True)
    reg = json.loads((ROOT/'registration.json').read_text())
    batches = json.loads((ROOT/'batches.json').read_text())
    if batch_keys is not None:
        selected_names = {name for key in batch_keys for name in batches[key]['frames']}
        reg = {name:record for name,record in reg.items() if name in selected_names}
    for name in reg:
        im = Image.open(ROOT/f'toned_2x/{name}.png').convert('RGBA')
        samples = lookup(np.asarray(im)[:,:,:3],config)
        coverage = samples[2].copy()
        # Accepted identity rectangles remain byte-identical. In moving poses,
        # overlapping staff/leg bounds also contain green coat pixels: exclude
        # only warm enhanced-art pixels, with a soft R-G transition from 0 to 8.
        rgb = np.asarray(im)[:,:,:3].astype(float)
        warm = np.clip((rgb[:,:,0]-rgb[:,:,1])/8, 0, 1)
        if hair_regions is not None:
            allowed = np.zeros(coverage.shape, dtype=bool)
            for x0,y0,x1,y1 in hair_regions[name]:
                allowed[y0:y1,x0:x1] = True
            coverage[~allowed] *= 1-warm[~allowed]
        else:
            exclusions = json.loads((ROOT/'enhanced_material_exclusions.json').read_text())[name]
            for x0,y0,x1,y1 in exclusions:
                if name.startswith('m420sa'):
                    coverage[y0:y1,x0:x1] = 0
                else:
                    coverage[y0:y1,x0:x1] *= 1-warm[y0:y1,x0:x1]
        if name in skin_regions:
            protected = Image.new('L', im.size)
            painter = ImageDraw.Draw(protected)
            for polygon in skin_regions[name]:
                painter.polygon([tuple(point) for point in polygon], fill=255)
            coverage[np.asarray(protected)>0] = 0
        coverage[np.asarray(im)[:,:,3]==0] = 0
        mask = np.round(coverage*255).astype(np.uint8)
        Image.fromarray(mask).save(ROOT/f'masks_2x/{name}.png')
        for palette in PALETTES:
            variant = recolor(im,mask,palette,config,samples)
            assert np.array_equal(np.asarray(im)[:,:,3],np.asarray(variant)[:,:,3])
            assert palette!=421 or np.array_equal(im,variant)
            variant.save(ROOT/f'previews/{name}_{palette}.png')
            queue.native(ROOT,name,palette).save(ROOT/f'native_variants/{name}_{palette}.png')
    for key,batch in batches.items():
        if batch_keys is not None and key not in batch_keys:
            continue
        if any(name not in reg for name in batch['frames']):
            continue
        sheet = Image.new('RGB',(256*len(batch['frames']),280*(len(PALETTES)+1)),(35,35,35))
        draw = ImageDraw.Draw(sheet)
        for i,name in enumerate(batch['frames']):
            im = Image.open(ROOT/f'toned_2x/{name}.png').convert('RGBA')
            a = np.array(im)
            mask = np.asarray(Image.open(ROOT/f'masks_2x/{name}.png'))/255
            a[:,:,:3] = np.round(a[:,:,:3]*(1-.65*mask[:,:,None])+
                                      np.array([255,70,30])*.65*mask[:,:,None]).astype(np.uint8)
            pics = [Image.open(ROOT/f'previews/{name}_{p}.png') for p in PALETTES]+[Image.fromarray(a)]
            for row,pic in enumerate(pics):
                bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic)
                bg.thumbnail((256,256),Image.Resampling.LANCZOS)
                sheet.paste(bg.convert('RGB'),(i*256,row*280+24))
                draw.text((i*256+4,row*280+4),name+' '+str([*PALETTES,'mask'][row]),fill='white')
        sheet.save(ROOT/f'review/variants/{key}.png')
    print('Derived',len(reg),'R8 masks and deterministic previews for all processed frames')

if __name__=='__main__':
    run()
