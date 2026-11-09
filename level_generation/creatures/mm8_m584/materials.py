"""Soft coverage on enhanced Raven Man pixels and frozen native palette color interpolation."""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from scipy import ndimage as ndi
from process import ROOT, queue, save

PALETTES = [585, 586, 587]

def feature(rgb):
    r, g, b = np.moveaxis(np.asarray(rgb, dtype=float), -1, 0)
    return np.stack((r-g, b-g, .5*(.2126*r+.7152*g+.0722*b)), axis=-1)

def settings():
    source = json.loads((ROOT/'sources.json').read_text())
    palettes = {key: np.frombuffer((queue.REPO/rec['path']).read_bytes()[:768], np.uint8)
                .reshape(256,3).astype(float) for key,rec in source['palette_sources'].items()}
    base = palettes['585']
    changed = np.maximum(np.max(abs(palettes['586']-base),axis=1),
                         np.max(abs(palettes['587']-base),axis=1)) >= 10
    changed[0] = False
    return {'base_palette':585, 'base_exact_bypass':True,
            'operation':'soft_native_palette_delta_knn_v1',
            'color_space':'sRGB RGB8, linear coverage',
            'regions':['green polearm blade and green equipment accents'],
            'protected':'Native unchanged black/gray feathers, tan skin, brown leather, pale beak, silver knee ornaments and talons; green equipment follows native palette deltas; no spatial native mask transfer.',
            'mask_method':'Enhanced semantic equipment support plus interior cool metal coverage, with reviewed protected-region exclusions; eight nearest native palette color samples classify enhanced RGB pixels; inverse fourth-power distance weights.',
            'feature':'(R-G, B-G, 0.5*luma709), RGB8', 'neighbors':8, 'distance_floor':2,
            'base_samples':base[1:].tolist(),
            'changed_samples':changed[1:].astype(int).tolist(),
            'palette_deltas':{k:(v-base)[1:].tolist() for k,v in palettes.items()}}

def lookup(rgb, config):
    points = np.asarray(config['base_samples'])
    flat=np.asarray(rgb).reshape(-1,3).astype(np.uint32)
    packed=(flat[:,0]<<16)|(flat[:,1]<<8)|flat[:,2]
    _,first,inverse=np.unique(packed,return_index=True,return_inverse=True)
    dist,ids=cKDTree(feature(points)).query(feature(flat[first]),k=config['neighbors'])
    dist,ids=dist[inverse],ids[inverse]
    weights = 1/np.maximum(dist,config['distance_floor'])**4
    weights /= weights.sum(axis=1,keepdims=True)
    changed = np.asarray(config['changed_samples'])[ids]
    selected = weights*changed
    coverage = selected.sum(axis=1)
    return ids, selected/np.maximum(coverage[:,None],1e-12), coverage.reshape(rgb.shape[:-1])

def masks(im, config, name):
    a = np.asarray(im)
    _, _, coverage = lookup(a[:,:,:3],config)
    rgb=a[:,:,:3].astype(float)
    cool=np.clip((np.minimum(rgb[:,:,1]-rgb[:,:,0],rgb[:,:,2]-rgb[:,:,0])-4)/8,0,1)
    support=np.asarray(Image.open(ROOT/f'material_support_2x/{name}.png'))/255
    cool*=np.clip((ndi.distance_transform_edt(a[:,:,3]>240)-3)/3,0,1)
    permission=np.maximum(support,cool)
    for x,y,x2,y2 in json.loads((ROOT/'material_region_overrides.json').read_text()).get(name,{}).get('exclude',[]):
        permission[y:y2,x:x2]=0
    coverage*=permission
    coverage[a[:,:,3]==0] = 0
    return np.round(coverage*255).astype(np.uint8)

def recolor(im, mask, palette, config):
    if int(palette)==585:
        return im.copy()
    a = np.array(im)
    rgb = a[:,:,:3].astype(float)
    ids, weights, _ = lookup(rgb,config)
    deltas = np.asarray(config['palette_deltas'][str(palette)])
    delta = (deltas[ids]*weights[:,:,None]).sum(axis=1).reshape(rgb.shape)
    a[:,:,:3] = np.round(rgb+delta*np.asarray(mask)[:,:,None]/255).clip(0,255).astype(np.uint8)
    return Image.fromarray(a)

def run():
    config = settings()
    save(ROOT/'material_settings.json',config)
    for folder in ['masks_2x','previews','native_variants','review/variants']:
        (ROOT/folder).mkdir(exist_ok=True,parents=True)
    reg = json.loads((ROOT/'registration.json').read_text())
    for name in reg:
        im = Image.open(ROOT/f'toned_2x/{name}.png').convert('RGBA')
        mask = masks(im,config,name)
        Image.fromarray(mask).save(ROOT/f'masks_2x/{name}.png')
        for palette in PALETTES:
            variant = recolor(im,mask,palette,config)
            assert np.array_equal(np.asarray(im)[:,:,3],np.asarray(variant)[:,:,3])
            assert palette!=585 or np.array_equal(im,variant)
            variant.save(ROOT/f'previews/{name}_{palette}.png')
            queue.native(ROOT,name,palette).save(ROOT/f'native_variants/{name}_{palette}.png')
    batches = json.loads((ROOT/'batches.json').read_text())
    for key,batch in batches.items():
        if any(name not in reg for name in batch['frames']):
            continue
        sheet = Image.new('RGB',(256*len(batch['frames']),1120),(35,35,35))
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
