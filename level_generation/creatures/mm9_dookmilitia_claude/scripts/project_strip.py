#!/usr/bin/env python3
"""The cheek strip under the cheek bars from ONE paint source (run 2, coordinator): the tier's left side view
(references_head/<t>_03_left_clean.png) with the lower bar painted out by Codex (references_head/strip/<t>_03_left_nobar.png).
The bars hang 6.5 cm higher than built, so the cheek they covered at paint time was never painted (project_head.py filled it).

  mask  <tiers>   writes references_head/strip/<t>_03_left_mask.png (where the strip lies in that view) and a red overlay
  apply <tiers>   projects the edited view onto the strip on the left cheek (project_head.py's camera and silhouette fit, the
                  same mapping that painted the cheek round it), mirrors it onto the right strip (as project_head.py mirrors
                  the left cheek onto the right), fades it in over FEATHER and brings its low frequencies (Gaussian SIG, in
                  3D) to the cheek round the strip, so no edge is left. Colour into textures/dook_head_<t>_raw.png and
                  _final.png (dark texel block as finish_tex.py), the normal map inside the strip from the new colour by
                  project_head.py's formula, faded the same way. Inputs kept in work/run2/tex_r12/ and re-read from there.
The edited image is first registered to the original on the area outside the mask (phase correlation), so a shifted return
still lands. Head-space box of the strip (head_faces.npz: x side, -y forward, z up) checked by a debug paint in the viewer."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from head_raster import raster
mode, tiers = sys.argv[1], sys.argv[2]
H = Path('references_head'); SD = H / 'strip'; SD.mkdir(exist_ok=True)
T = Path('textures'); KEEP = Path('work/run2/tex_r12'); KEEP.mkdir(parents=True, exist_ok=True)
LO = np.array([0.040, -0.078, 0.680]); HI = np.array([0.200, -0.016, 0.754]); FEATHER, SIG = 0.012, 0.010      # back edge 8 mm past the bar: the line where the old views stopped
LOWK = 0.0      # the 3D tone match pulled in the shaded neck under the jaw (a dark patch); the seamless clone in the view already meets the paint round the strip
ORTHO = 0.5; C = np.array([0.0, 0.01788879930973053, 0.7927634119987488]); S = 1792
d_ = np.array([1.0, 0, 0]); up = np.array([0, 0, 1.0]); r_ = np.cross(up, d_); r_ /= np.linalg.norm(r_); u_ = np.cross(d_, r_)
pos, cov, prt = raster(S)
skin = cov & np.isin(prt, (2, 20))
ys, xs = np.nonzero(skin); P = pos[ys, xs]
q = np.c_[np.abs(P[:, 0]), P[:, 1], P[:, 2]]
dist = np.linalg.norm(np.maximum(np.maximum(LO - q, q - HI), 0), axis=1)
f = np.clip(1 - dist / FEATHER, 0, 1); f = f * f * (3 - 2 * f)
clay = np.asarray(Image.open(H / 'clay_03_left.png').convert('RGBA'))[..., 3] > 128


def bbox(m):
    yy, xx = np.nonzero(m); return xx.min(), xx.max() + 1, yy.min(), yy.max() + 1


def mapping(t):
    """image pixel coordinates of head points in tier t's left view (project_head.py's silhouette fit)"""
    im = np.asarray(Image.open(H / f'{t}_03_left_clean.png').convert('RGBA'))
    Hh, Ww = im.shape[:2]; al = im[..., 3] > 127
    ax0, ax1, ay0, ay1 = bbox(al); CH, CW = clay.shape; bx0, bx1, by0, by1 = bbox(clay)
    kx = (ax1 - ax0) / Ww / ((bx1 - bx0) / CW); ky = (ay1 - ay0) / Hh / ((by1 - by0) / CH)
    ox = ax0 / Ww - bx0 / CW * kx; oy = ay0 / Hh - by0 / CH * ky
    def f_(X):
        sx = (X - C) @ r_ / ORTHO + 0.5; sy = 0.5 - (X - C) @ u_ / ORTHO
        return (sx * kx + ox) * Ww - 0.5, (sy * ky + oy) * Hh - 0.5
    return im, f_


def bilinear(im, x, y):
    h, w = im.shape[:2]; x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[..., None], (y - y0)[..., None]; im = im.reshape(h, w, -1)
    return im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy) + im[y0 + 1, x0] * (1 - fx) * fy + im[y0 + 1, x0 + 1] * fx * fy


left = P[:, 0] > 0
if mode == 'mask':
    for t in tiers:
        im, mp = mapping(t)
        sel = left & (dist < 0.004)
        ix, iy = mp(P[sel])
        m = np.zeros(im.shape[:2], bool); m[np.clip(iy.round().astype(int), 0, im.shape[0] - 1), np.clip(ix.round().astype(int), 0, im.shape[1] - 1)] = True
        m = ndimage.binary_closing(ndimage.binary_dilation(m, iterations=3), iterations=6); m = ndimage.binary_fill_holes(m)
        Image.fromarray(m.astype('u1') * 255).save(SD / f'{t}_03_left_mask.png')
        ov = im[..., :3].astype(np.float32).copy(); ov[m] = ov[m] * 0.45 + np.array([255, 0, 0]) * 0.55
        Image.fromarray(ov.astype('u1')).save(SD / f'{t}_03_left_overlay.png')
        print('MASK', t, int(m.sum()), 'px, bbox', bbox(m))
    sys.exit()

D = json.load(open('work/dark_texel.json'))['head']


def lum_normal(col):
    lum = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    im1k = np.asarray(Image.fromarray((np.clip(lum, 0, 1) * 255).astype('u1')).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    hp = im1k - ndimage.gaussian_filter(im1k, 6)
    gx = ndimage.sobel(hp, axis=1) * 2.0; gy = ndimage.sobel(hp, axis=0) * 2.0
    n = np.dstack([-gx, gy, np.ones_like(gx)]); return n / np.linalg.norm(n, axis=2, keepdims=True)


for t in tiers:
    for k in ('raw', 'final', 'normal'):
        if not (KEEP / f'dook_head_{t}_{k}.png').exists():
            Image.open(T / f'dook_head_{t}_{k}.png').save(KEEP / f'dook_head_{t}_{k}.png')
    orig, mp = mapping(t)
    ed = np.asarray(Image.open(SD / f'{t}_03_left_nobar.png').convert('RGB').resize(orig.shape[1::-1], Image.LANCZOS), np.float32) / 255
    og = orig[..., :3].astype(np.float32) / 255
    # register the edit to the original outside the mask (a regenerated image may shift by a few pixels)
    mk = np.asarray(Image.open(SD / f'{t}_03_left_mask.png')) > 0
    roi = ndimage.binary_dilation(mk, iterations=120) & ~ndimage.binary_dilation(mk, iterations=10) & (orig[..., 3] > 127)
    g1 = (og @ [0.3, 0.6, 0.1]) * roi; g2 = (ed @ [0.3, 0.6, 0.1]) * roi
    Fc = np.fft.fft2(g1) * np.conj(np.fft.fft2(g2)); cc = np.fft.ifft2(Fc / np.maximum(np.abs(Fc), 1e-9)).real
    sy_, sx_ = np.unravel_index(cc.argmax(), cc.shape)
    if sy_ > cc.shape[0] // 2: sy_ -= cc.shape[0]
    if sx_ > cc.shape[1] // 2: sx_ -= cc.shape[1]
    ed = ndimage.shift(ed, (sy_, sx_, 0), order=1, mode='nearest')
    res_off = float(np.abs((og - ed)[roi]).mean())
    print('REGISTER', t, 'shift px', (int(sy_), int(sx_)), 'mean abs diff outside the strip', round(res_off, 3))
    # seamless clone: Codex pasted its edit back with a tone step at the edge of the red area. Inside the area (dilated) the
    # edit gets a smooth offset that meets the original on its border (a membrane: Laplace solve, at quarter resolution),
    # outside it the original itself, so the strip's surround is the very paint the cheek round it was projected from
    R = ndimage.binary_dilation(mk, iterations=12)
    q4 = 4; h4, w4 = R.shape[0] // q4, R.shape[1] // q4
    R4 = np.asarray(Image.fromarray(R.astype('u1') * 255).resize((w4, h4), Image.BILINEAR)) > 0
    R4 = ndimage.binary_dilation(R4, iterations=1)
    diff = og - ed
    D4 = np.stack([np.asarray(Image.fromarray(diff[..., c].astype(np.float32)).resize((w4, h4), Image.BILINEAR)) for c in range(3)], -1)
    O = np.where(R4[..., None], 0.0, D4)
    for _ in range(3000):
        avg = (np.roll(O, 1, 0) + np.roll(O, -1, 0) + np.roll(O, 1, 1) + np.roll(O, -1, 1)) / 4
        O = np.where(R4[..., None], avg, D4)
    Ofull = np.stack([np.asarray(Image.fromarray(O[..., c].astype(np.float32)).resize((R.shape[1], R.shape[0]), Image.BILINEAR)) for c in range(3)], -1)
    ed = np.where(R[..., None], np.clip(ed + Ofull, 0, 1), og)
    Image.fromarray((ed * 255 + 0.5).astype('u1')).save(SD / f'{t}_03_left_nobar_cloned.png')
    im = np.asarray(Image.open(KEEP / f'dook_head_{t}_raw.png').convert('RGB'), np.float32) / 255
    Ccol = im[ys, xs]
    tgt = np.where(f > 0)[0]
    # left strip from the view; right strip from the left by mirror (nearest left texel at the mirrored point)
    lt = tgt[left[tgt]]; rt = tgt[~left[tgt]]
    new = np.zeros((len(tgt), 3), np.float32); idx = {k: i for i, k in enumerate(tgt)}
    ix, iy = mp(P[lt]); colL = bilinear(ed, ix, iy)
    li = np.where(left & (f > 0))[0]
    lpos = {k: v for k, v in zip(lt, colL)}
    tr = cKDTree(P[lt]); _, nn = tr.query(P[rt] * np.array([-1, 1, 1]))
    colR = colL[nn]
    new[np.searchsorted(tgt, lt)] = colL; new[np.searchsorted(tgt, rt)] = colR
    # low frequencies: the projected strip's own (Gaussian SIG over the strip) replaced by the cheek's round it
    out = np.where((dist > 0.001) & (dist < FEATHER + 3 * SIG))[0]
    to = cKDTree(P[out]); tn = cKDTree(P[tgt])
    def gm(tree, vals, pts):
        dd, ii = tree.query(pts, k=200, distance_upper_bound=3 * SIG)
        ok = np.isfinite(dd); w = np.where(ok, np.exp(-0.5 * (np.where(ok, dd, 0) / SIG) ** 2), 0); ii = np.where(ok, ii, 0)
        return (vals[ii] * w[..., None]).sum(1) / np.maximum(w.sum(1, keepdims=True), 1e-6)
    low_round = gm(to, Ccol[out], P[tgt]); low_new = gm(tn, new, P[tgt])
    k_ = np.clip(1 - dist[tgt] / 0.004, 0, 1)[:, None]                  # deep in the strip the cheek's tone; at its edge the view's own (same source as the cheek round it)
    fin = np.clip(new + (low_round - low_new) * LOWK * (0.5 + 0.5 * k_), 0, 1) if LOWK else new
    res = im.copy(); res[ys[tgt], xs[tgt]] = Ccol[tgt] * (1 - f[tgt, None]) + fin * f[tgt, None]
    raw8 = (res * 255 + 0.5).astype('u1'); Image.fromarray(raw8).save(T / f'dook_head_{t}_raw.png')
    a = raw8.copy(); x, y = int(D['u'] * S), int(D['v'] * S); r = max(6, S // 100); a[y - r:y + r, x - r:x + r] = (16, 11, 9)
    Image.fromarray(a).save(T / f'dook_head_{t}_final.png')
    nnew = lum_normal(res)
    fm = np.zeros((S, S), np.float32); fm[ys[tgt], xs[tgt]] = f[tgt]
    f1k = np.asarray(Image.fromarray((fm * 255).astype('u1')).resize((1024, 1024), Image.BILINEAR), np.float32) / 255
    N = np.asarray(Image.open(KEEP / f'dook_head_{t}_normal.png').convert('RGB'), np.float32) / 255 * 2 - 1
    N2 = N * (1 - f1k[..., None]) + nnew * f1k[..., None]; N2 /= np.maximum(np.linalg.norm(N2, axis=2, keepdims=True), 1e-6)
    o8 = np.asarray(Image.open(KEEP / f'dook_head_{t}_normal.png').convert('RGB')).copy(); m1k = f1k > 0
    o8[m1k] = ((N2[m1k] * 0.5 + 0.5) * 255 + 0.5).astype('u1')
    Image.fromarray(o8).save(T / f'dook_head_{t}_normal.png')
    print('STRIP', t, 'texels', len(tgt), 'left', len(lt), 'right', len(rt))
