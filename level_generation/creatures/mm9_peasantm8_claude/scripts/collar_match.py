#!/usr/bin/env python3
"""Head-set collar cloth matched to the body tunic (PeasantM8, 2026-11-02, head close-ups r1: a jagged lighter orange band
where Forad's head faces reach over the tunic collar: the head retexture painted the collar from the head masters' warmer
brown, the body retexture the tunic darker). Each head-square texel of cloth (rest z below Z_MAX, luminance below LUM,
soft edge) is multiplied per channel (linear light) by the ratio of the body paint's local mean colour (body tunic texels
within R of it in 3D) to the head paint's local mean (head cloth texels within R), so the detail stays the head paint's
and the tone follows the body's across the seam. Skin, hair and the hands are untouched.
Reads v2/textures/<prefix>_head_basecolor.png (backup <prefix>_head_basecolor_precollar.png on the first run, which is the
input of every later run), the graded body colour, a dump_mesh.py npz and texel_pos.py's head npz.
Usage (project folder): collar_match.py <prefix> <dump npz> <head texpos npz> [R 0.03] [LUM 0.40] [Z_MAX 0.675]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
pre, dump, tpos = sys.argv[1:4]
R = float(sys.argv[4]) if len(sys.argv) > 4 else 0.03
LUM = float(sys.argv[5]) if len(sys.argv) > 5 else 0.40
ZMAX = float(sys.argv[6]) if len(sys.argv) > 6 else 0.675
T = Path('v2/textures'); src = T / f'{pre}_head_basecolor.png'; bak = T / f'{pre}_head_basecolor_precollar.png'
if not bak.exists(): shutil.copy(src, bak)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
H = np.asarray(Image.open(bak).convert('RGB'), np.float32) / 255
B = np.asarray(Image.open(f'textures/{pre}_basecolor_graded.png').convert('RGB'), np.float32) / 255
N = H.shape[0]; S = int(round(0.8 * N))
hp = np.load(tpos)['pos']
d = np.load(dump, allow_pickle=True)
P, L, ls, lt, U = d['P'], d['L'], d['ls'], d['lt'], d['uv']
# body texel positions (UVMap, body faces only)
NB = B.shape[0]
bpos = np.full((NB, NB, 3), np.nan, np.float32)
for f in np.where(~(d['head'].astype(bool) | d['hand'].astype(bool)))[0]:
    li = np.arange(ls[f], ls[f] + lt[f]); xyzc = P[L[li]]
    if xyzc[:, 2].min() > ZMAX + 0.05 or xyzc[:, 2].max() < ZMAX - 0.25: continue
    for k in range(1, lt[f] - 1):
        tri = [li[0], li[k], li[k + 1]]
        uv = U[tri] * [NB, NB]; uv[:, 1] = NB - uv[:, 1]; xyz = P[L[tri]]
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, NB - 1), min(y1, NB - 1)
        if x1 < x0 or y1 < y0: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = uv
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12: continue
        w0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
        w1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
        w2 = 1 - w0 - w1; m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        ys, xs = np.where(m)
        bpos[y0 + ys, x0 + xs] = w0[m, None] * xyz[0] + w1[m, None] * xyz[1] + w2[m, None] * xyz[2]
yy, xx = np.mgrid[0:N, 0:N]
lumH = H @ np.array([0.299, 0.587, 0.114], np.float32)
soft = np.clip((LUM + 0.05 - lumH) / 0.10, 0, 1)
hm = np.isfinite(hp[..., 0]) & (xx < S) & (yy >= N - S) & (hp[..., 2] < ZMAX) & (soft > 0)
lumB = B @ np.array([0.299, 0.587, 0.114], np.float32)
bm = np.isfinite(bpos[..., 0]) & (lumB < LUM)
hy, hx = np.where(hm); by, bx = np.where(bm)
HP = hp[hy, hx]; BP = bpos[by, bx]
HL = lin(H[hy, hx]); BL = lin(B[by, bx])
rng = np.random.default_rng(0)
hs = rng.choice(len(HP), min(len(HP), 60000), replace=False); bs = rng.choice(len(BP), min(len(BP), 60000), replace=False)
th, tb = cKDTree(HP[hs]), cKDTree(BP[bs])
def local_mean(tree, cols, q):
    out = np.zeros((len(q), 3), np.float32); cnt = np.zeros(len(q))
    for i0 in range(0, len(q), 20000):
        nb = tree.query_ball_point(q[i0:i0 + 20000], R)
        for j, ids in enumerate(nb):
            if ids: out[i0 + j] = cols[ids].mean(0); cnt[i0 + j] = len(ids)
    return out, cnt
# gains on a coarse set of head texels, then nearest-neighbour to all
gs = rng.choice(len(HP), min(len(HP), 20000), replace=False)
mh, ch = local_mean(th, HL[hs], HP[gs]); mb, cb = local_mean(tb, BL[bs], HP[gs])
ok = (ch > 5) & (cb > 5)
gain = np.ones((len(gs), 3), np.float32); gain[ok] = np.clip(mb[ok] / np.maximum(mh[ok], 1e-4), 0.3, 2.0)
_, nn = cKDTree(HP[gs][ok]).query(HP)        # texels without body paint within R take the nearest covered gain
G = gain[ok][nn]
w = soft[hy, hx][:, None]
newL = HL * (1 - w + w * G)
out = H.copy(); out[hy, hx] = srgb(newL)
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(src)
print('COLLAR', dict(head_cloth_texels=int(len(HP)), body_ref_texels=int(len(BP)), gain_p10=np.percentile(gain[ok], 10, 0).round(2).tolist(),
                     gain_p50=np.median(gain[ok], 0).round(2).tolist(), gain_p90=np.percentile(gain[ok], 90, 0).round(2).tolist(), covered=float(ok.mean())))
