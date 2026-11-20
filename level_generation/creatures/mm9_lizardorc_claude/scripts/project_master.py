"""Project four Codex masters onto a texel set. Body: texels -> upload-pose points (co_up). Used for the tier A pattern mask (free, no retexture). Near-orthographic views: front looks along -z (camera at +z), left: camera at +x, back, right.
Each view is fitted by the mesh's silhouette box to the master's alpha box; a depth buffer stops limbs printing through. Library: project(points, normals, tris3d, dir, names)."""
import numpy as np
from PIL import Image
VIEWS = {'01_front': (lambda p: (p[..., 0] * -1 * -1, p[..., 1], p[..., 2]), np.array([0, 0, 1.])),
         '03_left': (lambda p: (-p[..., 2], p[..., 1], p[..., 0]), np.array([1., 0, 0])),
         '02_back': (lambda p: (-p[..., 0], p[..., 1], -p[..., 2]), np.array([0, 0, -1.])),
         '04_right': (lambda p: (p[..., 2], p[..., 1], -p[..., 0]), np.array([-1., 0, 0]))}
def load_view(path):
    im = np.asarray(Image.open(path).convert('RGBA'), np.float32) / 255
    a = im[..., 3] > .5; ys, xs = np.where(a)
    return im, (xs.min(), xs.max(), ys.min(), ys.max())
def depth_buffer(u, v, d, tris, W, H):
    Z = np.full((H, W), -1e9, np.float32)
    for t in tris:
        x, y, z = u[t], v[t], d[t]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), W - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), H - 1))
        if x1 < x0 or y1 < y0: continue
        ys, xs = np.meshgrid(np.arange(y0, y1 + 1), np.arange(x0, x1 + 1), indexing='ij')
        de = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(de) < 1e-9: continue
        a = ((y[1] - y[2]) * (xs - x[2]) + (x[2] - x[1]) * (ys - y[2])) / de; b = ((y[2] - y[0]) * (xs - x[2]) + (x[0] - x[2]) * (ys - y[2])) / de; c = 1 - a - b
        m = (a >= 0) & (b >= 0) & (c >= 0)
        zz = a * z[0] + b * z[1] + c * z[2]
        sub = Z[ys[m], xs[m]]; Z[ys[m], xs[m]] = np.maximum(sub, zz[m])
    return Z
def project(pts, nrm, mesh_v, mesh_t, master_dir, mirror_lr=False):
    """pts (N,3), nrm (N,3): returns rgb (N,3) and weight (N)."""
    col = np.zeros((len(pts), 3), np.float32); wt = np.zeros(len(pts), np.float32)
    for name, (f, dirv) in VIEWS.items():
        im, (x0, x1, y0, y1) = load_view(f'{master_dir}/{name}_clean.png' if False else f'{master_dir}/{name}.png')
        H, W = im.shape[:2]
        mu, mv, md = f(mesh_v); pu, pv, pd = f(pts)
        sx = (x1 - x0) / (mu.max() - mu.min()); sy = (y1 - y0) / (mv.max() - mv.min())
        U = x0 + (mu - mu.min()) * sx; V = y1 - (mv - mv.min()) * sy
        Z = depth_buffer(U / 2, V / 2, md, mesh_t, W // 2, H // 2)
        Pu = x0 + (pu - mu.min()) * sx; Pv = y1 - (pv - mv.min()) * sy
        ix = np.clip(Pu.astype(int), 0, W - 1); iy = np.clip(Pv.astype(int), 0, H - 1)
        vis = pd > Z[iy // 2, ix // 2] - .035
        w = np.clip(nrm @ dirv, 0, 1) ** 3 * vis * (im[iy, ix, 3] > .5)
        col += im[iy, ix, :3] * w[:, None]; wt += w
    return col / np.maximum(wt, 1e-5)[:, None], wt
