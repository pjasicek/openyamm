#!/usr/bin/env python3
"""Wing meshes (2D, image space) and wing texture from the HD top view (references_hd/05_wings_top.png).

Writes work/wing_mesh2d.json and textures/icky_wing_basecolor_src.png (2048x512, the wing crop with the wing colour
dilated past the outline so filtering never pulls in the background; UV = (pixel - crop origin) / crop size).

Per side (image right = the creature's right, -X; the head is at the image top):
- membrane: the alpha mask beyond the body column, opened by OPEN px (cuts the thin wrist claw off), largest
  component; outline sampled every OUTLINE_STEP px, interior grid every GRID_STEP px kept GRID_MARGIN px inside;
  Delaunay, triangles whose centroid lies outside the mask dropped; 'h' per vertex = thickness factor (0 on the
  outline, smoothstep to 1 at RIDGE px inside), so build_wings.py can make a closed leaf.
- claw: the alpha pixels the opening removed near the wrist (the component in front of the leading edge); base centre
  (pixels touching the membrane), tip (farthest pixel) and half width, for a small cone.
The root and tip landmarks (image root = body edge at the mean row where the membrane touches the body column; tip =
the membrane pixel farthest from it) map the image onto the MM9 wing by a 2D similarity in build_wings.py.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import Delaunay

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / 'references_hd' / '05_wings_top.png'
OPEN = 7
LEG_ROW = 512
LEG_HALF = 130
OUTLINE_STEP = 14
GRID_STEP = 42
GRID_MARGIN = 16
RIDGE = 40.0
CROP = (36, 196, 1500, 560)
TEX = (2048, 512)

im = np.array(Image.open(SRC).convert('RGBA')).astype(np.float32)
alpha = im[..., 3] > 128
H, W = alpha.shape
# body column: the narrow run under the wings (tail rows) gives the centre; the shoulder rows give its half width
rows = alpha[560:640]
cols = np.nonzero(rows.any(0))[0]
cx = float(np.median(np.nonzero(alpha[660:760])[1]))
body_half = 46.0
wingpix = alpha.copy()
wingpix[:, int(cx - body_half):int(cx + body_half) + 1] = False
# the hind legs hang beside the body column below the trailing-edge root
wingpix[LEG_ROW:, int(cx - LEG_HALF):int(cx + LEG_HALF) + 1] = False
# wrist claws: cream / orange pixels (the membrane is green-teal), in front of the root row
rgbf = im[..., :3] / 255.0
mx, mn = rgbf.max(-1), rgbf.min(-1)
hue = np.zeros_like(mx)
dlt = mx - mn + 1e-9
r_, g_, b_ = rgbf[..., 0], rgbf[..., 1], rgbf[..., 2]
hue = np.where(mx == r_, ((g_ - b_) / dlt) % 6, np.where(mx == g_, (b_ - r_) / dlt + 2, (r_ - g_) / dlt + 4)) * 60
warm = wingpix & ((hue < 62) | (hue > 330)) & (mx > 0.3) & (dlt / (mx + 1e-9) > 0.2)
warm = ndimage.binary_dilation(ndimage.binary_opening(warm, iterations=1), iterations=2) & wingpix
clab, cnum = ndimage.label(warm)
claw_masks = {}
for j in range(cnum):
    m = clab == j + 1
    yy, xx = np.nonzero(m)
    if m.sum() < 300 or yy.mean() > 330:
        continue
    claw_masks.setdefault('right' if xx.mean() > cx else 'left', []).append(m)
claw_masks = {k: max(v, key=lambda m: m.sum()) for k, v in claw_masks.items()}
membrane_src = wingpix.copy()
for m in claw_masks.values():
    membrane_src &= ~m
opened = ndimage.binary_opening(membrane_src, structure=np.ones((OPEN, OPEN), bool))
out = {'image': str(SRC.relative_to(HERE)), 'size': [W, H], 'centre_x': cx, 'body_half': body_half, 'crop': CROP,
       'texture_size': TEX, 'wings': {}}


def outline(mask):
    """ordered boundary pixels of a single-component mask (Moore tracing on the padded mask)"""
    m = np.pad(mask, 1)
    ys, xs = np.nonzero(m)
    start = (ys[0], xs[0])
    dirs = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    pts = [start]
    cur, back = start, 6
    for _ in range(200000):
        found = False
        for k in range(8):
            d = (back + 1 + k) % 8
            ny, nx = cur[0] + dirs[d][0], cur[1] + dirs[d][1]
            if m[ny, nx]:
                back = (d + 4) % 8
                cur = (ny, nx)
                found = True
                break
        if not found or cur == start:
            break
        pts.append(cur)
    return np.array([(x - 1, y - 1) for y, x in pts], float)


for side, sign in (('right', 1), ('left', -1)):  # image right = creature's right (-X)
    half = (np.arange(W)[None, :] > cx) if sign > 0 else (np.arange(W)[None, :] < cx)
    lab, n = ndimage.label(opened & half)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    mem = lab == (int(np.argmax(sizes)) + 1)
    mem = ndimage.binary_fill_holes(mem)
    # root: body edge at the mean row where the membrane touches the body column
    edge_x = int(cx + sign * (body_half + 1))
    touch = np.nonzero(mem[:, edge_x - 2:edge_x + 3].any(1))[0]
    root = np.array([cx + sign * body_half, float(touch.mean())])
    ys, xs = np.nonzero(mem)
    d = np.hypot(xs - root[0], ys - root[1])
    tip = np.array([xs[d.argmax()], ys[d.argmax()]], float)
    # outline, resampled by arc length
    ol = outline(mem)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(np.vstack([ol, ol[:1]]), axis=0).T))]
    k = max(12, int(seg[-1] / OUTLINE_STEP))
    s = np.linspace(0, seg[-1], k, endpoint=False)
    closed = np.vstack([ol, ol[:1]])
    bx = np.interp(s, seg, closed[:, 0]); by = np.interp(s, seg, closed[:, 1])
    bnd = np.c_[bx, by]
    dist_in = ndimage.distance_transform_edt(mem)
    gx, gy = np.meshgrid(np.arange(0, W, GRID_STEP), np.arange(0, H, GRID_STEP))
    gx = gx.ravel() + (gy.ravel() // GRID_STEP % 2) * GRID_STEP / 2  # staggered rows: better triangles
    gy = gy.ravel()
    inside = (gx < W) & (dist_in[gy.astype(int), np.clip(gx.astype(int), 0, W - 1)] > GRID_MARGIN)
    grid = np.c_[gx[inside], gy[inside]]
    extra = np.zeros((0, 2))
    for it in range(8):
        P = np.vstack([bnd, grid, extra])
        tri = Delaunay(P).simplices
        cen = P[tri].mean(1)
        inm = lambda q: mem[np.clip(q[:, 1].round().astype(int), 0, H - 1), np.clip(q[:, 0].round().astype(int), 0, W - 1)]
        keep = inm(cen)
        # also drop triangles whose edge midpoints leave the mask (spanning a scallop), outline edges excepted
        nb_ = len(bnd)
        for a_, b_ in ((0, 1), (1, 2), (2, 0)):
            mid = (P[tri[:, a_]] + P[tri[:, b_]]) / 2
            outline_edge = (tri[:, a_] < nb_) & (tri[:, b_] < nb_) & (
                (np.abs(tri[:, a_] - tri[:, b_]) == 1) | (np.abs(tri[:, a_] - tri[:, b_]) == nb_ - 1))
            keep &= inm(mid) | outline_edge
        tri = tri[keep]
        edges = np.sort(np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), 1)
        u, cnt = np.unique(edges, axis=0, return_counts=True)
        on_b = np.zeros(len(P), bool); on_b[u[cnt == 1].ravel()] = True
        # chords: interior edges between two outline vertices collapse top onto bottom; split them
        chords = u[(cnt == 2) & on_b[u[:, 0]] & on_b[u[:, 1]]]
        if len(chords) == 0:
            break
        extra = np.vstack([extra, (P[chords[:, 0]] + P[chords[:, 1]]) / 2])
    used = np.unique(tri)
    remap = -np.ones(len(P), int); remap[used] = np.arange(len(used))
    P = P[used]; tri = remap[tri]; on_b = on_b[used]
    dd = dist_in[np.clip(P[:, 1].round().astype(int), 0, H - 1), np.clip(P[:, 0].round().astype(int), 0, W - 1)]
    t = np.clip(dd / RIDGE, 0, 1); h = np.maximum(t * t * (3 - 2 * t), 0.2); h[on_b] = 0.0
    # claw: the warm-coloured blob at the wrist; base = its pixels touching the membrane, tip = farthest pixel
    claw = None
    if side in claw_masks:
        m = claw_masks[side]
        yy, xx = np.nonzero(m)
        base_px = m & ndimage.binary_dilation(mem, iterations=4)
        by_, bx_ = np.nonzero(base_px) if base_px.any() else (yy, xx)
        base = np.array([bx_.mean(), by_.mean()])
        dd2 = np.hypot(xx - base[0], yy - base[1])
        ctip = np.array([xx[dd2.argmax()], yy[dd2.argmax()]], float)
        width = float(m.sum() / max(dd2.max(), 1.0))
        claw = {'base': base.tolist(), 'tip': ctip.tolist(), 'half_width': width / 2, 'pixels': int(m.sum())}
    out['wings'][side] = {'root': root.tolist(), 'tip': tip.tolist(), 'verts': P.tolist(), 'tris': tri.tolist(),
                          'h': h.tolist(), 'boundary': on_b.tolist(), 'claw': claw, 'pixels': int(mem.sum())}
    print(side, 'verts', len(P), 'tris', len(tri), 'root', root.round(1), 'tip', tip, 'claw', claw)
(HERE / 'work' / 'wing_mesh2d.json').write_text(json.dumps(out))

# texture: crop, dilate colour of the wings (membranes and claws) into the background, resize
rgb = im[..., :3]
fill = ~wingpix
_, (iy, ix) = ndimage.distance_transform_edt(fill, return_indices=True)
dil = rgb[iy, ix]
x0, y0, x1, y1 = CROP
crop = Image.fromarray(dil[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)).resize(TEX, Image.LANCZOS)
(HERE / 'textures').mkdir(exist_ok=True)
crop.save(HERE / 'textures' / 'icky_wing_basecolor_src.png')
# review: the triangulation over the image
from PIL import ImageDraw
rv = Image.open(SRC).convert('RGBA')
bg = Image.new('RGBA', rv.size, (70, 70, 70, 255)); bg.alpha_composite(rv)
dr = ImageDraw.Draw(bg)
for side, w in out['wings'].items():
    P = np.array(w['verts'])
    for t in w['tris']:
        pts = [tuple(P[i]) for i in t] + [tuple(P[t[0]])]
        dr.line(pts, fill=(255, 255, 0, 255), width=1)
    if w['claw']:
        dr.line([tuple(w['claw']['base']), tuple(w['claw']['tip'])], fill=(255, 0, 0, 255), width=3)
    dr.ellipse([w['root'][0] - 5, w['root'][1] - 5, w['root'][0] + 5, w['root'][1] + 5], fill=(0, 255, 255, 255))
    dr.ellipse([w['tip'][0] - 5, w['tip'][1] - 5, w['tip'][0] + 5, w['tip'][1] + 5], fill=(255, 0, 255, 255))
bg.convert('RGB').save(HERE / 'work' / 'wing_mesh2d.png')
