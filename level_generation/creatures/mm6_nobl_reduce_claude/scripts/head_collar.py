#!/usr/bin/env python3
"""The collar's upper band lies in the head texture set (installed head maps, unchanged layout): its Meshy paint is
streaked by grazing projection. Collar texels (head-set triangles below z 1.52 m, saturated orange/gold, outside the
neck: radius > 7.2 cm from the neck axis or very saturated) are de-streaked like the detail set: blurred within colour
clusters (dark, gold, orange) plus an even grain from 3D position. Writes textures/nobl_head_basecolor_1k.png and pastes
it into the head section (x 1056) of the base-colour atlas of <glb> in place (optional).
Usage: head_collar.py [<glb>]"""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]; N = 1024; CX = -.007
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(ROOT / 'tools')); from merge_head_material import read_glb, image_of  # noqa: E402
doc, binary = read_glb(ROOT / 'assets_source/worlds/mm6/models/mm6_nobl.glb')
base = np.asarray(image_of(doc, binary, doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'])[0].convert('RGB'), float)[:, 1056:] / 255
hsv = lambda x: np.asarray(Image.fromarray(np.uint8(np.clip(x, 0, 1) * 255)).convert('HSV'), float) / 255
src = np.load(P / 'work/mesh_in.npz'); w = src['wuv'].reshape(-1, 3, 2); head = w[:, :, 0].mean(1) > .5
uv = w[head].copy(); uv[..., 0] = (uv[..., 0] * 2080 - 1056) / 1024; P3 = src['verts'][src['faces'][head]]
h = hsv(base); cu = uv.mean(1)
px = h[np.clip(((1 - cu[:, 1]) * N).astype(int), 0, N - 1), np.clip((cu[:, 0] * N).astype(int), 0, N - 1)]
c = P3.mean(1); rad = np.hypot(c[:, 0] - CX, c[:, 1])
collar_tri = (c[:, 2] < 1.52) & (px[:, 1] > .3) & (px[:, 0] * 360 < 45) & ((rad > .072) | (px[:, 1] > .6))
# raster the collar triangles (texel -> 3D position)
cov = np.zeros((N, N), bool); pos = np.zeros((N, N, 3))
for t, p in zip(uv[collar_tri] * N, P3[collar_tri]):
    lo = np.maximum(0, np.floor(t.min(0)).astype(int)); hi = np.minimum(N - 1, np.ceil(t.max(0)).astype(int))
    m = np.column_stack([t[1] - t[0], t[2] - t[0]])
    if hi[0] < lo[0] or hi[1] < lo[1] or abs(np.linalg.det(m)) < 1e-12:
        continue
    xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
    ww = (np.stack([xx, yy], -1) - t[0]) @ np.linalg.inv(m).T; w0 = 1 - ww.sum(-1)
    inside = (ww[..., 0] >= 0) & (ww[..., 1] >= 0) & (w0 >= 0)
    rows = N - 1 - (yy[inside] - .5).astype(int); cols = (xx[inside] - .5).astype(int)
    cov[rows, cols] = True; pos[rows, cols] = w0[inside, None] * p[0] + ww[inside, 0, None] * p[1] + ww[inside, 1, None] * p[2]


def lattice(q):
    i = np.floor(q).astype(np.int64); f = q - i; f = f * f * (3 - 2 * f); out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                k = (i[:, 0] + dx) * 73856093 ^ (i[:, 1] + dy) * 19349663 ^ (i[:, 2] + dz) * 83492791
                r = ((k * 2654435761) % 4294967296) / 4294967296.0 * 2 - 1
                out = out + r * np.where(dx, f[:, 0], 1 - f[:, 0]) * np.where(dy, f[:, 1], 1 - f[:, 1]) * np.where(dz, f[:, 2], 1 - f[:, 2])
    return out


a = base.copy(); dark = h[..., 2] < .22; gold = (h[..., 0] * 360 > 32) & (h[..., 0] * 360 < 65) & (h[..., 1] > .3) & (h[..., 2] > .35)
blur = lambda x: ndimage.gaussian_filter(x, 4)
for cluster in (dark, gold, ~dark & ~gold):
    m = cov & cluster
    if m.sum() < 30:
        continue
    for ch in range(3):
        low = blur(a[..., ch] * m) / np.maximum(blur(m.astype(float)), 1e-6); a[..., ch][m] = low[m]
    q = pos[m]; a[m] = np.clip(a[m] * (1 + .08 * (.65 * lattice(q / .003) + .35 * lattice(q / .0012 + 17.3)))[:, None], 0, 1)
out = P / 'textures/nobl_head_basecolor_1k.png'; Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(out, optimize=True)
print('COLLAR triangles', int(collar_tri.sum()), 'texels', int(cov.sum()))
if len(sys.argv) < 2:
    sys.exit(0)
path = Path(sys.argv[1]); gdoc, gbin = R.read_glb(path); gbin = bytearray(gbin)
img = gdoc['images'][gdoc['textures'][gdoc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
view = gdoc['bufferViews'][img['bufferView']]
atlas = Image.open(io.BytesIO(bytes(gbin[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]))); atlas.load()
part = Image.open(out).convert(atlas.mode); atlas.paste(part, (1056, 0)); atlas.paste(part.crop((0, 0, 1, N)).resize((16, N)), (1040, 0))
buf = io.BytesIO(); atlas.save(buf, 'PNG', optimize=True); data = buf.getvalue()
gbin.extend(b'\0' * (-len(gbin) % 4)); gdoc['bufferViews'].append({'buffer': 0, 'byteOffset': len(gbin), 'byteLength': len(data)})
gbin.extend(data); img['bufferView'] = len(gdoc['bufferViews']) - 1
gdoc, gbin = R._compact(gdoc, gbin); R.write_glb(path, gdoc, gbin); print('WROTE', path, atlas.size)
