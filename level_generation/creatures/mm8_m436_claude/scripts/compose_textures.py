"""Cook body/head PBR maps, native palette ramps and shared vest/shorts mask. Skin uses one albedo across sets."""
import json, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm8_m436' / 'native_variants'
N = 1024
SKIN = np.array([164, 119, 83]) / 255           # sRGB albedo
SKIN_MIX = 0.65; RAMP_GAIN = 1.15
PALS = {'m436_a': 437, 'm436_b': 438, 'm436_c': 439}   # dsft.bin: m437/m438/m439 Ogre Peasant A/B/C
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
FR = ['m436Sa0.bmp','m436Sa1.bmp','m436Sa2.bmp','m436Sa3.bmp','m436Sa4.bmp','m436Wa0.bmp','m436Wc0.bmp']
palette_root=HERE.parents[2]/'assets_dev/worlds/mm8/textures'
palettes={k:np.frombuffer((palette_root/f'pal{i}.act').read_bytes(),np.uint8)[:768].reshape(256,3)/255 for k,i in PALS.items()}
native={k:[] for k in PALS}
for f in FR:
    index=np.asarray(Image.open(HERE.parents[2]/'assets_dev/engine/sprites'/f))
    ims={k:palette[index] for k,palette in palettes.items()}
    ha,sa,va=hsv(ims['m436_a']);mask=(index!=0)&(ha>65)&(ha<165)&(sa>.35)&(va>.04)&(np.max(abs(ims['m436_a']-ims['m436_b']),axis=-1)>.04)&(np.max(abs(ims['m436_a']-ims['m436_c']),axis=-1)>.04)
    for k in PALS:native[k].append(ims[k][mask])
for k in PALS:
    X=np.concatenate(native[k]);L=R.luminance(X);X,L=X[L>.001],L[L>.001];o=np.argsort(L);native[k]=(X[o],L[o])


def ramps_for(texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); middle = np.median(texel_lum)
    out = {}
    for k in PALS:
        X, _ = native[k]
        # Native sprites contain baked black shadows; use their lit cloth colour and retain our fabric shading.
        colour = lin(np.clip(np.median(X[int(len(X)*.70):int(len(X)*.95)],axis=0)*RAMP_GAIN,0,1))
        cols = [np.clip(colour*(max(Li,.001)/middle)**.65,0,1).round(6).tolist() for Li in np.linspace(lo,hi,16)]
        out[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
    return out


# Surface membership comes from the fitted mesh; colour only selects painted cloth borders.
reports = {}; cloth_ramps = None
for head, uv in [(False, 'UVMap'), (True, 'HeadUV')]:
    prefix = 'm436_head' if head else 'm436'
    M = HERE / 'work' / ('uv_repaired_HeadUV' if head else 'uv_repaired_UVMap')
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
    eye=cov & np.isin(piece,[101,102]);mouth=cov & np.isin(piece,[103,104]);hair=cov & (piece==105);ivory=np.zeros_like(cov)
    leather=cov & np.isin(piece,[3,4,5,7,8,9,48,91,94]);iron=cov & (piece==6);cloth=cov & ~(skin|eye|mouth|hair|leather|iron)
    masks = [('skin',skin,1),('eye',eye,6),('mouth',mouth,7),('cloth',cloth,8),('leather',leather,8),('iron',iron,9),('ivory',ivory,10),('hair',hair,2)]
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
        trousers=cloth & (hue>60) & (hue<170) & (sat>.18)
        assert trousers.sum()>1000 and skin.sum()>1000
        cloth_ramps=ramps_for(R.luminance(g[trousers]))
        R.write_mask([ndimage.gaussian_filter(pad(trousers.astype(float),cov),.7)],T/'m436_region_mask.png',size=N)
        reports[prefix]['trousers']=int(trousers.sum())
    reports[prefix]['skin_median_rgb']=np.round(np.median(g[skin],axis=0)*255).astype(int).tolist()
cfg={'variants':list(PALS),'materials':[{'base':'M436_A','prefix':'M436','mask':'m436_region_mask.png','regions':['vest_and_shorts'],'palettes':PALS,'ramps':cloth_ramps}]}
(T/'m436_ramps.json').write_text(json.dumps(cfg,indent=1)+'\n')
(HERE/'work/texture_classes.json').write_text(json.dumps(reports,indent=2)+'\n')
print(reports)

