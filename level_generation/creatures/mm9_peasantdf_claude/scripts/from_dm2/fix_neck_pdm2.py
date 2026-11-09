#!/usr/bin/env python3
"""Neck under the beard (PeasantM1/DM1 collar-paint lesson): the head references show the tunic's knitted neckline round
the neck, so the head retexture painted the lowest neck faces (y < NECK_TOP, all round the neck) as dark knit with
orange specks, a "leopard" rim inside the real collar. Dark head texels there (lum < 85: the beard and hair are light and
stay) take the tier's own skin (median cheek colour) darkened toward the collar, with 15 % of the paint's fine
luminance detail (35 % kept the knit's island-edge lines as dark scratches), on a soft mask; gutters refilled.
Rewrites textures/<prefix>_head_basecolor.png (backup <prefix>_head_basecolor_preneck.png on the first run).
Usage (project folder): fix_neck_pdm2.py <export glb> <prefix> [...]"""
import os, sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
NECK_TOP = 0.955      # m above the floor (export GLB rest pose): the knit-painted ring lies below this
glb, prefixes = sys.argv[1], sys.argv[2:]
N = 2048
pos, cov = texel_positions(glb, 'PeasantDM2Head', N)
y = np.nan_to_num(pos[..., 1]); x = np.nan_to_num(pos[..., 0]); z = np.nan_to_num(pos[..., 2])
zone = cov & (np.abs(x) < 0.16) & (y < NECK_TOP)
# face pass 2026-11-02: the knit also covers the neck sides and back up to 1.02 m (behind the face, z < 0.05; the hair is a
# separate part and light, the lips and nostrils are in front)
zone |= cov & (np.abs(x) < 0.16) & (y >= NECK_TOP) & (y < float(os.environ.get('NECK_SIDE_TOP', 1.02))) & (z < 0.05)
cheek = cov & (y > 1.035) & (y < 1.07) & (np.abs(x) > 0.025) & (np.abs(x) < 0.07) & (z > 0.10)
for p in prefixes:
    f = Path(f'textures/{p}_head_basecolor.png')
    bk = Path(f'textures/{p}_head_basecolor_preneck.png')
    if not bk.exists():
        shutil.copyfile(f, bk)
    img = np.asarray(Image.open(bk).convert('RGB'), float)
    lum = img @ [0.299, 0.587, 0.114]
    ref = np.median(img[cheek], 0)
    chroma = img / np.maximum(img.sum(-1, keepdims=True), 1)
    dist = np.linalg.norm(chroma - ref / ref.sum(), axis=-1)
    mx_, mn_ = img.max(-1), img.min(-1)
    sat = (mx_ - mn_) / np.maximum(mx_, 1)
    # the knit is dark and saturated brown and lies behind the beard (z < 0.07); the beard's dark strand gaps are grey
    # and further forward: growing the mask into them turned the beard tip pink, so growth needs saturation
    nb = zone & (z < float(os.environ.get('NECK_Z', 0.115)))
    bad = nb & (lum < 85) & (sat > 0.35)
    bad = ndimage.binary_dilation(ndimage.binary_closing(bad, iterations=3), iterations=6) & nb & (sat > 0.3)
    w = ndimage.gaussian_filter(bad.astype(float), 2.0) * nb
    shade = (0.5 + 0.3 * np.clip((y - 0.88) / (NECK_TOP - 0.88), 0, 1))[..., None]
    detail = np.clip(lum - ndimage.gaussian_filter(lum, 4), -6, 6)[..., None] * 0.15
    out = img * (1 - w[..., None]) + (ref[None, None] * shade + detail) * w[..., None]
    near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    # thin dark strokes in the neck skin (Meshy's knit seams, too light for the knit test): texels much darker than a
    # 7 px grey closing take the closed colour (skin only: saturated, behind the beard)
    clo = np.stack([ndimage.grey_closing(out[..., c], size=(7, 7)) for c in range(3)], -1)
    cmx, cmn = clo.max(-1), clo.min(-1)
    csat = (cmx - cmn) / np.maximum(cmx, 1)
    skinz = nb & (csat > 0.3)                    # the surroundings are skin (the beard's closing is grey: left alone)
    dl = (clo @ [0.299, 0.587, 0.114]) - (out @ [0.299, 0.587, 0.114])
    line = skinz & (dl > 10)
    lw = ndimage.gaussian_filter(line.astype(float), 1.0) * skinz
    out = out * (1 - lw[..., None]) + clo * lw[..., None]
    print('FIXNECK lines', p, int(line.sum()))
    out[~cov] = out[iy[~cov], ix[~cov]]          # every gutter from its nearest island texel (old dark knit bled in at seams)
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
    print('FIXNECK', p, 'skin ref', ref.round(), 'texels recoloured', int((w > 0.5).sum()))

# ---- normal map: Meshy's head normal carries the knit's rib and seam lines on the neck, which shaded as dark scratches
# on the repainted skin. Inside the neck zone (behind the beard, saturated texels) the 1K head normal is eased to flat
# (20 % of its own detail kept). Backup <prefix>_head_normal_1k_preneck.png on the first run.
pos1, cov1 = texel_positions(glb, 'PeasantDM2Head', 1024)
y1 = np.nan_to_num(pos1[..., 1]); x1 = np.nan_to_num(pos1[..., 0]); z1 = np.nan_to_num(pos1[..., 2])
nz = cov1 & (np.abs(x1) < 0.16) & (y1 < NECK_TOP + 0.01) & (z1 < float(os.environ.get('NECK_Z', 0.115)))
for p in prefixes:
    f = Path(f'textures/{p}_head_normal_1k.png')
    bk = Path(f'textures/{p}_head_normal_1k_preneck.png')
    if not bk.exists():
        shutil.copyfile(f, bk)
    nm = np.asarray(Image.open(bk).convert('RGB'), float)
    col = np.asarray(Image.open(f'textures/{p}_head_basecolor.png').convert('RGB').resize((1024, 1024), Image.BILINEAR), float)
    mx_, mn_ = col.max(-1), col.min(-1)
    sat1 = (mx_ - mn_) / np.maximum(mx_, 1)
    m = nz & (sat1 > 0.3)
    w = ndimage.gaussian_filter(m.astype(float), 1.5) * cov1 * 0.8
    flat = np.array([128.0, 128.0, 255.0])
    out = nm * (1 - w[..., None]) + flat * w[..., None]
    _, (iy, ix) = ndimage.distance_transform_edt(~cov1, return_indices=True)
    out[~cov1] = out[iy[~cov1], ix[~cov1]]
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
    print('FIXNECK normal', p, int((w > 0.4).sum()))
