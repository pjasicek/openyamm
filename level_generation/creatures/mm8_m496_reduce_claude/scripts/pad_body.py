#!/usr/bin/env python3
"""UV padding of the Fire Elemental's body atlas (m496_body, 1040x1024): the 1024-square skin bake (x >= 16) has black
gutters between its ~1,100 charts, so any UV corner on a chart border samples black. The installed model already shows
black slivers at the throat, mouth corners and ear folds, and a collapse that moves a corner onto a border enlarges them.
Every skin texel outside the source's UV islands (work/mesh_in.npz, eye faces left out) takes the colour of the nearest
island texel; texels under the source UVs stay identical, and the 16-pixel eye swatch (x < 16) is untouched.
Other images are copied byte for byte. Usage: pad_body.py <in.glb> <out.glb>"""
import io, sys
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
uv = uv[uv[..., 0].max(1) >= 16 / 1040]          # eye faces sample the swatch
newdata = {}
for i, im_def in enumerate(doc['images']):
    if im_def.get('name') != 'm496_body':
        continue
    bv = doc['bufferViews'][im_def['bufferView']]
    im = Image.open(io.BytesIO(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))
    a = np.asarray(im).copy(); h, w = a.shape[:2]
    cov = Image.new('L', (w, h), 0); dr = ImageDraw.Draw(cov)
    for t in uv:
        dr.polygon([(u * w, (1 - v) * h) for u, v in t], fill=255)
    c = np.asarray(cov) > 0
    c[:, :16] = True                                # never pad into or from the eye swatch
    idx = ndimage.distance_transform_edt(~c, return_distances=False, return_indices=True)
    p = a[idx[0], idx[1]]; p[:, :16] = a[:, :16]
    assert (p[c] == a[c]).all()
    print('PADDED', im_def['name'], a.shape, 'covered', round(float(c[:, 16:].mean()), 3),
          'dark texels before', int((a[:, 16:, :3].sum(2) < 40).sum()), 'after', int((p[:, 16:, :3].sum(2) < 40).sum()))
    buf = io.BytesIO(); Image.fromarray(p.astype(np.uint8), im.mode).save(buf, 'PNG', optimize=True)
    newdata[im_def['bufferView']] = buf.getvalue()
nb = bytearray()
for k, bv in enumerate(doc['bufferViews']):
    data = newdata.get(k, bytes(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))
    nb += b'\0' * (-len(nb) % 4); bv['byteOffset'] = len(nb); bv['byteLength'] = len(data); nb += data
write_glb(out, doc, bytes(nb)); print('WROTE', out, len(nb))
