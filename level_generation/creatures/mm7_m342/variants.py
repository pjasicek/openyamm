"""Enhanced gown/hair coverage and fixed native palette fits for the human female peasant."""
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
        for channel, (a,b) in enumerate([(49,133),(190,244)]):
            base = palettes[343][a:b]
            if channel == 0:
                selected = (base[:,1]>base[:,0]*1.12)&(base[:,1]>base[:,2]*1.1)
            else:
                selected = (base[:,0]>base[:,1]*1.1)&(base[:,1]>base[:,2]*1.05)
            indices = np.arange(a,b)[selected]
            base = palettes[343][indices]
            target = colors[indices]
            luminance=base@np.array([.2126,.7152,.0722])
            ramp=(luminance[:,None]*target).sum(axis=0)/(luminance*luminance).sum()
            matrix=np.outer([.2126,.7152,.0722],ramp)
            if channel == 1:
                matrix *= .65
            regions.append(dict(channel=channel,rgb_matrix=matrix.tolist(),native_indices=indices.tolist(),
                                mean_fit_error=float(abs(base@matrix-target).mean())))
        descriptors = [int(d) for d,binding in sources['descriptor_bindings'].items()
                       if sources['groups'][binding['standing']]['frames'][0]['palette_id']==palette]
        variants.append(dict(id=f'mm7:palette{palette}',palette_id=palette,default=palette==343,
                             exact_bypass=palette==343,descriptors=descriptors,regions=regions))
    masks = {}
    face_polygons=json.loads((HERE/'face_protection.json').read_text())
    for name in registration:
        im = Image.open(HERE/f'aligned_2x/{name}.png')
        rgba = np.array(im);rgb = rgba[:,:,:3].astype(float)
        r,g,b = rgb.transpose(2,0,1)
        alpha=rgba[:,:,3]>0
        green=(g-np.maximum(r,b))/np.maximum(g,1)
        cloth=np.round(np.clip((green-.03)/.14,0,1)*255).astype(np.uint8)
        cloth[~alpha]=0
        box=im.getbbox();yy,xx=np.indices(r.shape)
        head_zone=yy<box[1]+(box[3]-box[1])*.42
        brown=(r>g*1.2)&(b<g*.85)&((b>g*.45)|(g<12))&alpha&head_zone
        labels,_=ndimage.label(ndimage.binary_closing(brown,iterations=2))
        areas=np.bincount(labels.ravel());areas[0]=0
        head_component=labels==areas.argmax()
        distance=ndimage.distance_transform_edt(~head_component)
        head_support=(distance<3)&alpha&head_zone
        face=np.zeros(r.shape,bool)
        if name in face_polygons:
            face_image=Image.new('L',im.size)
            ImageDraw.Draw(face_image).polygon([tuple(p) for p in face_polygons[name]],fill=255)
            face=np.array(face_image)>0
        hair_region=head_support & brown & ~face
        holes=ndimage.binary_fill_holes(hair_region)&~hair_region
        hair_region |= holes & ~face
        protected_hands={
            'm342nb1': [[(196,176),(219,174),(224,208),(220,233),(198,236),(190,215)]],
            'm342nc1': [[(173,255),(195,252),(195,281),(194,314),(174,314)]]}
        if name in protected_hands:
            zone=Image.new('L',im.size)
            for polygon in protected_hands[name]:ImageDraw.Draw(zone).polygon(polygon,fill=255)
            hair_region[np.array(zone)>0]=False
        if name in ['m342db0','m342dc0']:
            hair_region[:]=False
        death_hair={
            'm342da0': [[(220,321),(260,313),(285,321),(293,339),(288,356),(275,364),(261,357),(240,351),(225,346)],
                       [(215,356),(224,365),(219,397),(209,410),(207,395),(208,374)]],
            'm342dd0': [[(273,480),(287,480),(294,493),(284,501),(271,496)]],
            'm342xa0': [[(219,449),(235,440),(259,439),(277,453),(273,460),(258,455),(231,458),(218,463)],
                       [(198,461),(213,460),(225,463),(216,472),(194,477)],
                       [(275,452),(286,454),(298,466),(294,472),(282,464)]]}
        if name in death_hair:
            zone=Image.new('L',im.size);draw=ImageDraw.Draw(zone)
            for polygon in death_hair[name]:draw.polygon(polygon,fill=255)
            if name=='m342da0':
                draw.polygon([(263,328),(276,329),(286,340),(281,351),(275,354),(273,362),
                              (250,355),(245,346),(250,337),(259,337)],fill=0)
            hair_region=(np.array(zone)>0)&(r>g*1.2)&(b<g*.85)&alpha
        hair=hair_region.astype(np.uint8)*255
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
    data=dict(variants=variants,regions=[dict(id='green_cloth',channel='R',construction='Soft enhanced green cloth hue coverage; white linen, laces, skin and leather excluded.'),
        dict(id='hair',channel='G',construction='Enhanced brown hair component with authored face, hand and prone-pose protection; soft contour weights.')],
        recolor=dict(operation='independent_masked_rgb_matrices',color_space='encoded sRGB 0..255',
          rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
          mask_format='RGB8 linear; R green cloth, G hair, B reserved zero',
          calibration='Native green cloth within 49..132 and brown hair within 190..243; fixed fits for every frame; hair matrix gain 0.65 compensates the brighter enhanced brown hair while base palette bypasses exactly.',
          mask_filter='Alpha-normalized Gaussian sigma 0.45 physical pixels; overlap normalization; zero outside alpha.',
          pose_corrections='48 authored face boundaries, two hand protection polygons and three falling/corpse hair zones; db0/dc0 hair is hidden. All-frame contacts guide local corrections.'))
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
