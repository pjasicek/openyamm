"""Remove Meshy's projected lighting patches, retaining fine skin detail and the native brown chroma."""
import json, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

P = Path(__file__).resolve().parents[1]
BEFORE = P / 'work/review_round2_before'
LUMA = np.array([.2126, .7152, .0722])
linear = lambda c: np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - .055)
native = np.array(Image.open(P.parent / 'mm6_natm/native/natmsta0.png').convert('RGB')) / 255.
rois = {'head': [164,62,190,96], 'neck': [169,92,186,106], 'chest': [150,132,205,154]}
samples = {}
for name, (x0,y0,x1,y1) in rois.items():
    c = native[y0:y1,x0:x1]; lum = c @ LUMA
    samples[name] = c[(c[...,0] > c[...,1]*1.05) & (c[...,1] > c[...,2]*1.05) & (lum > .04)]
reference = np.concatenate(list(samples.values()))
chroma = np.median(linear(reference) / np.maximum((linear(reference) @ LUMA)[:,None], 1e-8), axis=0)
chroma /= chroma @ LUMA
# One albedo across all anatomy. Native lighting remains in the sprite comparison, not painted onto the neck.
target = .056
base = srgb(chroma * target)
def stats(c):
    lum = c @ LUMA
    hsv = np.array([colorsys.rgb_to_hsv(*v) for v in c[::max(1,len(c)//20000)]])
    return {'pixels': len(c), 'mean_srgb_255': float(lum.mean()*255),
            'p05_p50_p95_p98_srgb_255': (np.percentile(lum,[5,50,95,98])*255).tolist(),
            'mean_hue_deg': float(hsv[:,0].mean()*360)}
report = {'method': __doc__, 'native_rois': rois, 'native': {n:stats(c) for n,c in samples.items()},
          'base_srgb_255': (base*255).tolist(), 'regions': {},
          'limitation': 'Native sprite luminance includes strong directional shadows. Uniform albedo is compared separately; no claim that its highlight percentiles reproduce the painted lighting.'}
for level in range(4):
    for material in range(2):
        raster = np.load(P / f'work/round2_raster_{level}_{material}.npz')
        piece, pos = raster['piece'], raster['pos']; valid = piece >= 0
        _, near = distance_transform_edt(~valid, return_indices=True)
        skin = piece[tuple(near)] == 0; pos = pos[tuple(near)]
        relative = f'export/textures_lod{level}/body/{material}_basecolor.png'
        rgba = np.array(Image.open(BEFORE / relative).convert('RGBA'),float)/255
        old = rgba[...,:3]; lum = old @ LUMA
        x,y,z = pos.transpose(2,0,1)
        # UV-island high-pass residuals formed triangular patches; skin grain must agree in object space.
        grain = (np.sin(x*751+y*613+z*997) + np.sin(x*479-y*827+z*571)) * .008
        factor = 1 + grain
        corrected = srgb(chroma[None,None,:] * target * factor[...,None])
        # Keep small facial features, with a soft geometric boundary rather than a texture island boundary.
        eyes = np.exp(-((abs(x)-.030)/.019)**4 - ((z-1.605)/.021)**4) * (y < -.13)
        lips = np.exp(-(x/.030)**4 - ((z-1.535)/.011)**4) * (y < -.155)
        features = np.clip(eyes*.80 + lips*.35, 0, .85)
        feature_luma = np.clip(lum/(base@LUMA), .18, 1.15)
        corrected *= (1-features + features*feature_luma)[...,None]
        rgba[...,:3][skin] = corrected[skin]
        assert np.isfinite(rgba).all()
        Image.fromarray(np.uint8(np.clip(rgba,0,1)*255+.5)).save(P / relative)
        if material == 0:
            normal_path = relative.replace('_basecolor.png', '_normal.png')
            normals = np.array(Image.open(BEFORE / normal_path).convert('RGBA'))
            vectors = normals[...,:3].astype(float)/127.5-1
            vectors[...,:2][skin] *= .15
            vectors /= np.maximum(np.linalg.norm(vectors,axis=2,keepdims=True),1e-8)
            normals[...,:3][skin] = np.uint8(np.clip((vectors[skin]+1)*127.5,0,255)+.5)
            Image.fromarray(normals).save(P / normal_path)
            report['body_skin_normal_strength'] = .15
        if level == 0:
            regions = {'head': (z>1.52), 'neck': (z>1.40)&(z<1.50), 'chest': (z>1.23)&(z<1.38)&(abs(x)<.17)&(y<-.07)}
            for name, region in regions.items():
                mask = region & valid & (piece==0) & (features<.05)
                if mask.any(): report['regions'][f'{material}_{name}'] = stats(rgba[...,:3][mask])
        print('SKIN', level, material, flush=True)
# Shared skin ramp preserves this single native chroma on every tier and both head/body maps.
path = P / 'textures/natm_ramps.json'; ramps = json.loads((BEFORE/'textures/natm_ramps.json').read_text())
for mat in ramps['materials']:
    for tier, values in mat['ramps'].items():
        r = values[1]; lo,hi = r['range']; r['colors'] = np.clip(np.linspace(lo,hi,16)[:,None]*chroma,0,1).tolist()
path.write_text(json.dumps(ramps,indent=2)+'\n')
means = [r['mean_srgb_255'] for r in report['regions'].values()]
assert max(means)-min(means) < 3, means
report['maximum_region_mean_difference_srgb_255'] = max(means)-min(means)
(P/'review/round2_skin.json').write_text(json.dumps(report,indent=2)+'\n')
