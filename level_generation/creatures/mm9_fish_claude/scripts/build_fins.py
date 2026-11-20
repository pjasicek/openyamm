#!/usr/bin/env python3
"""Our own fin leaves for the MM9 fish, cut out by the side master's alpha (MM9 FISH.dtx draws its fins with alpha
cut-outs: MONSTERS.txt Transparent 1).

The fin outlines, rays and colours come from references_hd/03_left.png (a true side profile). work/fins_config.json
holds the annotated root lines (where each fin meets the body in the master) and the pectoral outline (it lies over the
flank, so it has no background around it). Master pixels map onto our body's side plane by the similarity that puts
the master's snout tip and caudal base on ours; each column of a dorsal/anal/pelvic fin then shifts so its root line
sits on our body's back or belly (the caudal fin shifts as a whole onto the peduncle end), and every leaf continues
bury_px into the body. Leaves are closed: two sheets 0.8 mm apart (normals out), on a grid of grid_px master pixels;
the outline is the alpha (MASK), not the geometry.
Placement: dorsal, anal, caudal on the midline (x = 0); pelvics on MM9's pelvic planes (x = +-6 mm, splaying out
downward as MM9's quads do); pectorals over the flanks, from 3 mm under the flank at the base, quickly 4 mm clear of it (the flank bulges as the body bends) and ~1.2 cm out at
the tip
(MM9's pectoral quads are swept back at about 20 degrees).
Usage: build_fins.py <body npz (dump_mesh: Body)> <out npz> <out atlas png>"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
cfg = json.load(open(HERE / 'work' / 'fins_config.json'))
body = np.load(sys.argv[1])
OUT, ATLAS = sys.argv[2], sys.argv[3]
BV = body['Body_v'].astype(np.float64)
m = Image.open(HERE / cfg['master']).convert('RGBA')
MA = np.asarray(m).astype(np.float32) / 255
H, W = MA.shape[:2]
G, BURY = cfg['grid_px'], cfg['bury_px']

# ---- similarity master px -> our side plane (Y, Z): snout tip and caudal base
ymin, ymax = BV[:, 1].min(), BV[:, 1].max()
s_o = complex(ymin, BV[BV[:, 1] < ymin + 0.003, 2].mean())
c_o = complex(ymax, BV[BV[:, 1] > ymax - 0.003, 2].mean())
s_m = complex(cfg['snout_px'][0], -cfg['snout_px'][1])
c_m = complex(cfg['caudal_base_px'][0], -cfg['caudal_base_px'][1])
A_ = (c_o - s_o) / (c_m - s_m)
B_ = s_o - A_ * s_m


def to_side(px, py):
    z = A_ * (np.asarray(px) - 1j * np.asarray(py)) + B_
    return z.real, z.imag


# our body's side profile: top/bottom z per 1 mm y bin, half-width per (y, z) 2 mm bin
yb = np.round(BV[:, 1] * 1000).astype(int)
top, bot = {}, {}
for y, z in zip(yb, BV[:, 2]):
    top[y] = max(top.get(y, -1), z); bot[y] = min(bot.get(y, 9), z)
keys = np.array(sorted(top))
topv = ndimage.uniform_filter1d(np.array([top[k] for k in keys]), 5)
botv = ndimage.uniform_filter1d(np.array([bot[k] for k in keys]), 5)
prof_top = lambda y: np.interp(np.asarray(y) * 1000, keys, topv)
prof_bot = lambda y: np.interp(np.asarray(y) * 1000, keys, botv)
hw = {}
for (x, y, z) in BV:
    k = (int(round(y * 500)), int(round(z * 500)))
    hw[k] = max(hw.get(k, 0.0), abs(x))


def half_width(y, z):
    k = (int(round(y * 500)), int(round(z * 500)))
    best = 0.0
    for dy in (-1, 0, 1):
        for dz in (-1, 0, 1):
            best = max(best, hw.get((k[0] + dy, k[1] + dz), 0.0))
    return best


def poly_side(root, px, py, kind):
    """+ on the fin side of the root polyline (above for top, below for bottom, behind for tail)."""
    r = np.array(root, float)
    if kind == 'tail':
        return px - np.interp(py, r[:, 1], r[:, 0])
    ry = np.interp(px, r[:, 0], r[:, 1])
    return (ry - py) if kind == 'top' else (py - ry)


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
regions, alphas = {}, {}
for name, f in cfg['fins'].items():
    if f['kind'] == 'polygon':
        poly = Image.new('L', (W, H), 0)
        ImageDraw.Draw(poly).polygon([tuple(p) for p in f['polygon']], fill=255)
        pa = np.asarray(poly.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
        alpha = pa * MA[..., 3]
        region = pa > 0.01
    else:
        sd = poly_side(f['root'], xx, yy, f['kind'])
        if f['kind'] == 'tail':
            inr = (yy >= f['y_range'][0]) & (yy <= f['y_range'][1])
        else:
            inr = (xx >= f['x_range'][0]) & (xx <= f['x_range'][1])
        fin = inr & (sd > 0)
        alpha = np.where(fin, MA[..., 3], 0)
        band = inr & (sd <= 0) & (sd > -BURY) & (MA[..., 3] > 0.5)     # the buried root band (body pixels only)
        alpha = np.where(band, 1.0, alpha)
        region = (inr & (sd > 0) & (alpha > 0.02)) | band
    regions[name], alphas[name] = region, alpha

# ---- atlas: crops at master resolution, shelf-packed into 1024 x 1024
PAD = G + 4      # every grid cell of a leaf samples only its own crop (alpha 0 around the fin)
crops = {}
for name, r in regions.items():
    ys, xs = np.nonzero(ndimage.binary_dilation(r, iterations=PAD))
    crops[name] = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
order = sorted(crops, key=lambda n: -(crops[n][3] - crops[n][1]))
AS = 1024
for SC in np.arange(1.0, 0.5, -0.02):     # largest uniform scale whose shelf packing fits the 1K atlas
    place, x, y, rowh = {}, 0, 0, 0
    for n in order:
        w = int(np.ceil((crops[n][2] - crops[n][0]) * SC)); h = int(np.ceil((crops[n][3] - crops[n][1]) * SC))
        if x + w > AS:
            x, y, rowh = 0, y + rowh, 0
        place[n] = (x, y); x += w; rowh = max(rowh, h)
    if y + rowh <= AS and all(place[n][0] + (crops[n][2] - crops[n][0]) * SC <= AS for n in order):
        break
atlas = np.zeros((AS, AS, 4), np.float32)
for n, (x0, y0, x1, y1) in crops.items():
    px0, py0 = place[n]
    rgb = MA[y0:y1, x0:x1, :3].copy()
    a = alphas[n][y0:y1, x0:x1]
    solid = a > 0.5
    if solid.any():   # bleed the fin colour outward so the cut-out edge filters to fin colour
        _, (iy, ix) = ndimage.distance_transform_edt(~solid, return_indices=True)
        rgb = np.where(solid[..., None], rgb, rgb[iy, ix])
    rgba = np.concatenate([rgb, a[..., None]], -1)
    w, h = int(round((x1 - x0) * SC)), int(round((y1 - y0) * SC))
    chans = [np.asarray(Image.fromarray((rgba[..., c] * 255).round().astype(np.uint8)).resize((w, h), Image.LANCZOS),
                        np.float32) / 255 for c in range(4)]
    atlas[py0:py0 + h, px0:px0 + w] = np.stack(chans, -1)
Image.fromarray((atlas * 255).round().astype(np.uint8), 'RGBA').save(ATLAS)

# ---- leaves
V, T, UV, FIN, ROOT = [], [], [], [], []
fin_ids = {n: i for i, n in enumerate(cfg['fins'])}
for name, f in cfg['fins'].items():
    r = ndimage.binary_dilation(regions[name], iterations=3)
    x0, y0, x1, y1 = crops[name]
    gx = np.arange(x0 - G // 2, x1 + G, G); gy = np.arange(y0 - G // 2, y1 + G, G)
    cells = []
    for j in range(len(gy) - 1):
        for i in range(len(gx) - 1):
            a, b = max(gx[i], 0), min(gx[i + 1], W); c, d = max(gy[j], 0), min(gy[j + 1], H)
            if b > a and d > c and r[c:d, a:b].any():
                cells.append((i, j))
    vid = {}
    pts = []
    for (i, j) in cells:
        for (di, dj) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            k = (i + di, j + dj)
            if k not in vid:
                vid[k] = len(pts); pts.append((gx[k[0]], gy[k[1]]))
    pts = np.array(pts, float)
    Ys, Zs = to_side(pts[:, 0], pts[:, 1])
    Ys, Zs = np.array(Ys), np.array(Zs)
    if f['kind'] in ('top', 'bottom'):
        rt = np.array(f['root'], float)
        rY, rZ = to_side(rt[:, 0], rt[:, 1])
        target = prof_top(rY) if f['kind'] == 'top' else prof_bot(rY)
        shift = np.interp(Ys, np.array(rY), target - np.array(rZ))
        Zs = Zs + shift
        if f['kind'] == 'top':
            rootd = Zs - prof_top(Ys)
        else:
            rootd = prof_bot(Ys) - Zs
    elif f['kind'] == 'tail':
        rt = np.array(f['root'], float)
        rY, rZ = to_side(rt[:, 0], rt[:, 1])
        dY = ymax - 0.002 - np.mean(rY)
        dZ = c_o.imag - np.mean(rZ)
        Ys, Zs = Ys + dY, Zs + dZ
        rootd = Ys - (ymax - 0.002)
    else:
        bY, bZ = to_side(*f['base_px'])
        rootd = np.hypot(Ys - bY, Zs - bZ)
    # x per vertex
    if name == 'pelvic':
        Xs = 0.006 + (0.152 * np.maximum(prof_bot(Ys) - Zs, 0)) / 0.988
    elif name == 'pectoral':
        Xs = np.array([half_width(y, z) for y, z in zip(Ys, Zs)]) - 0.003 + 0.6 * np.minimum(rootd, 0.012) + 0.25 * np.maximum(rootd - 0.012, 0)
        Xs = np.maximum(Xs, 0.003)
    else:
        Xs = np.zeros_like(Ys)
    px0, py0 = place[name]
    uv = np.stack([((pts[:, 0] - x0) * SC + px0) / AS, 1 - ((pts[:, 1] - y0) * SC + py0) / AS], 1)
    sides = [(+1, False), (-1, True)] if not f.get('paired') else [(+1, False), (-1, True)]
    copies = [1, -1] if f.get('paired') else [1]
    for mir in copies:
        for off, flip in sides:
            base = len(V)
            for p in range(len(pts)):
                V.append((mir * (Xs[p] + off * 0.0004), Ys[p], Zs[p]))
                UV.append(tuple(uv[p])); FIN.append(fin_ids[name] + (10 if mir < 0 else 0)); ROOT.append(rootd[p])
            for (i, j) in cells:
                q = [vid[(i, j)], vid[(i + 1, j)], vid[(i + 1, j + 1)], vid[(i, j + 1)]]
                # image y grows down: (i,j)->(i+1,j)->(i+1,j+1) is clockwise seen from +x (left view) -> reverse
                tri = [(q[0], q[2], q[1]), (q[0], q[3], q[2])]
                if flip != (mir < 0):
                    tri = [(a, c, b) for a, b, c in tri]
                for t in tri:
                    T.append(tuple(base + v for v in t))
V, T = np.array(V), np.array(T)
np.savez(OUT, v=V, t=T, uv=np.array(UV), fin=np.array(FIN), root=np.array(ROOT), names=np.array(list(cfg['fins'])))
print('FINS', json.dumps({'verts': len(V), 'tris': len(T), 'atlas_rows_used': int(y + rowh), 'atlas_scale': float(SC),
                          'scale_m_per_px': abs(A_), 'place': {k: list(map(int, v)) for k, v in place.items()}}))
