"""Last step on every map (UV study finding, uv_research_20261111/REPORT.md "Gutter"): every texel outside the UV
islands of the primitives that use an image (default and variant materials, every LOD; shadow meshes excluded) takes
the value of the nearest island texel, for colour, region mask, metal/roughness and normal maps alike. Coverage and
fill are claude_shared/gutter_fill.py's (`coverage`: any triangle touching a texel at 4x supersampling; `pad`); this
script only gathers, per image of the GLB, the triangles of every primitive that samples it.
Usage: hyd_gutter_fill.py <in glb> <out glb>"""
import io
import json
import sys

import numpy as np
from PIL import Image

import tp_common as C
from glb import Glb
from gutter_fill import coverage, pad

src, dst = sys.argv[1:3]
g = Glb(src)
doc = g.doc
lod0 = doc['meshes'][C.lod0_mesh_index(doc, C.config()['node'])]
shadows = set(lod0['extras'].get('openyamm_shadow_lods', []))
users = {}                                      # image -> list of (mesh, prim)
for mi, mesh in enumerate(doc['meshes']):
    if mi in shadows:
        continue
    for pi, pr in enumerate(mesh['primitives']):
        for m in C.primitive_materials(pr):
            for kind, tex in C.material_maps(doc['materials'][m]).items():
                users.setdefault(doc['textures'][tex]['source'], set()).add((mi, pi))
report = {}
for img_index, prims in sorted(users.items()):
    im = g.image(img_index)
    mode = im.mode
    a = np.asarray(im)
    h, w = a.shape[:2]
    tri_uv = []
    for mi, pi in prims:
        pr = doc['meshes'][mi]['primitives'][pi]
        f = g.accessor(pr['indices']).reshape(-1, 3)
        tri_uv.append(g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)[f])
    covered = coverage(np.concatenate(tri_uv), h, w)
    if covered.all() or not covered.any():
        continue
    filled = pad(a, covered)
    changed = float((np.abs(filled.astype(int) - a.astype(int)).max(-1) > 2).mean()) if a.ndim == 3 else 0.0
    buf = io.BytesIO()
    Image.fromarray(filled, mode).save(buf, 'PNG')
    g.set_image(img_index, buf.getvalue())
    name = doc['images'][img_index].get('name', str(img_index))
    report[name] = {'size': [w, h], 'covered': round(float(covered.mean()), 3), 'gutter_changed': round(changed, 3)}
    print('FILLED', name, report[name])
g.save(dst)
json.dump(report, open(dst.replace('.glb', '_gutter.json'), 'w'), indent=1)
print('WROTE', dst)
