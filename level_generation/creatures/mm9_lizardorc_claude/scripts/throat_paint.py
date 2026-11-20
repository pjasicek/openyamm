"""Jaw underside and throat from ONE paint source (run 2, third request). The region is painted by an orthographic projection from below
and in front (direction D) of one image: a render of the current paint from that view (`render`), repainted by Codex inside the region
(references_head/throat/throat_below_edit.png), projected back onto every texel that sees the camera (z-buffer over all skin surfaces,
facing weight), feathered in 3D and seam-matched to the paint round it by a membrane offset, as mm9_dookmilitia_claude's project_strip.py.
The neck-ring strip faces and the chin fans (one texel each in r16-r17, flat fills) get real UV cells in free head atlas space (`cells`), and
their texels take the paint by 3D position. Used by assemble.py (cells) and tex_pages.py (paint)."""
import json, sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
TD = HERE / 'references_head' / 'throat'
D = np.array([0, .62, -.785]); D /= np.linalg.norm(D)          # view direction: the camera sits below and in front, looking up and back
RX = np.array([1., 0, 0]); UPI = np.cross(D, RX); UPI /= np.linalg.norm(UPI)
if UPI[2] < 0: UPI = -UPI                                      # image up toward the jaw tip
BOX = dict(x=.13, y=(.44, .72), z=(-.02, .50)); K = 2200.        # px per metre
C0 = np.array([0, .60, .22]); TAG = 'throat_below'
VIEWS = {'below': dict(D=(0, .62, -.785), C0=(0, .60, .22), BOX=dict(x=.13, y=(.44, .72), z=(-.02, .50)), TAG='throat_below'),
         'front': dict(D=(0, .30, -1.), C0=(0, .58, .10), BOX=dict(x=.13, y=(.50, .70), z=(-.02, .30)), TAG='throat_front')}


def use(name):
    """second view (run 2, third request): the throat just over the neck ring faces forward, edge-on to the view from below"""
    global D, UPI, C0, BOX, TAG
    v = VIEWS[name]; D = np.array(v['D'], float); D /= np.linalg.norm(D); UPI = np.cross(D, RX); UPI /= np.linalg.norm(UPI)
    if UPI[1] + UPI[2] < 0: UPI = -UPI
    C0 = np.array(v['C0'], float); BOX = dict(v['BOX']); TAG = v['TAG']
IMG = 1024
CELL = 14; FREE = [(1868, 1024, 2048, 1376), (1932, 0, 2048, 116), (1932, 248, 2048, 480)]     # x0, y0, x1, y1 (image rows, 2048 px)


def strip_and_chin(J, zip_=True):
    tri, mat, copies = J['tri'], J['mat'], J['ringcopy']
    fh = tri[mat == 1]; st = fh[np.isin(fh, copies).any(1)]
    return (zipper(J, st) if zip_ else st), J['chin']


def zipper(J, st):
    """The neck-ring strip rebuilt (run 2, third request). join_liz.py's strip joins the head's cut rim to the body's ring copy, both
    lying in the cut plane, but its triangles cross the annulus (edges up to 10 cm, folded 180 deg, 287 cm2 in all): the pale slivers at
    the neck sides and jaw corner. The same two loops are zipped in angle order round the neck: as many triangles (rim + ring), each
    spanning only between neighbours, so the strip lies flat in the plane with near-zero area. Winding follows the old strip's edges
    shared with the head (each rim edge is used once, opposite to the head face that owns it)."""
    sys.path.insert(0, str(HERE / 'scripts')); import headfr as H
    co = J['co']; rc = J['ringcopy']; inner = np.unique(st[~np.isin(st, rc)])
    n = H.PLANE_N; cen = co[rc].mean(0); v_ = np.cross(n, [1., 0, 0])
    def ang(v):
        q = co[v] - cen; q = q - np.outer(q @ n, n); return np.arctan2(q @ v_, q[:, 0]) % (2 * np.pi)
    A = inner[np.argsort(ang(inner))]; B = rc[np.argsort(ang(rc))]; aa = np.sort(ang(inner)); bb = np.sort(ang(rc))
    # start both loops at the same angle
    i0 = 0; j0 = int(np.argmin(np.abs(((bb - aa[0] + np.pi) % (2 * np.pi)) - np.pi)))
    A = np.roll(A, -i0); aa = np.roll(aa, -i0); B = np.roll(B, -j0); bb = np.roll(bb, -j0)
    ua = np.unwrap(aa); ub = np.unwrap(bb); ub = ub - 2 * np.pi * np.round((ub[0] - ua[0]) / (2 * np.pi))
    ua = np.r_[ua, ua[0] + 2 * np.pi]; ub = np.r_[ub, ub[0] + 2 * np.pi]; A2 = np.r_[A, A[0]]; B2 = np.r_[B, B[0]]
    i = j = 0; out = []
    while i < len(A) or j < len(B):
        if j >= len(B) or (i < len(A) and ua[i + 1] <= ub[j + 1]):
            out.append([A2[i], A2[i + 1], B2[j]]); i += 1
        else:
            out.append([A2[i], B2[j + 1], B2[j]]); j += 1
    out = np.array(out)
    # winding: a rim edge (a, b) of the head appears in the head's own face; the strip must hold it as (b, a)
    head = J['tri'][(J['mat'] == 1)]; head = head[~np.isin(head, rc).any(1)]
    own = set()
    for t in head:
        for a, b in ((0, 1), (1, 2), (2, 0)): own.add((int(t[a]), int(t[b])))
    agree = sum(((int(t[b]), int(t[a])) in own) for t in out for a, b in ((0, 1), (1, 2), (2, 0)))
    clash = sum(((int(t[a]), int(t[b])) in own) for t in out for a, b in ((0, 1), (1, 2), (2, 0)))
    if clash > agree: out = out[:, [0, 2, 1]]
    return out


def cells(J, S=2048):
    """per face of strip then chin: three UVs (Blender v up) in its own cell: right triangle inside a CELL-px square with 2 px pad"""
    st, ch = strip_and_chin(J); faces = np.vstack([st, ch]); out = []
    slots = []
    for x0, y0, x1, y1 in FREE:
        for yy in range(y0, y1 - CELL + 1, CELL):
            for xx in range(x0, x1 - CELL + 1, CELL): slots.append((xx, yy))
    assert len(slots) >= len(faces), (len(slots), len(faces))
    for (xx, yy), f in zip(slots, faces):
        a, b = 2.5, CELL - 2.5
        px = np.array([[xx + a, yy + a], [xx + b, yy + a], [xx + a, yy + b]], float)
        out.append(np.c_[px[:, 0] / S, 1 - px[:, 1] / S])
    return np.array(out[:len(st)]), np.array(out[len(st):]), faces


def project(P):
    q = P - C0; return IMG / 2 + (q @ RX) * K, IMG / 2 - (q @ UPI) * K, q @ (-D)     # column, row, depth toward the camera


def inbox(P):
    return (np.abs(P[..., 0]) < BOX['x']) & (P[..., 1] > BOX['y'][0]) & (P[..., 1] < BOX['y'][1]) & (P[..., 2] > BOX['z'][0]) & (P[..., 2] < BOX['z'][1])


def _hsv_h(c):
    r, g, b = c[..., 0], c[..., 1], c[..., 2]; return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360


def run(surfs, mode='apply'):
    """surfs: list of dict(img (H,W,3) float array, edited in place where repainted; P (H,W,3) texel positions; N (H,W,3) face normals;
    m (H,W) covered; prt (H,W) part; paint (H,W) bool: texels that may be repainted). Returns per-surface weight maps."""
    allc, alld, allp, ref = [], [], [], []
    for k, s in enumerate(surfs):
        m = s['m'] & inbox(s['P']); ys, xs = np.nonzero(m); P = s['P'][ys, xs]; c, r, d = project(P)
        fac = (s['N'][ys, xs] @ -D); ok = fac > 0
        allc.append(np.c_[c[ok], r[ok]]); alld.append(d[ok]); allp.append(s['img'][ys[ok], xs[ok]]); ref.append((k, ys[ok], xs[ok], fac[ok]))
    cr = np.vstack(allc); dd = np.concatenate(alld); col = np.vstack(allp)
    ic = np.clip(cr[:, 0].astype(int), 0, IMG - 1); ir = np.clip(cr[:, 1].astype(int), 0, IMG - 1)
    zb = np.full((IMG, IMG), -9.); np.maximum.at(zb, (ir, ic), dd)
    zb = ndi.grey_dilation(zb, size=5)          # splat gaps: a texel is hidden when a surface within 2 px lies clearly in front of it
    front = dd >= zb[ir, ic] - .006
    o = np.argsort(dd); o = o[front[o]]; rend = np.zeros((IMG, IMG, 3)); cov = np.zeros((IMG, IMG), bool)
    rend[ir[o], ic[o]] = col[o]; cov[ir[o], ic[o]] = True
    cov2 = ndi.binary_closing(cov, iterations=3); _, (a, b) = ndi.distance_transform_edt(~cov, return_indices=True); rend = rend[a, b]
    rend[~ndi.binary_dilation(cov2, iterations=2)] = .35
    # region weights per texel
    W = []; mask = np.zeros((IMG, IMG), np.float32); off = 0
    for (k, ys, xs, fac), c_, d_ in zip(ref, allc, alld):
        s = surfs[k]; w = np.zeros(s['m'].shape, np.float32)
        vis = d_ >= zb[np.clip(c_[:, 1].astype(int), 0, IMG - 1), np.clip(c_[:, 0].astype(int), 0, IMG - 1)] - .006
        P = s['P'][ys, xs]
        fw = np.clip((fac - .12) / .25, 0, 1)
        e = np.minimum.reduce([(BOX['x'] - np.abs(P[:, 0])) / .03, (BOX['y'][1] - P[:, 1]) / .025, (P[:, 2] - BOX['z'][0]) / .03, (BOX['z'][1] - P[:, 2]) / .04])
        bw = np.clip(e, 0, 1)
        red = ((_hsv_h(s['img'][ys, xs]) < 25) | (_hsv_h(s['img'][ys, xs]) > 330)) & (s['img'][ys, xs].max(1) - s['img'][ys, xs].min(1) > .25)
        ww = fw * bw * vis * s['paint'][ys, xs] * ~red * (1 - s['prior'][ys, xs] if 'prior' in s else 1)
        w[ys, xs] = ww; W.append(w)
        rr = np.clip(c_[:, 1].astype(int), 0, IMG - 1); cc = np.clip(c_[:, 0].astype(int), 0, IMG - 1); np.maximum.at(mask, (rr, cc), ww)
    mask = ndi.grey_closing(mask, size=5)
    TD.mkdir(parents=True, exist_ok=True)
    if mode == 'render':
        Image.fromarray((np.clip(rend, 0, 1) * 255 + .5).astype(np.uint8)).save(TD / f'{TAG}.png')
        m8 = (mask > .3); ov = rend.copy(); ov[m8] = ov[m8] * .45 + np.array([1., 0, 0]) * .55
        Image.fromarray((np.clip(ov, 0, 1) * 255 + .5).astype(np.uint8)).save(TD / f'{TAG}_overlay.png')
        Image.fromarray((m8 * 255).astype(np.uint8)).save(TD / f'{TAG}_mask.png')
        print('THROAT', TAG, 'render', int(m8.sum()), 'mask px'); return W
    ed = np.asarray(Image.open(TD / f'{TAG}_edit.png').convert('RGB').resize((IMG, IMG), Image.LANCZOS), np.float32) / 255
    mk = np.asarray(Image.open(TD / f'{TAG}_mask.png')) > 0
    # register the edit to the render outside the mask (a regenerated image may shift)
    roi = ndi.binary_dilation(mk, iterations=60) & ~ndi.binary_dilation(mk, iterations=6) & cov2
    g1 = (rend @ [.3, .6, .1]) * roi; g2 = (ed @ [.3, .6, .1]) * roi
    Fc = np.fft.fft2(g1) * np.conj(np.fft.fft2(g2)); cc = np.fft.ifft2(Fc / np.maximum(np.abs(Fc), 1e-9)).real
    sy, sx = np.unravel_index(cc.argmax(), cc.shape); sy = sy - IMG if sy > IMG // 2 else sy; sx = sx - IMG if sx > IMG // 2 else sx
    ed = ndi.shift(ed, (sy, sx, 0), order=1, mode='nearest')
    print('THROAT register shift', (int(sy), int(sx)), 'mean abs diff outside', round(float(np.abs((rend - ed)[roi]).mean()), 3))
    # membrane: inside the (dilated) region the edit takes a smooth offset that meets the render on its border
    R = ndi.binary_dilation(mk, iterations=8); q4 = 4; h4 = IMG // q4
    R4 = ndi.binary_dilation(np.asarray(Image.fromarray(R.astype('u1') * 255).resize((h4, h4), Image.BILINEAR)) > 0, iterations=1)
    D4 = np.stack([np.asarray(Image.fromarray((rend - ed)[..., c].astype(np.float32)).resize((h4, h4), Image.BILINEAR)) for c in range(3)], -1)
    O = np.where(R4[..., None], 0., D4)
    for _ in range(2500):
        O = np.where(R4[..., None], (np.roll(O, 1, 0) + np.roll(O, -1, 0) + np.roll(O, 1, 1) + np.roll(O, -1, 1)) / 4, D4)
    Of = np.stack([np.asarray(Image.fromarray(O[..., c].astype(np.float32)).resize((IMG, IMG), Image.BILINEAR)) for c in range(3)], -1)
    edc = np.clip(ed + Of, 0, 1); Image.fromarray((edc * 255 + .5).astype(np.uint8)).save(TD / f'{TAG}_edit_cloned.png')
    for (k, ys, xs, fac), c_ in zip(ref, allc):
        s = surfs[k]; w = W[k][ys, xs]; sel = w > 0
        x, y = np.clip(c_[sel, 0] - .5, 0, IMG - 1.001), np.clip(c_[sel, 1] - .5, 0, IMG - 1.001); x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[:, None], (y - y0)[:, None]
        new = edc[y0, x0] * (1 - fx) * (1 - fy) + edc[y0, x0 + 1] * fx * (1 - fy) + edc[y0 + 1, x0] * (1 - fx) * fy + edc[y0 + 1, x0 + 1] * fx * fy
        yy, xx = ys[sel], xs[sel]; s['img'][yy, xx] = s['img'][yy, xx] * (1 - w[sel, None]) + new * w[sel, None]
        print('THROAT surface', k, 'texels repainted', int(sel.sum()), 'full', int((w > .99).sum()))
    return W


def lum_normal(col, size=1024):
    lum = col @ np.array([.2126, .7152, .0722], np.float32)
    im = np.asarray(Image.fromarray((np.clip(lum, 0, 1) * 255).astype('u1')).resize((size, size), Image.LANCZOS), np.float32) / 255
    hp = im - ndi.gaussian_filter(im, 6); gx = ndi.sobel(hp, axis=1) * 2.; gy = ndi.sobel(hp, axis=0) * 2.
    n = np.dstack([-gx, gy, np.ones_like(gx)]); return n / np.linalg.norm(n, axis=2, keepdims=True)
