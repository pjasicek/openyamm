#!/usr/bin/env python3
"""Tier B head colour (row 46 Town, PEASANTM5B) without credits: a different man on the same head, from tier A's final head set.
  render  <head png> <out png>                     flat unlit FRONT orthographic render of the head primitive (1254 px, centre
                                                   CX/CY in glTF bind metres, ORTHO wide), z-buffered (what Codex repaints)
  hair    <head png> <out png> <skin b png>        hair + beard texels (auburn: warm, saturated, darker than the skin) recoloured
                                                   to MM9 B's golden-brown hair by luminance ratio (detail kept)
  project <repaint png> <head png> <out png>       head texels visible from the front, inside the face window, facing the camera
                                                   (ramp 0.15..0.45 of +nz) take the repaint's colour (bilinear); the repaint's
                                                   low frequencies are matched to the base on a ring outside the window
Uses work/pm5_body_tex.glb (unmirrored, the head set's own UV layout). Project folder."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from pygltflib import GLTF2
R = 1254; CX, CY, ORTHO = 0.0, 1.615, 0.30
XW, YLO, YHI = 0.066, 1.50, 1.70          # face window (glTF bind)
g = GLTF2().load('work/pm5_body_tex.glb'); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)
pr = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name == 'PeasantM5Head')
P, NRM, UV = acc(pr.attributes.POSITION), acc(pr.attributes.NORMAL), acc(pr.attributes.TEXCOORD_0)
I = acc(pr.indices).reshape(-1, 3).astype(int)
def tri_raster(pts, n, cb):
    for f, t in enumerate(I):
        p = pts[t]; x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, n - 1), min(y1, n - 1)
        if x1 < x0 or y1 < y0: continue
        a, b, c = p; d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        l0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        l1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        l2 = 1 - l0 - l1; m = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
        if m.any(): cb(f, t, (gy[m] - 0.5).astype(int), (gx[m] - 0.5).astype(int), np.stack([l0, l1, l2], -1)[m])
scr = np.stack([((P[:, 0] - CX) / ORTHO + 0.5) * R, (0.5 - (P[:, 1] - CY) / ORTHO) * R], 1)
def zbuffer():
    Z = np.full((R, R), -1e9); F = -np.ones((R, R), int); B = np.zeros((R, R, 3))
    def cb(f, t, ys, xs, L):
        z = L @ P[t][:, 2]; k = z > Z[ys, xs]
        Z[ys[k], xs[k]] = z[k]; F[ys[k], xs[k]] = f; B[ys[k], xs[k]] = L[k]
    tri_raster(scr, R, cb); return Z, F, B
mode = sys.argv[1]
if mode == 'render':
    tex = np.asarray(Image.open(sys.argv[2]).convert('RGB'), float); N = tex.shape[0]
    Z, F, B = zbuffer(); img = np.full((R, R, 3), 102.0); m = F >= 0
    uv = np.einsum('nk,nkj->nj', B[m], UV[I[F[m]]]) * N
    img[m] = tex[np.clip(uv[:, 1].astype(int), 0, N - 1), np.clip(uv[:, 0].astype(int), 0, N - 1)]
    Image.fromarray(img.astype(np.uint8)).save(sys.argv[3]); print('RENDER', int(m.sum()))
elif mode == 'hair':
    tex = np.asarray(Image.open(sys.argv[2]).convert('RGB'), float) / 255; N = tex.shape[0]
    sb = np.asarray(Image.open(sys.argv[4]).convert('RGB'), float)[15:75, 35:105].reshape(-1, 3) / 255
    lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
    W = np.array([0.2126, 0.7152, 0.0722]); hb = np.median(lin(sb), 0); hb_l = hb @ W
    L = lin(tex); lum = L @ W
    mx, mn = tex.max(2), tex.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (tex[..., 1] - tex[..., 2]), 2 * tex[..., 0] - tex[..., 1] - tex[..., 2])) % 360
    k = int(round(N * 0.8)); sq = np.zeros((N, N), bool); sq[N - k:, :k] = True          # head square (hands stay)
    luma = tex @ [0.299, 0.587, 0.114]
    # auburn hair and beard: saturated and darker than the skin (skin sRGB luma ~0.65-0.75, sat ~0.35-0.45; lips are redder)
    hair = sq & (hue > 9) & (hue < 45) & (sat > 0.5) & (luma < 0.55)
    w = ndi.gaussian_filter(hair.astype(float), 1.0)
    # golden-brown: the A paint's luminance times B's hair chroma, lifted so A's median hair maps to B's (x GAIN)
    gain = 1.25 * hb_l / np.median(lum[hair])
    new = np.clip(lum[..., None] * gain * hb / hb_l, 0, 1)
    out = L * (1 - w[..., None]) + new * w[..., None]
    Image.fromarray((srgb(out) * 255 + 0.5).clip(0, 255).astype(np.uint8)).save(sys.argv[3])
    print('HAIR_B texels', int(hair.sum()), 'gain', round(float(gain), 2), 'B hair', (srgb(hb) * 255).round().tolist())
elif mode == 'project':
    rep = np.asarray(Image.open(sys.argv[2]).convert('RGB').resize((R, R), Image.LANCZOS), float)
    base = np.asarray(Image.open(sys.argv[3]).convert('RGB'), float); N = base.shape[0]
    Z, F, B = zbuffer()
    pos = np.full((N, N, 3), np.nan); nrm = np.zeros((N, N, 3)); fid = -np.ones((N, N), int)
    def cb(f, t, ys, xs, L):
        pos[ys, xs] = L @ P[t]; nrm[ys, xs] = L @ NRM[t]; fid[ys, xs] = f
    tri_raster(UV * N, N, cb)
    cov = fid >= 0; p = np.nan_to_num(pos)
    sx = ((p[..., 0] - CX) / ORTHO + 0.5) * R; sy = (0.5 - (p[..., 1] - CY) / ORTHO) * R
    ix, iy = np.clip(sx.astype(int), 0, R - 1), np.clip(sy.astype(int), 0, R - 1)
    vis = cov & (Z[iy, ix] - p[..., 2] < 0.002)
    ramp = lambda v, a, b: np.clip((v - a) / (b - a), 0, 1)
    win = ramp(XW - np.abs(p[..., 0] - CX), 0, 0.006) * ramp(p[..., 1] - YLO, 0, 0.006) * ramp(YHI - p[..., 1], 0, 0.006)
    face = ramp(nrm[..., 2] / np.maximum(np.linalg.norm(nrm, axis=2), 1e-6), 0.15, 0.45)
    w = vis * win * face
    col = np.stack([ndi.map_coordinates(rep[..., k], [sy - 0.5, sx - 0.5], order=1, mode='nearest') for k in range(3)], 2)
    # low-frequency match of the repaint to the base on the visible face edge ring (keeps neck/ears/hair tone continuous)
    ring = vis & (win > 0) & (win < 0.6)
    gain = np.median(base[ring] + 1, 0) / np.median(col[ring] + 1, 0)
    col = col * (1 + (gain - 1) * (1 - win)[..., None])
    out = base * (1 - w[..., None]) + col * w[..., None]
    # chart edges and gutters next to projected texels (the raster misses edge texels; bilinear filtering then pulled in
    # A's beard from the base as thin dark seam lines): they take the nearest well-projected texel's colour within 4 px
    good = w > 0.5
    dist, (iy2, ix2) = ndi.distance_transform_edt(~good, return_indices=True)
    edge = (~good) & (dist <= 4) & (ndi.maximum_filter(win * vis, 9) > 0.5)
    out[edge] = out[iy2[edge], ix2[edge]]
    # lips: the repaint's lip line came out a saturated red (lipstick); lip texels (red hue, saturated) move 40 % toward
    # the neighbouring skin's colour at their own luminance
    o = out / 255; mx, mn = o.max(2), o.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (o[..., 1] - o[..., 2]), 2 * o[..., 0] - o[..., 1] - o[..., 2])) % 360
    lip = (w > 0.3) & ((hue < 9) | (hue > 340)) & (sat > 0.42) & (np.abs(p[..., 1] - 1.565) < 0.03)
    sk = (w > 0.5) & (hue > 12) & (hue < 30) & (sat > 0.25) & (sat < 0.5)
    ref = np.median(o[sk], 0); lum = o @ [0.299, 0.587, 0.114]
    tgt = ref * (lum / (ref @ [0.299, 0.587, 0.114]))[..., None]
    lw = ndi.gaussian_filter(lip.astype(float), 1.0)[..., None] * 0.4
    out = (o * (1 - lw) + tgt * lw) * 255
    print('PROJECT edge texels', int(edge.sum()), 'lip texels', int(lip.sum()))
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(sys.argv[4])
    print('PROJECT texels', int((w > 0.01).sum()), 'edge gain', gain.round(3).tolist())
