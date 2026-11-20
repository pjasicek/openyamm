"""Enhanced tunic, hair and beard masks with fixed native ACT tonal ramps."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import ConvexHull
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'mm7_m514'))
from process import apply_variant


def polygon(size, points, box):
    x,y,x1,y1=box
    out=Image.new('L',size)
    ImageDraw.Draw(out).polygon([(round(x+a*(x1-x)),round(y+b*(y1-y))) for a,b in points],fill=255)
    return np.array(out)>0


def run():
    sources=json.loads((HERE/'sources.json').read_text())
    registration=json.loads((HERE/'registration.json').read_text())
    heads=json.loads((HERE/'head_bounds.json').read_text())
    beard_polygons=json.loads((HERE/'beard_zones.json').read_text())
    palettes={int(k):np.frombuffer((REPO/v['path']).read_bytes()[:768],np.uint8).reshape(256,3).astype(float)
              for k,v in sources['palette_sources'].items()}
    variants=[]
    for p,colors in palettes.items():
        indices=np.arange(110,211)
        base=palettes[353][indices];selected=(base[:,1]>base[:,0]*1.1)&(base[:,1]>base[:,2]*1.1)
        indices=indices[selected];base=palettes[353][indices];target=colors[indices]
        lum=base@np.array([.2126,.7152,.0722]);ramp=(lum[:,None]*target).sum(0)/(lum*lum).sum()
        regions=[dict(channel=0,rgb_matrix=np.outer([.2126,.7152,.0722],ramp).tolist(),native_indices=indices.tolist())]
        for channel,indices in [(1,[75,83,90,95]),(2,[231,234,237,243])]:
            if np.array_equal(colors[indices],palettes[353][indices]):
                regions.append(dict(channel=channel,rgb_matrix=np.eye(3).tolist(),native_indices=indices))
            else:
                if channel==2:
                    target=np.array([colors[231]*.1,colors[231]*.7,colors[234],colors[237]])
                    points=[0,8,20,50]
                else:
                    target=colors[indices];points=[0,12,40,85]
                regions.append(dict(channel=channel,tone_ramp=dict(shade_points=points,colors=target.tolist()),native_indices=indices))
        descriptors=[int(d) for d,b in sources['descriptor_bindings'].items()
                     if sources['groups'][b['standing']]['frames'][0]['palette_id']==p]
        variants.append(dict(id=f'mm7:palette{p}',palette_id=p,default=p==353,exact_bypass=p==353,descriptors=descriptors,regions=regions))
    # Authored boundaries in enhanced head-local coordinates. Native pixels are not resized into masks.
    beards={0:[(.24,.49),(.35,.6),(.49,.51),(.65,.59),(.74,.5),(.71,.76),(.53,.83),(.35,.77)],
            1:[(.48,.53),(.62,.63),(.83,.54),(1.2,.55),(1.2,.86),(.85,.86),(.65,.75)],
            2:[(.64,.52),(.77,.61),(.94,.54),(1.2,.55),(1.2,.81),(.89,.79),(.71,.69)]}
    corrections=json.loads((HERE/'head_boundary_corrections.json').read_text())
    masks={}
    for n in registration:
        im=Image.open(HERE/f'aligned_2x/{n}.png');a=np.array(im);rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1);alpha=a[:,:,3]/255
        green=(g-np.maximum(r,b))/np.maximum(g,1);cloth=np.clip((green-.03)/.14,0,1)*(alpha>0)
        box=heads[n]
        if n=='m352nb0':box=[235,181,289,218]
        yy,xx=np.indices(r.shape)
        zone=(xx>=box[0]-3)&(xx<box[2]+3)&(yy>=box[1]-3)&(yy<box[3]+3)
        dark=np.clip((65-rgb.mean(2))/20,0,1)
        view=int(n[-1])
        lum=rgb@np.array([.2126,.7152,.0722])
        skin=(lum>55)&(r>g*1.25)&(g>b*1.2)&(alpha>.5)&zone
        beard_zone=polygon(im.size,beards[view],box) if view in beards else np.zeros(r.shape,bool)
        if n in beard_polygons:
            region=Image.new('L',im.size);ImageDraw.Draw(region).polygon([tuple(p) for p in beard_polygons[n]],fill=255)
            beard_zone=np.array(region)>0
        if n in beard_polygons and n not in ['m352fd0','m352na2','m352nf1']:
            expanded=beard_zone.copy()
            for dy in range(8):
                for dx in range(11):
                    expanded[dy:,dx:] |= beard_zone[:beard_zone.shape[0]-dy,:beard_zone.shape[1]-dx]
            beard_zone=expanded
        if n in corrections['beards']:
            region=Image.new('L',im.size);ImageDraw.Draw(region).polygon([tuple(p) for p in corrections['beards'][n]],fill=255)
            beard_zone=np.array(region)>0
        ys,xs=np.where(skin|beard_zone);face=np.zeros(r.shape,bool)
        if len(xs)>5:
            points=np.stack((xs,ys),1);hull=ConvexHull(points);region=Image.new('L',im.size)
            ImageDraw.Draw(region).polygon([tuple(p) for p in points[hull.vertices]],fill=255)
            face=ndimage.binary_dilation(np.array(region)>0,iterations=1)
        if n in corrections['faces']:
            region=Image.new('L',im.size);ImageDraw.Draw(region).polygon([tuple(p) for p in corrections['faces'][n]],fill=255)
            face=np.array(region)>0
        hair=dark*(~face)*zone*(alpha>0)
        if view==0 and n not in beard_polygons:
            hx=(xx-box[0])/(box[2]-box[0]);hy=(yy-box[1])/(box[3]-box[1])
            side=zone&(hy>.57)&((hx<.26)|(hx>.76))&(~skin)&(~beard_zone)
            hair=np.maximum(hair,dark*side*(alpha>0))
        if n in corrections['hair_additions']:
            region=Image.new('L',im.size);ImageDraw.Draw(region).polygon([tuple(p) for p in corrections['hair_additions'][n]],fill=255)
            hair=np.maximum(hair,dark*(np.array(region)>0)*(alpha>0))
        beard=beard_zone*np.clip((60-rgb.max(2))/25,0,1)*(alpha>0)
        if n in ['m352db0','m352dc0','m352xa0']:
            hair[:]=0;beard[:]=0
        weights=np.dstack((cloth,hair,beard));weights[:,:,1:]*=(cloth==0)[:,:,None]
        denominator=ndimage.gaussian_filter(alpha,.45)
        for c in range(3):weights[:,:,c]=ndimage.gaussian_filter(weights[:,:,c]*alpha,.45)/np.maximum(denominator,1e-8)
        weights[alpha==0]=0;weights/=np.maximum(weights.sum(2),1)[:,:,None]
        mask=Image.fromarray(np.round(weights*255).astype(np.uint8));mask.save(HERE/f'masks_2x/{n}.png');masks[n]=mask
    data=dict(variants=variants,regions=[dict(id='tunic',channel='R'),dict(id='hair',channel='G'),dict(id='beard',channel='B')],
      recolor=dict(operation='independent_masked_rgb_matrix_or_tonal_ramp',color_space='encoded sRGB 0..255',
        rule='base + sum(mask[channel] * (target - base)); target is RGB matrix or piecewise linear luminance ramp; exact base bypass; alpha unchanged',
        calibration='Fixed cloth native ACT fit; hair samples 75,83,90,95 at enhanced luminance 0,12,40,85; beard samples 0.1*231,0.7*231,234,237 at luminance 0,8,20,50; unchanged regional palettes bypass.',
        mask_format='RGB8 linear; R tunic, G hair, B beard',mask_filter='Alpha-normalized Gaussian sigma 0.45 physical pixels; normalized overlap.'))
    (HERE/'variants.json').write_text(json.dumps(data,indent=2)+'\n')
    settings=json.loads((HERE/'processing_settings.json').read_text());settings.update(masks=data['recolor']['mask_format'],mask_regions=data['regions'],recolor=data['recolor']);(HERE/'processing_settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    names=list(masks)
    for start in range(0,len(names),16):
        out=Image.new('RGB',(1080,1200),(45,45,45));draw=ImageDraw.Draw(out)
        for i,n in enumerate(names[start:start+16]):
            im=Image.open(HERE/f'aligned_2x/{n}.png');a=np.array(im);w=np.array(masks[n])/255
            a[:,:,:3]=np.round(a[:,:,:3]*(1-w.sum(2)[:,:,None]*.7)+(w@np.array([[0,200,255],[255,180,0],[240,30,160]]))*.7).astype(np.uint8)
            tile=Image.fromarray(a).resize((256,256),Image.Resampling.LANCZOS);x=i%4*270;y=i//4*300;out.paste(tile,(x,y+20),tile);draw.text((x,y),n,fill='white')
        out.save(HERE/f'review/material_masks_{start//16}.png')
    out=Image.new('RGB',(1800,1280),(45,45,45));draw=ImageDraw.Draw(out)
    for row,n in enumerate([f'm352sa{v}' for v in range(5)]):
        im=Image.open(HERE/f'aligned_2x/{n}.png')
        for col,v in enumerate(variants):
            tile=apply_variant(im,masks[n],v).resize((230,230),Image.Resampling.LANCZOS);out.paste(tile,(col*200,row*256+20),tile);draw.text((col*200,row*256),str(v['palette_id']),fill='white')
    out.save(HERE/'review/identity_variants.png');print('Authored',len(masks),'masks and nine native variants; review pending')

if __name__=='__main__':run()
