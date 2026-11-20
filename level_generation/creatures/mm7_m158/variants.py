"""Fit deterministic native bat membrane palette transforms and review enhanced-art coverage."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
import sys
sys.path.insert(0,str(HERE.parent / 'mm7_m514'))
from process import apply_variant


def run():
    palettes = {p:np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{p}.act').read_bytes()[:768],
                               np.uint8).reshape(256,3).astype(float) for p in [159,160,161]}
    variants = []
    for p, descriptor in [(159,205),(160,206),(161,207)]:
        matrix = np.linalg.lstsq(palettes[159][64:208],palettes[p][64:208],rcond=None)[0]
        variants.append(dict(id=f'mm7:palette{p}',palette_id=p,default=p==159,exact_bypass=p==159,
            descriptors=[descriptor],rgb_matrix=matrix.tolist(),
            native_fit_mean_channel_error=float(abs(palettes[159][64:208]@matrix-palettes[p][64:208]).mean())))
    data = dict(variants=variants, regions=[dict(id='wing_membrane',channel='R',
        construction='Smooth enhanced RGB green dominance: smoothstep(0.03,0.15,(G-max(R,B))/max(G,1)).',
        protected='Warm fur, ear interiors, teeth, eyes and pink structural bones.')],
        recolor=dict(operation='masked_rgb_matrix',color_space='encoded sRGB 0..255',
                     rule='mix(base_rgb, base_rgb @ matrix, mask); alpha unchanged; base exact bypass',
                     calibration='Native wing palette indices 64..207; soft coverage authored on enhanced pixels.',
                     limitation='Subtle original pink-vein shifts are kept protected with the enhanced pink bone details.'))
    (HERE / 'variants.json').write_text(json.dumps(data,indent=2)+'\n')
    selected = json.loads((HERE / 'batches.json').read_text())['standing']['frames']
    contact = Image.new('RGB',(len(selected)*270,4*290),(45,45,45))
    draw = ImageDraw.Draw(contact)
    for col,n in enumerate(selected):
        im=Image.open(HERE / f'aligned_2x/{n}.png')
        mask=Image.open(HERE / f'masks_2x/{n}.png')
        for row,v in enumerate(variants):
            out=apply_variant(im,mask,v)
            assert np.array_equal(np.array(out)[:,:,3],np.array(im)[:,:,3])
            if v['exact_bypass']:assert np.array_equal(np.array(out),np.array(im))
            display=out.convert('RGBa').resize((256,256),Image.Resampling.LANCZOS).convert('RGBA')
            contact.paste(display,(col*270,row*290+24),display)
            draw.text((col*270+3,row*290+3),n+' '+str(v['palette_id']),fill='white')
        rgba=np.array(im);weight=np.array(mask)[:,:,None]/255*.7
        rgba[:,:,:3]=np.round(rgba[:,:,:3]*(1-weight)+np.array([0,200,255])*weight).astype(np.uint8)
        overlay=Image.fromarray(rgba).convert('RGBa').resize((256,256),Image.Resampling.LANCZOS).convert('RGBA')
        contact.paste(overlay,(col*270,3*290+24),overlay)
    contact.save(HERE / 'review/identity_variants.png')
    print('Authored native-calibrated variants and identity mask contact')


if __name__ == '__main__':
    run()
