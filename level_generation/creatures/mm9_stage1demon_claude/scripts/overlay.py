"""Overlay sheet (PIL painter's raster): the globally fitted Meshy body, front (x-z) and side (y-z, faces left), with MM9's joints
(red) and the estimates (green, fit_config.json "est") on a 10 cm grid. Args: meshy.glb mm9.glb config.json out.png [zoom box x0,x1,z0,z1]"""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __import__('os').path.dirname(__file__))
import demon_common as C
mg, sg, cfgp, out = sys.argv[1:5]
box = [float(x) for x in sys.argv[5].split(',')] if len(sys.argv) > 5 else None
cfg = json.load(open(cfgp))
A, FA, _ = C.load_mesh(sg)
if mg.endswith('.npz'):
    _z = np.load(mg); P, F = _z['V'], _z['F']; s, t = 1.0, 0.0
    if os.environ.get('PARTS'):
        keep = [int(x) for x in os.environ['PARTS'].split(',')]; F = F[np.isin(_z['part'][F[:, 0]], keep)]
else:
    P, F, _ = C.load_mesh(mg); s, t = C.global_fit(P, A); P = P * s + t
import os
if os.environ.get('SIDE'):
    th = float(os.environ.get('SIDE'))
    F = F[P[F].mean(1)[:, 0] < th]; FA = FA[A[FA].mean(1)[:, 0] < th]
J = C.joints(sg); E = {k: np.array(v) for k, v in cfg.get('est', {}).items()}
PX = int(os.environ.get('PX', 900))


def view(axes, depth, flip, mesh_only=None):
    x0, x1, z0, z1 = box or [-1.7, 1.7, -1.45, 1.45]
    if axes[0] == 1 and not box: x0, x1 = -1.2, 1.9
    if axes[0] == 1 and box and len(sys.argv) > 6: x0, x1 = [float(v) for v in sys.argv[6].split(',')]
    sc = PX / max(x1 - x0, z1 - z0)
    W, H = int((x1 - x0) * sc), int((z1 - z0) * sc)
    im = Image.new('RGB', (W, H), (40, 46, 52)); d = ImageDraw.Draw(im)
    def pr(p): return ((p[..., axes[0]] * flip - x0) * sc, (z1 - p[..., 2]) * sc)
    lbl = []
    for g in np.arange(-3, 3, 0.1):
        c = (70, 80, 90) if abs(g * 10 - round(g * 10)) < 1e-6 and round(g * 10) % 5 else (110, 120, 130)
        X, _ = pr(np.array([g * flip, g, 0])); _, Z = pr(np.array([0, 0, g]))
        d.line([(X, 0), (X, H)], fill=c); d.line([(0, Z), (W, Z)], fill=c)
        lbl.append((X, Z, round(g, 1)))
    tri = P[F]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    dep = tri[:, :, depth].mean(1) * (1 if depth == 1 else -1) * (-1 if flip < 0 else 1)
    order = np.argsort(-dep)
    lightv = np.zeros(3); lightv[depth] = -1 if depth == 1 else 1; lightv[2] = 0.5; lightv /= np.linalg.norm(lightv)
    for i in order:
        sh = int(60 + 150 * abs(n[i] @ lightv)); X, Z = pr(tri[i])
        d.polygon(list(zip(X, Z)), fill=(sh, sh, sh))
    from PIL import ImageFilter
    mk = Image.new('L', (W, H), 0); dm = ImageDraw.Draw(mk)
    for tr in A[FA]:
        X, Z = pr(tr); dm.polygon(list(zip(X, Z)), fill=255)
    edge = np.array(mk.filter(ImageFilter.MaxFilter(3))) != np.array(mk.filter(ImageFilter.MinFilter(3)))
    arr = np.array(im); arr[edge] = (255, 90, 60); im = Image.fromarray(arr); d = ImageDraw.Draw(im)
    for k, v in J.items():
        if 'Finger' in k and not k.endswith(('0', '1', '2', '3')): continue
        x, z = pr(v); d.ellipse([x - 3, z - 3, x + 3, z + 3], fill=(255, 40, 40))
    for k, v in E.items():
        x, z = pr(v); d.ellipse([x - 4, z - 4, x + 4, z + 4], outline=(40, 255, 40), width=2); d.text((x + 5, z - 5), k, fill=(150, 255, 150))
    for X, Z, g in lbl:
        if 0 < X < W: d.text((X + 2, 2), str(g), fill=(255, 255, 120))
        if 0 < Z < H: d.text((2, Z + 2), str(g), fill=(120, 255, 255))
    return im


a = view((0, 2), 1, 1); b = view((1, 2), 0, -1)
s_ = Image.new('RGB', (a.width + b.width, max(a.height, b.height))); s_.paste(a, (0, 0)); s_.paste(b, (a.width, 0)); s_.save(out)
print('SCALE', s, 'T', t)
