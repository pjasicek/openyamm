"""Enhanced trouser/hair coverage and fixed native palette fits for the female elf peasant."""
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
        for channel, (a,b) in enumerate([(124,170),(174,226)]):
            base = palettes[323][a:b]
            if channel == 0:
                selected = (base[:,1]>base[:,0]*1.12)&(base[:,1]>base[:,2]*1.1)
            else:
                selected = (base[:,0]>base[:,1]*1.5)&(base[:,1]>base[:,2]*1.1)
            indices = np.arange(a,b)[selected]
            base = palettes[323][indices]
            target = colors[indices]
            luminance=base@np.array([.2126,.7152,.0722])
            ramp=(luminance[:,None]*target).sum(axis=0)/(luminance*luminance).sum()
            matrix=np.outer([.2126,.7152,.0722],ramp)
            regions.append(dict(channel=channel,rgb_matrix=matrix.tolist(),native_indices=indices.tolist(),
                                mean_fit_error=float(abs(base@matrix-target).mean())))
        descriptors = [int(d) for d,binding in sources['descriptor_bindings'].items()
                       if sources['groups'][binding['standing']]['frames'][0]['palette_id']==palette]
        variants.append(dict(id=f'mm7:palette{palette}',palette_id=palette,default=palette==323,
                             exact_bypass=palette==323,descriptors=descriptors,regions=regions))
    masks = {}
    for name in registration:
        im = Image.open(HERE/f'aligned_2x/{name}.png')
        rgba = np.array(im);rgb = rgba[:,:,:3].astype(float)
        r,g,b = rgb.transpose(2,0,1)
        alpha=rgba[:,:,3]>0
        green=(g-np.maximum(r,b))/np.maximum(g,1)
        cloth=np.round(np.clip((green-.03)/.14,0,1)*255).astype(np.uint8)
        cloth[~alpha]=0
        box=im.getbbox();yy,xx=np.indices(r.shape)
        # Red/cool-red pigment separates enhanced chestnut hair from warm brown leather.
        head_zone=yy<box[1]+(box[3]-box[1])*.45
        if name[4]=='d' or name[4]=='x':
            head_zone=np.ones_like(alpha)
        candidate=(r>g*1.85)&(b>g*.56)&(r>b*1.05)&alpha&head_zone
        labels,count=ndimage.label(candidate)
        areas=np.bincount(labels.ravel());areas[0]=0
        chosen=int(areas.argmax())
        hair_region=labels==chosen
        distance=ndimage.distance_transform_edt(~hair_region)
        nearby=np.unique(labels[(distance<3)&candidate]);nearby=nearby[(nearby>0)&(areas[nearby]>20)]
        hair_region=np.isin(labels,nearby)
        hair_region=ndimage.binary_fill_holes(hair_region)
        distance=ndimage.distance_transform_edt(~hair_region)
        hair_region |= (distance<=2)&(r>g*1.8)&(r>b*.9)&alpha
        if name in ['m322nb0','m322nc0']:
            hair_region |= (xx>275)&(xx<293)&(yy>278)&(yy<318)&(r>g*1.8)&(b>g*.56)&alpha
        if name == 'm322dc0':
            hair_region |= (xx>248)&(xx<290)&(yy>402)&(yy<424)&(r>g*1.85)&(b>g*.56)&alpha
        if name == 'm322da0':
            hair_region |= (xx>199)&(xx<218)&(yy>367)&(yy<404)&(r>g*1.85)&(b>g*.56)&alpha
            hair_region |= (xx>250)&(xx<277)&(yy>309)&(yy<356)&(r>g*1.85)&(b>g*.56)&alpha
        if name == 'm322db0':
            hair_region |= (xx>245)&(xx<280)&(yy>379)&(yy<425)&(r>g*1.85)&(b>g*.56)&alpha
        if name in ['m322dd0','m322xa0']:

            hair_region[:]=False
        hair=(hair_region&alpha).astype(np.uint8)*255
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
    data=dict(variants=variants,regions=[dict(id='trousers',channel='R',construction='Soft enhanced green cloth hue coverage; open side panels, laces, skin, staff and leather excluded.'),
        dict(id='hair',channel='G',construction='Enhanced red hair component in head and upper back with adjacent red shadow support.')],
        recolor=dict(operation='independent_masked_rgb_matrices',color_space='encoded sRGB 0..255',
          rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
          mask_format='RGB8 linear; R trousers, G hair, B reserved zero',
          calibration='Native green cloth within 124..169 and red hair within 174..225; fixed fits for every frame.',
          mask_filter='Alpha-normalized Gaussian sigma 0.45 physical pixels; overlap normalization; zero outside alpha.',
          pose_corrections='Largest enhanced chestnut component with red shadow support, enclosed highlights filled; staff and leather components excluded; exposed hair islands restored in nb0/nc0/da0/db0/dc0, hidden hair excluded in dd0/xa0.'))
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
