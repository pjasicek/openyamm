#!/usr/bin/env python3
"""White net in front of, behind and below the ears (ear sweep 2026-11-02, `claude_shared/mm9_overview/ear_sweep_20261102.png`
rows 9-10). Head paint step after head_seam.py, before finish_tex.py.

Cause: both paid head-only paints (meshy/pm2_retex_head_{a,b}/, unchanged by every later step) drew the sideburn and the beard's
back edge as a net of thin white crossing strands on the skin of the face shell: on tier B (a clean-shaven man) a patch in front of
each ear, a strip down behind the jaw and a few strands on the ear's rim; on tier A (white beard with sideburns) the beard's upper
part next to the ear thins out into the same net.
Fix, on the face shell (part 20 of work/faces.npz; the hair shell is another part and is not touched) inside the ear zone
(|x| > ZONE_X, ZONE_Z, y > ZONE_Y; texel positions work/texpos_head.npz, Blender metres, face towards -y):
- strand texels: brighter than their grey opening (OPEN px) by more than RISE, whose opened colour is skin (the cheek's chroma
  within 0.06; the ash-grey and white hair stay out), dilated 1 px;
- tier B: every strand texel takes the mean of the strand-free skin around it (normalised convolution, the finest of 3/6/12 px
  with enough skin), blended in by a 1 px soft weight; then small leftover islands (< SPECK texels) of white or grey texels at
  the hair edge and on the ear rim take the skin around them;
- tier A (white beard): the net here is white strands on pale skin, so no skin test: every bright thin strand in the zone counts.
  The white density (share of texels brighter than the cheek by 20, Gaussian DENS_SIGMA px, grey opening DENSE_OPEN px so thin
  hooked strand lines do not count) keeps the dense beard on the jaw and chin (>= DENSE) and removes the net around it
  (< SPARSE), strands and bright texels taking the mean of the dark (non-white) skin around them; linear blend between. Only
  in the sideburn (z > A_Z, |x| > A_X, faded over A_FADE): removing the net at the beard's back edge below the jaw too cut the
  beard into a hook where the zone ended. Tried and dropped: densifying the sideburn net into a
  solid white sideburn (a pink fog with the net still visible, or white blotches on the neck wrinkles) and keeping 35 % of the
  strands (a faint net stays).
Reads the *_prenet.png backups (made from pm2_head_{t}_tone.png on the first run; delete them after head_seam.py rewrites the
tone images), writes textures/pm2_head_{t}_tone.png and review/fix_net_mask_{t}.png. Usage (project folder): fix_net_pm2.py [a b]"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ZONE_X, ZONE_Z, ZONE_Y = 0.045, (0.66, 0.83), -0.06       # Blender metres (texpos_head.npz frame)
OPEN, RISE = 5, 14.0
SPECK = 120                                        # tier B: leftover islands smaller than this (texels) are filled
DENS_SIGMA, SPARSE, DENSE = 8.0, 0.40, 0.65     # tier A: white density of the net (removed) and the dense beard (kept)
A_Z, A_X, A_FADE = 0.725, 0.060, 0.012            # tier A: the sideburn lies above z A_Z and beside |x| A_X
DENSE_OPEN = 15                                   # px: thin dense lines (a hooked strand line) do not count as beard
T = Path('textures')
D = np.load('work/texpos_head.npz')
pos, ok, fid = D['pos'], D['ok'], D['face']
PART = np.load('work/faces.npz')['part']
face = ok & (PART[np.maximum(fid, 0)] == 20)
x, y, z = (np.nan_to_num(pos[..., i]) for i in range(3))
zone = face & (np.abs(x) > ZONE_X) & (z > ZONE_Z[0]) & (z < ZONE_Z[1]) & (y > ZONE_Y)
cheek = face & (np.abs(x) > 0.03) & (np.abs(x) < 0.055) & (z > 0.74) & (z < 0.77) & (y < -0.07)


def local_mean(img, valid, sigma):
    wv = ndimage.gaussian_filter(valid.astype(float), sigma)
    return np.stack([ndimage.gaussian_filter(img[..., i] * valid, sigma) for i in range(3)], -1) / \
        np.maximum(wv, 1e-6)[..., None], wv


for t in (sys.argv[1:] or ['a', 'b']):
    f, bk = T / f'pm2_head_{t}_tone.png', T / f'pm2_head_{t}_tone_prenet.png'
    if not bk.exists():
        shutil.copyfile(f, bk)
    img = np.asarray(Image.open(bk).convert('RGB'), float)
    lum = img @ [0.299, 0.587, 0.114]
    ref = np.median(img[cheek], 0)
    op = ndimage.grey_opening(lum, size=(OPEN, OPEN))
    opc = ndimage.grey_opening(img, size=(OPEN, OPEN, 1))
    chroma = opc / np.maximum(opc.sum(-1, keepdims=True), 1)
    skin = np.linalg.norm(chroma - ref / ref.sum(), axis=-1) < 0.06
    strand = zone & skin & (lum - op > RISE)
    strand = ndimage.binary_dilation(strand, iterations=1) & zone
    fill = None
    for sg in (12.0, 6.0, 3.0):
        f2, w2 = local_mean(img, zone & skin & ~strand, sg)
        fill = f2 if fill is None else np.where((w2 > 0.15)[..., None], f2, fill)
    w = np.clip(ndimage.gaussian_filter(strand.astype(float), 0.7) * 1.5, 0, 1) * zone
    if t == 'a':
        # the net is white on white-ish skin here, so no skin test: every bright thin strand in the zone counts; the dense beard
        # (white density >= DENSE, Gaussian DENS_SIGMA px) is kept, the net around it removed, with a linear blend between
        bright = lum > np.median(lum[cheek]) + 20
        dens = ndimage.gaussian_filter((bright & face).astype(float), DENS_SIGMA)
        dens = ndimage.grey_opening(dens, size=(DENSE_OPEN, DENSE_OPEN))
        sa = ndimage.binary_dilation(zone & (lum - op > RISE), iterations=1) & zone
        base = zone & ~sa & ~bright
        fill = None
        for sg in (12.0, 6.0, 3.0):
            f2, w2 = local_mean(img, base, sg)
            fill = f2 if fill is None else np.where((w2 > 0.15)[..., None], f2, fill)
        k = np.clip((dens - SPARSE) / (DENSE - SPARSE), 0, 1)           # 0 net -> 1 dense beard
        # only the sideburn: above the jaw (z) and beside the ear (|x|), faded in over A_FADE so the beard keeps its edge
        side = np.clip((z - A_Z) / A_FADE + 0.5, 0, 1) * np.clip((np.abs(x) - A_X) / A_FADE + 0.5, 0, 1)
        rem = np.clip(ndimage.gaussian_filter((sa | (zone & bright)).astype(float), 0.7) * 1.5, 0, 1) * zone * (1 - k) * side
        out = img * (1 - rem[..., None]) + fill * rem[..., None]
        strand = sa
    else:
        out = img * (1 - w[..., None]) + fill * w[..., None]
        # specks: small islands of white / grey texels left at the hair edge and on the ear (their opened colour was not skin);
        # islands of fewer than SPECK texels that are not skin-coloured take the skin around them
        lo = out @ [0.299, 0.587, 0.114]
        ch = out / np.maximum(out.sum(-1, keepdims=True), 1)
        odd = zone & ((np.linalg.norm(ch - ref / ref.sum(), axis=-1) > 0.05) | (lo > np.median(lo[cheek]) + 30))
        lab, n = ndimage.label(odd)
        size = ndimage.sum(odd, lab, np.arange(1, n + 1))
        speck = odd & (size[np.maximum(lab - 1, 0)] < SPECK) & (lab > 0)
        speck = ndimage.binary_dilation(speck, iterations=1) & zone
        f3, _ = local_mean(out, zone & ~odd, 4.0)
        out[speck] = f3[speck]
        strand = strand | speck
    Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f)
    vis = img.astype(np.uint8).copy()
    vis[strand] = (255, 0, 255)
    vis[zone & ~strand] = (vis[zone & ~strand] * 0.7).astype(np.uint8)
    Image.fromarray(vis).resize((896, 896), Image.NEAREST).save(f'review/fix_net_mask_{t}.png')
    print('FIXNET', t, 'zone', int(zone.sum()), 'strand texels', int(strand.sum()), 'cheek ref', ref.round(1))
