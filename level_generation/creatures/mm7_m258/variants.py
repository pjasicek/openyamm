"""Enhanced Griffin material masks and fixed native-palette recoloring."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parent
REPO = P.parents[2]


def run():
    sources = json.loads((P/'sources.json').read_text())
    palettes = {int(k):np.frombuffer((REPO/v['path']).read_bytes()[:768],np.uint8).reshape(256,3).astype(float)
                for k,v in sources['palette_sources'].items()}
    base = palettes[259]
    histogram = np.zeros(256)
    for source in sources['sources'].values():
        histogram += np.bincount(np.array(Image.open(REPO/source['path'])).ravel(),minlength=256)
    variants=[]
    for palette,target in palettes.items():
        regions=[]
        for channel,(lo,hi) in enumerate([(154,249),(102,150),(18,95)]):
            ids=np.arange(lo,hi)
            if channel<2:
                luma_weights=np.array([.2126,.7152,.0722])
                luma=base[ids]@luma_weights
                weight=histogram[ids]/np.maximum(luma,8)**2
                gain=((luma*weight)@target[ids])/((luma*weight)@luma)
                matrix=np.outer(luma_weights,gain)
            elif palette in [259,260]:
                matrix=np.eye(3)
            else:
                # The native red preset also warms fur and gold. Fit that coupled
                # color transform, retaining their distinct brown/yellow hues.
                weight=np.sqrt(histogram[ids]/np.maximum(base[ids].mean(axis=1),8)**2)
                matrix=np.linalg.lstsq(base[ids]*weight[:,None],target[ids]*weight[:,None],rcond=None)[0]
            regions.append(dict(channel=channel,native_indices=ids.tolist(),rgb_matrix=matrix.tolist(),
                mean_fit_error=float(abs(base[ids]@matrix-target[ids]).mean())))
        descriptors=[int(d) for d,binding in sources['descriptor_bindings'].items()
                     if sources['groups'][binding['standing']]['frames'][0]['palette_id']==palette]
        variants.append(dict(id=f'mm7:palette{palette}',palette_id=palette,default=palette==259,
                             exact_bypass=palette==259,descriptors=descriptors,regions=regions))
    reg=json.loads((P/'registration.json').read_text())
    for name in reg:
        rgba=np.array(Image.open(P/f'aligned_2x/{name}.png'))
        r,g,b=rgba[:,:,:3].astype(float).transpose(2,0,1)
        alpha=rgba[:,:,3]/255
        maximum=np.maximum(np.maximum(r,g),np.maximum(b,1))
        green=np.clip(((g-r)/maximum-.015)/.12,0,1)
        warm=(r-g)/maximum
        yellow=(g-b)/maximum
        feather_seed=(warm>.015)&(warm<.22)&(yellow>.075)&(alpha>.5)&(green<.2)
        labels,_=ndimage.label(feather_seed)
        # Reviewed talon highlights form 40–100-pixel olive seed islands;
        # true flight-feather support forms much larger connected regions.
        sizes=np.bincount(labels.ravel());keep=sizes>=200;keep[0]=False
        feather_support=ndimage.distance_transform_edt(~keep[labels])<=4
        feather=np.clip((.23-warm)/.09,0,1)*np.clip((yellow-.02)/.075,0,1)*feather_support*(1-green)
        gold_fur=np.clip((warm-.14)/.12,0,1)*(1-green)*(1-feather)
        # Reviewed side-recoil beak highlights share the olive feather hue.
        # Transfer only their feather coverage into the warm beak region.
        beak_boxes={'m258nc2':(125,250,173,293),'m258nd2':(115,280,167,318)}
        if name in beak_boxes:
            x0,y0,x1,y1=beak_boxes[name]
            gold_fur[y0:y1,x0:x1]+=feather[y0:y1,x0:x1]
            feather[y0:y1,x0:x1]=0
        weights=np.dstack([green,feather,gold_fur])
        denominator=ndimage.gaussian_filter(alpha,.45)
        for channel in range(3):
            weights[:,:,channel]=ndimage.gaussian_filter(weights[:,:,channel]*alpha,.45)/np.maximum(denominator,1e-8)
        weights[alpha==0]=0
        weights/=np.maximum(weights.sum(axis=2),1)[:,:,None]
        Image.fromarray(np.round(weights*255).astype(np.uint8)).save(P/f'masks_2x/{name}.png')
    data=dict(variants=variants,regions=[dict(id='colored_plumage',channel='R'),
        dict(id='flight_feathers',channel='G'),dict(id='warm_fur_gold',channel='B')],
        recolor=dict(operation='independent_masked_rgb_matrices',color_space='encoded sRGB 0..255',
        rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
        mask_format='RGB8 linear; R colored plumage/tail tuft, G olive flight feathers, B brown fur/gold',
        calibration='Fixed native pixel-frequency-weighted relative-error ACT fits: plumage154..248, flight102..149; fur/gold18..94 uses identity for260 and a fitted full RGB matrix for261.',
        mask_filter='Enhanced teal support, olive feather seed components >=200 pixels with 4-pixel support, warm fur/gold hue support; reviewed nc2/nd2 beak boxes transfer feather coverage to gold; alpha-normalized Gaussian sigma0.45.',
        protected='Neutral talons, eye black, mouth cavity and native unchanged accent pixels. All masks require visual review.'))
    (P/'variants.json').write_text(json.dumps(data,indent=2)+'\n')
    p=P/'processing_settings.json';settings=json.loads(p.read_text());settings.update(masks=data['recolor']['mask_format'],mask_regions=data['regions'],recolor=data['recolor']);p.write_text(json.dumps(settings,indent=2)+'\n')
    print('Authored',len(reg),'three-region masks; review pending')


if __name__=='__main__':
    run()
