#!/usr/bin/env python3
"""One empty spot per texture set for the dark lining (body, head): the point of each UV layout farthest from any chart. Writes work/dark_texel.json. Run in the project folder."""
import json
import numpy as np
from PIL import Image, ImageDraw
from pygltflib import GLTF2
from scipy import ndimage
out = {}
for key, f, box in (('body', 'texturing/guard_body_upload.glb', (0, 0, 1, 1)), ('head', 'texturing/guard_heads_upload.glb', (0, 0.25, 0.5, 0.75))):
    g = GLTF2().load(f); b = g.binary_blob(); pr = g.meshes[0].primitives[0]
    def acc(i, n, dt):
        a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0)
        return np.frombuffer(b, dt, a.count * n, off).reshape(a.count, n)
    uv = acc(pr.attributes.TEXCOORD_0, 2, np.float32).copy(); ia = g.accessors[pr.indices]
    idx = acc(pr.indices, 1, {5123: np.uint16, 5125: np.uint32}[ia.componentType]).reshape(-1, 3)
    if key == 'head':
        # first copy, back to the 0..1 of HeadUV
        keep = (uv[idx, 0] < 0.5).all(1); idx = idx[keep]; uv = np.c_[uv[:, 0] * 2, (uv[:, 1] - 0.25) * 2]
    S = 1024
    im = Image.new('L', (S, S)); d = ImageDraw.Draw(im)
    for t in idx: d.polygon([(float(uv[i, 0] * S), float(uv[i, 1] * S)) for i in t], fill=255)
    a = np.asarray(im) > 0
    a[:12] = 1; a[-12:] = 1; a[:, :12] = 1; a[:, -12:] = 1
    dt = ndimage.distance_transform_edt(~a)
    y, x = np.unravel_index(np.argmax(dt), dt.shape)
    out[key] = dict(u=float((x + 0.5) / S), v=float((y + 0.5) / S), radius_px_1k=float(dt.max()))
    print(key, out[key])
json.dump(out, open('work/dark_texel.json', 'w'), indent=1)
