"""UV coverage and texel density of a creature GLB's LOD0 body (first skinned mesh, first primitive).
Usage: uv_density.py <glb> [split u] (merged atlas: body page = u < split, e.g. 2048/3104 = 0.6598; default 0.5)."""
import json, struct, sys, io
import numpy as np
from PIL import Image
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def load(p):
    raw = open(p, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]
    d = json.loads(raw[20:20 + n]); b = raw[28 + n:]
    return d, b
def acc(d, b, i):
    a = d['accessors'][i]; v = d['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); c = NC[a['type']]; t = np.dtype(CT[a['componentType']])
    st = v.get('byteStride', c * t.itemsize)
    arr = np.ndarray((a['count'], c), t, b, off, (st, t.itemsize))
    return arr.copy()
def img(d, b, i):
    im = d['images'][d['textures'][i]['source']]; v = d['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return Image.open(io.BytesIO(b[o:o + v['byteLength']]))
d, b = load(sys.argv[1])
node = next(n for n in d['nodes'] if 'mesh' in n and 'skin' in n)
prim = d['meshes'][node['mesh']]['primitives'][0]
P = acc(d, b, prim['attributes']['POSITION']); UV = acc(d, b, prim['attributes']['TEXCOORD_0'])
I = acc(d, b, prim['indices']).reshape(-1, 3)
mat = d['materials'][prim['material']]
base = img(d, b, mat['pbrMetallicRoughness']['baseColorTexture']['index']); W, H = base.size
mask = np.asarray(img(d, b, mat['extras']['openyamm_region_mask']['index']).convert('RGBA'), np.float32) / 255
split = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
t3 = P[I]; tu = UV[I]
a3 = 0.5 * np.linalg.norm(np.cross(t3[:, 1] - t3[:, 0], t3[:, 2] - t3[:, 0]), axis=1)
e1 = tu[:, 1] - tu[:, 0]; e2 = tu[:, 2] - tu[:, 0]
auv = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) * W * H        # texels^2
cen = tu.mean(1); head = cen[:, 0] >= split
mx = np.clip((cen[:, 0] * mask.shape[1]).astype(int), 0, mask.shape[1] - 1)
my = np.clip((cen[:, 1] * mask.shape[0]).astype(int), 0, mask.shape[0] - 1)
mv = mask[my, mx]; reg = np.where(mv.max(1) > 0.5, mv.argmax(1), 4)
dens = np.sqrt(auv / np.maximum(a3, 1e-12))
# coverage: rasterize at 1/4 res
def cover(sel, u0, u1):
    R = 512; im = Image.new('L', (R, R), 0)
    from PIL import ImageDraw; dr = ImageDraw.Draw(im)
    for t in tu[sel]:
        dr.polygon([(((x - u0) / (u1 - u0)) * R, y * R) for x, y in t], fill=255)
    return np.asarray(im).mean() / 255
print(sys.argv[1].split('/')[-1], 'atlas', W, H, 'tris', len(I), 'height', round(float(P[:, 1].max() - P[:, 1].min()), 3))
for name, sel, u0, u1 in [('body', ~head, 0, split), ('head', head, split, 1)]:
    w = a3[sel]; ds = dens[sel]; o = np.argsort(ds); cw = np.cumsum(w[o]) / w.sum()
    med = ds[o][np.searchsorted(cw, 0.5)]; p10 = ds[o][np.searchsorted(cw, 0.1)]
    print(f'  {name}: 3D {w.sum():.3f} m2, coverage {cover(sel, u0, u1)*100:.1f} % of its page, texels/m median {med:.0f} (p10 {p10:.0f})')
for r, nm in enumerate(['R', 'G', 'B', 'A', 'none']):
    sel = (~head) & (reg == r)
    if sel.sum() == 0: continue
    w = a3[sel]; ds = dens[sel]; o = np.argsort(ds); cw = np.cumsum(w[o]) / w.sum()
    print(f'    body region {nm}: {w.sum():.3f} m2, texels/m median {ds[o][np.searchsorted(cw, .5)]:.0f}')
