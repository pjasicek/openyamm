"""Raster of faces into a UV layout, and projection of the four master views onto it (silhouette fit per view, z-buffer, facing weight)."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def raster(uv, co, S):
    pos = np.zeros((S, S, 3), np.float32); nor = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool)
    bar = np.zeros((S, S, 3), np.float32); fid = np.zeros((S, S), np.int32)
    n = np.cross(co[:, 1] - co[:, 0], co[:, 2] - co[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    for t, (u, c) in enumerate(zip(uv, co)):
        x = u[:, 0] * S; y = (1 - u[:, 1]) * S
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), S - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), S - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-9: continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
        g = 1 - a - b
        m = (a >= -0.03) & (b >= -0.03) & (g >= -0.03)
        pos[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * c[0] + b[..., None] * c[1] + g[..., None] * c[2])[m]
        nor[y0:y1 + 1, x0:x1 + 1][m] = n[t]; cov[y0:y1 + 1, x0:x1 + 1][m] = True
        bar[y0:y1 + 1, x0:x1 + 1][m] = np.stack([a, b, g], -1)[m]; fid[y0:y1 + 1, x0:x1 + 1][m] = t
    return pos, nor, cov, bar, fid


def sample(img, uv):
    H, W = img.shape[:2]
    u = uv[..., 0] * W - 0.5; v = (1 - uv[..., 1]) * H - 0.5
    return np.stack([ndimage.map_coordinates(img[..., c], [v, u], order=1, mode='nearest') for c in range(img.shape[2])], -1)


VIEWS = {'01_front': (lambda p: p[..., 0], np.array([0, -1, 0.0])), '02_back': (lambda p: -p[..., 0], np.array([0, 1, 0.0])),
         '03_left': (lambda p: p[..., 1], np.array([1, 0, 0.0])), '04_right': (lambda p: -p[..., 1], np.array([-1, 0, 0.0]))}


def project(prefix, pos, nor, cov, tris, fine=False):
    """tris (F,3,3) of the whole figure for silhouette and depth. Returns colour, have mask, report."""
    S = pos.shape[0]
    acc = np.zeros((S, S, 3), np.float32); aw = np.zeros((S, S), np.float32); rep = {}
    for name, (hf, vd) in VIEWS.items():
        im = np.asarray(Image.open(f'{prefix}{name}_clean.png').convert('RGBA'), np.float32) / 255
        H, W = im.shape[:2]
        al = im[..., 3] > 0.5
        rows, cols = np.nonzero(al)
        tu, tv = hf(tris), tris[..., 2]
        # scale and shift from the silhouette box (height, then centre), refined on the mask
        mh = tv.max() - tv.min()
        best = (-1, None)
        small = al[::4, ::4]
        for ppm in np.arange(0.92, 1.06, 0.01) * ((rows.max() - rows.min()) / mh):
            cx0 = (cols.min() + cols.max()) / 2 - ppm * (tu.max() + tu.min()) / 2
            cy0 = rows.min() + ppm * tv.max()
            pts = np.c_[(tu.ravel() * ppm + cx0), (-tv.ravel() * ppm + cy0)]
            for dx in range(-48, 49, 8):
                for dy in range(-48, 49, 8):
                    px = ((pts[:, 0] + dx) / 4).astype(int); py = ((pts[:, 1] + dy) / 4).astype(int)
                    ok = (px >= 0) & (px < small.shape[1]) & (py >= 0) & (py < small.shape[0])
                    sc = small[py[ok], px[ok]].mean() * ok.mean()
                    if sc > best[0]: best = (sc, (ppm, cx0 + dx, cy0 + dy))
        sc, (ppm, cx, cy) = best
        rep[name] = (round(float(sc), 3), round(float(ppm)))
        u = hf(pos) * ppm + cx; v = -pos[..., 2] * ppm + cy
        DS = 2
        dep = np.full((H // DS, W // DS), -1e9, np.float32)
        tuu = (tu * ppm + cx) / DS; tvv = (-tv * ppm + cy) / DS; td = tris @ vd
        for a, b, c in zip(tuu, tvv, td):
            x0, x1 = int(max(a.min(), 0)), int(min(a.max() + 1, W // DS - 1)); y0, y1 = int(max(b.min(), 0)), int(min(b.max() + 1, H // DS - 1))
            if x1 < x0 or y1 < y0: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            d = (b[1] - b[2]) * (a[0] - a[2]) + (a[2] - a[1]) * (b[0] - b[2])
            if abs(d) < 1e-9: continue
            l0 = ((b[1] - b[2]) * (gx - a[2]) + (a[2] - a[1]) * (gy - b[2])) / d; l1 = ((b[2] - b[0]) * (gx - a[2]) + (a[0] - a[2]) * (gy - b[2])) / d; l2 = 1 - l0 - l1
            ins = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
            z = l0 * c[0] + l1 * c[1] + l2 * c[2]
            up = ins & (z > dep[y0:y1 + 1, x0:x1 + 1]); dep[y0:y1 + 1, x0:x1 + 1][up] = z[up]
        cd = pos @ vd.astype(np.float32)
        iu = np.clip((u / DS).astype(int), 0, W // DS - 1); iv = np.clip((v / DS).astype(int), 0, H // DS - 1)
        vis = cd > dep[iv, iu] - 0.015
        facing = np.clip(nor @ vd.astype(np.float32), 0, 1) ** 4
        s_ = np.stack([ndimage.map_coordinates(im[..., c], [v, u], order=1, mode='nearest') for c in range(4)], -1)
        w = facing * vis * cov * (s_[..., 3] > 0.9)
        acc += s_[..., :3] * w[..., None]; aw += w
    return acc / np.maximum(aw, 1e-4)[..., None], aw > 1e-3, rep
