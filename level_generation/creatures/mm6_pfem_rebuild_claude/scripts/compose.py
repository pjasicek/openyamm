#!/usr/bin/env python3
"""Texture sets for the MM6 PeasantF1 rebuild from the 4K Meshy paints on our uv_atlas layouts (TEXTURE_QUALITY_PASS.md):
body colour 4K -> 2K Lanczos once, head colour 4K -> 1K, normal and roughness 1K, padded into the gutters; the gentle grade
(grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15) on both; ORM = (AO, roughness >= 0.6, 0).
Skin: the user rejected pale skin and a graft line at the neck (v4), so the head set's skin is brought to the body's neck skin by one gain
measured on the texels either side of the head/neck seam (both sides sampled at the same seam points).
Tiers (v3's): one region, the green bodice and skirt bands (hue-picked in the body set); ramp colours are the installed v3's (palettes
786/787/788), the luminance range refitted to this paint (p2..p98). The head set is shared by every tier.
Writes textures/*, textures/pfem_ramps.json and work/uv_tex.npz (uv.npz + the texture table). Run in the project folder (gltf venv)."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree
T = Path('textures'); D = dict(np.load(__import__('os').environ.get('UVIN', 'work/uv.npz')))  # UVIN=work/uv3.npz: torso_unturn.py
co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
GRADE = ['--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15']


def raster(faces, values, size):
    im = Image.new('I', (size, size)); d = ImageDraw.Draw(im)
    for f, v in zip(faces, values):
        d.polygon([(float(u * size), float((1 - w) * size)) for u, w in uv[tri[f]]], fill=int(v))
    return np.asarray(im)


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return img[iy, ix]


def lum(rgb):
    return ((rgb / 255.0) ** 2.2) @ np.array([0.2126, 0.7152, 0.0722])



def seam_tone(col, P, sel, voxel=0.004, sigma_vox=2.0, keep=None, iters=3):
    """Meshy paints each UV chart with its own slight tone, so chart borders across the skin read as pale polygon patches. Each chart
    (connected texels of the selection) takes one colour offset: the median difference to a 3D surface average (voxel grid, gaussian,
    trilinear), repeated a few times; detail inside a chart is untouched."""
    sel = sel & ~np.isnan(P[..., 0])
    if not sel.any(): return col
    lab_, n_ = ndimage.label(sel)
    q = P[sel]; lo = q.min(0); ijk = np.floor((q - lo) / voxel).astype(int); dims = ijk.max(0) + 3
    f = ((q - lo) / voxel - 0.5).T; li = lab_[sel]
    kp = np.zeros(len(q)) if keep is None else keep[sel]
    out = col.copy(); c = col[sel].astype(float)
    for _ in range(iters):
        acc = np.zeros(tuple(dims) + (3,)); cnt = np.zeros(tuple(dims))
        np.add.at(acc, tuple(ijk.T), c); np.add.at(cnt, tuple(ijk.T), 1)
        acc = ndimage.gaussian_filter(acc, (sigma_vox,) * 3 + (0,)); cnt = ndimage.gaussian_filter(cnt, sigma_vox)
        cn = ndimage.map_coordinates(cnt, f, order=1, mode='nearest')
        L3 = np.stack([ndimage.map_coordinates(acc[..., k], f, order=1, mode='nearest') for k in range(3)], -1) / np.maximum(cn, 1e-6)[:, None]
        d = L3 - c; ok = kp < 0.5
        for k in range(3):
            num = ndimage.median(d[ok, k], li[ok], index=np.arange(1, n_ + 1))
            num = np.nan_to_num(np.asarray(num, float))
            c[:, k] += num[li - 1]
    out[sel] = np.clip(c, 0, 255)
    return out


fcomp = comp[tri[:, 0]]
sets = {}
for key, job, m, size in (('pfem', 'retexture_body_v2', 0, 2048), ('pfem_head', 'retexture_head_v2', 1, 1024)):
    faces = np.nonzero(mat == m)[0]
    lab = raster(faces, fcomp[faces] + 1, size); cov = lab > 0
    cov1 = np.asarray(Image.fromarray(cov.astype(np.uint8) * 255).resize((1024, 1024), Image.NEAREST)) > 0
    col = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_base_color.png').convert('RGB').resize((size, size), Image.LANCZOS))
    nrm = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS))
    rgh = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS))
    inner = ndimage.binary_erosion(cov, iterations=2 if size >= 2048 else 1)   # Meshy lightens each chart's outermost texels: pale outlines on skin
    Image.fromarray(pad(col, inner)).save(T / f'{key}_raw.png')
    Image.fromarray(pad(nrm, cov1)).save(T / f'{key}_normal.png')
    ao = T / ('pfem_ao_2k.png' if m == 0 else 'pfem_head_ao.png')
    # head set: no local-contrast term (on the face it turned Meshy's smooth skin into pale blotches along the charts), lighter AO
    g_ = GRADE if m == 0 else ['--fine', '1.0', '--local', '0.0', '--ao-strength', '0.3', '--contrast', '1.03', '--saturation', '1.05']
    subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(ao), *g_, str(T / f'{key}_raw.png')],
                          stdout=subprocess.DEVNULL)
    a = np.asarray(Image.open(ao).convert('L').resize((1024, 1024), Image.LANCZOS))
    Image.merge('RGB', [Image.fromarray(pad(a, cov1)), Image.fromarray(pad(np.maximum(rgh, 153), cov1)), Image.new('L', (1024, 1024), 0)]).save(T / f'{key}_orm.png')
    sets[key] = dict(lab=lab - 1, cov=cov, size=size, col=np.asarray(Image.open(T / f'{key}_raw_graded.png').convert('RGB')).astype(float))
    print('RAW', key, 'atlas', round(float(cov.mean()) * 100, 1))


# ---- skin across the head/neck seam: sample both sets at the seam points (positions shared by a head face and a dress face)
def texel_at(key, faces, bary_pts):
    s = sets[key]; size = s['size']; out = []
    for f, b in zip(faces, bary_pts):
        u = (uv[tri[f]] * b[:, None]).sum(0); x = int(np.clip(u[0] * size, 0, size - 1)); y = int(np.clip((1 - u[1]) * size, 0, size - 1))
        out.append(s['col'][y, x])
    return np.array(out)


hf = np.nonzero(mat == 1)[0]; bf = np.nonzero((mat == 0) & (fcomp == names.index('dress')))[0]
hc = co[tri[hf]].mean(1); bc = co[tri[bf]].mean(1)
skinh = fcomp[hf] == names.index('head')
kb = cKDTree(bc); d, nb = kb.query(hc)
seam = skinh & (d < 0.012)
cen = np.full((len(hf), 3), 1 / 3)
H = texel_at('pfem_head', hf[seam], cen[seam]); B = texel_at('pfem', bf[nb[seam]], cen[seam])
gain = np.clip(np.median(B, 0) / np.maximum(np.median(H, 0), 1), 0.75, 1.3)
print('SEAM faces', int(seam.sum()), 'head', np.median(H, 0).round(1), 'body', np.median(B, 0).round(1), 'gain', gain.round(3))
hs = sets['pfem_head']; skinmask = hs['lab'] == names.index('head')
hsv = np.asarray(Image.fromarray(hs['col'].astype(np.uint8)).convert('HSV')).astype(float)
skinlike = skinmask & (hsv[..., 0] * 360 / 255 < 45) & (hsv[..., 2] > 90)
w = ndimage.gaussian_filter(skinlike.astype(float), 2.0)
# the face keeps its own skin; the body's neck is brought to it instead (below, fading over 6 cm from the jaw seam)
# ---- face paint fixes by texel position (the v3 mouth is a closed slit: Meshy painted parted lips with teeth; nostrils and the nose
# underside came out near black; the circlet came out cream, v3's was brass)
sys.path.insert(0, 'scripts')
from meshlib import posmap
PM, FM = posmap(co, tri, uv, hf, 1024); hc_ = hs['col']
X, Y, Z = PM[..., 0], PM[..., 1], PM[..., 2]
L_ = hc_ @ np.array([0.299, 0.587, 0.114]); mx = hc_.max(-1); mn = hc_.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
mouth = (np.abs(X) < 0.026) & (Z > 0.5745) & (Z < 0.5935) & (Y < -0.02)
red = mouth & (hc_[..., 0] > hc_[..., 1] * 1.55) & (L_ > 90)
lip = np.median(hc_[red], 0) if red.any() else np.array([190., 100., 92.])
bad = mouth & ((L_ < 0.72 * L_[red].mean()) | ((sat < 0.3) & (L_ > 150)))
bad = ndimage.binary_dilation(bad, iterations=1) & mouth
hc_[bad] = lip * 0.94
fn_ = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); fn_ /= np.maximum(np.linalg.norm(fn_, axis=1, keepdims=True), 1e-12)
fwd = np.where(FM >= 0, -fn_[np.maximum(FM, 0), 1], 1.0)
cav = mouth & (np.abs(X) < 0.02) & (Z > 0.578) & (Z < 0.591) & (Y > -0.07) & (fwd < 0.35)   # the slit's cavity walls (teeth painted there)
hc_[cav] = lip * 0.8; bad = bad | cav
nose = (np.abs(X) < 0.022) & (Z > 0.596) & (Z < 0.617) & (Y < -0.068)
skin_ref = np.median(hc_[(np.abs(X) < 0.03) & (Z > 0.62) & (Z < 0.64) & (Y < -0.06)], 0)
dk = nose & (L_ < 0.75 * (skin_ref @ np.array([0.299, 0.587, 0.114])))
hc_[dk] = hc_[dk] * 0.3 + skin_ref * 0.8 * 0.7
band = FM >= 0; band[band] = fcomp[FM[band]] == names.index('band')
bl = L_[band] / max(np.percentile(L_[band], 90), 1)
hc_[band] = np.clip(np.array([214., 168., 86.])[None] * bl[:, None], 0, 255)
for m_k in (bad, dk):
    if m_k.any():
        sm = ndimage.gaussian_filter(hc_, (1.0, 1.0, 0)); r_ = ndimage.binary_dilation(m_k, iterations=2)
        hc_[r_] = sm[r_]
print('FACEFIX mouth', int(bad.sum()), 'nose', int(dk.sum()), 'band', int(band.sum()), 'lip', lip.round(0))
# chart-border tone on the face skin (eyes, brows and lips keep their own tone)
skin_h = (FM >= 0) & np.isin(np.where(FM >= 0, fcomp[np.maximum(FM, 0)], -1), [names.index('head')])
hsvh = np.asarray(Image.fromarray(np.clip(hc_, 0, 255).astype(np.uint8)).convert('HSV')).astype(float)
feat = ((hsvh[..., 2] < 110) | ((hsvh[..., 0] * 360 / 255 < 12) | (hsvh[..., 0] * 360 / 255 > 340)) & (hsvh[..., 1] > 90)).astype(float)
feat = ndimage.gaussian_filter(ndimage.binary_dilation(feat > 0, iterations=3).astype(float), 2)
hs['col'] = hc_
# skin normal maps mostly flat: the engine builds tangents per pixel from screen derivatives, so Meshy's per-chart normal map lights
# chart borders as pale polygon patches on smooth skin (v4 review 3); 25 % kept for the pores
def flatten_normals(path, skin, keep=0.25):
    nm_ = np.asarray(Image.open(path).convert('RGB')).astype(float)
    sk = np.asarray(Image.fromarray((skin * 255).astype(np.uint8)).resize(nm_.shape[1::-1], Image.BILINEAR)).astype(float) / 255
    sk = ndimage.gaussian_filter(sk, 1.5)[..., None]
    flat = np.array([128.0, 128.0, 255.0])
    Image.fromarray(np.clip(nm_ * (1 - sk * (1 - keep)) + flat * sk * (1 - keep), 0, 255).astype(np.uint8)).save(path)
flatten_normals(T / 'pfem_head_normal.png', skin_h.astype(float))
Image.fromarray(pad(hs['col'].astype(np.uint8), hs['cov'])).save(T / 'pfem_head_final.png')
# ---- tiers: the green garment, v3's ramp colours, range refitted
bs = sets['pfem']; col = bs['col']; lab = bs['lab']
BF = np.nonzero((mat == 0) & np.isin(fcomp, [names.index('dress'), names.index('hands')]))[0]
PB, FB_ = posmap(co, tri, uv, BF, 2048)
# the bodice bottom just above the belt: Meshy painted the belt's shadow onto it (a black band in front of the belt's top edge)
belt_top = float(co[comp == names.index('belt'), 2].max())
isdress = (FB_ >= 0) & (np.where(FB_ >= 0, fcomp[np.maximum(FB_, 0)], -1) == names.index('dress'))
Lb = col @ np.array([0.299, 0.587, 0.114])
ref = isdress & (PB[..., 2] > belt_top + 0.01) & (PB[..., 2] < belt_top + 0.03) & (Lb > 50)
green_ref = np.median(col[ref], 0)
band_ = isdress & (PB[..., 2] < belt_top + 0.008) & (Lb < 0.8 * (green_ref @ np.array([0.299, 0.587, 0.114])))
tz = np.clip((PB[..., 2] - (belt_top - 0.025)) / 0.033, 0, 1)
col[band_] = col[band_] * 0.15 + (green_ref[None] * (0.88 + 0.12 * tz[band_][:, None])) * 0.85
print('BODICE band recoloured', int(band_.sum()))
# chart-border tone on body skin (neck, chest, arms, hands)
hsvb = np.asarray(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).convert('HSV')).astype(float)
skin_b = (FB_ >= 0) & (hsvb[..., 0] * 360 / 255 < 40) & (hsvb[..., 1] > 50) & (hsvb[..., 2] > 120)
# dark specks on the white skirt (Meshy echoes the masters' hanging hands on the skirt sides): small blobs well under the local tone
sk_ = (lab == names.index('skirt')); Lc = col @ np.array([0.299, 0.587, 0.114])
med_ = ndimage.median_filter(np.where(sk_, Lc, np.nan_to_num(Lc)), size=25)
hsv_s = np.asarray(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).convert('HSV')).astype(float)
white_ = sk_ & (hsv_s[..., 1] < 70) & (med_ > 150)
dk_ = white_ & (Lc < 0.86 * med_)
lb_, nb_ = ndimage.label(dk_); szs = ndimage.sum(dk_, lb_, np.arange(1, nb_ + 1))
small_ = np.isin(lb_, np.nonzero(szs < 1500)[0] + 1)
small_ = ndimage.binary_dilation(small_, iterations=3) & white_
if small_.any():
    sm_ = np.stack([ndimage.median_filter(col[..., c], size=31) for c in range(3)], -1)
    col[small_] = sm_[small_]
print('SKIRT specks', int(small_.sum()), 'texels')
# skin-coloured patches on the skirt (the masters' hands beside the skirt projected onto it) take the local white
sk_skin = sk_ & (hsv_s[..., 0] * 360 / 255 < 40) & (hsv_s[..., 1] > 60) & (hsv_s[..., 2] > 120)
sk_skin = ndimage.binary_dilation(sk_skin, iterations=3) & sk_ & (hsv_s[..., 1] < 200)
if sk_skin.any():
    wref = np.median(col[white_ & ~sk_skin], 0); col[sk_skin] = wref * (0.85 + 0.15 * (Lc[sk_skin, None] / max(np.median(Lc[white_]), 1)))
print('SKIRT skin patches', int(sk_skin.sum()))
# lining and hem rim: one dark cloth tone with the paint's own light variation (Meshy painted it as a second outside, rim skin-orange)
li_ = lab == names.index('lining')
lv_ = Lc[li_] / max(np.median(Lc[li_]), 1)
col[li_] = np.array([150., 144., 132.])[None] * np.clip(0.85 + 0.15 * lv_, 0.7, 1.1)[:, None]
bs['col'] = col
flatten_normals(T / 'pfem_normal.png', skin_b.astype(float))
# neck: body skin near the head/neck seam takes the face's skin tone (1 / gain), fading out 6 cm below the seam: no graft line at the jaw
seam_pts = hc[seam]
if len(seam_pts):
    kd_s = cKDTree(seam_pts); okp = skin_b & ~np.isnan(PB[..., 0])
    dn, _ = kd_s.query(PB[okp]); wn = 1 - np.clip(dn / 0.06, 0, 1); wn = wn * wn * (3 - 2 * wn)
    bs['col'][okp] = np.clip(bs['col'][okp] * (1 + (1 / gain[None] - 1) * wn[:, None]), 0, 255)
    print('NECK toned', int((wn > 0.01).sum()), 'texels, gain', (1 / gain).round(3))
hsv = np.asarray(Image.fromarray(col.astype(np.uint8)).convert('HSV')).astype(float)
h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
green = (h > 60) & (h < 170) & (s > 0.22) & np.isin(lab, [names.index(x) for x in ('dress', 'skirt')])
green = ndimage.binary_opening(green, iterations=1); green = ndimage.binary_closing(green, iterations=2)
vals = lum(col)[green]
rng = [float(np.percentile(vals, 2)), float(np.percentile(vals, 98))]
OLD = json.load(open('work/v3_ramps.json'))
ramps = {t: [dict(range=[round(rng[0], 6), round(rng[1], 6)], colors=OLD[t])] for t in ('pfem_a', 'pfem_b', 'pfem_c')}
sys.path.insert(0, '../claude_shared')
import region_variants as RV
m_ = pad(green.astype(float), bs['cov']); m_ = ndimage.gaussian_filter(m_, 1.5)
RV.write_mask([m_], T / 'pfem_region_mask.png', size=1024)
Image.fromarray(pad(col.astype(np.uint8), bs['cov'])).save(T / 'pfem_body_final.png')
json.dump(dict(variants=['pfem_a', 'pfem_b', 'pfem_c'], materials=[dict(base='Peasant', prefix='Peasant', mask='pfem_region_mask.png', regions=['garment'],
          palettes={'pfem_a': 786, 'pfem_b': 787, 'pfem_c': 788}, ramps=ramps)], note='colours: installed v3 ramps; range refitted p2..p98'),
          open(T / 'pfem_ramps.json', 'w'), indent=1)
print('TIERS mask cover %', round(float(green.mean()) * 100, 1), 'range', [round(x, 4) for x in rng])
D['textures'] = json.dumps({'Peasant': dict(base='textures/pfem_body_final.png', normal='textures/pfem_normal.png', orm='textures/pfem_orm.png'),
                            'PeasantHead': dict(base='textures/pfem_head_final.png', normal='textures/pfem_head_normal.png', orm='textures/pfem_head_orm.png')})
# the bodice's lower rim (it faces down over the belt's top edge and read as a black band under top light): positions only, tucked
# 6 mm inside the belt at the same azimuth, so the belt's top edge covers it
bv_ = np.unique(tri[fcomp == names.index('dress')]); blt = co[comp == names.index('belt')]
cyb = 0.5 * (blt[:, 1].min() + blt[:, 1].max()); thb = np.arctan2(blt[:, 1] - cyb, blt[:, 0]); rb = np.hypot(blt[:, 0], blt[:, 1] - cyb)
low = bv_[co[bv_, 2] < belt_top + 0.004]; D['co'] = D['co'].copy(); moved = 0
for v in low:
    p_ = co[v]; th_ = np.arctan2(p_[1] - cyb, p_[0]); r_ = np.hypot(p_[0], p_[1] - cyb)
    k_ = np.abs(((thb - th_ + np.pi) % (2 * np.pi)) - np.pi) < 0.2
    if not k_.any(): continue
    rt = rb[k_].min() - 0.006
    if r_ > rt:
        f_ = rt / r_; D['co'][v, 0] = p_[0] * f_; D['co'][v, 1] = cyb + (p_[1] - cyb) * f_; moved += 1
key_ = {tuple(np.round(co[i], 6)): D['co'][i] for i in low}
for i in range(len(co)):
    k_ = tuple(np.round(co[i], 6))
    if k_ in key_: D['co'][i] = key_[k_]
print('BODICE rim tucked', moved, 'of', len(low))
# legs cut 11 cm below the knee and capped (positions and faces only, UVs kept): MM9's walk swings the shin forward and the knee pushed
# through the skirt's front (robe_gate: Walking 2.9 cm); under the skirt nothing above the cut is ever seen
LEGTOP = float(__import__('os').environ.get('LEGTOP', '-0.53'))
tri_ = D['tri']; fc_ = D['comp'][tri_[:, 0]]; cz = D['co'][tri_][:, :, 2].max(1)
drop = (fc_ == names.index('legs')) & (cz > LEGTOP)
keep_t = tri_[~drop]
lt = keep_t[D['comp'][keep_t[:, 0]] == names.index('legs')]
e_ = np.sort(np.r_[lt[:, [0, 1]], lt[:, [1, 2]], lt[:, [2, 0]]], axis=1); u_, c_ = np.unique(e_, axis=0, return_counts=True)
b_ = u_[c_ == 1]
# positions (not split copies) decide the rim; group boundary vertices into loops by their side
bv = np.unique(b_.ravel()); bv = bv[D['co'][bv, 2] > LEGTOP - 0.06]
newt = []
for sg in (-1, 1):
    vv = bv[np.sign(D['co'][bv, 0]) == sg]
    if not len(vv): continue
    cen = D['co'][vv].mean(0); ci = len(D['co'])
    for key in ('co', 'co_up'): D[key] = np.vstack([D[key], (D[key][vv].mean(0))[None]])
    D['uv'] = np.vstack([D['uv'], D['uv'][vv[0]][None]]); D['orig'] = np.r_[D['orig'], D['orig'][vv[0]]]; D['comp'] = np.r_[D['comp'], names.index('legs')]
    for a_, b2 in b_:
        if a_ in vv and b2 in vv:
            t_ = [a_, b2, ci]
            n_ = np.cross(D['co'][b2] - D['co'][a_], D['co'][ci] - D['co'][a_])
            if n_[2] < 0: t_ = [b2, a_, ci]
            newt.append(t_)
newt = np.array(newt, int).reshape(-1, 3)
D['tri'] = np.vstack([keep_t, newt]); D['mat'] = np.r_[D['mat'][~drop], np.zeros(len(newt), int)]; D['inner'] = np.r_[D['inner'][~drop], np.zeros(len(newt), bool)]
tri, mat = D['tri'], D['mat']; co = D['co']; fcomp = D['comp'][tri[:, 0]]
print('LEGS cut at', LEGTOP, 'faces dropped', int(drop.sum()), 'cap faces', len(newt))
# hair shell back faces (front half, below the circlet): a view past the cheek into the open hair panel saw the background
hair_f = np.nonzero((fcomp == names.index('hair')) & (co[tri][:, :, 1].mean(1) < 0.03))[0]
vn_ = np.zeros_like(co); fnn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
for k in range(3): np.add.at(vn_, tri[:, k], fnn)
vn_ /= np.maximum(np.linalg.norm(vn_, axis=1, keepdims=True), 1e-12)
vs_, inv_ = np.unique(tri[hair_f], return_inverse=True); n0 = len(co)
for key in ('co', 'co_up'): D[key] = np.vstack([D[key], D[key][vs_] - vn_[vs_] * 0.0015])
for key in ('uv',): D[key] = np.vstack([D[key], D[key][vs_]])
for key in ('orig', 'comp'): D[key] = np.r_[D[key], D[key][vs_]]
D['tri'] = np.vstack([tri, (inv_.reshape(-1, 3) + n0)[:, ::-1]]); D['mat'] = np.r_[mat, mat[hair_f]]; D['inner'] = np.r_[D['inner'], np.zeros(len(hair_f), bool)]
print('HAIR backs', len(hair_f))
np.savez('work/uv_tex.npz', **D)
print('COMPOSED')
