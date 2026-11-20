"""Compose native Swordsman colour ramps, material maps and dedicated head textures."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R

T = HERE / 'textures'; T.mkdir(exist_ok=True)
NAT = HERE.parent / 'mm6_nobl' / 'native_variants'
N = 1024
ALBEDO = 1.0
AO_STRENGTH, AO_FLOOR = 0.5, 0.3
# per class: (specular mask, roughness); skin gets a soft sheen like the sprites' oiled skin, metal a tight glint
SURFACE = {'skin': (.3,.6), 'hair': (.2,.65), 'leather': (.3,.65), 'silver': (.75,.35),
           'gold': (.85,.3), 'cloth': (.05,.9), 'other': (.2,.7)}
RAMP_GAIN = 1.3
PALS = {'nobl_a':777,'nobl_b':778,'nobl_c':779}
TARGET = {'skin':(178,139,116),'hair':(135,135,129),'gold':(183,145,62),'silver':(160,164,160)}



def load(path, mode='RGB'):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((N, N), Image.LANCZOS) if im.size != (N, N) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    return np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255


M = HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png')
rough = load(M / 'texture_urls_0_roughness.png', 'L')
normal = load(M / 'texture_urls_0_normal.png')
normal[...,1]=1-normal[...,1]  # Meshy +Y-down to Blender/glTF +Y-up.
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz')
piece, pos = Rz['piece'], Rz['pos']
H = hsv(base); hue, sat, val = H[..., 0] * 360, H[..., 1], H[..., 2]
cov = piece >= 0
yellow=(hue>32)&(hue<65)&(sat>.3)&(val>.35)
red=((hue<25)|(hue>340))&(sat>.4)&(val>.2)
collar=(piece==0)&(pos[...,2]>1.40)&(np.abs(pos[...,0])<.135)&(((hue<55)|(hue>315))&(sat>.25))
cls={}
cls['gold']=cov & yellow & (np.isin(piece,[6,7,18,19,20,21])|collar)
cls['silver']=cov & ~cls['gold'] & ((np.isin(piece,[6,7])&~red)|np.isin(piece,[19,20,21,28,*range(31,109),111,115]))
cls['hair']=cov & np.isin(piece,[3,12,15,16,17,24,25,26,27,116])
cls['skin']=cov & (piece==1)&(pos[...,2]>1.45)
cls['leather']=cov & np.isin(piece,[4,5,10,11,13,14,29,30,110])
cloak=cov & (piece==0)&~collar
tunic=cov & ((piece==9)|((piece==1)&(np.abs(pos[...,0])<.23)&(pos[...,2]>.90)&(pos[...,2]<1.42)))
tunic &= ~yellow & ~((piece==9)&(pos[...,2]>.92)&(hue>=12)&(hue<=65))
cls['cloth']=cov & (cloak|tunic|np.isin(piece,[1,2])) & ~cls['skin']
cls['other']=cov & ~np.any(list(cls.values()),axis=0)
assert np.max(np.sum(list(cls.values()),axis=0))==1
print('CLASSES texels', {k: int(v.sum()) for k, v in cls.items()})

graded = base.copy()
for k, tgt in TARGET.items():
    m = cls[k]
    if not m.any():continue
    med = np.median(base[m], 0)
    gain = np.array(tgt) / 255 * ALBEDO / np.maximum(med, 1e-3)
    graded[m] = base[m] * gain
    print('GRADE', k, 'median', np.round(med * 255).astype(int), '-> gain', np.round(gain, 2))
# The broad waist shell includes a red cast from Meshy's shirt paint; restore its invariant brown leather.
waist=cls['leather']&(piece==11)
if waist.any():
 luminance=base[waist]@np.array([.2126,.7152,.0722])
 graded[waist]=(np.array([78,51,32])/255)*(luminance/np.median(luminance))[:,None]
ao = load(HERE / 'work' / 'ao_body.png', 'L')
graded *= (1 - AO_STRENGTH * (1 - np.maximum(ao, AO_FLOOR)))[..., None]
graded = np.clip(graded, 0, 1)
# Keep cloth folds and normal detail while suppressing the albedo speckles amplified by native ramps.
for m in [cloak,tunic]:
 weight=ndimage.gaussian_filter(m.astype(float),1.2)
 for c in range(3):
  sm=ndimage.gaussian_filter(graded[...,c]*m,1.2)/np.maximum(weight,1e-8)
  graded[...,c][m]=sm[m]


def surface_maps(classes, meshy_rough, shape):
    """R specular mask and G roughness per class (Meshy's roughness detail kept around the class value); texels
    outside every class take the nearest class's values so mips do not blend in other values."""
    spec, rgh, known = np.zeros(shape), np.zeros(shape), np.zeros(shape, bool)
    for k, m in classes.items():
        if not m.any():
            continue
        sm, rv = SURFACE[k]
        spec[m] = sm
        rgh[m] = np.clip(rv + 0.5 * (meshy_rough[m] - np.median(meshy_rough[m])), 0.2, 1.0)
        known |= m
    idx = ndimage.distance_transform_edt(~known, return_distances=False, return_indices=True)
    return spec[tuple(idx)], rgh[tuple(idx)]

# ---------------------------------------------------------------- regions and ramps
idx=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
weights=[ndimage.gaussian_filter(m[tuple(idx)].astype(float),.7) for m in [cloak,tunic]]
R.write_mask(weights,T/'nobl_region_mask.png',size=N)
cols = {k: [] for k in PALS}; groups = []
for v in range(5):
    ims = {k: np.asarray(Image.open(NAT / f'noblsta{v}_{p}.png').convert('RGBA'), np.float64) / 255 for k, p in PALS.items()}
    a = ims['nobl_a']; al = a[..., 3] > 0.5
    d = np.maximum(np.abs(ims['nobl_b'][..., :3] - a[..., :3]).max(-1), np.abs(ims['nobl_c'][..., :3] - a[..., :3]).max(-1))
    ch = al & (d > 8 / 255)
    b = ims['nobl_b'][..., :3]
    g = np.where(a[..., 1] >= a[..., 0]*.95, 0, 1)[ch]                              # tier B: blue = armour, red = leather
    groups.append(g)
    for k in PALS:
        cols[k].append(ims[k][..., :3][ch])
groups = np.concatenate(groups); cols = {k: np.concatenate(v) for k, v in cols.items()}
LUMA = np.array([0.2126, 0.7152, 0.0722])
qs = np.linspace(0.03, 0.97, 16)
ramps = {k: [] for k in PALS}
report = {}
for ri, (name, m_tex) in enumerate((('cloak', cloak), ('tunic', tunic))):
    # native pixels of this region, without the sprite's near-black outline/antialias pixels
    sel = (groups == ri) & (cols['nobl_a'].max(1) > 0.06)
    assert sel.sum()>1000,(name,int(sel.sum()))
    lin_a = R.srgb_to_linear(cols['nobl_a'][sel]); order = np.argsort(lin_a @ LUMA)
    lum = np.sort(R.luminance(graded)[m_tex])
    lo, hi = np.percentile(lum, [2, 98])
    for k in PALS:
        lin = R.srgb_to_linear(cols[k][sel])[order]
        stops = []
        for i in range(16):
            # rank matching: the stop at luminance lo + t (hi - lo) takes the native colour at the same quantile that
            # luminance has among the region's texels (a linear t-to-quantile map left most texels on the dark stops)
            q = np.searchsorted(lum, lo + i / 15 * (hi - lo)) / len(lum)
            q = min(max(q, 0.02), 0.98)
            c = int(q * (len(lin) - 1)); w = max(4, len(lin) // 40)
            stops.append(np.clip(np.median(lin[max(0, c - w):c + w], 0) * RAMP_GAIN, 0, 1))
        ramps[k].append({'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': [[round(float(x), 6) for x in s] for s in stops]})
    report[name] = {'native_pixels': int(sel.sum()), 'texels': int(m_tex.sum()), 'range': [float(lo), float(hi)]}
print('RAMPS', report)

# ---------------------------------------------------------------- sword swatches in free texels (6 px clear)
occ = ndimage.binary_dilation(cov, iterations=6)
SW = {'blade': (205, 212, 220), 'edge': (240, 244, 248), 'gold': (214, 160, 40), 'gold_dark': (150, 100, 20),
      'grip': (32, 65, 125), 'gem': (30, 20, 40)}
swatches, r_px, swatch_rects = {}, 5, []
y, x = N - 10, N - 10
for name, rgb in SW.items():
    while occ[y - r_px:y + r_px, x - r_px:x + r_px].any():
        x -= 4
        if x < 12:
            x, y = N - 10, y - 4
    graded[y - r_px:y + r_px, x - r_px:x + r_px] = np.array(rgb) / 255
    metal = name in ('blade', 'edge', 'gold', 'gold_dark', 'gem')
    rough[y - r_px:y + r_px, x - r_px:x + r_px] = 0.35 if metal else 0.8
    swatch_rects.append((slice(y - r_px, y + r_px), slice(x - r_px, x + r_px), 1.0 if metal else 0.3))
    normal[y - r_px:y + r_px, x - r_px:x + r_px] = (0.5, 0.5, 1.0)
    occ[y - r_px - 3:y + r_px + 3, x - r_px - 3:x + r_px + 3] = True
    swatches[name] = [(x + 0.5) / N, 1 - (y + 0.5) / N, (r_px - 2) / N]
(T / 'nobl_sword_swatches.json').write_text(json.dumps(swatches, indent=1) + '\n')
# Sword swatches are invariant across all three native tiers.
for ys,xs,sm in swatch_rects:
 for weight in weights:weight[max(0,ys.start-3):min(N,ys.stop+3),max(0,xs.start-3):min(N,xs.stop+3)]=0
R.write_mask(weights,T/'nobl_region_mask.png',size=N)
assert all(not w[ys,xs].any() for ys,xs,sm in swatch_rects for w in weights)
# ---------------------------------------------------------------- write the body set
save(graded, T / 'nobl_basecolor_1k.png'); save(normal, T / 'nobl_normal_1k.png')
spec_r, rough_g = surface_maps({k: cls[k] for k in SURFACE}, rough, (N, N))
for ys, xs, sm in swatch_rects:                                     # the sword's swatches keep their own surface
    spec_r[ys, xs] = sm; rough_g[ys, xs] = rough[ys, xs]
save(np.stack([spec_r, rough_g, np.zeros_like(rough)], -1), T / 'nobl_metal_rough_1k.png')
cmap = np.zeros((N, N), np.uint8)
for k, lab in (('skin',1),('hair',2),('leather',8),('silver',9),('gold',9),('cloth',11),('other',11)):
    cmap[cls[k]] = lab
Image.fromarray(cmap).save(T / 'nobl_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Swordsman_A', 'prefix': 'Swordsman', 'mask': 'nobl_region_mask.png', 'regions': ['cloak', 'tunic'],
                      'palettes': PALS, 'ramps': ramps, 'report': report}]}
# ---------------------------------------------------------------- head set (optional)
HM = HERE / 'meshy' / 'head_retexture_v2'
if (HM / 'texture_urls_0_base_color.png').exists():
    hb = load(HM / 'texture_urls_0_base_color.png'); Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
    hp = Rh['piece']; HH = hsv(hb)
    hh, hs_, hv = HH[..., 0] * 360, HH[..., 1], HH[..., 2]
    # skin tones only: Meshy also painted hair onto the scalp (hidden under the hair shell; very saturated dark red)
    hskin = (hp == 1) & (hh > 8) & (hh < 40) & (hs_ > 0.15) & (hs_ < 0.7) & (hv > 0.3)
    print('HEAD skin median', np.round(np.median(hb[hskin], 0) * 255).astype(int))
    hgold = np.zeros_like(hskin)
    hhair=(hp>=0)&np.isin(hp,[3,12,15,16,17,24,25,26,27,116])
    hg = hb.copy()
    # the head skin is matched to the GRADED body skin at the neck seam (same ramps-free class, one gain)
    body_neck = cls['skin'] & (pos[..., 2] > 1.36)
    tgt = np.median(graded[body_neck], 0) if body_neck.any() else np.array(TARGET['skin']) / 255 * ALBEDO
    # The standing collar covers the neck seam; retain the dedicated face reference's skin colour.
    gain = np.ones(3)
    face = (hp == 1)                                               # one gain over the whole face/scalp shell (no seams)
    hg[face] = hb[face] * gain
    print('HEAD gain', np.round(gain, 2), 'target', np.round(tgt * 255).astype(int))
    if hgold.any():
        hg[hgold] = hb[hgold] * (np.array(TARGET['gold']) / 255 * ALBEDO / np.maximum(np.median(hb[hgold], 0), 1e-3))
    hg[hhair]=hb[hhair]*(np.array(TARGET['hair'])/255/np.maximum(np.median(hb[hhair],0),1e-3))
    save(np.clip(hg, 0, 1), T / 'nobl_head_basecolor_1k.png')
    hn=load(HM/'texture_urls_0_normal.png');hn[...,1]=1-hn[...,1]
    save(hn,T/'nobl_head_normal_1k.png')
    hr = load(HM / 'texture_urls_0_roughness.png', 'L')
    hother = (hp >= 0) & ~hskin & ~hgold & ~hhair
    hspec, hrough = surface_maps({'skin': hskin, 'hair': hhair, 'gold': hgold, 'other': hother}, hr, (N, N))
    save(np.stack([hspec, hrough, np.zeros_like(hr)], -1), T / 'nobl_head_metal_rough_1k.png')
    hc=np.zeros((N,N),np.uint8);hc[hskin]=1;hc[hhair]=2;hc[hother]=11
    Image.fromarray(hc).save(T/'nobl_head_material_classes.png')
    R.write_mask([np.zeros((N, N)), np.zeros((N, N))], T / 'nobl_head_region_mask.png', size=N)
    cfg['materials'].append({'base': 'SwordsmanHead_A', 'prefix': 'SwordsmanHead', 'mask': 'nobl_head_region_mask.png',
                             'regions': ['cloak', 'tunic'], 'palettes': PALS, 'ramps': ramps})
    print('HEAD graded: skin texels', int(hskin.sum()), 'gold', int(hgold.sum()))
(T / 'nobl_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
