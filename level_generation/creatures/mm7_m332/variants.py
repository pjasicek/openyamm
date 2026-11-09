"""Enhanced trouser/hair coverage and fixed native palette fits for the male elf peasant."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent/'mm7_m514'))
from process import apply_variant


def run():
    sources = json.loads((HERE/'sources.json').read_text())
    registration = json.loads((HERE/'registration.json').read_text())
    palettes = {int(p):np.frombuffer((REPO/r['path']).read_bytes()[:768],np.uint8).reshape(256,3).astype(float)
                for p,r in sources['palette_sources'].items()}
    variants = []
    for palette, colors in palettes.items():
        regions = []
        for channel, (a,b) in enumerate([(150,225),(113,150)]):
            base = palettes[59][a:b]
            if channel == 0:
                selected = (base[:,0]>base[:,1]*1.7)&(base[:,2]>base[:,1]*1.1)
            else:
                selected = (base[:,1]>base[:,0]*.9)&(base[:,2]<base[:,1]*.75)
            indices = np.arange(a,b)[selected]
            base = palettes[59][indices]
            target = colors[indices]
            matrix = np.linalg.lstsq(base,target,rcond=None)[0]
            regions.append(dict(channel=channel,rgb_matrix=matrix.tolist(),native_indices=indices.tolist(),
                                mean_fit_error=float(abs(base@matrix-target).mean())))
        descriptors = [int(d) for d,binding in sources['descriptor_bindings'].items()
                       if sources['groups'][binding['standing']]['frames'][0]['palette_id']==palette]
        variants.append(dict(id=f'mm7:palette{palette}',palette_id=palette,default=palette==59,
                             exact_bypass=palette==59,descriptors=descriptors,regions=regions))
    masks = {}
    for name in registration:
        im = Image.open(HERE/f'aligned_2x/{name}.png')
        rgba = np.array(im);rgb = rgba[:,:,:3].astype(float)
        r,g,b = rgb.transpose(2,0,1)
        trouser_candidate=(r>g*1.65)&(b>g*.82)&(rgba[:,:,3]>0)
        labels,count=ndimage.label(trouser_candidate)
        areas=np.bincount(labels.ravel());areas[0]=0
        trouser=np.isin(labels,np.flatnonzero(areas>max(200,areas.max()*.1)))
        trouser=ndimage.binary_fill_holes(trouser)
        trouser|=(ndimage.distance_transform_edt(~trouser)<2)&trouser_candidate
        cloth=(trouser&(rgba[:,:,3]>0)).astype(np.uint8)*255
        box = im.getbbox();yy,xx=np.indices(r.shape)
        candidate = (g>r*.76)&(r>g*.90)&((g-b)>(r-g)*1.6)&(rgba[:,:,3]>0)
        head_zone = yy < box[1]+(box[3]-box[1])*.38
        if name == 'm332db0':
            head_zone = ((xx>=225)&(xx<=278)&(yy>=306)&(yy<=358)) | ((xx>=184)&(xx<=234)&(yy>=347)&(yy<=436))
        elif name == 'm332dd0':
            head_zone = (xx>=228)&(xx<=283)&(yy>=457)
        elif name in ('m332dc0','m332xa0'):
            head_zone = np.zeros_like(candidate)
        candidate &= head_zone
        labels,count=ndimage.label(candidate)
        objects=ndimage.find_objects(labels)
        choices=[(i+1,sl) for i,sl in enumerate(objects)
                 if sl and np.count_nonzero(labels[sl]==i+1)>15]
        hair=np.zeros_like(cloth)
        if choices:
            chosen,sl=min(choices,key=lambda entry:entry[1][0].start)
            distance=ndimage.distance_transform_edt(labels!=chosen)
            support=(g>r*.74)&(r>g*.90)&((g-b)>(r-g)*1.5)&(rgba[:,:,3]>0)
            support &= head_zone
            support_labels,support_count=ndimage.label(support)
            for component in range(1,support_count+1):
                selection=support_labels==component
                if np.count_nonzero(selection)>10 and distance[selection].min()<20:
                    hair[selection]=255
        if name == 'm332db0':
            pony=Image.new('L',im.size)
            ImageDraw.Draw(pony).polygon([(198,389),(210,396),(204,411),(196,424),(188,431),(189,415)],fill=255)
            selection=(np.array(pony)>0)&(rgba[:,:,3]>0)&(g>r*.60)&(b<g*.80)
            hair[selection]=255
        hair[cloth>0]=0
        weights=np.dstack((cloth,hair,np.zeros_like(hair))).astype(float)/255
        alpha=rgba[:,:,3].astype(float)/255
        denominator=ndimage.gaussian_filter(alpha,.45)
        for channel in range(2):
            weights[:,:,channel]=ndimage.gaussian_filter(weights[:,:,channel]*alpha,.45)/np.maximum(denominator,1e-8)
        weights[alpha==0]=0
        weights/=np.maximum(weights.sum(axis=2),1)[:,:,None]
        mask=Image.fromarray(np.round(weights*255).astype(np.uint8))
        mask.save(HERE/f'masks_2x/{name}.png');masks[name]=mask
    data=dict(variants=variants,regions=[dict(id='trousers',channel='R',construction='Largest enhanced burgundy component, filled interior and adjacent hue support; protected leather, skin and metal excluded.'),
        dict(id='hair',channel='G',construction='Enhanced yellow hair component at head, including contiguous ponytail and local shadow support.')],
        recolor=dict(operation='independent_masked_rgb_matrices',color_space='encoded sRGB 0..255',
          rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
          mask_format='RGB8 linear; R trousers, G hair, B reserved zero',
          calibration='Native burgundy entries within 150..224 and yellow hair entries within 113..149; fixed fits for every frame.',
          mask_filter='Alpha-normalized Gaussian sigma 0.45 physical pixels; overlap normalization; zero outside alpha.',
          pose_corrections='Explicit enhanced-space head zones for falling db and prone dd; hidden hair disabled for dc and corpse; exposed falling ponytail polygon. See variants.py for exact settings.'))
    (HERE/'variants.json').write_text(json.dumps(data,indent=2)+'\n')
    settings=json.loads((HERE/'processing_settings.json').read_text());settings.update(masks=data['recolor']['mask_format'],
        mask_regions=data['regions'],recolor=data['recolor']);(HERE/'processing_settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    contact=Image.new('RGB',(1080,((len(masks)+3)//4)*300),(45,45,45));draw=ImageDraw.Draw(contact)
    for i,(name,mask) in enumerate(masks.items()):
        im=Image.open(HERE/f'aligned_2x/{name}.png');a=np.array(im);w=np.array(mask)/255
        a[:,:,:3]=np.round(a[:,:,:3]*(1-w.sum(axis=2)[:,:,None]*.7)+
            (w[:,:,0,None]*np.array([0,200,255])+w[:,:,1,None]*np.array([255,180,0]))*.7).astype(np.uint8)
        tile=Image.fromarray(a).resize((256,256),Image.Resampling.LANCZOS)
        x=i%4*270;y=i//4*300;contact.paste(tile,(x,y+20),tile);draw.text((x,y),name,fill='white')
    for i,y in enumerate(range(0,contact.height,1200)):
        contact.crop((0,y,1080,min(y+1200,contact.height))).save(HERE/f'review/material_masks_{i}.png')
    contact=Image.new('RGB',(9*200,5*256),(45,45,45));draw=ImageDraw.Draw(contact)
    for row,name in enumerate(json.loads((HERE/'batches.json').read_text())['standing']['frames']):
        im=Image.open(HERE/f'aligned_2x/{name}.png')
        for col,v in enumerate(variants):
            out=apply_variant(im,masks[name],v);tile=out.resize((230,230),Image.Resampling.LANCZOS)
            contact.paste(tile,(col*200,row*256+20),tile);draw.text((col*200,row*256),str(v['palette_id']),fill='white')
    contact.save(HERE/'review/identity_variants.png')
    print('Authored masks and nine native variants for',len(masks),'frames')


if __name__ == '__main__':
    run()
