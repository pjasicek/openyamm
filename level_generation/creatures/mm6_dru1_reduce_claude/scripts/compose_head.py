"""Head set maps (1024) for the new head layout from the Meshy head retexture (meshy/head_retexture_r66) ->
textures/head_r66_{basecolor,metal_rough,normal,region_mask}.png.
- Face (uvpart 1): Meshy's paint, skin matched per channel to the installed head skin median (the neck meets the
  body skin at the set border).
- Scalp / neck / ears (4): Meshy's paint below NECK_Z and at the front (texels painted hood-green, occluded in every
  reference, become skin), uniform dark hair above it at the back (scalp and ears under the hair); same skin match. The face's hairline/temple hair
  takes the reference hair hue at Meshy's luminance.
- Hair shell (2): Meshy painted most locks hood-green (the hair hangs inside the hood in every reference view), so
  the hair is a strand texture: line-integral convolution of noise along each lock's hanging direction (3D down
  projected into UV per face, smoothed), coloured by rank from the brown hair pixels of the HD head references (Meshy's hair texels lean olive), darker toward the roots
  under the hood, with light bands across the locks by height (waves).
- Hood outer/lining (3, 5): Meshy's velvet; luminance quantile-matched to the installed cloak so the shared cloth ramps
  give the same colour (region mask R = 1); the finest speckle damped to 60 % as on the cloak (review 6).
- Choker: the gold ring by height (CHOKER_Z) in the installed gold.
- Metal/rough per part as installed (skin 115/128, hair 20/217, hood 38/204); normals flat (the installed head normal
  map shaded the hood lining and hair crown black in the viewer). Empty texels take the nearest covered texel.
Usage: compose_head.py"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

S = 1024
E = lambda k, d: float(os.environ.get(k, d))
r = np.load('work/head_raster.npz'); fid, part, pos, nrm = r['fid'], r['part'], r['pos'], r['nrm']
d = np.load('work/headuv.npz')
cov = fid >= 0
lum = lambda c: c[..., :3] @ np.array([.2126, .7152, .0722])
mesh = np.asarray(Image.open('meshy/head_retexture_r66/texture_urls_0_base_color.png').convert('RGB').resize((S, S), Image.LANCZOS), np.float32) / 255
base = mesh.copy()
z = pos[..., 2]
# installed references: head skin median, cloak luminance distribution, choker gold
atlas = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255
amask = np.asarray(Image.open('work/dru1_region_mask_head_atlas.png').convert('RGBA'), np.float32)[..., 0] / 255
AH, AW = atlas.shape[:2]
c = d['auv'].mean(1); ax = np.clip((c[:, 0] * AW).astype(int), 0, AW - 1); ay = np.clip(((1 - c[:, 1]) * AH).astype(int), 0, AH - 1)
old = atlas[ay, ax]; fz = d['pos'].mean(1)[:, 2]
skin_ref = np.median(old[np.isin(d['uvpart'], (1, 4)) & (old[:, 0] > .6)], 0)
CH0, CH1 = E('CHOKER_Z0', '1.400'), E('CHOKER_Z1', '1.416')
gold = np.median(old[(fz > CH0) & (fz < CH1) & (old[:, 0] > .5) & (old[:, 2] < .3)], 0) if ((fz > CH0) & (fz < CH1)).any() else np.array([.85, .65, .15])
body = np.zeros_like(amask, bool); body[:, :1024] = True
cloak_l = np.sort(lum(atlas[body & (amask > .5)]))
print('REF skin', (skin_ref * 255).round(), 'gold', (gold * 255).round(), 'cloak lum median %.3f' % np.median(cloak_l))

green = (mesh[..., 1] > mesh[..., 0] * 1.05) & (mesh[..., 1] > mesh[..., 2] * 1.05)
skinish = (mesh[..., 0] > mesh[..., 1] * 1.1) & (mesh[..., 0] > .45)
# --- face and scalp/neck/ears
fr = (part == 1) | (part == 4)
hair_dark = None  # set from the hair palette below
NECK_Z = E('NECK_Z', '1.48')
fix = fr & green
front = pos[..., 1] < E('SCALP_Y', '-.02')  # the under-jaw and front of the neck are skin at any height
base[fix & ((z < NECK_Z) | front)] = np.median(mesh[(part == 1) & skinish], 0)
fix_hair = fix & (z >= NECK_Z) & ~front  # filled with the hair palette's dark third after the hair section
gain = skin_ref / np.median(base[fr & skinish & ~fix], 0)
base[fr] = np.clip(base[fr] * gain, 0, 1)
# Meshy baked a dark shadow under the chin (reads as stubble): skin texels below CHIN_Z darker than the skin median
# are lifted toward it
chin = fr & (z < E('CHIN_Z', '1.475')) & (lum(base) < lum(skin_ref) * .92) & (lum(base) > .12)
k = np.clip((lum(skin_ref) * .92 - lum(base[chin])) / (lum(skin_ref) * .5), 0, 1)[:, None]
base[chin] = base[chin] * (1 - k) + skin_ref * .9 * k
print('CHIN lifted', int(chin.sum()))
print('SKIN gain', gain.round(3), 'green fixed', int(fix.sum()), 'texels')
# --- hair strands
hair = part == 2
uv = d['huv'] * S; uv[..., 1] = S - uv[..., 1]
P = d['pos']; e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]; u1, u2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
n = np.cross(e1, e2); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
down = np.array([0, 0, -1.0]); dp = down - (n @ down)[:, None] * n          # down projected into each face
# solve dp = a e1 + b e2 (least squares) -> UV direction a u1 + b u2
G = np.stack([np.einsum('ij,ij->i', e1, e1), np.einsum('ij,ij->i', e1, e2), np.einsum('ij,ij->i', e2, e2)], 1)
rhs = np.stack([np.einsum('ij,ij->i', dp, e1), np.einsum('ij,ij->i', dp, e2)], 1)
det = G[:, 0] * G[:, 2] - G[:, 1] ** 2 + 1e-18
a = (rhs[:, 0] * G[:, 2] - rhs[:, 1] * G[:, 1]) / det; b = (rhs[:, 1] * G[:, 0] - rhs[:, 0] * G[:, 1]) / det
fdir = a[:, None] * u1 + b[:, None] * u2; fdir /= np.linalg.norm(fdir, axis=1, keepdims=True) + 1e-12
vx = np.where(hair, fdir[np.maximum(fid, 0), 0], 0); vy = np.where(hair, fdir[np.maximum(fid, 0), 1], 0)
# smooth the field inside the hair texels (sign-consistent: the down direction is consistent per lock)
w = ndimage.gaussian_filter(hair.astype(np.float32), 3) + 1e-6
vx, vy = ndimage.gaussian_filter(vx, 3) / w, ndimage.gaussian_filter(vy, 3) / w
nv = np.hypot(vx, vy) + 1e-9; vx, vy = vx / nv, vy / nv
rng = np.random.default_rng(7)
noise = rng.random((S, S)).astype(np.float32)
coarse = ndimage.gaussian_filter(rng.random((S, S)).astype(np.float32), 2.5)
coarse = (coarse - coarse.mean()) / (coarse.std() + 1e-9)  # strand clumps that still read at game distance
noise = (noise - noise.mean()) / noise.std() * .45 + coarse * .55
L, STEP = int(E('LIC_LEN', '22')), 1.0
ys, xs = np.nonzero(hair); acc = noise[ys, xs].copy(); cnt = np.ones(len(ys), np.float32)
for sgn in (1, -1):
    px, py = xs + .5, ys + .5
    for _ in range(L):
        ix, iy = np.clip(px.astype(int), 0, S - 1), np.clip(py.astype(int), 0, S - 1)
        ok = hair[iy, ix]
        px = px + sgn * vx[iy, ix] * STEP; py = py + sgn * vy[iy, ix] * STEP
        ix, iy = np.clip(px.astype(int), 0, S - 1), np.clip(py.astype(int), 0, S - 1)
        ok &= hair[iy, ix]
        acc += np.where(ok, ndimage.map_coordinates(noise, [py - .5, px - .5], order=1, mode='nearest'), 0); cnt += ok
lic = acc / cnt
lic = (lic - np.percentile(lic, 1)) / (np.percentile(lic, 99) - np.percentile(lic, 1) + 1e-9)
# a few broad highlight bands across the locks (wavy hair catches light in bands)
# waves: light bands across the locks by height (the hair hangs down), phase shifted slowly across the locks so
# neighbouring locks do not line up
phase = ndimage.gaussian_filter(rng.random((S, S)).astype(np.float32), 14)[ys, xs]
phase = (phase - phase.min()) / (phase.max() - phase.min() + 1e-9) * 2 * np.pi
wave = .5 + .5 * np.sin(2 * np.pi * pos[ys, xs, 2] / E('WAVE_M', '.05') + phase)
v = np.clip(E('LIC_W', '.5') * lic + (1 - E('LIC_W', '.5')) * wave ** 1.3, 0, 1)
# palette: the brown hair pixels of the HD head references (Meshy's own hair texels lean olive)
pal = []
for ref in ('00_front', '02_left', '04_right'):
    im = np.asarray(Image.open(f'references_head/{ref}.png').convert('RGB'), np.float32) / 255
    q = im.reshape(-1, 3); l_ = lum(q)
    sel = (q[:, 0] > q[:, 1] * 1.08) & (q[:, 1] > q[:, 2] * 1.02) & (q[:, 0] - q[:, 2] > .08) & (l_ > .04) & (l_ < E('PAL_MAX', '.48'))
    sel &= ~((q[:, 0] > .55) & (q[:, 1] > q[:, 0] * .6))  # not skin
    pal.append(q[sel])
pal = np.concatenate(pal); pal = pal[np.argsort(lum(pal))]
col = pal[np.clip((v * (len(pal) - 1)).astype(int), 0, len(pal) - 1)]
# darker toward the roots under the hood
zz = pos[ys, xs, 2]; root = np.clip((zz - E('ROOT_Z0', '1.45')) / (E('ROOT_Z1', '1.66') - E('ROOT_Z0', '1.45')), 0, 1)
shade = 1 - .45 * root
hair_ref = np.median(old[d['uvpart'] == 2], 0)  # installed hair median: keep the accepted brightness
hc = col * shade[:, None]; hair_gain = lum(hair_ref) / np.median(lum(hc)); hc *= hair_gain
base[ys, xs] = np.clip(hc, 0, 1)
print('HAIR texels', len(ys), 'palette', len(pal), 'median', (np.median(pal, 0) * 255).round())
base[fix_hair] = np.median(pal[:len(pal) // 3], 0)
# hidden scalp (rest part above the neck) is uniform dark hair; Meshy's olive hair paint at the hairline and temples
# of the face takes the reference hair hue at its own luminance
base[(part == 4) & (z >= NECK_Z) & ~front] = np.median(pal[:len(pal) // 3], 0)
pl = lum(pal)
hl_ = (part == 1) & ~skinish & (lum(mesh) < .32) & ((z > E('HAIRLINE_Z', '1.585')) | (np.abs(pos[..., 0]) > E('TEMPLE_X', '.055')))
idx = np.clip(np.searchsorted(pl, lum(base[hl_]) * .9), 0, len(pal) - 1)
base[hl_] = np.clip(pal[idx] * hair_gain, 0, 1)
print('HAIRLINE recoloured', int(hl_.sum()))
# --- hood: luminance rank-matched to the installed cloak
hood = (part == 3) | (part == 5)
hl = lum(mesh[hood]); rank = np.argsort(np.argsort(hl)) / max(len(hl) - 1, 1)
target = cloak_l[np.clip((rank * (len(cloak_l) - 1)).astype(int), 0, len(cloak_l) - 1)]
base[hood] = np.clip(mesh[hood] * (target / (hl + 1e-6))[:, None], 0, 1)
# review 6 rule: only the finest velvet speckle (below a 1.5 px blur) is damped to 60 % (the ramp is rank-matched,
# so the darkest speckle took near-black stops)
hw = ndimage.gaussian_filter(hood.astype(np.float32), 1.5) + 1e-6
for ch in range(3):
    bl = ndimage.gaussian_filter(np.where(hood, base[..., ch], 0), 1.5) / hw
    base[..., ch] = np.where(hood, bl + .6 * (base[..., ch] - bl), base[..., ch])
# --- choker
ch = fr & (z > CH0) & (z < CH1)
base[ch] = gold
print('CHOKER texels', int(ch.sum()))
# --- other maps
mr = np.zeros((S, S, 3), np.float32)
for k, (sp, ro) in {1: (115, 128), 4: (115, 128), 2: (20, 217), 3: (38, 204), 5: (38, 204)}.items():
    mr[part == k] = (sp / 255, ro / 255, 0)
mask = np.zeros((S, S, 4), np.float32); mask[hood, 0] = 1
normal = np.zeros((S, S, 3), np.float32); normal[:] = (128 / 255, 128 / 255, 1)
# fill every empty texel from the nearest covered texel (gutters and mips never blend in Meshy's unused paint)
dist, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
pad = dist > 0
for m in (base, mr, mask):
    m[pad] = m[iy[pad], ix[pad]]
os.makedirs('textures', exist_ok=True)
save = lambda a, name, mode: Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8), mode).save(f'textures/head_r66_{name}.png')
save(base, 'basecolor', 'RGB'); save(mr, 'metal_rough', 'RGB'); save(normal, 'normal', 'RGB'); save(mask, 'region_mask', 'RGBA')
print('WROTE textures/head_r66_*.png')
