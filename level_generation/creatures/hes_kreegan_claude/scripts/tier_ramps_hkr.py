"""hkr tiers (one shared texture set per material + region masks + ramps, CLAUDE_CREATURE_TEXTURES.md). No native
palette exists (a new Hesper creature): the colours come from the approved concept fam_troopers.png.
Body (the MM6 Demon's own 2K base colour and region mask: R skin, G harness): authored ramps, 16 stops over the
region's texel luminance range (0.5-99.5 %), each stop the tier's colour (shadow -> mid -> highlight anchors,
linear) scaled to the stop's luminance x GAIN, so the demon's painted shading and scales stay. The skin takes the
Trooper colours of claude_shared/kreegan_skin.py (user decision 2026-10-24): A violet, B slate blue, C black crimson
(highlights lifted); the harness dark leather on all three.
Armour (textures/hkr_armour_*: R ivory, G gold trim, B painted glow): region_variants.fit_ramps against target
images made from the base itself: A = the base (ivory, gold, orange), B = scorched ivory and bronze trim, C = gilded
plates, bright pale-gold trim, white-gold glow.
Writes textures/hkr_ramps.json (+ the fit report). Args: none"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import region_variants as rv
import kreegan_skin as ks
T = os.path.join(HERE, 'textures')
VAR = ['hkr_a', 'hkr_b', 'hkr_c']
lin = rv.srgb_to_linear
LUMA = np.array([0.2126, 0.7152, 0.0722])


def authored(lum, w, anchors, gain):
    core = w > 0.9; lo, hi = np.percentile(lum[core], 0.5), np.percentile(lum[core], 99.5)
    a = [lin(np.array(c) / 255.0) for c in anchors]
    stops = []
    for i in range(16):
        t = i / 15
        c = a[0] * (1 - 2 * t) + a[1] * 2 * t if t < 0.5 else a[1] * (2 - 2 * t) + a[2] * (2 * t - 1)
        L = (lo + t * (hi - lo)) * gain
        stops.append(np.clip(c * L / max(c @ LUMA, 1e-6), 0, 1))
    return {'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': np.round(np.array(stops), 6).tolist()}


body = rv.load_srgb(os.path.join(HERE, 'work', 'src_tex', '01_Image_0.png'))
mask = np.asarray(Image.open(os.path.join(T, 'hkr_body_region_mask.png')).convert('RGB').resize(body.shape[1::-1], Image.BILINEAR)) / 255.0   # RGB: PIL premultiplies RGBA (alpha 0) when resizing
lum = lin(body) @ LUMA
GREY = ([(128, 128, 128)] * 3, 1.0)   # the skin's luminance spread; kreegan_skin.recolour gives it the tier colour
HARN = {v: ([(24, 19, 17), (66, 52, 42), (126, 106, 86)], 1.0) for v in VAR}
body_r = {v: [ks.recolour(authored(lum, mask[..., 0], *GREY), ks.SKIN['trooper'][v[-1]]),
              authored(lum, mask[..., 1], *HARN[v])] for v in VAR}
arm = rv.load_srgb(os.path.join(T, 'hkr_armour_basecolor.png'))
am = np.asarray(Image.open(os.path.join(T, 'hkr_armour_region_mask.png')).convert('RGB')) / 255.0
alum = lin(arm) @ LUMA
enc = lambda x: np.where(x <= 0.0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - 0.055)
rel = (alum / max(np.median(alum[am[..., 0] > 0.9]), 1e-6))[..., None]
gild = enc(np.clip(lin(np.array([206, 160, 70]) / 255) * rel * 1.05, 0, 1))
targets_iv = {'hkr_a': arm, 'hkr_b': np.clip(arm * [0.74, 0.66, 0.56], 0, 1), 'hkr_c': gild}
targets_gd = {'hkr_a': arm, 'hkr_b': np.clip(arm * [0.72, 0.58, 0.42], 0, 1),
              'hkr_c': np.clip(arm * 0.4 + np.array([250, 228, 170]) / 255 * 0.6, 0, 1)}
glum = (alum / max(np.median(alum[am[..., 2] > 0.9]), 1e-6))[..., None]
targets_gl = {'hkr_a': arm, 'hkr_b': arm, 'hkr_c': enc(np.clip(lin(np.array([255, 226, 160]) / 255) * glum, 0, 1))}
ri, rep_i = rv.fit_ramps(arm, targets_iv, am[..., 0])
rg, rep_g = rv.fit_ramps(arm, targets_gd, am[..., 1])
rl, rep_l = rv.fit_ramps(arm, targets_gl, am[..., 2])
cfg = {'variants': VAR, 'materials': [
    {'base': 'Demon_Body_A', 'prefix': 'HKR', 'mask': 'hkr_body_region_mask.png', 'ramps': body_r},
    {'base': 'HKR_Plate', 'prefix': 'HKR_Plate', 'mask': 'hkr_armour_region_mask.png',
     'ramps': {v: [ri[v], rg[v], rl[v]] for v in VAR}}],
    'report': {'armour_ivory': rep_i, 'armour_gold': rep_g, 'armour_glow': rep_l,
               'body': 'authored (no native palette): kreegan_skin trooper skin (violet / slate blue / black crimson), dark leather harness'}}
json.dump(cfg, open(os.path.join(T, 'hkr_ramps.json'), 'w'), indent=1)
print('RAMPS', json.dumps(cfg['report'])[:600])
