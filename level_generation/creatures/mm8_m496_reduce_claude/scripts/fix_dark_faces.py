#!/usr/bin/env python3
"""Repaint the Fire Elemental body bake's isolated black faces: source faces that are near-black over at least half of
their interior while their edge neighbours average bright skin (throat notch below the chin, ear folds, between the
fingers, toes; 22 faces, bake rays that missed). The installed model shows them as black triangles that read as
holes. The dark texels inside each face's UV triangle (dilated by 2 px) take the mean colour of the bright samples of
its neighbours; nothing else in the atlas changes. Deep sockets (mouth, eyes) and creases whose neighbours are dark
too are left as baked. Runs before pad_body.py; needs work/basecolor.png and work/mesh_in.npz.
Usage: fix_dark_faces.py <in.glb> <out.glb>"""
import io, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
src, out = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src)
d = np.load(HERE / 'work/mesh_in.npz'); uv = d['wuv'].reshape(-1, 3, 2); f = d['faces']
im_i = next(i for i, im in enumerate(doc['images']) if im.get('name') == 'm496_body')
bv = doc['bufferViews'][doc['images'][im_i]['bufferView']]
img = Image.open(io.BytesIO(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))
a = np.asarray(img).copy(); h, w = a.shape[:2]
g = np.linspace(.05, .9, 6); bc = np.array([[x, y, 1 - x - y] for x in g for y in g if x + y < .95])
p = np.einsum('kj,fjc->fkc', bc, uv)
px = np.clip((p[..., 0] * w).astype(int), 0, w - 1); py = np.clip(((1 - p[..., 1]) * h).astype(int), 0, h - 1)
col = a[py, px, :3].astype(float); lum = col.sum(-1); dark = (lum < 40).mean(1)
eye = uv[..., 0].max(1) < 16 / 1040
edges = defaultdict(list)
for i, t in enumerate(f):
    for k in range(3):
        edges[tuple(sorted((t[k], t[(k + 1) % 3])))].append(i)
nb = defaultdict(set)
for fs in edges.values():
    for i in fs:
        nb[i].update(j for j in fs if j != i)
iso = [i for i in np.flatnonzero((dark >= .5) & ~eye) if np.mean([lum[j].mean() for j in nb[i]]) > 90]
for i in iso:
    s = np.concatenate([col[j][lum[j] >= 40] for j in nb[i]]); fill = s.mean(0)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).polygon([(u * w, (1 - v) * h) for u, v in uv[i]], fill=255)
    m = np.asarray(m.filter(ImageFilter.MaxFilter(5))) > 0
    m &= a[..., :3].astype(int).sum(-1) < 40
    a[m, :3] = np.round(fill).astype(np.uint8)
    print('FACE', i, 'texels', int(m.sum()), 'colour', np.round(fill).astype(int).tolist())
buf = io.BytesIO(); Image.fromarray(a, img.mode).save(buf, 'PNG', optimize=True)
newdata = {doc['images'][im_i]['bufferView']: buf.getvalue()}
nb_ = bytearray()
for k, b in enumerate(doc['bufferViews']):
    data = newdata.get(k, bytes(binary[b.get('byteOffset', 0):b.get('byteOffset', 0) + b['byteLength']]))
    nb_ += b'\0' * (-len(nb_) % 4); b['byteOffset'] = len(nb_); b['byteLength'] = len(data); nb_ += data
write_glb(out, doc, bytes(nb_)); print('REPAINTED', len(iso), 'faces ->', out)
