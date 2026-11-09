#!/usr/bin/env python3
"""The paint carries the rope on the cloth under it (Meshy projected the cords and belt onto the robe's faces), and the cords now hang elsewhere: pale rope-coloured strokes on cloth charts are replaced by the same chart's weave from a shifted copy, tone matched. Hands and forearms: Meshy's mottling low-passed. mk_body_raw0.png -> mk_body_raw.png. Project folder."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
D = np.load('work/uv_v1.npz'); uv, tri, mat, comp, inner = D['uv'], D['tri'], D['mat'], D['comp'], D['inner']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
S = 2048; fcomp = comp[tri[:, 0]]
def raster(sel):
    im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
    for f in np.where(sel)[0]: dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in tri[f]], fill=255)
    return np.asarray(im) > 0
cloth = raster((mat == 0) & (fcomp == pid['robe']) & ~inner); hands = raster((mat == 0) & (fcomp == pid['hands']))
im = np.asarray(Image.open('textures/mk_body_raw0.png').convert('RGB'), np.float32) / 255
lum = im @ np.array([0.2126, 0.7152, 0.0722], np.float32); sat = (im.max(2) - im.min(2)) / np.maximum(im.max(2), 1e-3)
base = ni.median_filter(lum, size=31)
med = float(np.median(lum[cloth])); hi = np.percentile(lum[cloth], 99.0)
# wide low-pass: what is brighter than the local cloth on a scale wider than the weave
low = ni.gaussian_filter(np.where(cloth, lum, med), 3.0)
strokes = cloth & (low > med * 1.32)
strokes = ni.binary_dilation(ni.binary_opening(strokes, iterations=1), iterations=9) & cloth
print('stroke texels', int(strokes.sum()), 'of cloth', int(cloth.sum()), 'med', med)
out = im.copy()
dist, idx = ni.distance_transform_edt(strokes, return_indices=True)
# the weave from a clean texel: shift each stroke texel along the nearest-clean direction by twice the distance + 40 texels of offset rows
yy, xx = np.mgrid[0:S, 0:S]
ys, xs = np.nonzero(strokes)
ny, nx = idx[0][ys, xs], idx[1][ys, xs]
dy, dx = ny - ys, nx - xs
sy = np.clip(ys + dy * 2, 0, S - 1); sx = np.clip(xs + dx * 2, 0, S - 1)
bad = strokes[sy, sx] | ~cloth[sy, sx]
sy[bad] = ny[bad]; sx[bad] = nx[bad]
pat = im[sy, sx]
out[ys, xs] = pat
# tone: the patch's low frequency to the surrounding cloth (normalised convolution of each side)
cl = (cloth & ~strokes).astype(np.float32)[..., None]; st = strokes.astype(np.float32)[..., None]
T_ = ni.gaussian_filter(im * cl, (14, 14, 0)) / np.maximum(ni.gaussian_filter(cl, (14, 14, 0)), 1e-3)
P_ = ni.gaussian_filter(out * st, (14, 14, 0)) / np.maximum(ni.gaussian_filter(st, (14, 14, 0)), 1e-3)
out[strokes] = (out + T_ - P_)[strokes]
soft = ni.gaussian_filter(strokes.astype(np.float32), 1.5)[..., None]
out = im * (1 - soft) + out * soft
# hands: low-pass the mottled paint, keep a little of the detail
sm = ni.gaussian_filter(out, (5, 5, 0)); hpf = out - sm
hm = ni.gaussian_filter(hands.astype(np.float32), 1.0)[..., None]
out = out * (1 - hm) + (sm + hpf * 0.35) * hm
# shoes: the same, or a dark tier's ramp posterises Meshy's mottled leather
shoes = raster((mat == 0) & (fcomp == pid['shoes']))
sm = ni.gaussian_filter(out, (6, 6, 0)); hpf = out - sm
hm = ni.gaussian_filter(shoes.astype(np.float32), 1.0)[..., None]
out = out * (1 - hm) + (sm + hpf * 0.25) * hm
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save('textures/mk_body_raw.png')
Image.fromarray((strokes * 255).astype('u1')).resize((1024, 1024)).save('review/strokes.png')
