"""Shaded normals of LOD0 (interpolated normal + normal map in the fs_model.sc frame) of two GLBs of the same mesh at
the same surface points: angle between them (p50/p90/p99 degrees). Usage: tp_normal_check.py <before glb> <after glb>"""
import sys
import types

import numpy as np

import tp_common as C
import texlib
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(C.CREATURES / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

cfg = C.config()
rng = np.random.default_rng(1)
res = []
for path in sys.argv[1:3]:
    g = C.Glb(path)
    doc = g.doc
    pr = doc['meshes'][C.lod0_mesh_index(doc, cfg['node'])]['primitives'][cfg['atlas_prims'][0]]
    p = g.accessor(pr['attributes']['POSITION']).astype(float)
    n = TT.normalize(g.accessor(pr['attributes']['NORMAL']).astype(float))
    u = g.accessor(pr['attributes']['TEXCOORD_0']).astype(float)
    f = g.accessor(pr['indices']).reshape(-1, 3)
    mat = doc['materials'][pr['material']]
    img = np.asarray(g.image(doc['textures'][mat['normalTexture']['index']]['source']).convert('RGB'), np.float32)
    scale = mat['normalTexture'].get('scale', 1.0)
    res.append((p, n, u, f, img, scale))
p, n, u, f, _, _ = res[0]
a = C.tri_area3(p[f])
N = 50000
t = rng.choice(len(f), N, p=a / a.sum())
b = rng.dirichlet((1, 1, 1), N)
key = (p[f[t]] * b[:, :, None]).sum(1)
outs = []
for p, n, u, f, img, scale in res:
    # same triangles in the same order (the pass splits vertices only)
    sh = TT.normalize((b[:, :, None] * n[f[t]]).sum(1))
    e1, e2 = p[f[t, 1]] - p[f[t, 0]], p[f[t, 2]] - p[f[t, 0]]
    uu = u[f[t]]
    tt, bb = TT.frame(e1, e2, uu[:, 1] - uu[:, 0], uu[:, 2] - uu[:, 0], sh)
    xy = texlib.bilinear(img, (b[:, :, None] * uu).sum(1))[:, :2] / 127.5 - 1
    z = np.sqrt(np.maximum(1 - (xy ** 2).sum(-1), 0))
    outs.append(TT.normalize(tt * xy[:, :1] * scale - bb * xy[:, 1:] * scale + sh * z[:, None]))
ang = np.degrees(np.arccos(np.clip((outs[0] * outs[1]).sum(-1), -1, 1)))
print('shaded normal angle before vs after: p50 %.1f p90 %.1f p99 %.1f deg' % tuple(np.percentile(ang, [50, 90, 99])))
