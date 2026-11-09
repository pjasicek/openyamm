#!/usr/bin/env python3
"""Body texture set, region mask and tier ramps for the Medusa (CLAUDE_CREATURE_TEXTURES.md; head set: compose_head.py).
Run after uv_raster.py (BODY 1024/2048, HEAD 1024) and bake_ao.py (work/ao_BODY.png).

Tiers (palettes from mm7_m282/manifest.json variants; sprite_frames/monsters/m283-285.yml): A Medusa = 283 (charcoal
scale-mail), B Queen Medusa = 284 (the bitmaps' own palette: silver mail, the HD masters' colours), C Empress Medusa =
285 (gold mail). Only the breastplate changes between the palettes (native palette indices 215-237, the sprite
package's single region), so there is ONE region: R = the scale-mail cups and their under-band. Skin, snake scales,
belly scutes, gold trim, quiver and hair snakes are in no region.
- Mail mask: skin-piece texels in the chest box that are low-saturation with the scale pattern's local contrast, plus the
  under-bust band, smoothed over 2 cm in 3D (KD tree on rest positions), gold excluded, padded into the UV gutters.
- Ramps: native mail pixels (indexed BMP pixels with index 215-237 on the standing/attack/walk frames) through each
  tier palette, sorted by luminance; a stop takes its hue/saturation from the native colour at the texel's luminance
  quantile (band-averaged chroma over a sixth of the pixels, 15th-95th percentile), its luminance from the texel scaled so the region mean equals the native mean x RAMP_GAIN; the darkest
  stops are desaturated (lead's Hydra rule).
- Base colour graded by the rest-pose AO at 2K and stored at 1K like normal/ORM/mask/classes (the merged body+head
  atlas needs equal sizes); ORM R = specular class, G roughness, B 0.
Writes textures/m282_*."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
T = HERE / 'textures'; T.mkdir(exist_ok=True)
M = HERE / 'meshy' / 'body_retexture_v1'
PALS = {'m282_a': 283, 'm282_b': 284, 'm282_c': 285}
RAMP_GAIN = 1.05
SAT_BOOST = {'m282_c': 1.35}
TIER_GAIN = {'m282_c': 1.12}
QUIVER, STUDS, COLLAR, RINGS, HANDS, EYES = {20}, {17, 18}, {19}, {21, 22}, {5, 6}, {28, 30}
HAIR = {1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 23, 24, 35}
SPEC = {'skin': 0.15, 'scale': 0.3, 'mail': 0.7, 'gold': 0.8, 'leather': 0.2, 'wood': 0.15, 'keratin': 0.35}
ROUGH = {'skin': 0.62, 'scale': 0.5, 'mail': 0.35, 'gold': 0.3, 'leather': 0.7, 'wood': 0.75, 'keratin': 0.5}
CLS = {'skin': 1, 'scale': 1, 'mail': 9, 'gold': 9, 'leather': 8, 'wood': 10, 'keratin': 4}
TIP = np.array([-1.568, 1.65, 0.108])


def load(path, n, mode='RGB'):
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


def classes(base, R):
    pc, pos = R['piece'], R['pos']; cov = pc >= 0
    H, S, V = hsv(base); L = base @ RV.LUMA
    loc = np.sqrt(np.maximum(ndimage.uniform_filter(L * L, 7 * len(L) // 1024) - ndimage.uniform_filter(L, 7 * len(L) // 1024) ** 2, 0))
    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    skin = cov & (pc == 0)
    gold = cov & (H > 25) & (H < 60) & (S > 0.4) & ~np.isin(pc, list(HAIR | QUIVER))
    box = skin & (z > 1.10) & (z < 1.47) & (np.abs(x) < 0.26)
    cand = box & (S < 0.14) & (loc > 0.03)
    Pp = pos[box]; kd = cKDTree(Pp); nb = kd.query_ball_point(Pp, 0.025); cc = cand[box].astype(float)
    score = np.zeros(box.shape); score[box] = [cc[n].mean() for n in nb]
    bluish = (H > 190) & (H < 290) & (S > 0.07)                     # the pale blue-grey skin around the cups
    c2 = box & (((score > 0.3) & (z < 1.30)) | ((score > 0.5) & (z < 1.37)) |
                ((z > 1.16) & (z < 1.27) & (y < 0.13) & (S < 0.35))) & ~gold & ~bluish
    cc = c2[box].astype(float); nb = kd.query_ball_point(Pp, 0.02)
    sm = np.zeros(box.shape); sm[box] = [cc[n].mean() for n in nb]
    mail = (sm > 0.5) & ~gold
    rattle = skin & (np.linalg.norm(pos - TIP, axis=-1) < 0.25) & ~gold & (S < 0.45)
    goldc = (H > 25) & (H < 60) & (S > 0.4) & (V > 0.35)
    C = {'mail': mail, 'gold': gold | (cov & np.isin(pc, list(RINGS | STUDS))) | (cov & np.isin(pc, list(COLLAR)) & goldc),
         'leather': cov & np.isin(pc, list(QUIVER)), 'wood': cov & ~np.isin(pc, list(HAIR | QUIVER | STUDS | COLLAR | RINGS | HANDS | EYES | {0})),
         'keratin': rattle}
    taken = np.zeros_like(cov)
    for k in ('gold', 'mail', 'leather', 'wood', 'keratin'):
        C[k] = C[k] & ~taken; taken |= C[k]
    C['scale'] = cov & ~taken & (np.isin(pc, list(HAIR)) | ((pc == 0) & (z < 0.92)))
    C['skin'] = cov & ~taken & ~C['scale']
    return C, cov, sm


R1 = np.load(HERE / 'work' / 'uvraster_BODY_1024.npz'); R2 = np.load(HERE / 'work' / 'uvraster_BODY_2048.npz')
base2 = load(M / 'texture_urls_0_base_color.png', 2048)
C2, cov2, _ = classes(base2, R2)
ao2 = load(HERE / 'work' / 'ao_BODY.png', 2048, 'L')
f = np.clip(0.6 + 0.4 * np.maximum(ao2, 0.45), 0, 1)
g2 = base2.copy(); g2[cov2] = base2[cov2] * f[cov2][:, None]
# the collar piece is a tall choker; Meshy painted everything above and below its gold band dark grey-green (a dark
# band under the chin in review): repaint the non-gold collar texels with the head set's neck skin
H2, S2, V2 = hsv(base2)
collar_skin = cov2 & np.isin(R2['piece'], list(COLLAR)) & ~((H2 > 25) & (H2 < 60) & (S2 > 0.4) & (V2 > 0.35))
hj = json.loads((T / 'm282_head.json').read_text())
NECK = np.array(hj['neck_rgb'])                            # = the head set's skin at the seam (compose_head.py)
g2[collar_skin] = NECK * (0.85 + 0.15 * (V2[collar_skin, None] / max(np.median(V2[collar_skin]), 1e-3)))
g2 = pad(g2, cov2)
base1 = np.asarray(Image.fromarray((np.clip(g2, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float64) / 255
save(base1, T / 'm282_basecolor_1k.png')          # body base 1K beside the 1K head set (merge_head_material: equal sizes)
C1, cov1, score1 = classes(load(M / 'texture_urls_0_base_color.png', 1024), R1)
normal = load(M / 'texture_urls_0_normal.png', 1024); rough_m = load(M / 'texture_urls_0_roughness.png', 1024, 'L')
cls = np.zeros((1024, 1024), np.uint8); spec = np.zeros((1024, 1024)); rgh = np.full((1024, 1024), 0.7)
for name, m in C1.items():
    cls[m] = CLS[name]; spec[m] = SPEC[name]
    if m.any():
        rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
save(pad(normal, cov1), T / 'm282_normal_1k.png')
save(np.stack([pad(spec, cov1), pad(rgh, cov1), np.zeros((1024, 1024))], -1), T / 'm282_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm282_material_classes.png')
mask = ndimage.gaussian_filter(pad(C1['mail'].astype(float), cov1), 0.7)
# bowstring swatch (the string stays in the body mesh after the bow is split off): an empty 1K block far from islands
dist = ndimage.distance_transform_edt(~cov1)
sy, sx = np.unravel_index(np.argmax(dist), dist.shape)
SW = 6
mask[sy - SW:sy + SW, sx - SW:sx + SW] = 0
RV.write_mask([mask], T / 'm282_region_mask.png', size=1024)
string_rgb = np.array([0.80, 0.76, 0.66])
gb = np.asarray(Image.open(T / 'm282_basecolor_1k.png').convert('RGB'), np.float64) / 255
gb[sy - SW:sy + SW, sx - SW:sx + SW] = string_rgb; save(gb, T / 'm282_basecolor_1k.png')
mr = np.asarray(Image.open(T / 'm282_metal_rough_1k.png').convert('RGB'), np.float64) / 255
mr[sy - SW:sy + SW, sx - SW:sx + SW] = (0.2, 0.6, 0.0); save(mr, T / 'm282_metal_rough_1k.png')
(T / 'm282_swatches.json').write_text(json.dumps({'string_uv': [(sx + 0.5) / 1024, 1 - (sy + 0.5) / 1024],
                                                  'clearance_px_1k': float(dist[sy, sx])}))
print('SWATCH string at 1K px', int(sx), int(sy), 'clearance', round(float(dist[sy, sx]), 1))
for name, size in (('bow', (128, 1024)), ('arrow', (1024, 128))):
    Image.new('RGB', (64, 64), (128, 128, 255)).save(T / 'props' / f'{name}_normal.png')
    Image.new('RGB', (64, 64), (40, 120, 0) if name == 'bow' else (25, 170, 0)).save(T / 'props' / f'{name}_metal_rough.png')
print('CLASSES', {n: int(m.sum()) for n, m in C1.items()}, 'covered', int(cov1.sum()))

# ---------------------------------------------------------------- native mail colours per tier
NAT = {}
acts = {k: np.frombuffer((ROOT / 'assets_dev/worlds/mm7/textures' / f'pal{p:03d}.act').read_bytes()[:768], np.uint8)
        .reshape(256, 3).astype(np.float64) / 255 for k, p in PALS.items()}
frames = [f'm282sa{v}' for v in range(5)] + [f'm282a{c}{v}' for c in 'abcdefgh' for v in (0, 1, 2)] + \
         [f'm282w{c}{v}' for c in 'abcdefg' for v in (0, 1)]
idx = []
for fr in frames:
    p = ROOT / 'assets_dev/engine/sprites' / f'{fr}.bmp'
    if p.exists():
        a = np.asarray(Image.open(p)); idx.append(a[(a >= 215) & (a <= 237)])
idx = np.concatenate(idx)
m = C1['mail']; lum = RV.luminance(base1[m]); lo, hi = np.percentile(lum, [2, 98]); srt = np.sort(lum)
tex_mean = float(np.mean(lum))
ramps = {}
for k in PALS:
    X = acts[k][idx]; LX = RV.luminance(X); o = np.argsort(LX); Xl = RV.srgb_to_linear(X)[o]; LX = LX[o]
    kgain = float(np.mean(LX)) * (RAMP_GAIN * TIER_GAIN.get(k, 1.0)) ** 2.2 / max(tex_mean, 1e-4)
    cols = []
    for i in range(16):
        Li = lo + (hi - lo) * i / 15
        q = np.searchsorted(srt, Li) / len(srt); j = int(np.clip(q, 0.15, 0.95) * (len(Xl) - 1))
        w = Xl[max(0, j - len(Xl) // 6):j + len(Xl) // 6 + 1]           # band-averaged chroma (cobra rule)
        c = (w / np.maximum(w @ RV.LUMA, 1e-5)[:, None]).mean(0)
        Lt = Li * kgain
        c = c * (Lt / max(float(c @ RV.LUMA), 1e-5))
        if k in SAT_BOOST:                                           # gold mail: the sprite's gold reads richer than the
            g = float(c @ RV.LUMA); c = g + (c - g) * SAT_BOOST[k]   # band-averaged chroma (white highlights mixed in)
        if i < 3:                                                   # darkest stops: desaturate toward grey
            g = float(c @ RV.LUMA); c = c * (0.5 + 0.5 * i / 3) + g * (0.5 - 0.5 * i / 3)
        cols.append([round(float(x), 6) for x in np.clip(c, 0, 1)])
    ramps[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
    print('RAMP', k, 'native mean lin %.4f' % float(np.mean(LX)), 'gain %.2f' % kgain, 'mid stop', cols[8])
cfg = {'variants': list(PALS), 'palettes': PALS,
       'materials': [{'base': 'M282_A', 'prefix': 'M282', 'mask': 'm282_region_mask.png', 'regions': ['mail'],
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm282_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
