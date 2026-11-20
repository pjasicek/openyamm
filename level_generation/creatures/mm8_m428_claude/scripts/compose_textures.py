"""Cook body/head PBR maps, native palette ramps and the shared dress mask (adapted from mm8_m424_claude). Skin uses one
albedo across both sets (the male's measured dark-elf skin). Region: the green dress (bodice, skirt, shoulder bands)
recolours green/blue/red from palettes 429/430/431; the grey chemise and underskirt, hair, skin, lacing, belt, buckle
and shoes stay fixed."""
import json, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm8_m428' / 'native_variants'
N = 1024
SKIN = np.array([145, 78, 65]) / 255           # sRGB albedo
SKIN_MIX = 0.85; RAMP_GAIN = 1.35
PALS = {'m428_a': 429, 'm428_b': 430, 'm428_c': 431}   # palette_id of m429/m430/m431 frames
SPEC = {'skin': 0.35, 'hair': 0.18, 'cloth': 0.2, 'leather': 0.4, 'eye': 0.8, 'mouth': 0.3}
ROUGH = {'skin': 0.78, 'hair': 0.8, 'cloth': 0.85, 'leather': 0.65, 'eye': 0.25, 'mouth': 0.7}


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
FR = ['m428sa0', 'm428sa1', 'm428sa2', 'm428sa3', 'm428sa4', 'm428wa0', 'm428wc0']
native = {k: [] for k in PALS}
for f in FR:
    ims = {k: np.asarray(Image.open(NATIVE / f'{f}_{p}.png').convert('RGBA')).astype(np.float64) / 255 for k, p in PALS.items()}
    al = ims['m428_a'][..., 3] > 0.5
    d = (np.abs(ims['m428_a'][..., :3] - ims['m428_b'][..., :3]).sum(-1) > 0.02) | (np.abs(ims['m428_a'][..., :3] - ims['m428_c'][..., :3]).sum(-1) > 0.02)
    ha,sa,va=hsv(ims['m428_a'][...,:3])
    tunic=al & d & (ha>65) & (ha<165) & (sa>.35) & (va>.14)
    for k in PALS:
        native[k].append(ims[k][tunic][:, :3])
for k in PALS:
    X = np.concatenate(native[k]); L = R.luminance(X); X, L = X[L > 0.005], L[L > 0.005]
    o = np.argsort(L); native[k] = (X[o], L[o])


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
    prefix = 'm428_head' if head else 'm428'
    M = HERE / 'meshy' / ('head_retexture_v1' if head else 'body_retexture_v1')
    base = load(M / 'texture_urls_0_base_color.png')
    normal = load(M / 'texture_urls_0_normal.png')
    rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
    rz = np.load(HERE / 'work' / f'uvraster_{uv}.npz')
    piece, pos = rz['piece'], rz['pos']; cov = piece >= 0
    hue, sat, val = hsv(base)
    warm = ((hue < 36) | (hue > 340)) & (sat > .22) & (val > .07)
    # pieces (step1_clean.py): 0 skin/bodice/sleeves/dress, 1 legs+shoes, 2 hair, 3/4 hands, 5 fringe, 8/9 eyes,
    # 17/18 mouth, 16/19/22 belt and buckle; the neckline skin lies above 1.30 m (square neckline)
    skin = cov & (np.isin(piece, [3,4]) | ((piece == 0) & (pos[...,2] > 1.30) & warm))
    # the neck column is skin whatever Meshy painted there (the head views put shadow, collar and hair-lock paint
    # under the jaw: a dark choker band at the head/body seam, review/close/rest_face.png)
    if head:
        skin |= cov & (piece == 0) & (pos[..., 2] < 1.56)
    else:
        skin |= cov & (piece == 0) & (pos[..., 2] > 1.40) & (np.abs(pos[..., 0]) < 0.09)
    eye = cov & np.isin(piece, [8,9]); mouth = cov & np.isin(piece, [17,18])
    hair = cov & (np.isin(piece,[2,5]) | ((piece == 0) & (pos[...,2] > 1.55) & ~warm)) & ~skin
    leather = cov & np.isin(piece,[1,16,19,22])
    cloth = cov & ~skin & ~eye & ~mouth & ~hair & ~leather
    masks = [('skin',skin,1),('hair',hair,2),('eye',eye,6),('mouth',mouth,7),('cloth',cloth,8),('leather',leather,8)]
    g = ao_grade(repaint_skin(base,skin),load(HERE/'work'/f'ao_{uv}.png','L'),cov,strength=.25)
    if not head:
        # the hidden legs (piece 1 above the shoes) were painted bare skin; the dress can open at the front split
        # (falls, running), so they read as dark hose: the grey underskirt colour darkened, Meshy's shading kept
        legs = cov & (piece == 1)
        f = np.clip((pos[..., 2] - 0.13) / 0.03, 0, 1)[legs][:, None]
        L = R.luminance(g[legs]); Lm = np.median(L) if L.size else 1.0
        hose = np.array([0.30, 0.30, 0.32]) * np.clip(L / max(Lm, 1e-4), 0.6, 1.4)[:, None]
        g[legs] = g[legs] * (1 - f) + hose * f
    spec=np.zeros((N,N)); rough=np.ones((N,N)); cls=np.zeros((N,N),np.uint8)
    for name,m,c in masks:
        cls[m]=c; spec[m]=SPEC[name]
        if m.any(): rough[m]=np.clip(ROUGH[name]+(rough_m[m]-np.median(rough_m[m]))*.3,.1,1)
    save(pad(g,cov),T/f'{prefix}_basecolor_1k.png')
    save(pad(normal,cov),T/f'{prefix}_normal_1k.png')
    save(np.stack([pad(spec,cov),pad(rough,cov),np.zeros((N,N))],-1),T/f'{prefix}_metal_rough_1k.png')
    Image.fromarray(cls).save(T/f'{prefix}_material_classes.png')
    reports[prefix]={name:int(m.sum()) for name,m,c in masks}
    if not head:
        tunic=cov & np.isin(piece,[0,10,11]) & (hue>58) & (hue<170) & (sat>.17) & (val>.06)
        assert tunic.sum()>10000 and skin.sum()>1000
        cloth_ramps=ramps_for(R.luminance(g[tunic]))
        R.write_mask([ndimage.gaussian_filter(pad(tunic.astype(float),cov),.7)],T/'m428_region_mask.png',size=N)
        reports[prefix]['tunic']=int(tunic.sum())
    reports[prefix]['skin_median_rgb']=np.round(np.median(g[skin],axis=0)*255).astype(int).tolist()
cfg={'variants':list(PALS),'materials':[{'base':'M428_A','prefix':'M428','mask':'m428_region_mask.png','regions':['dress'],'palettes':PALS,'ramps':cloth_ramps}]}
(T/'m428_ramps.json').write_text(json.dumps(cfg,indent=1)+'\n')
(HERE/'work/texture_classes.json').write_text(json.dumps(reports,indent=2)+'\n')
print(reports)
