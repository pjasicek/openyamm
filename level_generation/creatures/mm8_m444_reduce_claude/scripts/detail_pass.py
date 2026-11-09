#!/usr/bin/env python3
"""Surface detail for the Smuggler's body texture (user review 2026-10-19: "solid colour blobs ... like no normals").

Meshy's body retexture came back nearly flat (colour detail 6.3, normal tilt 1.8 degrees), so the tunic, trousers and
boots read as painted blobs next to the HD master. This adds, on the body half of the shared atlas only (the head set
is left as it is):
- the woven tunic, embossed cloth and tooled leather of the HD front master (`references_hd/01_front.png`): a high-pass
  of each swatch, made seamless and sampled triplanar by each texel's rest-pose position at the master's own scale
  (835 px/m), so the pattern keeps one size across UV islands and seams;
- the same pattern as relief in the normal map (texel-space height gradients, blended over the installed normals);
- short-range ambient occlusion of the rest pose (`bake_ao.py`), so folds, straps and the belt line shade.
Classes: the production class map keeps skin and metal out; fabric and leather are told apart by colour (grey tunic,
teal cloth, brown leather). The tier ramps recolour the teal cloth from its luminance, so the pattern carries into
every tier. UVs, geometry, the mask, the roughness map and the head are unchanged.

Usage: detail_pass.py <in.glb> <ao.png> <out.glb> [--preview dir]
"""
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

MASTER = HERE.parent / 'mm8_m444_claude/references_hd/01_front.png'
CLASSES = HERE.parent / 'mm8_m444_claude/textures/smuggler_material_classes.png'
MASTER_PX_PER_M = 835.0
BODY_WIDTH = 1024  # atlas columns of the body texture; the head set starts at 1056
# Swatch box in the HD master, high-pass radius (master pixels), colour-detail gain, normal relief and AO strength.
SWATCHES = {
    'tunic': {'box': (235, 430, 300, 520), 'sigma': 4, 'gain': 0.24, 'relief': 2.4, 'ao': 0.5},
    'cloth': {'box': (565, 660, 665, 790), 'sigma': 4, 'gain': 0.24, 'relief': 2.2, 'ao': 0.5},
    'leather': {'box': (310, 1345, 375, 1390), 'sigma': 5, 'gain': 0.32, 'relief': 2.0, 'ao': 0.35},
}
SKIN_AO = 0.35


def accessor(doc, binary, index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    return np.frombuffer(binary, dtype, a['count'] * count,
                         view.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], count)


def image(doc, binary, texture):
    view = doc['bufferViews'][doc['images'][doc['textures'][texture]['source']]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[start:start + view['byteLength']]))


def rasterise(uv, xyz, normals, indices, width, height):
    """Per atlas texel: rest-pose position and normal of the LOD0 triangle covering it (NaN outside the islands)."""
    position = np.full((height, width, 3), np.nan, np.float32)
    normal = np.zeros((height, width, 3), np.float32)
    pixels = uv * [width, height] - 0.5
    for tri in indices:
        p = pixels[tri]
        x0, y0 = np.floor(p.min(0)).astype(int)
        x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, width - 1), min(y1, height - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-9:
            continue
        w0 = ((p[1, 1] - p[2, 1]) * (gx - p[2, 0]) + (p[2, 0] - p[1, 0]) * (gy - p[2, 1])) / d
        w1 = ((p[2, 1] - p[0, 1]) * (gx - p[2, 0]) + (p[0, 0] - p[2, 0]) * (gy - p[2, 1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not inside.any():
            continue
        w = np.stack([w0[inside], w1[inside], w2[inside]], 1)
        position[gy[inside], gx[inside]] = w @ xyz[tri]
        normal[gy[inside], gx[inside]] = w @ normals[tri]
    return position, normal


def seamless(swatch, sigma):
    """High-pass luminance of a swatch, cross-faded with its half-shifted copy so it tiles without a seam."""
    lum = np.asarray(swatch.convert('L'), np.float32) / 255
    detail = lum - ndimage.gaussian_filter(lum, sigma)
    detail /= detail.std() + 1e-6
    h, w = detail.shape
    shifted = np.roll(detail, (h // 2, w // 2), (0, 1))
    fy = np.minimum(np.arange(h), h - 1 - np.arange(h)) / (h / 2)
    fx = np.minimum(np.arange(w), w - 1 - np.arange(w)) / (w / 2)
    edge = np.clip(np.minimum.outer(fy, fx) * 3, 0, 1)
    tile = detail * edge + shifted * (1 - edge)
    return (tile - tile.mean()) / (tile.std() + 1e-6)


def triplanar(tile, position, normal):
    """Sample the tile at each texel's position (metres -> master pixels) on the three axis planes."""
    h, w = tile.shape
    weights = np.abs(normal) ** 4
    weights /= weights.sum(-1, keepdims=True) + 1e-9
    result = np.zeros(position.shape[:2], np.float32)
    for axis, (a, b) in enumerate(((1, 2), (0, 2), (0, 1))):
        u = position[..., a] * MASTER_PX_PER_M
        v = position[..., b] * MASTER_PX_PER_M
        result += weights[..., axis] * ndimage.map_coordinates(tile, [np.mod(-v, h), np.mod(u, w)], order=1,
                                                               mode='grid-wrap')
    return result


def main():
    source, aoPath, target = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    preview = Path(sys.argv[sys.argv.index('--preview') + 1]) if '--preview' in sys.argv else None
    doc, binary = read_glb(source)
    material = doc['materials'][0]
    baseIndex = material['pbrMetallicRoughness']['baseColorTexture']['index']
    normalIndex = material['normalTexture']['index']
    base = np.asarray(image(doc, binary, baseIndex).convert('RGB'), np.float32) / 255
    normalMap = np.asarray(image(doc, binary, normalIndex).convert('RGB'), np.float32) / 127.5 - 1
    height, width = base.shape[:2]

    node = next(n for n in doc['nodes'] if 'mesh' in n and 'skin' in n)
    primitive = doc['meshes'][node['mesh']]['primitives'][0]
    uv = accessor(doc, binary, primitive['attributes']['TEXCOORD_0']).astype(np.float64)
    xyz = accessor(doc, binary, primitive['attributes']['POSITION']).astype(np.float64)
    normals = accessor(doc, binary, primitive['attributes']['NORMAL']).astype(np.float64)
    indices = accessor(doc, binary, primitive['indices']).reshape(-1, 3)
    body = uv[indices].mean(1)[:, 0] * width < BODY_WIDTH
    position, normal = rasterise(uv, xyz, normals, indices[body], width, height)
    covered = ~np.isnan(position[..., 0])
    # Pad positions and normals into the gutters (nearest island texel) so filtering at seams sees the same pattern.
    nearest = ndimage.distance_transform_edt(~covered, return_distances=False, return_indices=True)
    position = position[nearest[0], nearest[1]]
    normal = normal[nearest[0], nearest[1]]
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True) + 1e-9
    bodyColumns = np.zeros((height, width), bool)
    bodyColumns[:, :BODY_WIDTH] = True

    # Classes: production skin (1) and metal (9) stay out; fabric and leather by colour.
    classes = np.zeros((height, width), np.uint8)
    classes[:, :BODY_WIDTH] = np.asarray(Image.open(CLASSES))[:, :BODY_WIDTH]
    hsv = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).convert('HSV'), np.float32) / 255
    hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    free = bodyColumns & (classes != 1) & (classes != 9)
    masks = {
        'tunic': free & (sat < 0.16) & (val > 0.3),
        'cloth': free & (hue > 120) & (hue < 210) & (sat > 0.2),
        'leather': free & (hue > 8) & (hue < 50) & (sat > 0.35),
    }
    master = Image.open(MASTER).convert('RGB')
    detail = np.zeros((height, width), np.float32)
    relief = np.zeros((height, width), np.float32)
    aoWeight = np.where(bodyColumns & (classes == 1), SKIN_AO, 0).astype(np.float32)
    for name, spec in SWATCHES.items():
        mask = ndimage.gaussian_filter(masks[name].astype(np.float32), 1.0)
        pattern = triplanar(seamless(master.crop(spec['box']), spec['sigma']), position, normal)
        detail += mask * spec['gain'] * pattern
        relief += mask * spec['relief'] * pattern
        aoWeight = np.maximum(aoWeight, mask * spec['ao'])

    ao = np.asarray(Image.open(aoPath).convert('L').resize((width, height)), np.float32) / 255
    ao = ndimage.gaussian_filter(ao, 0.8)
    shade = (1 - aoWeight) + aoWeight * ao
    lit = np.clip(base * (1 + 0.5 * np.tanh(detail))[..., None] * shade[..., None], 0, 1)
    out = np.where(bodyColumns[..., None], lit, base)

    # Relief: texel-space gradients of the pattern (glTF normal maps: +x right, +y toward the image top).
    heightField = ndimage.gaussian_filter(relief, 0.7) * 0.05
    dx = np.gradient(heightField, axis=1)
    dy = np.gradient(heightField, axis=0)
    detailNormal = np.stack([-dx, dy, np.ones_like(dx)], -1)
    combined = normalMap.copy()
    combined[..., :2] += detailNormal[..., :2]
    combined /= np.linalg.norm(combined, axis=-1, keepdims=True) + 1e-9
    normalOut = np.where(bodyColumns[..., None], combined, normalMap)

    pngs = {}
    for index, array in ((baseIndex, (out * 255 + 0.5).astype(np.uint8)),
                         (normalIndex, ((normalOut + 1) * 127.5 + 0.5).clip(0, 255).astype(np.uint8))):
        buffer = io.BytesIO()
        Image.fromarray(array).save(buffer, 'PNG', optimize=True)
        pngs[doc['images'][doc['textures'][index]['source']]['bufferView']] = buffer.getvalue()
        if preview:
            preview.mkdir(parents=True, exist_ok=True)
            Image.fromarray(array).save(preview / f'{"basecolor" if index == baseIndex else "normal"}.png')
    new = bytearray()
    for i, view in enumerate(doc['bufferViews']):
        start = view.get('byteOffset', 0)
        data = pngs.get(i, binary[start:start + view['byteLength']])
        new.extend(b'\0' * (-len(new) % 4))
        view['byteOffset'] = len(new)
        view['byteLength'] = len(data)
        new.extend(data)
    write_glb(target, doc, bytes(new))
    tilt = np.degrees(np.arccos(np.clip(normalOut[:, :BODY_WIDTH, 2], -1, 1)))
    print(f'DETAIL body texels {covered.sum()}, tunic {masks["tunic"].sum()}, cloth {masks["cloth"].sum()}, '
          f'leather {masks["leather"].sum()}; normal tilt mean {tilt.mean():.1f} deg; {len(new) / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
