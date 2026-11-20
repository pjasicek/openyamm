#!/usr/bin/env python3
"""Tier region masks and ramps for PeasantDM3 (CLAUDE_CREATURE_TEXTURES.md: one shared set, region mask + ramps).

MM9 PeasantDM3 skins: B (PEASANTDM3B, row 11 Town; THE SHARED PAINT, from the body and head retextures) a charcoal-grey
tweed tunic open over a cream linen shirt, ochre braid trims (front edges, sleeve ends, hem), a beaded collar cord, rust
trousers, dark brown hair and beard; A (PEASANTDM3A, row 12 Shopkeeper) the same cut in deep purple knit with a pale
gold ring-chain yoke and front strip and no shirt panel, brown leggings, lighter grey-brown hair. The two skins paint
nearly the same face on one head (here: one face, hair/beard recoloured). Regions:
  body  R tunic (grey knit, both tunic stripes), G trim (ochre braid, brooch: A pale gold; the beaded collar is shared),
        B shirt panel (cream on the chest front: A takes A's purple knit), A trousers (rust above the boot cuff);
  head  R hair and beard (hair part + brown shell texels; eyes out).
Ramps: tier B fitted to our paint itself (B = the accepted look); tier A's target per texel is the MM9 A region colour at
the texel's luminance quantile x the gain that maps MM9 B's region onto our paint (median linear luminance).
Writes textures/pdm3_region_mask.png, pdm3_head_region_mask.png, pdm3_ramps.json, pdm3_tier_preview_<t>.png and
pdm3_head_tier_preview_<t>.png. Usage (project folder): tiers_pdm3.py <export glb> <body graded png> <head png>"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import region_variants as RV
from headpos import texel_positions

GLB, BODY, HEAD = sys.argv[1:4]
N = 1024
W = np.array([0.2126, 0.7152, 0.0722])
LIFT = 0.6044
T = Path('textures')


def hsl(img):
    mx, mn = img.max(2), img.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return hue, sat, img @ W


def pad_soft(w, cov):
    w = ndimage.gaussian_filter(w.astype(float), 0.8) * cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return w[iy, ix]


clean = lambda m, cov: ndimage.binary_opening(ndimage.binary_closing(m, iterations=2), iterations=1) & cov

# ---- body
pos, cov = texel_positions(GLB, 'PeasantDM3', N)
base = np.asarray(Image.open(BODY).convert('RGB').resize((N, N), Image.LANCZOS), np.float64) / 255
hue, sat, _ = hsl(base)
lin = RV.srgb_to_linear(base); lum = lin @ W
Y = np.nan_to_num(pos[..., 1], nan=-1); X = np.nan_to_num(pos[..., 0]); RY = np.nan_to_num(-pos[..., 2])   # rest y (front < 0)
HEM, CUFF, BELT = 0.385, 0.30, (0.595, 0.66)
tunic_zone = cov & (Y > HEM)
warm = (hue > 15) & (hue < 65)
gold = tunic_zone & warm & (hue > 28) & (sat > 0.45) & (base.max(2) > 0.30)
beads = cov & (Y > 0.90) & (hue < 65) & (sat > 0.40) & (base.max(2) > 0.22)
trim = clean(gold, cov)          # (the beaded collar stays shared: in one ramp with the braid, B fitted at p95 21 levels)
trim = trim & ~(cov & (Y > BELT[0]) & (Y < BELT[1]) & (sat > 0.6) & (hue < 25))
cream = warm & (sat > 0.10) & (sat < 0.45) & (base.max(2) > 0.45)
panel = clean(cov & cream & (np.abs(X) < 0.10) & (Y > 0.62) & (Y < 0.98) & (RY < -0.02), cov) & ~trim
belt = cov & (Y > BELT[0]) & (Y < BELT[1]) & (np.abs(X) < 0.35) & ~trim
undersleeve = cov & cream & (np.abs(X) > 0.12)
skin = cov & (hue > 10) & (hue < 40) & (sat > 0.25) & (sat < 0.65) & (base.max(2) > 0.5)
tunic = clean(tunic_zone & ~trim & ~panel & ~belt & ~undersleeve & ~skin & (sat < 0.40) & ~(warm & (sat > 0.3)), cov)
trousers = clean(cov & (Y > CUFF) & (Y < HEM + 0.05) & ((hue < 32) | (hue > 340)) & (sat > 0.35) & ~trim & ~belt & (np.abs(X) < 0.25), cov)
masks = {'tunic': tunic, 'trim': trim, 'panel': panel, 'trousers': trousers}
WS = [pad_soft(masks[k], cov) for k in masks]
tot = np.maximum(sum(WS), 1.0); WS = [w / tot for w in WS]
RV.write_mask(WS, T / 'pdm3_region_mask.png', size=N)

# MM9 skin regions (256 px skins; rectangles read from references_hd/mm9_skin_x4_*.png)
def skin_px(tier, key):
    a = np.asarray(Image.open(f'source/mm9/skins/pdm3{tier}.png').convert('RGB'), np.float64) / 255
    h, s, l = hsl(a)
    R = {'tunic': (125, 170, 85, 195), 'trousers': (200, 255, 83, 160), 'hair': (45, 110, 0, 75)}
    if key == 'trim':
        if tier == 'b':
            m = np.zeros(a.shape[:2], bool); m[85:197, 174:189] = True; m &= (h > 25) & (h < 60) & (s > 0.35) & (a.max(2) > 0.25)
        else:
            m = np.zeros(a.shape[:2], bool); m[98:122, 0:120] = True; m[100:240, 0:14] = True; m &= (l > 0.30) & (s < 0.55)
    elif key == 'panel':
        if tier == 'b':
            m = np.zeros(a.shape[:2], bool); m[162:232, 0:15] = True; m &= (l > 0.45)
        else:
            return skin_px('a', 'tunic')
    else:
        x0, x1, y0, y1 = R[key]; m = np.zeros(a.shape[:2], bool); m[y0:y1, x0:x1] = True
    return RV.srgb_to_linear(a[m])


def fit_region(base_img, lin_img, lum_img, w, key, ramps, report, vb='pdm3_b', va='pdm3_a'):
    core = w > 0.9
    la, lb = skin_px('a', key), skin_px('b', key)
    gain = np.median(lum_img[core]) / np.median(lb @ W)
    q = np.zeros_like(lum_img); rank = np.argsort(np.argsort(lum_img[core])); q[core] = rank / max(len(rank) - 1, 1)
    def qtarget(px):
        order = np.argsort(px @ W)
        t_lin = lin_img.copy()
        idx = np.clip((q[core] * (len(order) - 1)).astype(int), 0, len(order) - 1)
        t_lin[core] = np.clip(px[order[idx]] * gain, 0, 1)
        return np.where(t_lin <= 0.0031308, t_lin * 12.92, 1.055 * np.power(np.clip(t_lin, 0, 1), 1 / 2.4) - 0.055)
    target_a = qtarget(la * (A_SCALE.get(key, 1.0)))
    # MATCH_B: our paint's braid came out lemon yellow (grade saturation x 1.15 on Codex's bright ochre); tier B takes MM9 B's
    # own ochre there, as tiers_pdm2.py's MATCH_A did for DM2's belt
    target_b = qtarget(lb) if key in MATCH_B else base_img
    fit, err = RV.fit_ramps(base_img, {vb: target_b, va: target_a}, w)
    for v in (va, vb):
        ramps[v].append(fit[v])
    report[key] = {'texels_core': int(core.sum()), 'mm9_a_px': len(la), 'mm9_b_px': len(lb), 'gain_mm9b_to_ours': round(float(gain), 3), 'fit_8bit': err}


MATCH_B = {'trim'}
# tier A's trim: MM9 A's pale ring-chain colour at 0.55 (old gold): at full brightness every ochre band of B's paint read
# as a white stripe on the sleeves and hem (MM9 A has only the gold front strip and yoke)
A_SCALE = {'trim': 0.55}
body_ramps = {'pdm3_a': [], 'pdm3_b': []}; report = {}
for key, w in zip(masks, WS):
    fit_region(base, lin, lum, w, key, body_ramps, report)

# ---- head
hpos, hcov = texel_positions(GLB, 'PeasantDM3Head', N)
hbase = np.asarray(Image.open(HEAD).convert('RGB').resize((N, N), Image.LANCZOS), np.float64) / 255
hh, hs, _ = hsl(hbase); hlin = RV.srgb_to_linear(hbase); hlum = hlin @ W
hz = np.nan_to_num(hpos[..., 1], nan=-1) - LIFT; hx = np.nan_to_num(hpos[..., 0]); hy = np.nan_to_num(-hpos[..., 2])
xc = -0.0101
eyes = (hz > 0.448) & (hz < 0.488) & (np.abs(hx - xc) > 0.008) & (np.abs(hx - xc) < 0.06) & (hy < -0.07)
hairlike = hcov & (hh > 8) & (hh < 45) & (hs > 0.30) & (hbase.max(2) < 0.62) & (hz > 0.25)
handsq = np.zeros((N, N), bool); handsq[:int(0.4 * N), int(0.8 * N):] = True          # hand squares (image top right)
hair = ndimage.binary_erosion(clean(hairlike & ~eyes & ~handsq, hcov), iterations=2) & hcov   # (no skin at the beard edge)
HW = [pad_soft(hair, hcov)]
RV.write_mask(HW, T / 'pdm3_head_region_mask.png', size=N)
head_ramps = {'pdm3_a': [], 'pdm3_b': []}
# hair: a luminance-preserving chroma shift toward MM9 A's greyer brown (the quantile target of fit_region gave tier A
# high-contrast light strands over hair and beard and a pale rim at the beard edge: the "net-like" fault)
la, lb = skin_px('a', 'hair'), skin_px('b', 'hair')
ca = np.median(la, 0) / max(np.median(la @ W), 1e-6); cb = np.median(lb, 0) / max(np.median(lb @ W), 1e-6)
ratio = ca / cb; ratio = ratio / (ratio @ W)
t_lin = np.clip(hlin * ratio, 0, 1)
target_a = np.where(t_lin <= 0.0031308, t_lin * 12.92, 1.055 * np.power(t_lin, 1 / 2.4) - 0.055)
fit, err = RV.fit_ramps(hbase, {'pdm3_b': hbase, 'pdm3_a': target_a}, HW[0])
for v in ('pdm3_a', 'pdm3_b'):
    head_ramps[v].append(fit[v])
report['hair'] = {'texels_core': int((HW[0] > 0.9).sum()), 'chroma_ratio_a_over_b': [round(float(x), 3) for x in ratio], 'fit_8bit': err}

doc = {'variants': ['pdm3_a', 'pdm3_b'],
       'materials': [{'base': 'PeasantDM3', 'prefix': 'PeasantDM3', 'mask': 'pdm3_region_mask.png', 'ramps': body_ramps},
                     {'base': 'PeasantDM3Head', 'prefix': 'PeasantDM3Head', 'mask': 'pdm3_head_region_mask.png', 'ramps': head_ramps}],
       'regions': {'PeasantDM3': ['R tunic (B charcoal tweed, A deep purple knit)', 'G trim (B ochre braid + beaded collar, A pale gold)',
                                  'B shirt panel (B cream linen, A purple knit)', 'A trousers (B rust weave, A brown)'],
                   'PeasantDM3Head': ['R hair and beard (B dark brown, A grey-brown)']},
       'source': 'MM9 PEASANTDM3A (pdm3_a: row 12 Shopkeeper), PEASANTDM3B (pdm3_b: row 11 Town, the shared paint); tiers_pdm3.py',
       'report': report}
json.dump(doc, open(T / 'pdm3_ramps.json', 'w'), indent=1)


def apply(baseimg, linimg, lumimg, ws, ramps, out):
    o = linimg.copy()
    for k, w in enumerate(ws):
        rp = ramps[k]; lo, hi = rp['range']
        tt = np.clip((lumimg - lo) / (hi - lo), 0, 1) * 15
        i0 = np.floor(tt).astype(int).clip(0, 15); i1 = (i0 + 1).clip(0, 15); f = (tt - i0)[..., None]
        C = np.array(rp['colors']); col = C[i0] * (1 - f) + C[i1] * f
        o = o * (1 - w[..., None]) + col * w[..., None]
    s = np.where(o <= 0.0031308, o * 12.92, 1.055 * np.power(np.clip(o, 0, 1), 1 / 2.4) - 0.055)
    Image.fromarray(np.uint8(np.clip(s, 0, 1) * 255)).save(out)


for v in ('pdm3_a', 'pdm3_b'):
    apply(base, lin, lum, WS, body_ramps[v], T / f'pdm3_tier_preview_{v}.png')
    apply(hbase, hlin, hlum, HW, head_ramps[v], T / f'pdm3_head_tier_preview_{v}.png')
print('TIERS', json.dumps({k: {'core': r['texels_core'], 'fit': r['fit_8bit']} for k, r in report.items()}))
