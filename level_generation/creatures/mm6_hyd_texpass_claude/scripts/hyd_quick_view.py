"""Tiny orthographic shaded render of GLB meshes (no Blender): front (+Z toward the camera) and left (+X toward the
camera... the model's left side) views, for checking upload frames. Usage: hyd_quick_view.py <out png> <glb> [<glb>...]"""
import sys

import numpy as np
from PIL import Image, ImageDraw

from glb import Glb

RES = 256


def load(path):
    g = Glb(path)
    ps, fs, off = [], [], 0
    for m in g.doc['meshes']:
        for pr in m['primitives']:
            p = g.accessor(pr['attributes']['POSITION']).astype(np.float64)
            f = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
            ps.append(p)
            fs.append(f + off)
            off += len(p)
    return np.concatenate(ps), np.concatenate(fs)


def render(p, f, view):
    # camera axes: (right, up, toward camera)
    axes = {'front': ([1, 0, 0], [0, 1, 0], [0, 0, 1]), 'left': ([0, 0, 1], [0, 1, 0], [-1, 0, 0]),
            'top': ([1, 0, 0], [0, 0, -1], [0, 1, 0])}[view]
    A = np.array(axes, float)
    q = p @ A.T
    lo, hi = q[:, :2].min(0), q[:, :2].max(0)
    s = (RES - 8) / (hi - lo).max()
    xy = (q[:, :2] - (lo + hi) / 2) * s + RES / 2
    xy[:, 1] = RES - xy[:, 1]
    n = np.cross(q[f[:, 1]] - q[f[:, 0]], q[f[:, 2]] - q[f[:, 0]])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    shade = np.clip(np.abs(n[:, 2]) * 0.8 + 0.2, 0, 1)
    order = np.argsort(q[f].mean(1)[:, 2])
    img = Image.new('L', (RES, RES), 40)
    dr = ImageDraw.Draw(img)
    for t in order:
        dr.polygon([tuple(xy[v]) for v in f[t]], fill=int(255 * shade[t]))
    return img


out = Image.new('L', (RES * 3, RES * (len(sys.argv) - 2)), 0)
for i, path in enumerate(sys.argv[2:]):
    p, f = load(path)
    for j, v in enumerate(('front', 'left', 'top')):
        out.paste(render(p, f, v), (j * RES, i * RES))
out.save(sys.argv[1])
