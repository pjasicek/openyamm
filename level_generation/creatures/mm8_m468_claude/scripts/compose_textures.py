"""Cook body/head PBR maps, native palette ramps and shared trouser mask. Skin uses one albedo across sets."""
import json, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm8_m468' / 'native_variants'
N = 1024
SKIN = np.array([166, 192, 202]) / 255           # sRGB albedo
SKIN_MIX = 0.30; RAMP_GAIN = 1.25
PALS = {'m468_a': 469, 'm468_b': 470, 'm468_c': 471}   # dsft.bin: m469/m470/m471 Vampire A/B/C
SPEC = {'skin': 0.35, 'hair': 0.18, 'cloth': 0.2, 'leather': 0.4, 'eye': 0.8, 'mouth': 0.3, 'iron': .8, 'ivory': .3}
ROUGH = {'skin': 0.78, 'hair': 0.8, 'cloth': 0.85, 'leather': 0.65, 'eye': 0.25, 'mouth': 0.7, 'iron': .5, 'ivory': .6}


def load(path, mode='RGB', n=N):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def lin(x): return R.srgb_to_linear(x)
def srgb(x):
    x = np.asarray(x, np.float64); return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


def repaint_skin(img, m, sigma=6.0):
    """One albedo x fine shading (luminance over its masked blur) on the texels m, mixed SKIN_MIX over the original."""
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, 0.5, 1.5)
    new = srgb(np.clip(lin(SKIN)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


# ---------------------------------------------------------------- native recolour colours per tier
FR = ['m468Sa0.bmp','m468Sa1.bmp','m468Sa2.bmp','m468Sa3.bmp','m468Sa4.bmp','m468Wa0.bmp','m468Wc0.bmp']
palette_root=HERE.parent/'mm8_packed_outline_collection_20261002/families/mm8_m468/native_palettes'
palettes={k:np.frombuffer((palette_root/f'{i}.act').read_bytes(),np.uint8)[:768].reshape(256,3)/255 for k,i in PALS.items()}
native={k:[] for k in PALS}
for f in FR:
    index=np.asarray(Image.open(HERE.parents[2]/'assets_dev/engine/sprites'/f))
    ims={k:palette[index] for k,palette in palettes.items()}
    ha,sa,va=hsv(ims['m468_a']);mask=(index!=0)&(ha>65)&(ha<165)&(sa>.35)&(va>.04)
    for k in PALS:native[k].append(ims[k][mask])
for k in PALS:
    X=np.concatenate(native[k]);L=R.luminance(X);X,L=X[L>.001],L[L>.001];o=np.argsort(L);native[k]=(X[o],L[o])


def ramps_for(texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        X, _ = native[k]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN, 0, 1)), 0, 1)])
        out[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
    return out


# Surface membership comes from the fitted mesh; colour only selects painted cloth borders.
reports = {}; cloth_ramps = None
for head, uv in [(False, 'UVMap'), (True, 'HeadUV')]:
    prefix = 'm468_head' if head else 'm468'
    M = HERE / 'work/head_uv_repaired' if head else HERE / 'meshy/body_retexture_v1'
    base = load(M / 'texture_urls_0_base_color.png')
    normal = load(M / 'texture_urls_0_normal.png')
    rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
    sys.path.insert(0,str(HERE.parents[2]/'tools'))
    from normal_map_convention import measure
    correlation=measure((normal*255+.5).astype(np.uint8))
    if correlation <= -.1: normal[...,1]=1-normal[...,1]
    print('NORMAL_CONVENTION',prefix,correlation,'glTF +Y output')
    rz = np.load(HERE / 'work' / f'uvraster_{uv}.npz')
    piece, pos = rz['piece'], rz['pos']; cov = piece >= 0
    hue, sat, val = hsv(base)
    skin=cov & (piece==0)
    eye=cov & np.isin(piece,[5,6]);mouth=cov & (piece==7);ivory=cov & (piece>=8)
    cloth=cov & (piece==2);leather=cov & np.isin(piece,[1,4]);iron=cov & (piece==3)
    masks = [('skin',skin,1),('eye',eye,6),('mouth',mouth,7),('cloth',cloth,8),('leather',leather,8),('iron',iron,9),('ivory',ivory,10)]
    g = ao_grade(repaint_skin(base,skin),load(HERE/'work'/f'ao_{uv}.png','L'),cov,strength=.25)
    spec=np.zeros((N,N)); rough=np.ones((N,N)); cls=np.zeros((N,N),np.uint8)
    for name,m,c in masks:
        cls[m]=c; spec[m]=SPEC[name]
        if m.any(): rough[m]=np.clip(ROUGH[name]+(rough_m[m]-np.median(rough_m[m]))*.3,.1,1)
    save(pad(g,cov),T/f'{prefix}_basecolor_1k.png')
    save(pad(normal,cov),T/f'{prefix}_normal_1k.png')
    save(np.stack([pad(spec,cov),pad(rough,cov),pad(iron.astype(float),cov)],-1),T/f'{prefix}_metal_rough_1k.png')
    Image.fromarray(cls).save(T/f'{prefix}_material_classes.png')
    reports[prefix]={name:int(m.sum()) for name,m,c in masks}
    if not head:
        trousers=cloth
        assert trousers.sum()>1000 and skin.sum()>1000
        cloth_ramps=ramps_for(R.luminance(g[trousers]))
        R.write_mask([ndimage.gaussian_filter(pad(trousers.astype(float),cov),.7)],T/'m468_region_mask.png',size=N)
        reports[prefix]['trousers']=int(trousers.sum())
    reports[prefix]['skin_median_rgb']=np.round(np.median(g[skin],axis=0)*255).astype(int).tolist()
cfg={'variants':list(PALS),'materials':[{'base':'M468_A','prefix':'M468','mask':'m468_region_mask.png','regions':['trousers'],'palettes':PALS,'ramps':cloth_ramps}]}
(T/'m468_ramps.json').write_text(json.dumps(cfg,indent=1)+'\n')
(HERE/'work/texture_classes.json').write_text(json.dumps(reports,indent=2)+'\n')
print(reports)

