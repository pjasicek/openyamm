#!/usr/bin/env python3
"""The helmet's front in real geometry: the Meshy helmet has one straight wide opening; MM9's helmets and the Codex views close it to a T (cheek returns on every tier, plus the eye mask on the steel
helmet). The plate is cut from the front view's own helmet pixels (head_masks.face_mask), 7 mm off the face, with a thin back rim. Writes work/plate_{a,c}.npz (Blender-space triangles for
project_heads.py's exposure) and export/mm9_guard_plate_{a,c}.glb (Bip01 Head attachment). Args: none."""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import Delaunay, cKDTree
sys.path.insert(0, 'scripts')
from head_masks import face_mask, view_fit
from head_zbuf import zbuffer

D = np.load('work/head_faces.npz'); P3, PT = D['p'].astype(float), D['part']
helm = P3[PT == 3].reshape(-1, 3); lo, hi = helm.min(0), helm.max(0)
face = P3[PT == 2]
Ct = np.array([0, 0.02, 0.8]); HALF = 0.2; RES = 1000
Fz, Zz, _ = zbuffer(face, 0, 0, RES, HALF, Ct)                         # camera at -y: depth grows toward the camera
ok = Fz >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~ok, return_indices=True)
ZF = ndimage.gaussian_filter(ndimage.grey_dilation(Zz[iy, ix], size=(15, 15)), 5)      # over the nose ridge, not through it
OFF, RIM = 0.007, 0.005
HEAD_DY = None


def face_y(x, z):
    sx = (x / HALF + 1) * RES / 2; sy = (1 - (z - Ct[2]) / HALF) * RES / 2
    v = ndimage.map_coordinates(ZF, [sy, sx], order=1, mode='nearest')
    return -v + Ct[1]                                                  # camera-depth to Blender y (front is -y)


def trace(mask):
    """Closed loops along the pixel edges of a boolean mask, as (row, col) corner points."""
    m = np.pad(mask, 1); nxt = {}
    h, w = m.shape
    for r in range(h - 1):
        for c in range(w - 1):
            a = m[r, c]
            if a != m[r, c + 1]:                                       # vertical edge
                (p, q) = ((r, c + 1), (r + 1, c + 1)) if a else ((r + 1, c + 1), (r, c + 1))
                nxt.setdefault(p, []).append(q)
            if a != m[r + 1, c]:                                       # horizontal edge
                (p, q) = ((r + 1, c + 1), (r + 1, c)) if a else ((r + 1, c), (r + 1, c + 1))
                nxt.setdefault(p, []).append(q)
    loops = []
    while nxt:
        s = next(iter(nxt)); p = s; L = []
        while True:
            L.append(p); o = nxt[p]; q = o.pop()
            if not o: del nxt[p]
            p = q
            if p == s or p not in nxt: break
        loops.append(np.array(L, float) - 1)
    return loops


def dp(pts, tol):
    """Douglas-Peucker on an open polyline."""
    keep = np.zeros(len(pts), bool); keep[[0, -1]] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop()
        if b <= a + 1: continue
        ab = pts[b] - pts[a]; n = max(np.linalg.norm(ab), 1e-9)
        d = np.abs(ab[0] * (pts[a + 1:b, 1] - pts[a, 1]) - ab[1] * (pts[a + 1:b, 0] - pts[a, 0])) / n
        i = int(d.argmax())
        if d[i] > tol:
            k = a + 1 + i; keep[k] = True; st += [(a, k), (k, b)]
    return pts[keep]


def simplify(L, tol=3.5, maxlen=50.0):
    i = len(L) // 2
    a = dp(L[:i + 1], tol); b = dp(np.vstack([L[i:], L[:1]]), tol)
    c = np.vstack([a[:-1], b[:-1]]); out = []
    for k in range(len(c)):
        p, q = c[k], c[(k + 1) % len(c)]; n = int(np.ceil(np.linalg.norm(q - p) / maxlen))
        out += [p + (q - p) * j / n for j in range(n)]
    return np.array(out)


def png(arr):
    b = io.BytesIO(); Image.fromarray(arr).save(b, 'PNG'); return b.getvalue()


def write_glb(path, name, V, Vn, Uv, T0, T1, images, material):
    """One rigid mesh, LOD1-3: front faces only (rim dropped)."""
    blob = bytearray(); views = []; acc = []
    def add(data, target=None):
        nonlocal blob
        blob += b'\0' * (-len(blob) % 4); views.append(dict(buffer=0, byteOffset=len(blob), byteLength=len(data))); blob += data
        if target: views[-1]['target'] = target
        return len(views) - 1
    def accessor(a, ctype, typ, target):
        d = dict(bufferView=add(a.tobytes(), target), componentType=ctype, count=len(a), type=typ)
        if typ == 'VEC3': d['min'] = a.min(0).tolist(); d['max'] = a.max(0).tolist()
        acc.append(d); return len(acc) - 1
    imgs = [dict(bufferView=add(data), mimeType='image/png', name=n) for n, data in images]
    pa = accessor(V.astype(np.float32), 5126, 'VEC3', 34962); na = accessor(Vn.astype(np.float32), 5126, 'VEC3', 34962); ua = accessor(Uv.astype(np.float32), 5126, 'VEC2', 34962)
    meshes = []
    for k, (nm, tri) in enumerate(((name, T0), (name + '_LOD1', T1), (name + '_LOD2', T1), (name + '_LOD3', T1))):
        ia = accessor(tri.astype(np.uint32).ravel(), 5125, 'SCALAR', 34963)
        meshes.append(dict(name=nm, primitives=[dict(attributes=dict(POSITION=pa, NORMAL=na, TEXCOORD_0=ua), indices=ia, material=0)]))
    meshes[0]['extras'] = dict(openyamm_lods=[1, 2, 3])
    doc = dict(asset=dict(version='2.0', generator='make_plate.py'), scene=0, scenes=[dict(nodes=[0])], nodes=[dict(name=name, mesh=0)], meshes=meshes, materials=[material],
               textures=[dict(source=i, sampler=0) for i in range(len(imgs))], images=imgs, samplers=[dict(magFilter=9729, minFilter=9987, wrapS=33071, wrapT=33071)],
               accessors=acc, bufferViews=views, buffers=[dict(byteLength=len(blob))])
    js = json.dumps(doc, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4); blob += b'\0' * (-len(blob) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)


cen = helm[np.abs(helm[:, 0]) < 0.02]
brow_z = cen[(cen[:, 1] < -0.06)][:, 2].min()
print('brow z', round(brow_z, 3), 'helmet z', lo[2].round(3), hi[2].round(3))
HW = json.load(open('scripts/head_bind.json'))                         # Bip01 Head inverse bind (glTF column major) and the head's Blender-to-GLB lift
IB = np.array(HW['inverse_bind']).reshape(4, 4).T; LIFT = HW['lift']
for t, gain, metal, rough in (('a', 0.7, 0.0, 0.62), ('c', 0.86, 0.85, 0.42)):
    im = np.asarray(Image.open(f'references_head/{t}_01_front.png').convert('RGBA'), np.float32) / 255
    fit = view_fit(im, lo, hi, 0)
    fm = face_mask(im, '01_front')
    al = im[..., 3] > 0.5
    col_of = lambda x: fit['c0'] + (x - lo[0]) * fit['pxm']; row_of = lambda z: fit['y0'] + (hi[2] - z) * fit['pxm']
    cx = col_of(0.0)
    R = al & ~ndimage.binary_dilation(fm, iterations=1)
    H, W = R.shape; rr, cc = np.mgrid[:H, :W]
    Yt, Yb = row_of(brow_z + 0.006), row_of(0.700)
    R &= (np.abs(cc - cx) < 0.0705 * fit['pxm']) & (rr > Yt) & (rr < Yb)
    R = ndimage.binary_opening(R, iterations=5)
    lab, n = ndimage.label(R); sz = ndimage.sum(R, lab, range(1, n + 1))
    R = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s > 15000])
    R = ndimage.binary_fill_holes(R) & ~ndimage.binary_erosion(ndimage.binary_fill_holes(R) & ~R, iterations=0) if False else R
    loops = [simplify(L) for L in trace(R) if len(L) > 60]
    B = np.vstack(loops); nb = len(B)
    inner = ndimage.binary_erosion(R, iterations=20)
    gy, gx = np.mgrid[int(Yt):int(Yb):55, H // 4:3 * H // 4:55]; gx = gx + (((gy - int(Yt)) // 55) % 2) * 27
    k = inner[gy.ravel(), gx.ravel()]; G = np.c_[gy.ravel()[k], gx.ravel()[k]].astype(float)
    Q = np.vstack([B, G])
    Tr = Delaunay(Q).simplices
    c = Q[Tr].mean(1); keep = R[c[:, 0].astype(int), c[:, 1].astype(int)]
    Tr = Tr[keep]
    e1 = Q[Tr[:, 1]] - Q[Tr[:, 0]]; e2 = Q[Tr[:, 2]] - Q[Tr[:, 0]]
    ar = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
    Tr = Tr[np.abs(ar) > 1.0]; ar = ar[np.abs(ar) > 1.0]
    x = lo[0] + (Q[:, 1] - fit['c0']) / fit['pxm']; z = hi[2] - (Q[:, 0] - fit['y0']) / fit['pxm']
    y = face_y(x, z) - OFF
    V = np.c_[x, y, z]
    # winding: outward (-y) in Blender space
    tv = V[Tr]; nz = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
    fl = nz[:, 1] > 0; Tr[fl] = Tr[fl][:, [0, 2, 1]]
    # rim: the loops pushed back; same uv
    rim_tris = []; Vb = V[:nb].copy(); Vb[:, 1] += RIM; off = 0
    for L in loops:
        n = len(L)
        for i in range(n):
            a, b = off + i, off + (i + 1) % n
            rim_tris += [(a, a + len(V), b), (b, a + len(V), b + len(V))]
        off += n
    rim = np.array(rim_tris); Va = np.vstack([V, Vb])
    tv = Va[rim]; nr = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0]); cmid = tv.mean(1)
    # rim faces outward from the plate's solid: test a point just along the normal against the mask
    pc = np.c_[fit['y0'] + (hi[2] - cmid[:, 2]) * fit['pxm'], fit['c0'] + (cmid[:, 0] - lo[0]) * fit['pxm']]
    nn = nr / np.maximum(np.linalg.norm(nr, axis=1, keepdims=True), 1e-12)
    probe = pc + np.c_[-nn[:, 2], nn[:, 0]] * 6
    ins = R[np.clip(probe[:, 0].astype(int), 0, H - 1), np.clip(probe[:, 1].astype(int), 0, W - 1)]
    rim[ins] = rim[ins][:, [0, 2, 1]]
    # split the rim from the front (hard edge): separate vertices
    Vr = Va[rim.ravel()]; rimT = np.arange(len(Vr)).reshape(-1, 3) + len(Va)
    Vall = np.vstack([Va, Vr])
    box0 = Q.min(0) - 8; size = float((Q.max(0) - Q.min(0)).max() + 16)
    QA = np.vstack([Q, Q[:nb]]); QR = QA[rim.ravel()]; Qall = np.vstack([QA, QR])
    Uv = np.c_[(Qall[:, 1] - box0[1]) / size, (Qall[:, 0] - box0[0]) / size]
    T0 = np.vstack([Tr, rim_T if False else rimT]); T1 = Tr
    # vertex normals (front smooth, rim flat by its own vertices)
    Vn = np.zeros_like(Vall)
    for tri in T0:
        p = Vall[tri]; n_ = np.cross(p[1] - p[0], p[2] - p[0]); Vn[tri] += n_
    Vn /= np.maximum(np.linalg.norm(Vn, axis=1, keepdims=True), 1e-12)
    np.savez(f'work/plate_{t}.npz', p=Vall[T0], region=R)
    # to GLB, then Bip01 Head space
    Gp = np.c_[Vall[:, 0], Vall[:, 2] + LIFT, -Vall[:, 1], np.ones(len(Vall))]
    Lp = (IB @ Gp.T).T[:, :3]
    Gn = np.c_[Vn[:, 0], Vn[:, 2], -Vn[:, 1]]; Ln = (IB[:3, :3] @ Gn.T).T; Ln /= np.maximum(np.linalg.norm(Ln, axis=1, keepdims=True), 1e-12)
    # texture crop, outside the plate filled from it
    S = 1024
    y0_, x0_ = np.round(box0).astype(int); s_ = int(round(size))
    crop = im[max(y0_, 0):y0_ + s_, max(x0_, 0):x0_ + s_, :3]; mk = ndimage.binary_erosion(R, iterations=2)[max(y0_, 0):y0_ + s_, max(x0_, 0):x0_ + s_]
    _, (iy_, ix_) = ndimage.distance_transform_edt(~mk, return_indices=True)
    crop = crop[iy_, ix_] * gain
    base = np.asarray(Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS))
    lum = base.astype(np.float32).mean(2) / 255; hp = lum - ndimage.gaussian_filter(lum, 8)
    gy_, gx_ = np.gradient(ndimage.gaussian_filter(hp, 0.9)); n_ = np.dstack([-gx_ * 7, gy_ * 7, np.ones_like(gx_)]); n_ /= np.linalg.norm(n_, axis=2, keepdims=True)
    nim = np.asarray(Image.fromarray(((n_ * 0.5 + 0.5) * 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS))
    orm = np.full((64, 64, 3), 255, np.uint8); orm[..., 1] = int(rough * 255); orm[..., 2] = int(metal * 255)
    Image.fromarray(base).save(f'textures/guard_plate_{t}.png')
    mat = dict(name=f'GuardPlate_{t.upper()}', pbrMetallicRoughness=dict(baseColorTexture=dict(index=0), metallicRoughnessTexture=dict(index=1), metallicFactor=1.0, roughnessFactor=1.0),
               normalTexture=dict(index=2), alphaMode='OPAQUE', doubleSided=False)
    write_glb(f'export/mm9_guard_plate_{t}.glb', f'Plate_{t}', Lp, Ln, Uv, T0, T1, ((f'plate_{t}_base', png(base)), (f'plate_{t}_orm', png(orm)), (f'plate_{t}_normal', png(nim))), mat)
    print('PLATE', t, 'verts', len(Vall), 'tris', len(T0), 'front', len(T1), 'loops', [len(l) for l in loops])
