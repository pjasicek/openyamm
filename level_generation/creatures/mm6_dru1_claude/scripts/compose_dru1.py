#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the druidess (CLAUDE_CREATURE_TEXTURES.md; material contract of
mm6_bar1_claude/compose_bar1.py, mask padding of mm6_gob2_claude/compose_gob2.py).

Tiers (palettes 722 Druid / 723 Great Druid / 194 Grand Druid) recolour ONLY the hood and cloak (green -> muted rose
-> blue; mm6_dru1/config.json): one region (R = cloth), shared by the body set (cloak, piece 100) and the head set
(hood, piece 3), so hood and cloak take the same colours in every tier.
Body set (Meshy retexture_v1, its own UV layout, 2K -> 1K), texel classes from the UV raster (piece, rest position) and
colour: cloth = piece 100; gold = yellow texels (armbands, studs, rims, medallion 14); leather = dark brown texels on
the bodysuit (painted on the torso shell, piece 0), boots 6/7, belt 8, bracers 9/10, front panel 11; skin = the rest of
pieces 0, 2, 4, 5 in skin tones.
Grading toward the native tier-A class medians (native_variants, pixels unchanged between palettes): skin fully,
leather and gold GRADE_PART of the way (the sprite's near-black leather read black on Meshy's detail), x ALBEDO.
Rest-pose AO (work/ao_body.png) darkens creases; ORM: R per-class specular mask ("openyamm_specular_mask"), G per-class
roughness around Meshy's detail, B 0.
Ramps (cloth): native pixels that change between the palettes, near-black outline pixels dropped, sorted by tier-A
luminance; each stop takes the native colour at the quantile its luminance has among the cloth texels (body + hood),
x RAMP_GAIN. Head set (head_retexture_v1, HeadUV) when present: face skin matched to the graded body skin at the neck
(one gain), hair as painted (mild grade toward the native hair), hood in the cloth region.
Writes textures/dru1_*. Args: none"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R

T = HERE / 'textures'; T.mkdir(exist_ok=True)
NAT = HERE.parent / 'mm6_dru1' / 'native_variants'
N = 1024
ALBEDO = 1.1
GRADE_PART = 0.6
AO_STRENGTH, AO_FLOOR = 0.5, 0.3
RAMP_CONTRAST = 0.7
RAMP_GAIN = 1.0           # 1.15 read lighter than the sprites in game (thief: 1.3 was 30-40 % too bright)
SKIN_ALBEDO = 0.9         # x1.1 clipped toward white and read pale/grey next to the sprites' warm tan
SURFACE = {'skin': (0.45, 0.5), 'hair': (0.08, 0.85), 'leather': (0.35, 0.6), 'gold': (1.0, 0.3),
           'cloth': (0.15, 0.8), 'other': (0.3, 0.6)}
PALS = {'dru1_a': 722, 'dru1_b': 723, 'dru1_c': 194}
CLOAK, HOOD, HAIR = 100, 3, 1
LEATHER_PIECES = [0, 6, 7, 8, 9, 10, 11]
SKIN_PIECES = [0, 2, 4, 5]


def load(path, mode='RGB'):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((N, N), Image.LANCZOS) if im.size != (N, N) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]
    return out


def classify(rgb, piece):
    h, s, v = hsv(rgb)
    cov = piece >= 0
    c = {}
    c['cloth'] = cov & np.isin(piece, [CLOAK, HOOD])
    c['hair'] = cov & (piece == HAIR)
    rest = cov & ~c['cloth'] & ~c['hair']
    c['gold'] = rest & (h > 34) & (h < 64) & (s > 0.35) & (v > 0.45)
    c['leather'] = rest & ~c['gold'] & np.isin(piece, LEATHER_PIECES) & (v < 0.42) & ((h < 40) | (h > 330)) & (s > 0.3)
    c['skin'] = rest & ~c['gold'] & ~c['leather'] & np.isin(piece, SKIN_PIECES) & (h < 45) & (s > 0.12) & (v > 0.35)
    c['other'] = rest & ~c['gold'] & ~c['leather'] & ~c['skin']
    return c


# ---------------------------------------------------------------- native class colours (tier A, unchanged pixels)
nat = {k: [] for k in ('skin', 'leather', 'gold')}
cols = {k: [] for k in PALS}
for v_ in range(5):
    ims = {k: np.asarray(Image.open(NAT / f'dru1sta{v_}_{p}.png').convert('RGBA'), np.float64) / 255 for k, p in PALS.items()}
    a = ims['dru1_a']; al = a[..., 3] > 0.5
    d = np.maximum(np.abs(ims['dru1_b'][..., :3] - a[..., :3]).max(-1), np.abs(ims['dru1_c'][..., :3] - a[..., :3]).max(-1))
    ch = al & (d > 8 / 255); un = al & ~ch
    h, s, v = hsv(a[..., :3])
    nat['skin'].append(a[..., :3][un & (h > 8) & (h < 40) & (s > 0.15) & (s < 0.55) & (v > 0.6)])
    nat['gold'].append(a[..., :3][un & (h > 38) & (h < 62) & (s > 0.45) & (v > 0.5)])
    nat['leather'].append(a[..., :3][un & (h < 35) & (s > 0.4) & (v > 0.12) & (v < 0.45)])
    for k in PALS:
        cols[k].append(ims[k][..., :3][ch])
TARGET = {k: np.median(np.concatenate(v), 0) for k, v in nat.items()}
cols = {k: np.concatenate(v) for k, v in cols.items()}
print('NATIVE medians', {k: np.round(t * 255).astype(int).tolist() for k, t in TARGET.items()}, 'cloth pixels', len(cols['dru1_a']))

# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png')
rough = load(M / 'texture_urls_0_roughness.png', 'L')
normal = load(M / 'texture_urls_0_normal.png')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece, pos = Rz['piece'], Rz['pos']
cov = piece >= 0
cls = classify(base, piece)
# leather vs skin on the torso shell by 3D neighbourhood (review 1: Meshy painted dark shadow/hair tones onto skin faces;
# by colour they counted as leather, survived the skin repaint and showed as dark blotches): the leather fraction of
# piece-0 texels is voxelised (VOX), smoothed in 3D (sigma VOX_SIG voxels) and a texel is leather only where its
# neighbourhood is mostly leather (the bodysuit is one large region; blotches are a few faces)
VOX, VOX_SIG = 0.01, 2.0
m0 = (piece == 0) & ~cls['gold']
P0 = pos[m0]; lo3 = P0.min(0); ijk = np.floor((P0 - lo3) / VOX).astype(int); shape = ijk.max(0) + 1
tot = np.zeros(shape); lea = np.zeros(shape)
np.add.at(tot, tuple(ijk.T), 1.0); np.add.at(lea, tuple(ijk.T), cls['leather'][m0].astype(float))
frac = ndimage.gaussian_filter(lea, VOX_SIG) / np.maximum(ndimage.gaussian_filter(tot, VOX_SIG), 1e-6)
lea3 = frac[tuple(ijk.T)] > 0.5
before = int(cls['leather'][m0].sum())
L0 = np.zeros_like(cls['leather']); L0[m0] = lea3
# bright texels inside the leather neighbourhood are the skin along the V edge (review 1: pale lavender slivers): skin
_h, _s, _v = hsv(base)
L0 &= ~((_v > 0.55) & ~cls['gold'])
cls['leather'] = (cls['leather'] & (piece != 0)) | L0
cls['skin'] = cls['skin'] | (m0 & ~L0 & ~cls['cloth'])
cls['other'] = cls['other'] & ~(m0 & ~L0)
print('TORSO leather by 3D majority: texels', before, '->', int(L0.sum()))
print('CLASSES texels', {k: int(v.sum()) for k, v in cls.items()})
graded = base.copy()
for k, part in (('skin', 1.0), ('leather', GRADE_PART), ('gold', GRADE_PART)):
    m = cls[k]
    med = np.median(base[m], 0)
    gain = (np.clip(TARGET[k] * (SKIN_ALBEDO if k == 'skin' else ALBEDO), 0, 1) / np.maximum(med, 1e-3)) ** part
    graded[m] = base[m] * gain
    print('GRADE', k, 'median', np.round(med * 255).astype(int).tolist(), '-> gain', np.round(gain, 2).tolist())
# painted hair on the neck/upper chest (Meshy projected the hair hanging in the references onto the skin under it;
# beside the head set it read as patches): skin texels above NECK_Z (body) and below the chin (head set) are repainted
# with the chest skin colour times their own fine shading
NECK_Z = 1.22


def flatten(img, skin_m, zone, target_rgb, sigma=6.0, flat=False):
    """Repaint skin texels in the zone with the target skin colour times the texture's own fine shading (luminance
    over its local skin-only blur, clamped 0.85-1.1): the painted hair colour and shadow go, the fine detail stays."""
    L = R.luminance(img)
    w = skin_m.astype(float)
    blur = ndimage.gaussian_filter(L * w, sigma) / np.maximum(ndimage.gaussian_filter(w, sigma), 1e-4)
    detail = np.clip(L / np.maximum(blur, 1e-4), 0.95, 1.05)   # +-15 % kept the patch edges (review 1)
    if flat:                                                # review 2: any UV-space detail differs per island
        detail = np.ones_like(L)
    m = skin_m & zone
    out = img.copy(); out[m] = np.clip(np.asarray(target_rgb)[None, :] * detail[m][:, None], 0, 1)
    return out, int(m.sum())


SKIN_RGB = np.median(graded[cls['skin'] & (pos[..., 2] > 1.0) & (pos[..., 2] < 1.2)], 0)   # chest/midriff skin
# saturated once here (in game the lit skin read pale grey next to the sprites' warm tan); every skin repaint (body,
# head-set neck) and the face match use this one colour (review 1: separate saturation passes left a tone seam at the
# neck and an orange face)
SKIN_SAT = 1.4
SKIN_RGB = np.clip(SKIN_RGB.mean() + (SKIN_RGB - SKIN_RGB.mean()) * SKIN_SAT, 0, 1)
# the neck between the shoulder straps, by position (hair-painted texels there are not 'skin' by colour)
# (a cylinder round the neck joint: the bodysuit straps rise beside the neck and an x band repainted them)
NECK_AXIS = np.array(json.load(open(HERE / 'work' / 'joints_final.json'))['joints']['Neck'][:2])
neck_zone = (pos[..., 2] > 1.34) & (np.hypot(pos[..., 0] - NECK_AXIS[0], pos[..., 1] - NECK_AXIS[1]) < 0.065)
graded, ng = flatten(graded, (piece == 0) & ~cls['gold'], neck_zone, SKIN_RGB)
# user review 1: "triangle-polygon-like patches shaded on the skin" (upper arm, thigh, neck): Meshy's projection left
# whole faces in another tone where the references occluded them (cloak, hair, the other leg). All body skin (skin
# pieces minus leather, gold, cloth texels) is repainted the same way with a finer detail (sigma 3) so no patch tone
# survives; the form comes from the AO, the normal map and the lighting.
# the neck between the straps is skin whatever its colour or neighbourhood (review 1: the 3D majority rule kept some
# hair-painted neck texels as leather: near-black texels and full AO under the head set's brighter neck)
nz = (piece == 0) & neck_zone & ~cls['gold']
cls['leather'] &= ~nz; cls['other'] &= ~nz; cls['skin'] |= nz
skin_all = np.isin(piece, SKIN_PIECES) & ~cls['leather'] & ~cls['gold'] & ~cls['cloth']
graded, na = flatten(graded, skin_all, skin_all, SKIN_RGB, flat=True)
print('SKIN repaint texels', na)
print('NECK repaint: skin', np.round(SKIN_RGB * 255).astype(int).tolist(), 'texels', ng)
# skin saturation (in game the lit skin read pale grey next to the sprites' warm tan): chroma around the luminance x SKIN_SAT


def saturate(img, m, k):
    lum = img[m].mean(1, keepdims=True)
    out = img.copy(); out[m] = np.clip(lum + (img[m] - lum) * k, 0, 1)
    return out


ao = load(HERE / 'work' / 'ao_body.png', 'L')
aof = (1 - AO_STRENGTH * (1 - np.maximum(ao, AO_FLOOR)))
aof[cls['cloth']] = 1.0     # the cloak moves (rest-pose AO turned occluded inner faces into black patches via the ramp)
# skin: the rest-pose bake counts the hanging hair and cloak over the shoulders, which move (review 1: brown patches on
# the shoulders, 25-30 % darker): a weak skin AO (strength 0.25, floor 0.6) keeps only the body's own creases
# review 2 (patches still visible): the AO bake is per UV island too; the skin's AO is averaged in 3D (1 cm voxels,
# Gaussian 2 voxels), so its value depends only on the position on the body, never on the island a texel sits in
sk_ao = 1 - 0.3 * (1 - np.maximum(ao, 0.5))
VX = 0.01
Ps = pos[skin_all]; lo_s = Ps.min(0); ij = np.floor((Ps - lo_s) / VX).astype(int); shp = ij.max(0) + 1
acc_a = np.zeros(shp); acc_n = np.zeros(shp)
np.add.at(acc_a, tuple(ij.T), sk_ao[skin_all]); np.add.at(acc_n, tuple(ij.T), 1.0)
ao3 = ndimage.gaussian_filter(acc_a, 2.0) / np.maximum(ndimage.gaussian_filter(acc_n, 2.0), 1e-6)
ao3_n = ndimage.gaussian_filter(acc_n, 2.0)


def ao_at(P):
    """3D-smoothed skin AO at positions P (n x 3); 1 where no body skin is near."""
    k = np.clip(np.floor((P - lo_s) / VX).astype(int), 0, np.array(shp) - 1)
    v = ao3[tuple(k.T)]; n = ao3_n[tuple(k.T)]
    return np.where(n > 0.05, v, 1.0)


aof[skin_all] = ao_at(pos[skin_all])
# no skin AO on the neck (review 2: the head-set neck has no AO data; mixing filled and empty voxels stepped between
# triangles): faded out over z 1.30-1.36 in the body set, none in the head set
fz = np.clip((pos[..., 2] - 1.30) / 0.06, 0, 1)
aof[skin_all] = 1 - (1 - aof[skin_all]) * (1 - fz[skin_all])
graded *= aof[..., None]
graded = np.clip(graded, 0, 1)
# choker (review 2: only a painted sliver at the front): a gold ring on the neck skin by 3D position, in both texture
# sets, z CHOKER_Z, round the neck axis; shaded by the same AO and a soft top highlight
CHOKER_Z = (1.400, 1.416)                  # the painted sliver on the body set (z 1.404-1.415)
CHOKER_RGB = np.clip(TARGET['gold'] * ALBEDO * 1.15, 0, 1)


def choker(img, P, m):
    band = m & (P[..., 2] > CHOKER_Z[0]) & (P[..., 2] < CHOKER_Z[1]) & (np.hypot(P[..., 0] - NECK_AXIS[0], P[..., 1] - NECK_AXIS[1]) < 0.075)
    t = (P[..., 2] - CHOKER_Z[0]) / (CHOKER_Z[1] - CHOKER_Z[0])
    shade = 0.75 + 0.4 * np.sin(np.pi * np.clip(t, 0, 1))
    out = img.copy(); out[band] = np.clip(CHOKER_RGB[None, :] * shade[band][:, None], 0, 1)
    return out, band


cls['gold'] &= ~((piece == 0) & neck_zone)             # the old painted sliver: skin first, then the ring
graded, ch_b = choker(graded, pos, (piece == 0))
cls['gold'] |= ch_b; cls['skin'] &= ~ch_b
print('CHOKER body texels', int(ch_b.sum()))


def surface_maps(classes, meshy_rough, shape):
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


# ---------------------------------------------------------------- head set (optional)
HM = HERE / 'meshy' / 'head_retexture_v1'
head = (HM / 'texture_urls_0_base_color.png').exists()
BAKED = (HERE / 'work' / 'bake_face_color.png').exists()   # face graft (face_bake.py, review 3)
if head:
    Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
    hp, hpos = Rh['piece'], Rh['pos']; hcov = hp >= 0
    if BAKED:
        # head set = the previous composed head (hair, hood, neck) baked into the new HeadUV, with the face from the
        # head-only Meshy model inside a 3D face mask (the face ellipse of face_bake.py, feathered over its outer 25 %);
        # the model's skin tone is matched to the body skin colour on skin-hued face texels
        FC_, FR_ = (-0.007, 1.553), (0.058, 0.080)
        prev_c = load(HERE / 'work' / 'bake_prev_color.png')
        # colour by nearest model surface point (face_nearest.py: the ray-cast bake left shards and holes where our face
        # geometry differs from the model's); the ray-cast bake stays the source of the face normals
        face_c = load(HERE / 'work' / 'near_face_color.png')
        face_hit = load(HERE / 'work' / 'bake_face_color.png').max(-1) > 0.02
        ef = np.hypot((hpos[..., 0] - FC_[0]) / FR_[0], (hpos[..., 2] - FC_[1]) / FR_[1])
        inmask = (hp == 0) & (hpos[..., 1] < -0.05) & (ef < 1.0)
        # bake misses (rays that found no model surface: mouth corners) take the nearest baked face texel, not the old
        # texture (dark dots at the mouth corners)
        hit = face_c.max(-1) > 0.02
        _, (iy_, ix_) = ndimage.distance_transform_edt(~(hit & (hp == 0)), return_indices=True)
        miss = inmask & ~hit
        face_c[miss] = face_c[iy_[miss], ix_[miss]]
        _fh, _fs, _fv = hsv(face_c)
        # the model's hair falls over its temples: hair-dark texels in the outer face (ellipse > 0.55) stay skin
        lat = np.clip((np.abs(hpos[..., 0] - FC_[0]) - 0.025) / 0.012, 0, 1)
        hairline = (hpos[..., 2] > 1.603) | (np.abs(hpos[..., 0] - FC_[0]) > 0.05)    # above the brows / past the brow ends
        hairy = hairline & (_fv < 0.42) & (_fh < 45)
        hairy = ndimage.binary_dilation(hairy, iterations=2) & hairline
        # the face ellipse stops before the temples and the hairline (the model's hair falls over them) and fades into
        # the flat skin over its outer 45 % (hard hairline masks left blotch edges, review 3)
        efs = np.hypot((hpos[..., 0] - FC_[0]) / 0.050, (hpos[..., 2] - 1.550) / 0.068)
        # the face colour (with the model's own temple/hairline darkening) reaches the edge of the face; the flat-skin
        # band left between the shaded face and the hair read as pale chips (review 4)
        # below the eyes (cheeks, mouth, jaw) the face colour reaches the edge of the face (a flat-skin band there read
        # as pale chips, review 4); above, the narrower ellipse (the model's hairline and hood paint stay out)
        fw_lo = np.clip((1.2 - ef) / 0.25, 0, 1)
        fw_hi = np.clip((1.0 - efs) / 0.45, 0, 1)
        up = np.clip((hpos[..., 2] - 1.555) / 0.015, 0, 1)
        fw = fw_lo * (1 - up) + fw_hi * up; fw = fw * fw * (3 - 2 * fw) * inmask
        fw = fw * (1 - np.clip((efs - 0.82) / 0.1, 0, 1) * up * lat)  # temples: hair colour wins over the face paint
        fskin = (fw > 0.9) & (_fh > 12) & (_fh < 40) & (_fs > 0.2) & (_fs < 0.6) & (_fv > 0.4)
        fgain = SKIN_RGB / np.maximum(np.median(face_c[fskin], 0), 1e-3)
        prev_c[hp == 0] = SKIN_RGB                     # all head skin outside the face: flat skin (no old hairline paint)
        # head skin beside and above the face (temples, hairline; above the jaw) is under the jagged hair shell: hair
        # colour there, so the shell's edge does not show pale skin chips (review 3)
        HAIR_RGB0 = np.clip(np.array([66, 48, 41]) / 255 * ALBEDO * 1.15, 0, 1)
        # at the temples (above the cheekbones) the hair colour starts further in (review 4: light faceted wedges)
        lat = np.clip((np.abs(hpos[..., 0] - FC_[0]) - 0.025) / 0.012, 0, 1)        # sides only, not the forehead
        s0 = 1.0 - 0.12 * np.clip((hpos[..., 2] - 1.55) / 0.02, 0, 1) * lat
        side = np.clip((efs - s0) / 0.12, 0, 1) * (hp == 0) * np.clip((hpos[..., 2] - 1.50) / 0.02, 0, 1)
        prev_c = prev_c * (1 - side[..., None]) + HAIR_RGB0 * side[..., None]
        hb = prev_c * (1 - fw[..., None]) + np.clip(face_c * fgain, 0, 1) * fw[..., None]
        print('FACEGRAFT face texels', int((fw > 0).sum()), 'skin-tone gain', np.round(fgain, 2).tolist())
    else:
        hb = load(HM / 'texture_urls_0_base_color.png')
    hcls = classify(hb, hp)
    hg = hb.copy()
    body_neck = cls['skin'] & (pos[..., 2] > 1.30)
    tgt = SKIN_RGB
    face = hcls['skin']
    gain = tgt / np.maximum(np.median(hb[face], 0), 1e-3)
    skinish = (hp == 0)                                  # one gain over the whole face/neck shell (no seams)
    hg[skinish & ~hcls['gold']] = hb[skinish & ~hcls['gold']] * gain
    if hcls['gold'].any():
        g = (np.clip(TARGET['gold'] * ALBEDO, 0, 1) / np.maximum(np.median(hb[hcls['gold']], 0), 1e-3)) ** GRADE_PART
        hg[hcls['gold']] = hb[hcls['gold']] * g
    # hair toward the native dark brown (Meshy painted it near-black)
    HAIR_RGB = np.array([66, 48, 41]) / 255
    hm = hcls['hair'] | ((hp == HAIR) & ~hcls['gold'])
    # repainted as the native colour times the strands' own detail: per-channel gains on Meshy's olive-brown hair
    # turned it red
    hL = R.luminance(hb); hblur = ndimage.gaussian_filter(hL * hm, 8) / np.maximum(ndimage.gaussian_filter(hm.astype(float), 8), 1e-4)
    hdet = np.clip(hL / np.maximum(hblur, 1e-4), 0.55, 1.5)
    hg[hm] = np.clip(np.clip(HAIR_RGB * ALBEDO * 1.15, 0, 1)[None, :] * hdet[hm][:, None], 0, 1)
    print('HEAD hair repainted', int(hm.sum()), 'texels; Meshy median', np.round(np.median(hb[hm], 0) * 255).astype(int).tolist())
    hg = np.clip(hg, 0, 1)
    hskin_all = (hp == 0) & ~hcls['gold']
    # the neck under the hanging hair carries the same painted shadow as the body's: flattened to the same target
    # neck: repainted below 1.48 m, blended into the face's own paint up to 1.505 m (the lips start at ~1.51)
    hrep, hng = flatten(hg, hskin_all, hpos[..., 2] < 1.512, SKIN_RGB, flat=True)
    wz = np.clip((1.512 - hpos[..., 2]) / (1.512 - 1.495), 0, 1)[..., None]   # under the chin flat too (review 2)
    hg = np.where(hskin_all[..., None], hrep * wz + hg * (1 - wz), hg)
    # the same 3D skin AO as the body (review 2: the un-AO'd head-set neck met the AO'd chest in patches)
    hao = np.ones(hp.shape)
    hg = np.clip(hg * hao[..., None], 0, 1)
    hneck_gold = (hp == 0) & hcls['gold'] & (hpos[..., 2] < 1.49)
    hg[hneck_gold] = SKIN_RGB * hao[hneck_gold][:, None]
    # hood lining (review 5: a black jagged patch above the forehead was the hood's inside seen through the notch of
    # the hair shell): Meshy painted the lining in deep baked shadow and the cloth ramp maps it to near black. The
    # engine lights the inside of the hood itself, so hood texels get a luminance floor (the hood's 40th percentile),
    # hue kept
    hood = hp == HOOD
    hl_ = R.luminance(hg)
    floor_ = np.percentile(hl_[hood], 40)
    dark = hood & (hl_ < floor_)
    hg[dark] = np.clip(hg[dark] * (floor_ / np.maximum(hl_[dark], 1e-4))[:, None], 0, 1)
    print('HOOD lining texels lifted', int(dark.sum()), 'to luminance', round(float(floor_), 4))
    hg, hch = choker(hg, hpos, hp == 0)
    hcls['gold'] = (hcls['gold'] & ~hneck_gold) | hch
    print('CHOKER head texels', int(hch.sum()))
    print('HEAD neck repaint texels', hng)
    if not BAKED:                                      # the patch steps of reviews 1-2 (old head layout only)
        # eyes on the eye caps: the HD head reference's own eyes (eye_uv.py fits each cap's lid opening onto the same
        # eye's opening; user review 1: the painted disc read as a doll's eye). Each crop is pasted into its atlas square,
        # with a 2 px edge padding so filtering does not pull in the neighbouring texels
        # lids and brows re-projected from the HD front head reference (review 1 follow-up: the head UV layout splits the
        # lids into tiny islands that Meshy painted inconsistently - shards round the eyes). Front orthographic alignment
        # from the two eye centres (model loop centroids <-> reference iris centres); face texels within EYE_R of an eye,
        # facing forward, take the reference colour (x a per-channel gain matching the reference skin to the face tone),
        # blended out over the outer 25 %
        REFH = np.asarray(Image.open(HERE / 'references_head' / '00_front.png').convert('RGB'), np.float64) / 255
        E_MOD = {'R': (-0.0310, 1.5734), 'L': (0.0178, 1.5726)}; E_REF = {'R': (548.5, 453.5), 'L': (711.0, 452.5)}
        k_ = (E_REF['L'][0] - E_REF['R'][0]) / (E_MOD['L'][0] - E_MOD['R'][0])
        rx = E_REF['R'][0] + (hpos[..., 0] - E_MOD['R'][0]) * k_
        ry = E_REF['R'][1] - (hpos[..., 2] - E_MOD['R'][1]) * k_
        ix = np.clip(np.round(rx).astype(int), 0, REFH.shape[1] - 1); iy = np.clip(np.round(ry).astype(int), 0, REFH.shape[0] - 1)
        proj = REFH[iy, ix]
        EYE_R = 0.024
        dmin = np.minimum(np.hypot(hpos[..., 0] - E_MOD['R'][0], hpos[..., 2] - E_MOD['R'][1]),
                          np.hypot(hpos[..., 0] - E_MOD['L'][0], hpos[..., 2] - E_MOD['L'][1]))
        front = (hp == 0) & (hpos[..., 1] < -0.085) & (dmin < EYE_R)
        ringm = front & (dmin > 0.017) & hcls['skin']
        gain_ = np.median(hg[ringm], 0) / np.maximum(np.median(proj[ringm], 0), 1e-3)
        w_ = np.clip((EYE_R - dmin) / (0.25 * EYE_R), 0, 1)[..., None] * front[..., None]
        hg = np.clip(hg * (1 - w_) + proj * gain_ * w_, 0, 1)
        print('EYEPROJ texels', int(front.sum()), 'gain', np.round(gain_, 2).tolist(), 'px/m', round(k_))
        # Meshy projected the reference eye's white sclera onto the lid faces round the hole (review 1: shards round the
        # eyes, worse on her left eye): near-white, unsaturated face texels within 1.3 cm of an eye centre become the
        # surrounding face skin tone (median of the face skin 1.3-2.5 cm from the eye)
        _hh, _hs, _hv = hsv(hg)                              # after the projection: it paints sclera onto lid skin too
        for ec_ in ([0.017, -0.107, 1.573], [-0.030, -0.107, 1.573]):
            d_ = np.linalg.norm(hpos - np.array(ec_), axis=-1)
            ring = (hp == 0) & (d_ > 0.013) & (d_ < 0.025) & hcls['skin']
            tone = np.median(hg[ring], 0)
            shard = (hp == 0) & (d_ < 0.016) & (_hv > 0.7) & (_hs < 0.3)
            hg[shard] = tone
            print('EYELID shards', int(shard.sum()), 'tone', np.round(tone * 255).astype(int).tolist())
        # mouth re-projected from the HD front head reference (review 2: "lips may need more attention"): its own affine
        # (the eye alignment put the mouth 5 mm low) from the painted lips' bounding box on the model (x -2.2..+1.0 cm,
        # z 1.513..1.527 m) onto the reference lips (x 568..687, y 592..638 px); an ellipse 3.4 x 1.9 cm round the mouth,
        # forward-facing texels, blended out over its outer 30 %, skin matched to the face tone
        MB = (-0.022, 1.513, 0.010, 1.527); RB = (568.0, 592.0, 687.0, 638.0)
        kx = (RB[2] - RB[0]) / (MB[2] - MB[0]); kz = (RB[3] - RB[1]) / (MB[3] - MB[1])
        mx = RB[0] + (hpos[..., 0] - MB[0]) * kx; my = RB[1] + (MB[3] - hpos[..., 2]) * kz
        mproj = REFH[np.clip(np.round(my).astype(int), 0, REFH.shape[0] - 1), np.clip(np.round(mx).astype(int), 0, REFH.shape[1] - 1)]
        cxm, czm = (MB[0] + MB[2]) / 2, (MB[1] + MB[3]) / 2
        e_ = np.hypot((hpos[..., 0] - cxm) / 0.034, (hpos[..., 2] - czm) / 0.019)
        mfront = (hp == 0) & (hpos[..., 1] < -0.095) & (e_ < 1.0)
        _ph, _ps, _pv = hsv(mproj)
        mring = mfront & (_ph > 14) & (_ph < 40) & (_ps < 0.55)        # skin-hued reference pixels only (no lip red)
        mgain = np.median(SKIN_RGB[None, :] * np.ones((int(mring.sum()), 1)), 0) / np.maximum(np.median(mproj[mring], 0), 1e-3)
        mw = np.clip((1.0 - e_) / 0.3, 0, 1)[..., None] * mfront[..., None]
        hg = np.clip(hg * (1 - mw) + mproj * mgain * mw, 0, 1)
        print('MOUTHPROJ texels', int(mfront.sum()), 'gain', np.round(mgain, 2).tolist(), 'px/m', round(kx), round(kz))
        EM = json.load(open(HERE / 'work' / 'eye_map.json'))
        REF = Image.open(HERE / 'references_head' / '00_front.png').convert('RGB')
        for side, e in EM.items():
            S_ = e['size']; X0, Y0 = e['square']
            patch = np.asarray(REF.crop(tuple(int(round(c)) for c in e['crop'])).resize((S_, S_), Image.LANCZOS), np.float64) / 255
            ph, ps, pv_ = hsv(patch)
            sk_ = (ph < 40) & (ps > 0.25) & (pv_ > 0.35)          # the crop's lid skin takes the face tone (pale cap corners)
            patch[sk_] = np.clip(patch[sk_] * gain_, 0, 1)
            patch[(pv_ > 0.6) & (ps < 0.25)] *= 0.85              # sclera a little darker (it read as a stare in the viewer)
            P2 = np.pad(patch, ((2, 2), (2, 2), (0, 0)), mode='edge')
            hg[Y0 - 2:Y0 + S_ + 2, X0 - 2:X0 + S_ + 2] = P2
            hcov[Y0 - 2:Y0 + S_ + 2, X0 - 2:X0 + S_ + 2] = True
        print('EYES pasted from the head reference', {k: v['square'] for k, v in EM.items()})
    print('HEAD classes', {k: int(v.sum()) for k, v in hcls.items()}, 'face gain', np.round(gain, 2).tolist())

# ---------------------------------------------------------------- calmer cloth (review 6: dark dots on the cloak)
# Meshy's velvet mottle (fine speckle) became high-contrast dots through the ramp: per set, the cloth luminance's
# fine part (around a SPECK_SIG px masked blur) is kept at SPECK_K; the large fold shading stays


def calm_speckle(img, m, sig=1.5, k=0.6):
    """only the finest speckle (below a 1.5 px masked blur) at k: larger blurs exposed island-level tone steps"""
    L = R.luminance(img); w = m.astype(float)
    blur = ndimage.gaussian_filter(L * w, sig) / np.maximum(ndimage.gaussian_filter(w, sig), 1e-4)
    L2 = blur + (L - blur) * k
    out = img.copy(); out[m] = np.clip(img[m] * (L2[m] / np.maximum(L[m], 1e-5))[:, None], 0, 1)
    return out


graded = calm_speckle(graded, cls['cloth'])
if head:
    hg = calm_speckle(hg, hcls['cloth'])
# ---------------------------------------------------------------- hood matches the cloak (review 6)
# the hood (head set) was painted ~30 % darker than the cloak (median luminance 0.047 vs 0.066), so the shared ramp put
# it on its darkest stops: in game a black-green hood over a green cloak. Each hood texel's luminance is mapped to the
# cloak's luminance at the same rank (quantile matching), hue kept.
if head:
    hood_m = hcls['cloth']
    lb_ = np.sort(R.luminance(graded)[cls['cloth']]); lh_ = R.luminance(hg)[hood_m]
    rank = np.argsort(np.argsort(lh_)) / max(len(lh_) - 1, 1)
    tgt_l = lb_[np.clip((rank * (len(lb_) - 1)).astype(int), 0, len(lb_) - 1)]
    hg[hood_m] = np.clip(hg[hood_m] * (tgt_l / np.maximum(lh_, 1e-5))[:, None], 0, 1)
    print('HOOD matched to the cloak: median', round(float(np.median(lh_)), 4), '->', round(float(np.median(tgt_l)), 4))
# ---------------------------------------------------------------- cloth ramps (body cloak + head hood)
LUMA = np.array([0.2126, 0.7152, 0.0722])
sel = cols['dru1_a'].max(1) > 0.06
lin_a = R.srgb_to_linear(cols['dru1_a'][sel]); order = np.argsort(lin_a @ LUMA)
lum = R.luminance(graded)[cls['cloth']]
if head:
    lum = np.r_[lum, R.luminance(hg)[hcls['cloth']]]
lum = np.sort(lum)
lo, hi = np.percentile(lum, [2, 98])
ramps = {}
for k in PALS:
    lin = R.srgb_to_linear(cols[k][sel])[order]
    stops = []
    for i in range(16):
        q = np.searchsorted(lum, lo + i / 15 * (hi - lo)) / len(lum)
        q = min(max(q, 0.18), 0.98)          # the lowest stops stay off the sprite's darkest shades (review 6: black dots)
        c = int(q * (len(lin) - 1)); w = max(4, len(lin) // 40)
        stops.append(np.clip(np.median(lin[max(0, c - w):c + w], 0) * RAMP_GAIN, 0, 1))
    # contrast toward the middle stop (review 6): rank matching spreads every paint variation over the whole native
    # palette, so mottle and island tone steps became near-black/bright patches
    mid = stops[8]
    stops = [mid + (st - mid) * RAMP_CONTRAST for st in stops]
    ramps[k] = [{'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': [[round(float(x), 6) for x in s] for s in stops]}]
report = {'native_pixels': int(sel.sum()), 'texels_body': int(cls['cloth'].sum()),
          'texels_head': int(hcls['cloth'].sum()) if head else 0, 'range': [float(lo), float(hi)], 'ramp_gain': RAMP_GAIN}
print('RAMPS', report)

# ---------------------------------------------------------------- write the body set
graded_p = pad(graded, cov)
save(graded_p, T / 'dru1_basecolor_1k.png'); save(pad(normal, cov), T / 'dru1_normal_1k.png')
spec_r, rough_g = surface_maps({k: cls[k] for k in SURFACE}, rough, (N, N))
save(np.stack([spec_r, rough_g, np.zeros_like(rough)], -1), T / 'dru1_metal_rough_1k.png')
cloth_m = pad(cls['cloth'].astype(float), cov)
R.write_mask([ndimage.gaussian_filter(cloth_m, 0.7)], T / 'dru1_region_mask.png', size=N)
cmap = np.zeros((N, N), np.uint8)
for k, lab in (('skin', 1), ('hair', 2), ('leather', 8), ('cloth', 8), ('gold', 9), ('other', 11)):
    cmap[cls[k]] = lab
Image.fromarray(cmap).save(T / 'dru1_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Druidess_A', 'prefix': 'Druidess', 'mask': 'dru1_region_mask.png', 'regions': ['cloth'],
                      'palettes': PALS, 'ramps': ramps, 'report': report}]}
if head:
    save(pad(hg, hcov), T / 'dru1_head_basecolor_1k.png')
    if BAKED:
        fnorm = load(HERE / 'work' / 'bake_face_normal.png')
        fnorm[~face_hit] = (0.5, 0.5, 1.0)                     # ray misses: flat (the geometry carries the shape)
        # review 4: Blender-baked tangent-space face normals do not match the tangents the viewer/engine derive, so
        # every UV island border lit as a seam (cracks across the cheeks, mouth corners); the face shape is in the
        # geometry (face_bake.py moved our face onto the model), so the face normals are flat
        fnorm[:] = (0.5, 0.5, 1.0)
        hn = load(HERE / 'work' / 'bake_prev_normal.png') * (1 - fw[..., None]) + fnorm * fw[..., None]
        save(pad(hn, hcov), T / 'dru1_head_normal_1k.png')
        hr = np.full((N, N), 0.6)
    else:
        save(pad(load(HM / 'texture_urls_0_normal.png'), hcov), T / 'dru1_head_normal_1k.png')
        hr = load(HM / 'texture_urls_0_roughness.png', 'L')
    hspec, hrough = surface_maps({k: hcls[k] for k in SURFACE}, hr, (N, N))
    save(np.stack([hspec, hrough, np.zeros_like(hr)], -1), T / 'dru1_head_metal_rough_1k.png')
    R.write_mask([ndimage.gaussian_filter(pad(hcls['cloth'].astype(float), hcov), 0.7)], T / 'dru1_head_region_mask.png', size=N)
    hc = np.zeros((N, N), np.uint8)
    for k, lab in (('skin', 1), ('hair', 2), ('cloth', 8), ('gold', 9), ('other', 11)):
        hc[hcls[k]] = lab
    Image.fromarray(hc).save(T / 'dru1_head_material_classes.png')
    cfg['materials'].append({'base': 'DruidessHead_A', 'prefix': 'DruidessHead', 'mask': 'dru1_head_region_mask.png',
                             'regions': ['cloth'], 'palettes': PALS, 'ramps': ramps})
(T / 'dru1_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
print('WROTE', T)
