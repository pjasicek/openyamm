#!/usr/bin/env python3
"""Job 7 paint pass (user review 2026-11-04, `review/user_20261104/ears.png`) on one design's final maps, after the paint
chain; always restarts from the `_prejob7` copies it writes on its first run (idempotent).

1. Island borders (head set): Meshy's paint left a 1-2 texel darker rim along every UV island (border texels 3 % darker
   in the median, 11 % at p10 on d1's face), which reads as faint polygon crack lines across the cheeks and jaw once
   the islands meet in 3D. Texels within BORDER px of an island's edge take the colour of the nearest texel further in;
   every gutter is then re-padded from its nearest covered texel.
2. Painted ear outline: the skin shell around the old ear (side of the head, under and in front of the new ears) takes
   a 3D median of the skin texels within 7 mm (thin outline strokes drop out), feathered at the zone's edge.
3. New ear islands (add_ears_pdf.py's npz): the cheek's skin tone in front of the ear x cavity shading from the ears'
   ambient occlusion, a slight warm flush on the rim and lobe, fine skin grain; the head normal map is flat there and the
   ORM takes the cheek's median; islands padded 8 px. textures/ear_uv_mask.png (1K) marks them for tiers_pdf.py.
4. Neck tone (the hard horizontal line across the lower neck: r6 moved the faces between the old level cut at 0.909 m
   and the new seam under the jaw at 0.927 m to the body material, whose paint there came from tiny upload islands of
   another tone): the broad colour (mask-normalised low-pass, sigma 10 texels at 2K) of every skin texel of both sets
   between 0.865 and 0.96 m is replaced by one 3D-smooth field (Gaussian over the neighbouring skin texels of both sets
   in 3D, sigma 1 cm, over 2 mm voxels), the paint's own detail kept (faded to 30 % at the two seam lines); island borders on the neck healed as in 1; the body normal map is
   eased flat within 1 cm of 0.909 m. Necklace and cloth texels are never touched (skin rule of seam_tone.py).
Usage (project folder): ear_paint.py <design d1..d4> <ears npz> [--glb work/pdf_pos.glb]"""
import argparse, json, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
from headpart import texel_parts
ap = argparse.ArgumentParser()
ap.add_argument('design'); ap.add_argument('npz'); ap.add_argument('--glb', default='work/pdf_pos.glb')
ap.add_argument('--border', type=int, default=2)
o = ap.parse_args()
pre = f'pdf{o.design[1]}_tp'
rep = {'design': o.design}


def load(name, mode='RGB'):
    f = Path(f'textures/{pre}_{name}.png'); bk = f.with_name(f.stem + '_prejob7.png')
    if not bk.exists():
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert(mode), float)


def save(f, I):
    tmp = f.with_name(f.stem + '.tmp.png')
    Image.fromarray(np.uint8(np.clip(np.round(I), 0, 255))).save(tmp); os.replace(tmp, f)


def hsv_sat(I):
    mx, mn = I.max(-1), I.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    r, g, b = I[..., 0], I[..., 1], I[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return hue, sat, mx


def skinlike(I):                     # seam_tone.py's rule: warm skin hue, moderate saturation, not dark
    hue, sat, mx = hsv_sat(I)
    return (hue > 8) & (hue < 40) & (sat > 0.18) & (sat < 0.62) & (mx > 120)


def cloth(I):
    hue, sat, mx = hsv_sat(I)
    return (sat < 0.15) | ((hue > 60) & (hue < 300))


def heal(I, cov, k, region=None):
    """Texels of `cov` within k px of an island edge (inside) take the nearest texel at least k + 1 px in, of the same
    island (8-connected); rings of islands too thin to have an inside stay as they are."""
    lab, _ = ndimage.label(cov, structure=np.ones((3, 3)))
    inner = ndimage.binary_erosion(cov, iterations=k, border_value=0)
    idx = ndimage.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    ring = cov & ~inner & (lab[idx[0], idx[1]] == lab)
    if region is not None: ring &= region
    out = I.copy(); out[ring] = I[idx[0][ring], idx[1][ring]]
    return out, int(ring.sum())


def pad(I, cov):
    idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    return I[idx[0], idx[1]]


def finalize(orig, edited, cov, extra=None):
    """The original everywhere except the texels this pass changed; a gutter texel (outside `cov`) is refilled only when
    its nearest covered texel was changed and lies within 3 px (the paint's own padding elsewhere is kept: sub-texel
    sliver faces live in those gutters, and a global re-pad gave them a neighbouring island's colour)."""
    M = (np.abs(edited - orig).max(-1) > 0.5) & cov
    out = orig.copy(); out[M] = edited[M]
    d, idx = ndimage.distance_transform_edt(~cov, return_indices=True)
    G = ~cov & (d <= 3) & M[idx[0], idx[1]]
    out[G] = edited[idx[0][G], idx[1][G]]
    if extra is not None:                       # new islands (the ears) and their own padding
        out[extra] = edited[extra]
    return out


def lowpass(I, m, s):
    num = ndimage.gaussian_filter(I * m[..., None], (s, s, 0)); den = ndimage.gaussian_filter(m.astype(float), s)
    return num / np.maximum(den, 1e-3)[..., None]


# ---------------------------------------------------------------- head set
fh, H = load('head_basecolor'); NH = H.shape[0]
ph, parth, _ = texel_parts(o.glb, 'PeasantDFHead', NH)
covh = parth >= 0
gy, gx = np.mgrid[0:NH, 0:NH]; U = (gx + 0.5) / NH; Vb = 1 - (gy + 0.5) / NH
braid = (U > 0.82) & (U < 0.98) & (Vb > 0.05) & (Vb < 0.55)          # d3's plait column (not in pdf_pos.glb)
covh_all = covh | (braid & (o.design == 'd3'))
P = np.nan_to_num(ph)
# 1. island borders
H1, n = heal(H, covh, o.border); rep['head_border_texels'] = n
# 2. painted ear outline on the skin shell
skin = (parth == 0)
zone = skin & (np.abs(P[..., 0]) > 0.033) & (P[..., 1] > 0.955) & (P[..., 1] < 1.055) & (P[..., 2] > -0.03) & (P[..., 2] < 0.065)
src = skin & (np.abs(P[..., 0]) > 0.03) & (P[..., 1] > 0.94) & (P[..., 1] < 1.07) & (P[..., 2] > -0.05) & (P[..., 2] < 0.085)
qi = np.argwhere(src); tree = cKDTree(P[src]); cols = H1[src]
zi = np.argwhere(zone)
med = np.empty((len(zi), 3))
for s0 in range(0, len(zi), 4000):
    nb = tree.query_ball_point(P[zone][s0:s0 + 4000], 0.007)
    med[s0:s0 + 4000] = [np.median(cols[b], 0) for b in nb]
# feather: weight 1 inside, easing to 0 within 6 mm of the zone's box faces
def edge_w(p):
    d = np.minimum.reduce([np.abs(p[:, 0]) - 0.033, p[:, 1] - 0.955, 1.055 - p[:, 1], p[:, 2] + 0.03, 0.065 - p[:, 2]])
    return np.clip(d / 0.006, 0, 1)
w = edge_w(P[zone])[:, None]
H2 = H1.copy(); H2[zone] = H1[zone] * (1 - w) + med * w
rep['outline_zone_texels'] = int(zone.sum())
# 3. ear islands
E = np.load(o.npz)
tuv = E['tri_uv'].copy(); tri = E['tris']; ao = E['ao'].copy(); meta = E['meta']; pos = E['pos']
# the per-vertex occlusion (48 rays) is noisy: three neighbour-averaging passes over the ear mesh
nbr = [set() for _ in range(len(ao))]
for t in tri:
    for i in t: nbr[i].update(t)
for _ in range(3):
    ao = np.array([0.5 * ao[i] + 0.5 * np.mean([ao[j] for j in nbr[i]]) for i in range(len(ao))])
cheek = skin & (np.abs(P[..., 0]) > 0.035) & (P[..., 1] > 0.965) & (P[..., 1] < 1.02) & (P[..., 2] > 0.045) & (P[..., 2] < 0.075) \
    & skinlike(H2)
C = np.median(H2[cheek], 0); rep['cheek_rgb'] = C.round(1).tolist()
ear = np.zeros((NH, NH), bool); A = np.zeros((NH, NH, 4))         # ao, rim, lobe, lateral
for t, uv in zip(tri, tuv):
    q = np.stack([uv[:, 0] * NH, (1 - uv[:, 1]) * NH], 1)
    x0, y0 = np.maximum(np.floor(q.min(0)).astype(int) - 1, 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int) + 1, NH - 1)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = q
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12: continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    L = np.stack([l0, l1, 1 - l0 - l1], -1); ins = (L >= -0.02).all(-1)
    if not ins.any(): continue
    yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
    att = np.stack([ao[t], meta[t, 2], meta[t, 3], meta[t, 1]], 1)
    A[yy, xx] = L[ins] @ att; ear[yy, xx] = True
assert not (ear & covh_all).any(), 'ear islands overlap painted islands'
aoT = A[..., 0]
shade = 0.66 + 0.34 * np.clip((aoT - 0.15) / 0.6, 0, 1) ** 0.9
flush = np.clip(0.7 * A[..., 1] + 0.6 * A[..., 2], 0, 1)
tint = np.stack([1 + 0.035 * flush, 1 - 0.03 * flush, 1 - 0.035 * flush], -1)
rng = np.random.default_rng(int(o.design[1]))
grain = ndimage.gaussian_filter(rng.normal(size=(NH, NH)), 1.1); grain = grain / grain[ear].std() * 0.012
grain2 = ndimage.gaussian_filter(rng.normal(size=(NH, NH)), 4.0); grain2 = grain2 / grain2[ear].std() * 0.012
earcol = C[None, None] * shade[..., None] * tint * (1 + grain + grain2)[..., None]
H3 = H2.copy(); H3[ear] = earcol[ear]
rep['ear_texels'] = int(ear.sum()); rep['ear_rgb_median'] = np.median(H3[ear], 0).round(1).tolist()
# re-pad every gutter (painted islands + ear islands); the ear islands pad into free texels only
allcov = covh_all | ear
H4 = pad(H3, allcov)
save(fh, H4)
# ear UV mask for tiers_pdf.py (1K, dilated 6 px at 2K)
em = ndimage.binary_dilation(ear, iterations=6)
Image.fromarray(np.uint8(em) * 255).resize((1024, 1024), Image.NEAREST).save('textures/ear_uv_mask.png')
# head normal (1K): flat on the ear islands (+ their pad); ORM: the cheek's median
fn, Nm = load('head_normal_1k'); n1 = Nm.shape[0]
em1 = np.asarray(Image.fromarray(np.uint8(ndimage.binary_dilation(ear, iterations=8)) * 255).resize((n1, n1), Image.NEAREST)) > 0
Nm2 = Nm.copy(); Nm2[em1] = (128, 128, 255); save(fn, Nm2)
fo, Om = load('head_metal_rough_1k')
ch1 = np.asarray(Image.fromarray(np.uint8(cheek) * 255).resize((n1, n1), Image.NEAREST)) > 0
oc = np.median(Om[ch1], 0); Om2 = Om.copy(); Om2[em1] = oc; save(fo, Om2); rep['ear_orm'] = oc.tolist()

# ---------------------------------------------------------------- 4. neck tone (both sets)
fb, B = load('basecolor_graded'); NB = B.shape[0]
pb, cb = texel_positions(o.glb, 'PeasantDF', NB)
PB = np.nan_to_num(pb)
NECK0, NECK1 = 0.865, 0.96
sb = cb & skinlike(B) & ~cloth(B) & (PB[..., 1] > NECK0 - 0.03) & (PB[..., 1] < NECK1 + 0.03)
# (no morphological opening: the neck band's small low-density islands are only a few texels wide and would drop out)
# jewellery and cloth texels plus a 2 px halo keep their paint (the necklace links' shaded pixels are skin-coloured)
_, satB, mxB = hsv_sat(B)
chain = (satB < 0.3) & (mxB > 200) if o.design in ('d1', 'd3') else np.zeros(cb.shape, bool)   # pale silver links
jewel = ndimage.binary_dilation(cb & (cloth(B) | chain) & (PB[..., 1] > NECK0 - 0.03) & (PB[..., 1] < NECK1 + 0.03), iterations=2)
sb = sb & ~jewel
sh = skin & skinlike(H4) & (P[..., 1] > NECK0 - 0.03) & (P[..., 1] < NECK1 + 0.03)

# island borders on the neck (body set) first
neckreg = cb & (PB[..., 1] > NECK0 - 0.01) & (PB[..., 1] < NECK1 + 0.01) & ~cloth(B) & ~jewel
B1, n = heal(B, cb, o.border, neckreg); rep['body_neck_border_texels'] = n
lpB = lowpass(B1, sb, 10 * NB / 2048); lpH = lowpass(H4, sh, 10 * NH / 2048)
ptsB, ptsH = PB[sb], P[sh]
pts = np.concatenate([ptsB, ptsH]); lps = np.concatenate([lpB[sb], lpH[sh]])
# area-uniform samples: the head set has ~10x the body's texels per cm2, so texel samples would make each side's own
# texels the whole neighbourhood; average per 2 mm voxel, smooth over voxels (sigma 1 cm), interpolate to the texels
VOX = 0.002
vk = np.floor(pts / VOX).astype(np.int64)
_, vinv = np.unique(vk, axis=0, return_inverse=True); vinv = vinv.ravel(); nvx = vinv.max() + 1
cnt = np.bincount(vinv, minlength=nvx).astype(float)
vc = np.stack([np.bincount(vinv, pts[:, j], nvx) for j in range(3)], 1) / cnt[:, None]
vl = np.stack([np.bincount(vinv, lps[:, j], nvx) for j in range(3)], 1) / cnt[:, None]
vt = cKDTree(vc); TV = np.empty_like(vl)
for s0 in range(0, nvx, 2000):
    nb = vt.query_ball_point(vc[s0:s0 + 2000], 0.025)
    for j, b in enumerate(nb):
        w_ = np.exp(-((np.linalg.norm(vc[b] - vc[s0 + j], axis=1) / 0.01) ** 2) / 2)
        TV[s0 + j] = (w_[:, None] * vl[b]).sum(0) / w_.sum()
rep['neck_voxels'] = int(nvx)


def field(q):
    d, i = vt.query(q, 4)
    w_ = 1 / np.maximum(d, 1e-4)
    return (w_[..., None] * TV[i]).sum(1) / w_.sum(1)[:, None]


def weight(y):
    return np.clip((y - NECK0) / 0.02, 0, 1) * np.clip((NECK1 - y) / 0.02, 0, 1)


def apply(I, lp, m, Pp):
    out = I.copy(); y = Pp[m][:, 1]; wt = weight(y)[:, None]
    T = field(Pp[m])
    # at the two seam lines (old level cut 0.909 m, head/body seam 0.926 m) the paint's own detail also fades (to 30 %
    # at the line, over 5 mm), so neither the tone nor a change of texel density/detail draws a crisp line there
    R = np.clip(I[m] / np.maximum(lp[m], 1), 0.3, 3.0)
    al = 1 - 0.7 * np.maximum(np.exp(-((y - 0.909) / 0.005) ** 2), np.exp(-((y - 0.926) / 0.005) ** 2))
    out[m] = I[m] * (1 - wt) + T * R ** al[:, None] * wt
    return out


def band_med(I, Pp, m, y0, y1):
    k = m & (Pp[..., 1] > y0) & (Pp[..., 1] < y1) & (np.abs(Pp[..., 0]) < 0.06) & (Pp[..., 2] > 0)
    return np.median(I[k], 0).round(1).tolist() if k.any() else None


rep['neck_before'] = {'body_0.895_0.909': band_med(B, PB, sb, 0.895, 0.909), 'body_0.909_0.925': band_med(B, PB, sb, 0.909, 0.925),
                      'head_0.927_0.945': band_med(H4, P, sh, 0.927, 0.945)}
B2 = apply(B1, lpB, sb, PB); H5 = apply(H4, lpH, sh, P)
rep['neck_after'] = {'body_0.895_0.909': band_med(B2, PB, sb, 0.895, 0.909), 'body_0.909_0.925': band_med(B2, PB, sb, 0.909, 0.925),
                     'head_0.927_0.945': band_med(H5, P, sh, 0.927, 0.945)}
save(fb, finalize(B, B2, cb))
earpad = ndimage.binary_dilation(ear, iterations=8) & ~covh_all
save(fh, finalize(H, pad(H5, allcov), covh, earpad))
# body normal: eased flat within 1 cm of the old level cut (0.909 m)
fbn, BN = load('normal_1k'); nb1 = BN.shape[0]
pb1, cb1 = texel_positions(o.glb, 'PeasantDF', nb1); y1 = np.nan_to_num(pb1[..., 1])
t = ndimage.gaussian_filter(np.clip(1 - np.abs(y1 - 0.909) / 0.01, 0, 1) * cb1, 1.0)
# the necklace keeps its relief (the flattened band made its links read glassy)
j1 = np.asarray(Image.fromarray(np.uint8(ndimage.binary_dilation(jewel, iterations=4)) * 255).resize((nb1, nb1), Image.NEAREST)) > 0
t = t * ~j1
save(fbn, BN * (1 - t[..., None]) + np.array([128, 128, 255.0]) * t[..., None])
print('EARPAINT', json.dumps(rep))
