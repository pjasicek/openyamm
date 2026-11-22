#!/usr/bin/env python3
"""Pose attachments into model space at a clip time (review only): posed_extras.py <body.glb> <clip> <t> <out.glb>
<att.glb>:<node> [...]. The attachments' first mesh is transformed by the node's world matrix."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pglb import load, Glb  # noqa: E402
from gltf_write import Writer  # noqa: E402
import io
body, clip, t, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
g, m, names = load(body)
W = m.world(m.sample(clip, t)) if clip != '-' else m.world({})
w = Writer()
for spec in sys.argv[5:]:
    path, node = spec.split(':')
    a = Glb(path)
    j = a.json
    M = W[names[node]]
    img = j['images'][0]; view = j['bufferViews'][img['bufferView']]
    data = bytes(a.bin[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])
    from PIL import Image
    tex = w.image(Image.open(io.BytesIO(data)), Path(path).stem)
    mat = w.material(Path(path).stem, tex, double=True)
    prim = j['meshes'][0]['primitives'][0]
    v = a.accessor(prim['attributes']['POSITION']).astype(float)
    n = a.accessor(prim['attributes']['NORMAL']).astype(float)
    uv = a.accessor(prim['attributes']['TEXCOORD_0']).astype(float)
    f = a.accessor(prim['indices']).astype(np.int64).reshape(-1, 3)
    vt = (np.c_[v, np.ones(len(v))] @ M.T)[:, :3]
    nt = n @ M[:3, :3].T
    w.node(Path(path).stem, w.mesh(Path(path).stem, [(vt, nt, uv, f, mat)]))
w.write(out)
