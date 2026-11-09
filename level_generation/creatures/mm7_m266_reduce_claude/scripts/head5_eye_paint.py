#!/usr/bin/env python3
"""Paint head 5's eye (head5_eyes.py lenses) into the free sixth tile of the head atlas of a runtime GLB, in place:
base colour: orange iris (yellow centre to red-orange edge), dark rim, vertical slit pupil, small glint, after the
head 5 HD master's eyes; region mask: R = 0 over the cell (so the tiers do not recolour the eyes); metal/rough:
roughness 70 (wet), metal 0; normal map: flat. An 8 px (4 px at half resolution) border around the cell takes the rim
colour against mip bleeding. No face but the eyes uses that tile. One more local repaint in head 5's own tile: the
ivory paint Meshy left on the skin where the three removed horns stood (texels with G/R > 0.6 and R > 120 inside the
UV footprint of the head 5 skin faces within 4.5 cm of each horn root; teeth and other separate pieces excluded) takes the colour of the nearest skin texel of
that footprint. Every other texel stays identical.
The patched base colour and region mask are also written to textures/ for viewer_tiers.py.
Usage: head5_eye_paint.py <glb>"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
glb = Path(sys.argv[1]); doc, binary = read_glb(glb)
cell = json.load(open(P / 'work' / 'head5_eye_cell.json'))['px']


def eye_rgb(X, Y):
    r = np.sqrt(X ** 2 + Y ** 2)
    t = np.clip(r / .85, 0, 1)[..., None]
    iris = np.array([255, 205, 70]) * (1 - t) ** 2 + np.array([238, 112, 22]) * 2 * t * (1 - t) + np.array([165, 38, 12]) * t ** 2
    rim = np.clip((r - .8) / .15, 0, 1)[..., None]
    col = iris * (1 - rim) + np.array([55, 14, 10]) * rim
    half = .14 * np.sqrt(np.clip(1 - (Y / .9) ** 2, 0, 1))
    pupil = np.clip((half - np.abs(X)) / .04 + .5, 0, 1)[..., None] * (np.abs(Y) < .9)[..., None]
    col = col * (1 - pupil) + np.array([12, 6, 6]) * pupil
    glint = np.clip(1 - np.hypot(X + .33, Y - .38) / .11, 0, 1)[..., None] ** 1.5
    return np.clip(col * (1 - glint) + np.array([255, 246, 225]) * glint, 0, 255)


def paint(name, fn):
    im = next(i for i in doc['images'] if i.get('name') == name)
    v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    pil = Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']]))); mode = pil.mode
    arr = np.asarray(pil).copy(); fn(arr)
    out = Image.fromarray(arr, mode); buf = io.BytesIO(); out.save(buf, 'PNG')
    return im['bufferView'], buf.getvalue(), out


ROOTS = np.array([(0.712, -1.186, 1.401), (0.874, -1.200, 1.412), (0.850, -1.322, 1.354)])


def spill(a):
    from scipy import ndimage
    c = np.load(P / 'work' / 'mesh_r78.npz'); v, f = c['verts'], c['faces']; uv = c['wuv'].reshape(-1, 3, 2)
    w = np.load(P / 'work' / 'weights_r78.npz'); h5 = w['weights'][:, [str(x) for x in w['names']].index('Head5')]
    near = (np.linalg.norm(v[:, None] - ROOTS[None], axis=2).min(1) < .045)
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v),) * 2), directed=False)
    skin = np.bincount(lab)[lab[f[:, 0]]] > 400          # the skin surface only, never the ivory teeth beside it
    sel = np.where((uv[:, 0, 0] >= 2) & (h5[f] > .99).all(1) & near[f].any(1) & skin)[0]
    H, W = a.shape[:2]; foot = Image.new('L', (W, H), 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(foot)
    for i in sel:
        d.polygon([((u - 2) * W, (1 - vv) * H) for u, vv in uv[i]], fill=255)
    foot = ndimage.binary_dilation(np.asarray(foot) > 0, iterations=2)
    r, g = a[..., 0].astype(float), a[..., 1].astype(float)
    bad = foot & (r > 120) & (g > .6 * r)
    bad = ndimage.binary_dilation(bad, iterations=1) & foot
    good = foot & ~bad
    _, (iy, ix) = ndimage.distance_transform_edt(~good, return_indices=True)
    a[bad] = a[iy[bad], ix[bad]]
    print('SPILL', int(foot.sum()), 'footprint texels,', int(bad.sum()), 'repainted')


def base(a):
    spill(a)
    x0, y0, x1, y1 = cell['base_1536x1024']; m = 8
    ys, xs = np.mgrid[y0 - m:y1 + m, x0 - m:x1 + m] + .5
    cx, cy, h = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2
    a[y0 - m:y1 + m, x0 - m:x1 + m, :3] = eye_rgb((xs - cx) / h, (cy - ys) / h).astype(np.uint8)


def half(fn_px):
    def f(a):
        x0, y0, x1, y1 = cell['half_768x512']; m = 4
        fn_px(a[y0 - m:y1 + m, x0 - m:x1 + m])
    return f


def mask(s):
    s[..., 0] = 0


def mr(s):
    s[..., 1] = 70; s[..., 2] = 0


def nrm(s):
    s[..., :3] = (128, 128, 255)


new = {}
for name, fn in (('m266_heads_basecolor', base), ('m266_heads_region_mask', half(mask)),
                 ('m266_heads_metal_rough', half(mr)), ('m266_heads_normal', half(nrm))):
    view, data, pil = paint(name, fn); new[view] = data
    if name in ('m266_heads_basecolor', 'm266_heads_region_mask'):
        (P / 'textures').mkdir(exist_ok=True); pil.save(P / 'textures' / f'{name}.png')
# rebuild the binary chunk in view order with the replaced image views
out = bytearray()
for i, v in enumerate(doc['bufferViews']):
    o = v.get('byteOffset', 0); data = new.get(i, bytes(binary[o:o + v['byteLength']]))
    out.extend(b'\0' * (-len(out) % 4)); v['byteOffset'] = len(out); v['byteLength'] = len(data); out.extend(data)
write_glb(glb, doc, bytes(out))
print('EYEPAINT', glb.name, 'replaced', len(new), 'images', f'{len(out) / 1e6:.2f} MB')
