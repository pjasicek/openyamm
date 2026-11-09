#!/usr/bin/env python3
"""UV padding for the eye's shared textures: every texel outside the UV islands of the pre-cut source
(work/mesh_in.npz) takes the colour of the nearest island texel, in all four images (base colour, region mask,
normal, metal/roughness). Texels under the source UVs stay identical. The Meshy layout had dark gutters, so any UV
that the old Blender cut (or a later collapse) slid off an island edge rendered as a black shard.
Optional ivory cell (work/ivory_cell.json from ivory_cell.py) is painted after the padding.
Usage: pad_textures.py <in.glb> <out.glb>"""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
src, out = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src)
uv = np.load(HERE / 'work/mesh_in.npz')['wuv'].reshape(-1, 3, 2)
cell = json.loads((HERE / 'work/ivory_cell.json').read_text()) if (HERE / 'work/ivory_cell.json').exists() else None


def coverage(w, h):
    im = Image.new('L', (w, h), 0); dr = ImageDraw.Draw(im)
    for t in uv:
        dr.polygon([(u * w, (1 - v) * h) for u, v in t], fill=255)
    return np.asarray(im) > 0


def pad(name, a):
    c = coverage(a.shape[1], a.shape[0])
    idx = ndimage.distance_transform_edt(~c, return_distances=False, return_indices=True)
    p = a[idx[0], idx[1]]
    if cell:
        s = a.shape[0] / cell['size']; x0, y0, x1, y1 = (int(round(k * s)) for k in cell['paint_px'])
        if name in cell['paint']:
            spec = cell['paint'][name]
            if spec.get('gradient'):
                g0, g1 = np.array(spec['gradient'][0], float), np.array(spec['gradient'][1], float)
                t = np.linspace(0, 1, y1 - y0)[:, None, None]   # root (top row) -> tip (bottom row)
                block = g0 + (g1 - g0) * t
                rng = np.random.default_rng(3); noise = ndimage.gaussian_filter(rng.normal(0, 1, (y1 - y0, x1 - x0)), 1.2)
                block = block + noise[..., None] * spec.get('noise', 0)
                p[y0:y1, x0:x1, :3] = np.clip(np.broadcast_to(block, (y1 - y0, x1 - x0, 3)), 0, 255)
            else:
                p[y0:y1, x0:x1, :len(spec['value'])] = spec['value']
    return p


images = {i: im.get('name') for i, im in enumerate(doc['images'])}
newdata = {}
for i, name in images.items():
    bv = doc['bufferViews'][doc['images'][i]['bufferView']]
    im = Image.open(io.BytesIO(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))
    mode = im.mode; a = np.asarray(im).copy()
    p = pad(name, a)
    buf = io.BytesIO(); Image.fromarray(p.astype(np.uint8), mode).save(buf, 'PNG', optimize=True)
    newdata[doc['images'][i]['bufferView']] = buf.getvalue()
    print('PADDED', name, a.shape, mode, len(buf.getvalue()))
# rebuild the binary chunk view by view (images replaced, everything else byte-for-byte)
nb = bytearray()
for k, bv in enumerate(doc['bufferViews']):
    data = newdata.get(k, bytes(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))
    nb += b'\0' * (-len(nb) % 4); bv['byteOffset'] = len(nb); bv['byteLength'] = len(data); nb += data
write_glb(out, doc, bytes(nb)); print('WROTE', out, len(nb))
