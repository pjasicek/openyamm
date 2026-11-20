#!/usr/bin/env python3
"""Textures, region mask and tier ramps for a New Sorpigal peasant with a grafted head (CLAUDE_CREATURE_TEXTURES.md).
Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py. Settings: creature.json 'compose'.

Body set (Meshy retexture meshy/<compose.retexture, default retexture_v1>, Meshy's layout copied onto our faces):
- classes per texel by piece and colour: the green garment (the one region the native palettes change), skin, rest;
- skin repainted as ONE albedo x Meshy's fine shading (Meshy paints face-sized patches), and that albedo is the
  grafted head's own skin, so the neck seam meets the same colour;
- AO graded; ORM red = per-class specular mask, green = roughness.
Head set (the head-only Meshy model meshy/head_v1; its UV layout is HeadUV): Meshy's texture kept as it is (the face
is the point of the graft) with the normal map from head_normal_bake.py when present; AO only on the hair; the
neck band (within the neck's radius) fades over 4 cm above the seam (work/graft.json z_seam) into the body skin,
whose albedo is the head's own neck colour just above the fade; head skin carries no normal map (head_skin_normal); `throat_fill` repaints texels darker than its value under its height and in front of y_max (the
invented bust's shirt painted up the throat) with the head's skin albedo. `repaint_light` repaints a light cloth piece
(the male's trousers, boots kept by colour) as one albedo x Meshy's fine shading. `debrown` turns hair-coloured texels of one piece above a height into skin (inside the decolletage box) or the
garment's median (elsewhere): Meshy retextures sometimes project the hair onto the bust.
`ramp_spread` widens the ramp range about its middle (the cloth then spans only the palette's middle tones).
`calm_garment` [lo, hi] repaints the garment as its median colour x Meshy's fine detail clipped to lo..hi.
`garment_skin_fix` turns skin-coloured texels on the garment
pieces (a hand projected onto the cloth) into the garment's median colour inside its mask. `neck_flat` makes the body's
neck above a height flat skin with a flat normal (Meshy painted hair strands along the open rim under the head).
Ramps: the old project's palette ramps (`ramps_from`, native palettes, one region) with the luminance range refitted
to this texture's garment texels (2nd-98th percentile, linear). The head material gets an empty mask and the same
ramps (merge_head_material.py). Variant names stay the old project's (pfem_a.., pman_a..). PREVIEW=1 writes work/classes_body.png. Writes textures/<prefix>_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
CJ = json.load(open(HERE / 'creature.json'))
CF = CJ['compose']; X = CJ['prefix']; MESH = CJ['mesh']
T = HERE / 'textures'; T.mkdir(exist_ok=True)
N = 1024
SKIN_MIX = 0.85
SPEC = {'garment': 0.2, 'cloth': 0.2, 'skin': 0.25, 'other': 0.35}   # skin 0.45 shone white on the forehead
ROUGH = {'garment': 0.85, 'cloth': 0.85, 'skin': 0.6, 'other': 0.6}


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


def repaint(img, m, albedo, sigma=6.0, clip=(0.5, 1.5), mix=SKIN_MIX):
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, *clip)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - mix) + new * mix
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def skin_of(rgb):
    h, s, v = hsv(rgb)
    return (h > 5) & (h < 40) & (s > 0.18) & (s < 0.62) & (v > 0.45)


def maps(meshy):
    return (load(meshy / 'texture_urls_0_base_color.png'), load(meshy / 'texture_urls_0_normal.png'),
            load(meshy / 'texture_urls_0_roughness.png', 'L'))


def orm(C, rough_m, cov):
    spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        if m.any():
            spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1)


# ---- head ------------------------------------------------------------------------------------------------------------
hbase, hnorm, hrough = maps(HERE / 'meshy' / 'head_v1')
if (HERE / 'work' / 'head_normal_rebake.png').exists():   # head_normal_bake.py: Meshy's map re-baked for smooth shading
    hnorm = load(HERE / 'work' / 'head_normal_rebake.png')
GJ = json.load(open(HERE / 'work' / 'graft.json'))
HZ = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hcov = HZ['piece'] >= 0; hpos = HZ['pos']
hskin = hcov & skin_of(hbase)
_, hs_, hv_ = hsv(hbase)
albedo = np.median(hbase[hskin & (hs_ < 0.5) & (hv_ > 0.55)], 0)   # the face's skin, not copper/chestnut hair
GJ0 = json.load(open(HERE / 'work' / 'graft.json')); ZS = GJ0.get('z_seam', GJ0['z_cut'])
SEAM = 0.04
band = hskin & (hpos[..., 2] > ZS + SEAM) & (hpos[..., 2] < ZS + SEAM + 0.03)
if band.sum() > 500:                                   # the body skin takes the colour of the head's own neck just above
    face_alb = albedo                                  # the fade (the male's neck is darker than his lit face)
    albedo = np.median(hbase[band], 0) * CF.get('skin_tone', 1.0)
    print('SKIN albedo from the head neck band', np.round(albedo * 255).tolist(), '(face', np.round(face_alb * 255).tolist(), ')')
hg = hbase.copy()
TF = CF.get('throat_fill')
if TF:
    th = hcov & (hpos[..., 2] < TF['below_z']) & (hsv(hbase)[2] < TF['value_max']) & (hpos[..., 1] < TF.get('y_max', 1.0))
    th = ndimage.binary_dilation(th, iterations=2) & hcov & (hpos[..., 2] < TF['below_z'] + 0.01)
    flat = np.where(th[..., None], albedo[None, None, :] * 0.92, hg)
    w = ndimage.gaussian_filter(th.astype(float), 1.5)[..., None]
    hg = hg * (1 - w) + flat * w
    print('THROAT texels repainted', int(th.sum()))
# the neck band above the welded seam fades into the same flat skin as the body's neck below it (no colour step)
# the engine builds each pixel's tangent frame from screen derivatives (fs_model.sc), flat per triangle, while the map
# was baked against smooth MikkTSpace tangents: on the decimated head with stretched UVs that left triangle-shaped
# smudges when the head turned. The face's form is in the full-density geometry; skin keeps a quarter of the map.
SKIN_NM = CF.get('head_skin_normal', 0.0)              # 0.25 still drew the baked facets of Meshy's flat-shaded head
hnorm = np.where(hskin[..., None], np.array([0.5, 0.5, 1.0]) * (1 - SKIN_NM) + hnorm * SKIN_NM, hnorm)
# the fade is chosen by position (within the neck's radius of its axis), not by colour: Meshy's shaded neck side did
# not pass the skin test and kept a hard edge; hair (dark and saturated) is left alone
nk_ring = hcov & (np.abs(hpos[..., 2] - ZS) < 0.01)
ax = np.median(hpos[nk_ring][:, :2], axis=0) if nk_ring.any() else np.zeros(2)
rr = np.linalg.norm(hpos[..., :2] - ax, axis=-1)
r_neck = np.percentile(rr[nk_ring], 80) if nk_ring.any() else 0.07
hair_like = (hv_ < 0.42) & (hs_ > 0.5)
sw = hcov & (rr < r_neck + 0.012) & ~hair_like
t = np.clip(1 - (hpos[..., 2] - ZS) / SEAM, 0, 1); t = t * t * (3 - 2 * t)
t = np.where(sw, t, 0.0)
flat_h = repaint(hg, hcov & (t > 0), albedo, clip=(0.97, 1.03), mix=1.0)
hg = hg * (1 - t[..., None]) + flat_h * t[..., None]
hnorm = hnorm * (1 - t[..., None]) + np.array([0.5, 0.5, 1.0]) * t[..., None]
print('SEAM head texels faded to the neck skin', int((t > 0.01).sum()))
if GJ.get('neck_uv'):                                 # the extended neck's UV spot (graft_head_parts.py neck_extend)
    nu, nvv = GJ['neck_uv']
    yy, xx = np.mgrid[0:N, 0:N]
    spot = (yy - (N - 1 - nvv * N)) ** 2 + (xx - nu * N) ** 2 < 14 ** 2
    hg[spot] = albedo; hnorm[spot] = (0.5, 0.5, 1.0); hcov = hcov | spot; hskin = hskin | spot
    print('NECKUV spot painted with the neck skin', int(spot.sum()), 'texels at uv', np.round(GJ['neck_uv'], 3).tolist())
# Meshy's head texture carries its own shading: baked AO only darkens the hair (on the face it left grey smudges)
hg = ao_grade(hg, load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov & ~hskin & (t == 0))
HC = {'skin': hskin, 'other': hcov & ~hskin}
save(pad(hg, hcov), T / f'{X}_head_basecolor_1k.png'); save(pad(hnorm, hcov), T / f'{X}_head_normal_1k.png')
save(orm(HC, hrough, hcov), T / f'{X}_head_metal_rough_1k.png')
R.write_mask([np.zeros((N, N))], T / f'{X}_head_region_mask.png', size=N)

# ---- body ------------------------------------------------------------------------------------------------------------
base, normal, rough_m = maps(HERE / 'meshy' / CF.get('retexture', 'retexture_v1'))
BZ = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece = BZ['piece']; cov = piece >= 0
h, s, v = hsv(base)
C = {}
C['garment'] = cov & np.isin(piece, CF['garment_pieces']) & (h > 65) & (h < 170) & (s > 0.15) & (v > 0.06)
C['skin'] = cov & np.isin(piece, CF['skin_pieces']) & skin_of(base) & ~C['garment']
if CF.get('garment_skin_fix'):                        # pm3: Meshy painted the master's hanging hand onto the tunic
    gp = cov & np.isin(piece, CF['garment_pieces'])
    ghost = ndimage.binary_dilation(gp & skin_of(base), iterations=2) & gp & ~C['garment']
    base = base.copy(); base[ghost] = np.median(base[C['garment']], 0)
    C['garment'] |= ghost
    print('GHOST skin texels on the garment made garment', int(ghost.sum()))
DB = CF.get('debrown')                                 # pf4: Meshy painted hair colour over the bust and the strap tops
if DB:
    pos3 = BZ['pos']
    brown = cov & (piece == DB['piece']) & (pos3[..., 2] > DB['above_z']) & (h > 5) & (h < 42) & (s > 0.35) & (v < 0.7)
    brown = ndimage.binary_dilation(brown, iterations=2) & cov & (piece == DB['piece']) & (pos3[..., 2] > DB['above_z']) \
        & ~C['garment'] & ~((s < 0.2) & (v > 0.75))       # not the white trim
    deco = brown & (np.abs(pos3[..., 0]) < DB['deco_x']) & (pos3[..., 1] < DB['deco_y'])
    base = base.copy()
    base[deco] = albedo
    base[brown & ~deco] = np.median(base[C['garment']], 0)
    C['skin'] |= deco; C['garment'] |= brown & ~deco
    h, s, v = hsv(base)
    print('DEBROWN texels to skin', int(deco.sum()), 'to garment', int((brown & ~deco).sum()))
C['cloth'] = cov & ~C['garment'] & ~C['skin'] & np.isin(piece, CF['garment_pieces'] + CF.get('cloth_pieces', []))
C['other'] = cov & ~C['garment'] & ~C['skin'] & ~C['cloth']
g = repaint(base, C['skin'], albedo, clip=(0.8, 1.2))
NF = CF.get('neck_flat')                              # Meshy painted hair along the body's open neck rim under the head
if NF:
    nk = cov & np.isin(piece, NF['pieces']) & (BZ['pos'][..., 2] > NF['above_z']) & \
        (np.abs(BZ['pos'][..., 0]) < NF.get('max_abs_x', 0.075))   # the neck, not the shoulders' chemise
    g = repaint(g, nk, albedo, clip=(0.97, 1.03), mix=1.0)
    normal = normal.copy(); normal[nk] = (0.5, 0.5, 1.0)
    C['skin'] |= nk; C['cloth'] &= ~nk; C['other'] &= ~nk; C['garment'] &= ~nk
    print('NECK flat skin texels', int(nk.sum()))
DF = CF.get('deco_flat')                              # pf4: the decolletage skin plain (Meshy painted lace over it)
if DF:
    pos3 = BZ['pos']
    dk = C['skin'] & np.isin(piece, DF['pieces']) & (pos3[..., 2] > DF['above_z']) & \
        (np.abs(pos3[..., 0]) < DF['max_abs_x']) & (pos3[..., 1] < DF['max_y'])
    g = repaint(g, dk, albedo, clip=(0.96, 1.04), mix=1.0)
    normal = normal.copy(); normal[dk] = (0.5, 0.5, 1.0)
    print('DECO flat skin texels', int(dk.sum()))
RT = CF.get('repaint_light')                          # pm3: Meshy blotched the cream trousers grey-green
if RT:
    pl = cov & np.isin(piece, RT['pieces'])
    boot = pl & (h > 8) & (h < 45) & (s > 0.35) & (v < 0.62)
    cloth = pl & ~boot
    alb = np.median(base[cloth & (v > np.percentile(v[cloth], 60))], 0)
    g = repaint(g, ndimage.binary_erosion(cloth, iterations=1) | (cloth & ~ndimage.binary_erosion(pl, iterations=2)),
                alb, clip=(0.95, 1.05), mix=1.0)            # whole islands were green: no blur-relative detail
    normal = normal.copy(); normal[cloth] = normal[cloth] * 0.4 + np.array([0.5, 0.5, 1.0]) * 0.6   # the blotches are relief too
    rough_m = rough_m.copy(); rough_m[cloth] = np.median(rough_m[cloth])                          # and gloss
    print('REPAINT light cloth texels', int(cloth.sum()), 'albedo', np.round(alb * 255).tolist(), 'boots kept', int(boot.sum()))
CALM = CF.get('calm_garment')                        # a mottled Meshy cloth: one colour x mild fine detail
if CALM:
    gm = C['garment']
    g = repaint(g, gm, np.median(base[gm], 0), clip=tuple(CALM), mix=1.0)
    print('CALM garment texels', int(gm.sum()), 'detail clip', CALM)
g = ao_grade(g, load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov & ~(nk if NF else np.zeros_like(cov)))
print('CLASSES body', {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()), 'skin albedo (head)',
      np.round(albedo * 255).tolist())
if os.environ.get('PREVIEW'):
    pv = np.zeros((N, N, 3), np.uint8)
    for k, col in (('garment', (40, 200, 40)), ('skin', (230, 170, 140)), ('cloth', (230, 230, 230)), ('other', (120, 60, 20))):
        pv[C[k]] = col
    Image.fromarray(pv).save(HERE / 'work' / 'classes_body.png')
save(pad(g, cov), T / f'{X}_basecolor_1k.png'); save(pad(normal, cov), T / f'{X}_normal_1k.png')
save(orm(C, rough_m, cov), T / f'{X}_metal_rough_1k.png')
mask = ndimage.gaussian_filter(pad(C['garment'].astype(float), cov), 0.7)
R.write_mask([mask], T / f'{X}_region_mask.png', size=N)

# ---- ramps: the old project's native palette colours, range refitted to this texture ---------------------------------
old = json.load(open(HERE.parent / CF['ramps_from']))
om = old['materials'][0]
L = R.luminance(g)[C['garment']]                    # linear luminance of the sRGB texels
lo, hi = (float(x) for x in np.percentile(L, [2, 98]))
if CF.get('ramp_spread'):                             # cloth over the ramp's middle tones only: small texel variation
    mid, half = (lo + hi) / 2, (hi - lo) / 2 * CF['ramp_spread']    # stays a small colour variation
    lo, hi = max(0.0, mid - half), min(1.0, mid + half)
ramps = {var: [{'range': [round(lo, 6), round(hi, 6)], 'colors': om['ramps'][var][0]['colors']}] for var in old['variants']}
mats = [{'base': f'{MESH}_A', 'prefix': MESH, 'mask': f'{X}_region_mask.png', 'regions': om['regions'], 'ramps': ramps},
        {'base': f'{MESH}Head_A', 'prefix': f'{MESH}Head', 'mask': f'{X}_head_region_mask.png', 'regions': om['regions'],
         'ramps': ramps}]
out = {'variants': old['variants'], 'materials': mats, 'palettes': om['palettes'],
       'note': f"colours from {CF['ramps_from']} (native palettes); range = 2nd-98th percentile of this texture's garment"}
json.dump(out, open(T / f'{X}_ramps.json', 'w'), indent=1)
print('RAMPS', old['variants'], 'range', round(lo, 4), round(hi, 4), 'garment texels', int(C['garment'].sum()))
