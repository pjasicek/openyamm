"""Elf archer enhanced cloth/hair masks and fixed native ACT transforms."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    source = json.loads((HERE/'sources.json').read_text())
    names = json.loads((HERE/'registration.json').read_text())
    zones = json.loads((HERE/'hair_regions.json').read_text())
    corrections=json.loads((HERE/'hair_overlap_corrections.json').read_text())
    palettes = {int(p): np.frombuffer((REPO/r['path']).read_bytes()[:768],np.uint8).reshape(256,3).astype(float)
                for p,r in source['palette_sources'].items()}
    base = palettes[216]
    variants = []
    for p,target in palettes.items():
        regions = []
        for channel,(low,high) in enumerate([(104,172),(62,104)]):
            ids=np.arange(low,high)
            if channel==0:
                ids=ids[(base[ids,1]>base[ids,0]*1.08)&(base[ids,1]>base[ids,2]*1.08)]
                matrix=np.linalg.lstsq(base[ids],target[ids],rcond=None)[0]
            else:
                ids=ids[(base[ids].max(axis=1)-base[ids].min(axis=1)<base[ids].max(axis=1)*.18)&(base[ids].mean(axis=1)>30)]
                lum=base[ids]@np.array([.2126,.7152,.0722])
                ramp=(lum[:,None]*target[ids]).sum(axis=0)/(lum*lum).sum()
                matrix=np.outer([.2126,.7152,.0722],ramp)
            regions.append(dict(channel=channel,rgb_matrix=matrix.tolist(),native_indices=ids.tolist()))
        descriptors=[int(d) for d,b in source['descriptor_bindings'].items()
                     if source['groups'][b['standing']]['frames'][0]['palette_id']==p]
        variants.append(dict(id=f'mm7:palette{p}',palette_id=p,default=p==216,exact_bypass=p==216,
                             descriptors=descriptors,regions=regions))
    contacts=[]
    for name in names:
        im=Image.open(HERE/f'aligned_2x/{name}.png').convert('RGBA');a=np.array(im)
        r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);alpha=a[:,:,3]/255
        chroma=(g-np.maximum(r,b))/np.maximum(g,1)
        cloth=np.clip((chroma-.025)/.16,0,1)
        clabels,ccount=ndimage.label((chroma>.16)&(alpha>.5))
        areas=np.bincount(clabels.ravel());keep=areas>=100;keep[0]=False
        cloth*=ndimage.distance_transform_edt(~keep[clabels])<=3
        yy,xx=np.indices(r.shape);x0,y0,x1,y1=zones[name]
        zone=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)
        neutral=(r>20)&(g>r*.85)&(g<r*1.3)&(b>r*.8)&(b<r*1.7)&(alpha>0)
        labels,count=ndimage.label(neutral);sizes=np.bincount(labels.ravel());sizes[0]=0
        overlap=np.bincount(labels[zone].ravel(),minlength=len(sizes));overlap[0]=0
        chosen=overlap.argmax()
        hair=labels==chosen if chosen else np.zeros_like(neutral)
        hair=ndimage.binary_fill_holes(hair)
        hair|=(ndimage.distance_transform_edt(~hair)<=2)&neutral
        if name in corrections['feather_exclusions']:
            cut=Image.new('L',im.size);ImageDraw.Draw(cut).polygon([tuple(v) for v in corrections['feather_exclusions'][name]],fill=255)
            hair[np.array(cut)>0]=False
        if name in corrections['hair_inclusions']:
            cut=Image.new('L',im.size);ImageDraw.Draw(cut).polygon([tuple(v) for v in corrections['hair_inclusions'][name]],fill=255)
            hair=neutral&(np.array(cut)>0)
        if name in corrections.get('cloth_exclusions', {}):
            cut=Image.new('L',im.size);ImageDraw.Draw(cut).polygon([tuple(v) for v in corrections['cloth_exclusions'][name]],fill=255)
            cloth[np.array(cut)>0]=0
        weights=np.dstack((cloth,hair,np.zeros_like(cloth))).astype(float)
        den=np.maximum(ndimage.gaussian_filter(alpha,.45),1e-8)
        for c in range(2):weights[:,:,c]=ndimage.gaussian_filter(weights[:,:,c]*alpha,.45)/den
        weights[alpha==0]=0;weights/=np.maximum(weights.sum(axis=2),1)[:,:,None]
        Image.fromarray(np.round(weights*255).astype(np.uint8)).save(HERE/f'masks_2x/{name}.png')
        overlay=a.copy();overlay[:,:,:3]=np.clip(a[:,:,:3]*(1-weights.sum(axis=2)[:,:,None]*.6)+.6*(weights[:,:,0,None]*[0,220,255]+weights[:,:,1,None]*[255,170,0]),0,255)
        tile=Image.fromarray(overlay).crop((max(0,x0-30),max(0,y0-30),min(im.width,x1+30),min(im.height,y1+30)));tile.thumbnail((175,160));contacts.append((name,tile))
    for start in range(0,len(contacts),30):
        out=Image.new('RGB',(1080,900),'#303030');draw=ImageDraw.Draw(out)
        for i,(name,tile) in enumerate(contacts[start:start+30]):
            x=i%6*180;y=i//6*180;out.paste(tile,(x,y+20),tile);draw.text((x,y),name,fill='white')
        out.save(HERE/f'review/hair_mask_review_{start//30}.png')
    data=dict(variants=variants,regions=[dict(id='garments',channel='R'),dict(id='hair',channel='G')],recolor=dict(
        operation='independent_masked_rgb_matrices',color_space='encoded sRGB 0..255',
        rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
        mask_format='RGB8 linear; R green garments, G silver hair, B reserved zero',
        calibration='Native green cloth ACT 104..171 and neutral silver hair ACT 62..103; fixed transforms for all frames.',
        mask_filter='Enhanced green chroma and enhanced neutral connected hair within coarse head rectangles; native masks are not resized. Alpha-normalized Gaussian sigma .45; normalized overlap.',
        protected='Skin, ivory piping and back leaf trim, arrow feathers, brown bow, bracer and quiver, gold fittings and red studs.'))
    (HERE/'variants.json').write_text(json.dumps(data,indent=2)+'\n')
    settings=json.loads((HERE/'processing_settings.json').read_text());settings.update(masks=data['recolor']['mask_format'],mask_regions=data['regions'],recolor=data['recolor']);(HERE/'processing_settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    print('Authored',len(names),'enhanced garment/hair masks; visual review pending')


if __name__=='__main__':
    run()
