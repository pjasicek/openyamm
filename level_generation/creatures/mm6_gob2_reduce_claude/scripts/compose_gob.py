#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the 55 % goblin retexture (copy of mm6_gob2_claude/scripts/compose_gob2.py;
user 2026-10-13: fix the teeth and shin-guard spikes, regenerate textures). Added: the rebuilt teeth and shin spikes
are painted ivory, ivory smears on the greave plates are filled from the plate around them, the mouth interior is
dark, no sword swatches (the sword is its own GLB).
Original notes (CLAUDE_CREATURE_TEXTURES.md):

Tiers (palettes 745 Goblin / 746 Goblin Shaman / 747 Goblin King) recolour the SKIN only: one region (R), shared by
the body and the head set, so neck and face take the same colours in every tier.
- Body set (retexture_v1, Meshy's own layout, 2K -> 1K) with texel classes from the UV raster (piece, rest position)
  and colour: skin = pieces 0-2 (body skin and the foot/shin shells) in olive hues; claws = light yellow texels on
  those pieces (kept, like the native gold claws); leather, iron and gold are left as Meshy painted them, with a mild
  saturation lift on leather (Meshy desaturates).
- Head set (head_retexture_v1, HeadUV): skin = piece 0 in olive or brown (ears) hues, minus the painted eyes (near the
  removed eye shells) and light yellow texels (teeth, hoops are their own pieces and stay out); its luminance is
  matched to the body skin at the neck with one gain (a per-channel match overcorrected the first goblin's ears).
- Ramps per tier: native standing frames (gobsta0-4, palette 745) are mapped back to palette indices; the skin
  entries are those that differ between 745 and 747 (747 changes only the skin). Each tier's 16 stops are rank-matched
  to the luminance distribution of the skin texels (body + head) and scaled by RAMP_GAIN (sprites carry baked shading).
- Sword swatches (blade, edge, gold, gold_dark, grip, gem) are painted into free body-atlas texels.
Writes textures/gob2_* (base colour, normal, ORM with R=255, region masks, material classes, ramps json).
Args: none"""
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
FRAMES = HERE.parent / 'mm6_goblin' / 'stage1_20261006' / 'source' / 'frames'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm6' / 'textures'
N = 1024
RAMP_GAIN = 1.2
PALS = {'gob2_a': 745, 'gob2_b': 746, 'gob2_c': 747}
EYES = [np.array([0.044, -0.12, 1.508]), np.array([-0.059, -0.119, 1.508])]   # removed eye shells P25/P26 (rest pos)


def load(path, mode='RGB'):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((N, N), Image.LANCZOS) if im.size != (N, N) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def palette(n):
    return np.frombuffer((PALDIR / f'pal{n}.act').read_bytes()[:768], np.uint8).reshape(256, 3).astype(np.float64) / 255


def linear_to_srgb(x):
    x = np.asarray(x, np.float64)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


def pad(img, cov):
    """Texels outside the islands take the nearest island colour (mips must not bleed Meshy's padding)."""
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]
    return out


# ---------------------------------------------------------------- installed maps (user review: keep its definition)
import io  # noqa: E402
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb  # noqa: E402
_doc, _bin = read_glb(HERE.parents[2] / 'assets_source' / 'worlds' / 'mm6' / 'models' / 'mm6_gob2.glb')


def _image(tex):
    v = _doc['bufferViews'][_doc['images'][_doc['textures'][tex]['source']]['bufferView']]; o = v.get('byteOffset', 0)
    return np.asarray(Image.open(io.BytesIO(_bin[o:o + v['byteLength']])).convert('RGB'), np.float64) / 255


_m = _doc['materials'][0]
OLD_C = _image(_m['pbrMetallicRoughness']['baseColorTexture']['index'])
OLD_N = _image(_m['normalTexture']['index'])                           # glTF convention (prepared)
OLD_MASK = _image(_m['extras']['openyamm_region_mask']['index'])[..., :1]   # skin region (R)


def sample(img, uv):
    h, w = img.shape[:2]; x = np.clip(uv[:, 0] * w - .5, 0, w - 1); y = np.clip((1 - uv[:, 1]) * h - .5, 0, h - 1)
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=1, mode='nearest') for c in range(img.shape[2])], -1)


def masked_blur(L, m, sigma):
    return ndimage.gaussian_filter(L * m, sigma) / np.maximum(ndimage.gaussian_filter(m.astype(float), sigma), 1e-4)


DETAIL_SIGMA = 5.0
_oL = OLD_C @ np.array([.2126, .7152, .0722])
OLD_DETAIL = (np.log(_oL + 0.02) - np.log(ndimage.gaussian_filter(_oL, DETAIL_SIGMA) + 0.02))[..., None]

# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'body_retexture_r55'
base = load(M / 'texture_urls_0_base_color.png')
rough = load(M / 'texture_urls_0_roughness.png', 'L')
normal = load(M / 'texture_urls_0_normal.png')
Rz = np.load(HERE / 'work' / 'uvraster_body.npz'); piece = Rz['piece']
cov = piece >= 0
hue, sat, val = hsv(base)
skinp = np.isin(piece, [0, 1, 2])
# claws by position (a colour rule alone took 75k skin highlights): within 4 cm of a fingertip (finger_joints.json
# tips) or on the toes (foot shells below 6 cm, front half), and light yellow
FJ = json.load(open(HERE.parent / 'mm6_gob2_claude' / 'work' / 'finger_joints.json'))
tips = [np.array(v) for sd in FJ.values() for n, v in sd.items() if n.endswith('_tip')]
pos = Rz['pos']
near_tip = np.zeros_like(cov)
for t_ in tips:
    near_tip |= np.linalg.norm(pos - t_, axis=-1) < 0.04
toes = np.isin(piece, [1, 2]) & (pos[..., 2] < 0.06) & (pos[..., 1] < -0.05)
claw = skinp & (near_tip | toes) & (hue > 20) & (hue < 62) & (val > 0.5) & (sat > 0.25)
# the belly skin right behind the belt buckle carries a sliver of the buckle's yellow (retexture projection): kept as
# painted, or tiers B/C turn it into a bright red/blue rim on the buckle
box = (np.abs(pos[..., 0]) < 0.1) & (pos[..., 1] < -0.08) & (pos[..., 2] > 0.85) & (pos[..., 2] < 1.0)
buckle = skinp & box & (hue > 35) & (hue < 58) & (val > 0.6) & (sat > 0.3)
buckle = ndimage.binary_dilation(buckle, iterations=2) & skinp & box
skin = skinp & ~claw & ~buckle                   # pieces 0-2 carry only skin, claws and the buckle sliver
leather = cov & (hue > 10) & (hue < 40) & (sat > 0.4) & (val < 0.55) & ~skinp
graded = base.copy()
# leather: Meshy desaturated the native's saturated brown (first goblin: H25 S0.69); lift saturation 1.2x
lum = graded[leather].mean(1, keepdims=True)
graded[leather] = np.clip(lum + (graded[leather] - lum) * 1.2, 0, 1)
# rebuilt shin spikes: clean ivory (they had smeared onto the greaves); ivory smears left on the greave plates (14/15)
# are filled from the nearest clean plate texel
SPIKES, PLATES, TEETH = [37, 62, 50, 59], [14, 15], [60, 61, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 78]


def ivory(img, m, tint=(1.0, 0.94, 0.76)):
    if not m.any():
        return
    lum = R.luminance(img[m])
    img[m] = np.clip((0.72 + 0.25 * np.sqrt(np.clip(lum, 0, 1)))[:, None] * np.array(tint), 0, 1)


spike = np.isin(piece, SPIKES)
plate = np.isin(piece, PLATES)
# the greaves are grey iron: any warm, saturated texel on them is spike paint (dilated 2 px inside the plate)
smear = plate & (hue > 15) & (hue < 75) & (val > 0.35) & (sat > 0.12)
smear = ndimage.binary_dilation(smear, iterations=2) & plate
if smear.any():
    _, (sy, sx) = ndimage.distance_transform_edt(~(plate & ~smear), return_indices=True)
    graded[smear] = graded[sy[smear], sx[smear]]
ivory(graded, spike, (1.0, 0.84, 0.5))            # gold-ivory like the goblin's other spikes and claws
# the new Meshy albedo carries softer painted definition than the installed one (abs, pecs, arm lines): keep the new
# colour and broad tone, take the installed detail band (5 px) at the same 3D point; the installed normal map is
# carried into the new tangent frames. Rebuilt spikes keep their own paint.
LB = np.load(HERE / 'work' / 'installed_lookup_body.npz')
tr = cov & (LB['uv'][..., 0] >= 0) & ~spike
uvb = LB['uv'][tr]
d_old = sample(OLD_DETAIL, uvb)[:, 0]          # applied after the skin store (both maps' skin is stored alike)
on = sample(OLD_N, uvb) * 2 - 1
obj = LB['t_old'][tr] * on[:, :1] + LB['b_old'][tr] * on[:, 1:2] + LB['n_old'][tr] * on[:, 2:]
tn, bn, nn_ = (LB[k][tr] / np.maximum(np.linalg.norm(LB[k][tr], axis=1, keepdims=True), 1e-6) for k in ('t_new', 'b_new', 'n_new'))
ts = np.stack([(obj * tn).sum(1), (obj * bn).sum(1), (obj * nn_).sum(1)], 1)
ts /= np.maximum(np.linalg.norm(ts, axis=1, keepdims=True), 1e-6)
ts[:, 2] = np.abs(ts[:, 2])
normal_gltf = np.zeros_like(normal) + np.array([.5, .5, 1.])
normal_gltf[tr] = ts * 0.5 + 0.5
BODY_NORMAL_GLTF = True
print('CLASSES texels', {'spike': int(spike.sum()), 'plate_smear_filled': int(smear.sum()), 'skin': int(skin.sum()), 'claw': int(claw.sum()), 'buckle': int(buckle.sum()), 'leather': int(leather.sum()), 'covered': int(cov.sum())})

# ---------------------------------------------------------------- head set
HM = HERE / 'meshy' / 'head_retexture_r55'
hb = load(HM / 'texture_urls_0_base_color.png'); Rh = np.load(HERE / 'work' / 'uvraster_head.npz')
hp, hpos = Rh['piece'], Rh['pos']; hcov = hp >= 0
hh, hs_, hv = hsv(hb)
# only the eye itself stays out of the skin ramp: yellow iris, white and pupil within 2.4 cm of the eye centre (a 3 cm
# sphere of raw texels left pale/dark facets on the brow and nose bridge where its edge cut across the skin)
near_eye = np.zeros_like(hcov)
for e in EYES:
    near_eye |= np.linalg.norm(hpos - e, axis=-1) < 0.024
eye = near_eye & (((hh > 28) & (hh < 62) & (hv > 0.42) & (hs_ > 0.33)) | (hv < 0.12) | ((hs_ < 0.16) & (hv > 0.62)))
eye = ndimage.binary_dilation(eye, iterations=1) & near_eye
hyellow = (hh > 25) & (hh < 60) & (hv > 0.58) & (hs_ > 0.35)
# all of it (yellow included: the eye mask already holds the irises; yellow nose speckles left out stayed orange on
# B/C): pale/grey skin left out stayed as grey streaks in B/C
hskin = (hp == 0) & ~eye
# one luminance gain over the head skin so the face meets the body skin at the neck (ramps then colour both alike)
Rb = Rz['pos']
neck_b = skin & (Rb[..., 2] > 1.25) & (Rb[..., 2] < 1.40)
neck_h = hskin & (hpos[..., 2] < 1.40)
lb, lh = np.median(R.luminance((base[neck_b]))), np.median(R.luminance((hb[neck_h])))
hgain = float((lb / max(lh, 1e-4)) ** (1 / 2.2))
hg = hb.copy(); hg[hp == 0] = np.clip(hb[hp == 0] * hgain, 0, 1)
teeth = np.isin(hp, TEETH)
# goblin teeth: dirty yellowed ivory, dark at the gum and light at the tip, one tone for both rows (user review); the
# lower row faces up into the light, so it is painted 18 % darker to read like the shaded upper row
for t_ in TEETH:
    m = hp == t_
    if not m.any():
        continue
    z = hpos[m][:, 2]; upper = z.mean() > 1.41
    tip_t = (z.max() - z) / max(np.ptp(z), 1e-4) if upper else (z - z.min()) / max(np.ptp(z), 1e-4)
    root, tipc = np.array([0.36, 0.27, 0.13]), np.array([0.86, 0.76, 0.5])
    col = root + (tipc - root) * (np.clip(tip_t, 0, 1) ** 0.7)[:, None]
    col *= (0.92 + 0.16 * R.luminance(hb[m]) / max(float(R.luminance(hb[m]).mean()), 1e-3))[:, None]
    hg[m] = np.clip(col * (1.0 if upper else 0.82), 0, 1)
# the mouth interior (skin behind the lips, between the tooth rows, not facing forward) is dark: Meshy painted it pale
hn = Rh['normal']
mouth = (hp == 0) & (np.abs(hpos[..., 0] + 0.012) < 0.05) & (hpos[..., 1] > -0.17) & (hpos[..., 1] < -0.09) \
    & (hpos[..., 2] > 1.388) & (hpos[..., 2] < 1.432) & (hn[..., 1] > -0.35)
mouth_c = np.array([0.16, 0.05, 0.045])
hg[mouth] = mouth_c * (0.75 + 0.5 * R.luminance(hb[mouth]) / max(float(R.luminance(hb[mouth]).mean()), 1e-3))[:, None] if mouth.any() else hg[mouth]
hg[mouth] = np.clip(hg[mouth], 0, 1)
# the gum under the teeth (red-pink lip lining in the mouth box, facing forward) stays as dark gum
mouthbox = (hp == 0) & (np.abs(hpos[..., 0] + 0.012) < 0.055) & (hpos[..., 1] > -0.18) & (hpos[..., 1] < -0.09) \
    & (hpos[..., 2] > 1.38) & (hpos[..., 2] < 1.44)
from scipy.spatial import cKDTree  # noqa: E402
_tooth_pts = hpos[teeth]
near_teeth = np.zeros_like(hcov)
if len(_tooth_pts):
    _d, _ = cKDTree(_tooth_pts[::4]).query(hpos[mouthbox]); near_teeth[mouthbox] = _d < 0.008
gum = mouthbox & ~mouth & near_teeth & ((hh < 25) | (hh > 320)) & (hs_ > 0.2)
if gum.any():
    gl = R.luminance(hb[gum]); hg[gum] = np.clip(np.array([0.19, 0.055, 0.045]) * (0.75 + 0.5 * gl / max(float(gl.mean()), 1e-3))[:, None], 0, 1)
hskin &= ~mouth & ~teeth & ~gum
print('HEAD gum texels', int(gum.sum()))
print('HEAD teeth texels', int(teeth.sum()), 'mouth interior', int(mouth.sum()))
# UV islands of the face that Meshy painted in another tone than the skin around them (pale/dark facets beside the
# eyes): each island's mean skin colour is compared with the skin of the other islands next to it in 3D (30 nearest
# texels, other islands only); an island off by more than 10 % is shifted per channel to its neighbours' tone, keeping
# its own detail
lab, nlab = ndimage.label(hcov)
sk_idx = np.argwhere(hskin); sk_lab = lab[hskin]; sk_pos = hpos[hskin]; sk_col = hg[hskin]
tree = cKDTree(sk_pos); fixed = 0; rng = np.random.default_rng(0)
for isl in np.unique(sk_lab):
    sel = np.flatnonzero(sk_lab == isl)
    if len(sel) > 20000:
        continue
    pick = sel if len(sel) <= 200 else rng.choice(sel, 200, replace=False)
    _, nb = tree.query(sk_pos[pick], k=40)
    nb = nb[sk_lab[nb] != isl]
    if len(nb) < 20:
        continue
    own, around = sk_col[sel].mean(0), sk_col[nb].mean(0)
    ratio = np.clip(around / np.maximum(own, 1e-3), 0.6, 1.6)
    if abs(float(R.luminance(around[None])[0] / max(float(R.luminance(own[None])[0]), 1e-4)) - 1) > 0.10:
        ys, xs = sk_idx[sel].T
        hg[ys, xs] = np.clip(hg[ys, xs] * ratio, 0, 1); fixed += 1
print('HEAD islands', nlab, 'tone-matched', fixed)
print('HEAD skin texels', int(hskin.sum()), 'eye', int(eye.sum()), 'neck luminance body/head', round(float(lb), 4),
      round(float(lh), 4), '-> gain', round(hgain, 3))

# ---------------------------------------------------------------- ramps
# Tier A keeps Meshy's own skin colour per luminance (graded toward the native olive); B and C are the palette
# transfer of A (least-squares affine map from the 745 skin entries to 746 / 747), as on the accepted first goblin.
# Rank-matching the native pixels instead copied the sprites' baked near-black shadows into the ramp (black cheeks,
# mottled skin).
pals = {k: palette(n) for k, n in PALS.items()}
_h, _s, _ = hsv(pals['gob2_a'][None])
skin_idx = np.where((np.abs(pals['gob2_a'] - pals['gob2_c']).sum(1) > 0.06) & (_h[0] > 40) & (_h[0] < 110) & (_s[0] > 0.15))[0]
src = pals['gob2_a'][skin_idx]
MAPS = {k: np.linalg.lstsq(np.c_[src, np.ones(len(src))], pals[k][skin_idx], rcond=None)[0] for k in PALS}
lut = {tuple((pals['gob2_a'][i] * 255).round().astype(int)): i for i in range(256)}
idx = []
for v in range(5):
    im = np.asarray(Image.open(FRAMES / f'gobsta{v}.png').convert('RGBA'))
    idx += [lut.get(tuple(int(c) for c in p), -1) for p in im[im[..., 3] > 128][:, :3]]
idx = np.array(idx); sel = idx[np.isin(idx, skin_idx)]
nh, ns, nv = hsv(np.median(pals['gob2_a'][sel], 0)[None, None])
print('SKIN palette entries', len(skin_idx), 'native skin median HSV', round(float(nh[0, 0])), round(float(ns[0, 0]), 2),
      round(float(nv[0, 0]), 2))
# log-luminance store (spreads the heavy-tailed skin luminance over the 16 stops; hue kept for the soft mask edge)
LO, HI = 0.01, 0.30
lb_ = R.luminance(graded[skin]); lh_ = R.luminance(hg[hskin])
allL = np.sort(np.r_[lb_, lh_]); allC = np.r_[graded[skin], hg[hskin]]
l1, l99 = np.log(np.percentile(allL, [1, 99]))
tof = lambda L: np.clip((np.log(np.maximum(L, 1e-5)) - l1) / (l99 - l1), 0, 1)
allT = tof(np.r_[lb_, lh_])


def store(img, m, L):
    tgt = LO + tof(L) * (HI - LO)
    lin = R.srgb_to_linear(img[m]) * (tgt / np.maximum(L, 1e-5))[:, None]
    img[m] = np.clip(linear_to_srgb(np.clip(lin, 0, 1)), 0, 1)


th, ts_, _ = hsv(np.median(allC, 0)[None, None]); th, ts_ = float(th[0, 0]), float(ts_[0, 0])
# in game a 60 % grade read dull olive against the grass (first goblin, revision 8: as flat as the grass): full hue and
# saturation shift to the native skin median, and the stops' value spread around the median raised 1.4x (form contrast)
HUE_SHIFT = float(nh[0, 0]) - th; SAT_GAIN = float(ns[0, 0]) / ts_; CONTRAST = 1.4
v_med = float(hsv(np.median(allC, 0)[None, None])[2][0, 0])
a_stops = []
for i in range(16):
    m = np.abs(allT - i / 15) < 0.5 / 15
    c = np.median(allC[m], 0) if m.sum() > 20 else (a_stops[-1] if a_stops else np.median(allC, 0))
    h_, s2, v_ = (x[0, 0] for x in hsv(c[None, None]))
    v_ = v_med * (max(v_, 1e-3) / v_med) ** CONTRAST
    rgb = np.asarray(Image.fromarray(np.uint8(np.clip([[[(h_ + HUE_SHIFT) % 360 / 360, min(s2 * SAT_GAIN, 1), v_]]], 0, 1) * 255),
                                     'HSV').convert('RGB'), np.float64)[0, 0] / 255
    a_stops.append(rgb)
store(graded, skin, lb_); store(hg, hskin, lh_)
nL = graded @ np.array([.2126, .7152, .0722])
new_detail = np.log(nL + 0.02) - np.log(masked_blur(nL, cov, DETAIL_SIGMA) + 0.02)
graded[tr] = np.clip(graded[tr] * np.exp(d_old - new_detail[tr])[:, None], 0, 1)
# skin: the tier ramps colour skin by luminance alone, and the installed skin luminance carries the painted muscle
# definition (wide groove lines the 5 px band misses): where both are skin, the new skin takes the installed stored
# luminance (hue kept for the soft mask edge)
both = np.zeros_like(cov); both[tr] = sample(OLD_MASK, uvb)[:, 0] > 0.6
both &= skin
lo_new = graded[both] @ np.array([.2126, .7152, .0722]); lo_old = sample(OLD_C, LB['uv'][both]) @ np.array([.2126, .7152, .0722])
graded[both] = np.clip(graded[both] * (lo_old / np.maximum(lo_new, 1e-3))[:, None], 0, 1)
print('SKIN luminance from the installed texture', int(both.sum()), 'of', int(skin.sum()))
# head skin keeps its new detail but takes the installed face's luminance distribution (quantile match), so the
# installed ramps colour it like the installed face (the new face's stored range reached their bright top stops:
# pale/yellow blotches)
LH = np.load(HERE / 'work' / 'installed_lookup_head.npz')
hok = hskin & (LH['uv'][..., 0] >= 0)
old_face = sample(OLD_MASK, LH['uv'][hok])[:, 0] > 0.6
Lo = np.sort(sample(OLD_C, LH['uv'][hok][old_face]) @ np.array([.2126, .7152, .0722]))
Ln = hg[hok] @ np.array([.2126, .7152, .0722])
rank = np.argsort(np.argsort(Ln)) / max(len(Ln) - 1, 1)
target = np.interp(rank, np.linspace(0, 1, len(Lo)), Lo)
hg[hok] = np.clip(hg[hok] * (target / np.maximum(Ln, 1e-3))[:, None], 0, 1)
print('SKIN head luminance matched to the installed face', int(hok.sum()), 'median', round(float(np.median(Ln)), 3), '->', round(float(np.median(target)), 3))
print('DETAIL body texels', int(tr.sum()), 'installed detail std', round(float(d_old.std()), 4), 'new', round(float(new_detail[tr].std()), 4))
lo, hi = LO, HI
ramps = {}
for k in PALS:
    cols = [np.clip(np.r_[c, 1] @ MAPS[k], 0, 1) for c in a_stops]
    ramps[k] = [{'range': [lo, hi], 'colors': [[round(float(x), 6) for x in R.srgb_to_linear(c)] for c in cols]}]
print('GRADE A skin: texture median hue', round(th), 'sat', round(ts_, 2), '-> hue shift', round(HUE_SHIFT, 1), 'sat gain', round(SAT_GAIN, 2))
# the body skin carries the installed skin luminance (above), so it keeps the installed tier ramps: ramps rebuilt from
# the softer Meshy skin spanned 0.02-0.19 linear luminance against the installed 0.01-0.82 and flattened the muscle
# definition (user review)
for k in PALS:
    ramps[k] = next(m['extras']['openyamm_region_ramps'] for m in _doc['materials'] if m['name'] == 'Goblin_' + k[-1].upper())
RAMP_GAIN = 1.0
report = {'native_skin_pixels': int(len(sel)), 'skin_texels_body': int(skin.sum()), 'skin_texels_head': int(hskin.sum()),
          'range': [float(lo), float(hi)], 'ramp_gain': RAMP_GAIN}
print('RAMPS', report)

swatch_px = np.zeros((N, N), bool)
normal = normal_gltf          # body normals: the installed map in the new tangent frames (glTF convention), spikes flat
graded = pad(graded, cov); normal = pad(normal, cov); rough = pad(rough, cov)

# ---------------------------------------------------------------- write
save(graded, T / 'gob2_basecolor_1k.png'); save(normal, T / 'gob2_normal_1k.png')
save(np.stack([np.ones_like(rough), rough, np.zeros_like(rough)], -1), T / 'gob2_metal_rough_1k.png')
# the mask is padded like the colour: a mask that stopped at the island edges left the gutters (and the cracks between
# carried UV faces) unrecoloured, and filtering drew them as olive lines along every seam on tiers B/C
skin_m = pad(skin.astype(float), cov); skin_m[swatch_px] = 0
R.write_mask([ndimage.gaussian_filter(skin_m, 0.7)], T / 'gob2_region_mask.png', size=N)
cmap = np.zeros((N, N), np.uint8); cmap[cov] = 11
cmap[cov & (sat < 0.15)] = 9; cmap[leather] = 8; cmap[skin] = 1; cmap[claw] = 4; cmap[spike] = 4
Image.fromarray(cmap).save(T / 'gob2_material_classes.png')
hg = pad(hg, hcov)
save(hg, T / 'gob2_head_basecolor_1k.png')
save(pad(load(HM / 'texture_urls_0_normal.png'), hcov), T / 'gob2_head_normal_1k.png')
hr = pad(load(HM / 'texture_urls_0_roughness.png', 'L'), hcov)
save(np.stack([np.ones_like(hr), hr, np.zeros_like(hr)], -1), T / 'gob2_head_metal_rough_1k.png')
R.write_mask([ndimage.gaussian_filter(pad(hskin.astype(float), hcov), 0.7)], T / 'gob2_head_region_mask.png', size=N)
hc = np.zeros((N, N), np.uint8); hc[hcov] = 11; hc[hskin] = 1; hc[eye & hcov] = 6
hc[np.isin(hp, [5, 6, 12, 13])] = 9; hc[teeth] = 5; hc[mouth] = 7
Image.fromarray(hc).save(T / 'gob2_head_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Goblin_A', 'prefix': 'Goblin', 'mask': 'gob2_region_mask.png', 'regions': ['skin'],
                      'palettes': PALS, 'ramps': ramps, 'report': report},
                     {'base': 'GoblinHead_A', 'prefix': 'GoblinHead', 'mask': 'gob2_head_region_mask.png',
                      'regions': ['skin'], 'palettes': PALS, 'ramps': ramps}]}
(T / 'gob2_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
