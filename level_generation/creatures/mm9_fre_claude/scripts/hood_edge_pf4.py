#!/usr/bin/env python3
"""Hood front edge as one clean line (PF3 pass 3, 2026-11-02; user: "the veil's front edge sits over the hair as big white jagged teeth").
F1's head/hood shell was one Meshy surface split into parts along a zigzag of triangles, so the hood's linen paint and the hair paint meet in
teeth. In the zone round that border (head and hood faces within ZONE of it, above 1.58 m, in front of the ears), every texel is assigned to
linen or hair by the share of hood surface round its 3D point (area-weighted face centroids within RADIUS): over 0.5 linen, else hair. Linen
texels take the colour of the nearest clean hood texel, hair texels of the nearest clean hair texel (in 3D, fine detail kept), and a narrow
hem just inside the line is shaded x0.88. Positions, UVs and parts unchanged. Args: <in png> <out png>   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
from scipy.spatial import cKDTree
RADIUS, ZONE, Z0 = 0.016, 0.018, -0.9297
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
kh, ks = names.index('head'), names.index('scarf')
im = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32); S = im.shape[0]
fc = comp[tri[:, 0]]; hf = np.where((mat == 1) & np.isin(fc, [kh, ks]))[0]
cen = co[tri[hf]].mean(1); area = np.linalg.norm(np.cross(co[tri[hf, 1]] - co[tri[hf, 0]], co[tri[hf, 2]] - co[tri[hf, 0]]), axis=1) / 2
isS = fc[hf] == ks
kd = cKDTree(cen)
POS = np.full((S, S, 3), np.nan); PRT = np.full((S, S), -1); NY = np.zeros((S, S))
_fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); _fn /= np.maximum(np.linalg.norm(_fn, axis=1, keepdims=True), 1e-12)
for f in hf:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    M = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(M)) < 1e-12: continue
    l = np.linalg.solve(M, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]; ok = (l3 > -0.01).all(1)
    yy, xx = pts[ok, 1].astype(int), pts[ok, 0].astype(int); POS[yy, xx] = l3[ok] @ co[tri[f]]; PRT[yy, xx] = fc[f]; NY[yy, xx] = _fn[f, 1]
cov = PRT >= 0
# border zone: within ZONE of a centroid of the other part, front of the head, above 1.58 m
hb = cKDTree(cen[~isS]); sb = cKDTree(cen[isS])
ty, tx = np.where(cov); P = POS[ty, tx]
dH = hb.query(P)[0]; dS = sb.query(P)[0]
zone = (np.minimum(dH, dS) < 1e-9) | ((np.where(PRT[ty, tx] == kh, dS, dH) < ZONE)) 
zone &= (P[:, 2] - Z0 > 1.52) & (P[:, 1] < 0.03)      # down past the ear: the hood faces interleaved with the cheek drew a white zigzag there
zy, zx, Pz = ty[zone], tx[zone], P[zone]
nbr = kd.query_ball_point(Pz, RADIUS)
frac = np.array([(area[n] * isS[n]).sum() / max(area[n].sum(), 1e-12) for n in nbr])
lin = frac > 0.5
lin &= ~((PRT[zy, zx] == kh) & (Pz[:, 2] - Z0 < 1.625))      # pass 4: head faces beside the face below the hood's rim stay hair/skin (one turned at the rim showed as a white shard)
lum = im @ np.array([0.2126, 0.7152, 0.0722]); det = lum - ni.gaussian_filter(lum, 1.5)
clean_l = cov & (PRT == ks); clean_l[zy, zx] = False
clean_h = cov & (PRT == kh); clean_h[zy, zx] = False
out = im.copy()
for want, clean in ((lin, clean_l), (~lin, clean_h)):
    cy, cx = np.where(clean)
    # only clean texels near the zone (a few cm) as sources
    pc = POS[cy, cx]; near = cKDTree(Pz).query(pc)[0] < 0.03; cy, cx, pc = cy[near], cx[near], pc[near]
    k = cKDTree(pc); _, j = k.query(Pz[want], k=4)
    col = im[cy[j], cx[j]].mean(1)
    out[zy[want], zx[want]] = np.clip(col + det[zy[want], zx[want]][:, None] * 0.5, 0, 255)
# pass 4 (orchestrator: "a white zigzag streak on the cheek in front of the ear", in profile): tweak_pf1.py clamps the ear zone to
# |x| <= 6.3 cm, head vertices AND their coincident hood twins, which folds a few hood faces flat onto the cheek (dihedral 107-180 deg) in
# front of the ear; painted linen they drew the white "<" streak (F1 has the same). Hood texels lying on that cheek plane (|x| < 6.6 cm,
# in front of the ear, 1.55-1.68 m) take the nearest head texel (cheek skin, or hair at the temple).
flap = (PRT == ks) & cov & (np.abs(np.nan_to_num(POS[..., 0])) < 0.068) & (np.nan_to_num(POS[..., 1]) < 0.0) & (np.nan_to_num(POS[..., 1]) > -0.07) \
    & (np.nan_to_num(POS[..., 2]) - Z0 > 1.55) & (np.nan_to_num(POS[..., 2]) - Z0 < 1.68)
skin_src = (PRT == kh) & cov & (np.abs(np.nan_to_num(POS[..., 0])) > 0.040) \
    & (np.nan_to_num(POS[..., 2]) - Z0 > 1.53) & (np.nan_to_num(POS[..., 2]) - Z0 < 1.70) & (np.nan_to_num(POS[..., 1]) < 0.0)      # the head under it: skin or hair
# and the small hood teeth hanging below the rim beside the braid's top, facing forward (|x| 6.8-9 cm, below 1.63 m): white shards there
flap |= (PRT == ks) & cov & (NY < -0.5) & (np.abs(np.nan_to_num(POS[..., 0])) < 0.090) & (np.nan_to_num(POS[..., 2]) - Z0 < 1.63) \
    & (np.nan_to_num(POS[..., 2]) - Z0 > 1.55) & (np.nan_to_num(POS[..., 1]) < 0.0)
_oh = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
skin_src &= ~((_oh[..., 1] < 0.18) & (_oh[..., 2] > 0.6))      # not linen-white head texels
if flap.any() and skin_src.any():
    fy, fx = np.where(flap); sy, sx = np.where(skin_src)
    _, j = cKDTree(POS[sy, sx]).query(POS[fy, fx], k=6)
    out[fy, fx] = np.clip(out[sy[j], sx[j]].mean(1) + det[fy, fx][:, None] * 0.3, 0, 255)
print('FLAP hood texels to cheek skin', int(flap.sum()))
hem = lin & (frac < 0.62)
out[zy[hem], zx[hem]] *= 0.88
Image.fromarray((np.clip(out, 0, 255) + 0.5).astype('u1')).save(sys.argv[2])
print('HOODEDGE zone', int(zone.sum()), 'linen', int(lin.sum()), 'hair', int((~lin).sum()), 'hem', int(hem.sum()))
