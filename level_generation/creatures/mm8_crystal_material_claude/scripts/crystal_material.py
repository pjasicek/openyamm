#!/usr/bin/env python3
"""Gem-crystal material for the MM8 Crystal Dragon (m548) and Crystal Walker (m596), user review 2026-10-19:
"adapt the crystal dragon (and crystal walker also, its really similar imo)". Both read as matte pastel pink in game;
the native sprites (palettes 548 / 596) are lighter, less saturated (median HSV saturation 0.33 against 0.42 in the
textures) and cut-gem: a long bright tail (99th luminance percentile 0.96-0.99, 2-4 % near-white glints), about 1 %
lavender / blue-violet facets, and no dark maroon (5th percentile 0.37-0.39).

The engine (GltfModelLoader / fs_model.sc) uses: metallicFactor x metallic-roughness blue, roughnessFactor x green,
extras openyamm_specular (sun, point-light and sky specular scale; with openyamm_specular_mask it is multiplied by the
metallic-roughness red channel per texel) and openyamm_edge_darkening. Emissive is one constant colour that also
feeds the bloom pass, so no emission is used here.

Variants:
  gloss  material only: roughness 0.15 (m548: the ORM green channel; m596: roughnessFactor), specular as below.
  full   gloss + per-facet colour in the base-colour texture (deterministic, seed 548 / 596), plus per-facet roughness
         and specular mask on m548 (its ORM). Textures keep their size, UVs and painted detail (each texel is
         recoloured relative to its facet's tone); geometry, rig, animation and every other buffer stay byte-identical.
Facets: m548's texture-aware UVs are unique per triangle, so its LOD0 triangles are grouped into flat facets
(position-welded edge neighbours within 12 deg) and each facet's UV area is rasterised into a facet map, dilated into
the gutters so the LOD1-3 triangles, which reuse the atlas, pick up the tone under them. m596 is 64 swatches of
256 px with 19 LOD0 faces each (rigid closed sections, overlapping UVs), so each swatch gets one tone.
The painted pink is first remapped in HSV value (0.35-0.95 -> 0.50-0.82) and shifted 7 deg toward mauve. Tones per facet: 5 % near-white glint, 3 % lavender / blue-violet, 20 % brighter, 15 % deeper rose (never below the
native dark end), the rest a small brightness and hue jitter; the whole texture is first desaturated to the native
saturation. m548's amber eyes (texels with hue 20-60 deg and saturation over 0.45) are left as painted.
Usage: crystal_material.py <in.glb> <out.glb> <m548|m596> <gloss|full|subtle>  (subtle: m548 only, review 2)"""
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import accessor_bytes, read_glb, write_glb  # noqa: E402

ROUGHNESS = 0.15
SPECULAR = {'m548': 0.8, 'm596': 0.8}   # was 0.45 x mask 0.863 (m548) and 0.6 (m596)
EDGE = {'m548': 0.25, 'm596': 0.2}      # was 0.35 / 0.25: the glossy facets turned away now reflect the sky
SATURATION = 0.34
V_LOW, V_HIGH = 0.46, 0.72   # value remap (0.35 -> V_LOW, 0.95 -> V_HIGH) of the painted pink before the facet tones
HUE_SHIFT = -0.02            # toward the sprites' mauve (hue 330 deg against the textures' 338)
FACET_DEG = 12.0


def accessor(doc, binary, index):
    a = doc['accessors'][index]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    x = np.frombuffer(accessor_bytes(doc, binary, index), dtype)
    return x.reshape(-1, n) if n > 1 else x


def image_of(doc, binary, texture_index):
    view = doc['bufferViews'][doc['images'][doc['textures'][texture_index]['source']]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[start:start + view['byteLength']]))


def png_bytes(array):
    out = io.BytesIO(); Image.fromarray(array).save(out, 'PNG', optimize=True)
    return out.getvalue()


def replace_views(doc, binary, replacements):
    """rebuild the binary chunk with some buffer views replaced; the others are copied byte for byte in order"""
    new = bytearray()
    for i, view in enumerate(doc['bufferViews']):
        start = view.get('byteOffset', 0)
        data = replacements.get(i, binary[start:start + view['byteLength']])
        new.extend(b'\0' * (-len(new) % 4)); view['byteOffset'] = len(new); view['byteLength'] = len(data)
        new.extend(data)
    return bytes(new)


def tones(count, seed):
    """per facet: (kind, value) with kind 0 jitter, 1 bright, 2 deep, 3 glint, 4 violet"""
    rng = np.random.default_rng(seed)
    u = rng.random(count)
    kind = np.select([u < 0.05, u < 0.08, u < 0.28, u < 0.43], [3, 4, 1, 2], 0)
    return kind, rng.random(count), rng.normal(0.0, 1.0, count)


def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-12), 0.0)
    dd = np.maximum(d, 1e-12)
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) / 6.0
    return np.stack([np.where(d > 0, h, 0.0), s, mx], -1)


def hsv_to_rgb(hsv):
    h, s, v = (hsv[..., 0] % 1.0) * 6, np.clip(hsv[..., 1], 0, 1), np.clip(hsv[..., 2], 0, 1)
    i = np.floor(h).astype(int) % 6; f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    table = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]
    out = np.zeros(hsv.shape)
    for k, (a, b, c) in enumerate(table):
        m = i == k
        out[..., 0][m], out[..., 1][m], out[..., 2][m] = a[m], b[m], c[m]
    return out


def apply_lut(base, labels, count, seed, keep):
    """recolour base (H, W, 3 uint8) per label (facet or swatch), each texel relative to its own value so the
    painted detail stays; keep: texels left as they are"""
    kind, r, n = tones(count, seed)
    rgb = base.astype(np.float64) / 255.0
    h, s, v = np.moveaxis(rgb_to_hsv(rgb), -1, 0)
    k, rr, nn = kind[labels], r[labels], n[labels]
    s = s * (SATURATION / 0.42)
    # lift the dark end (HSV value 0.35 -> 0.56, 0.95 kept): native sprites have no dark maroon
    v = np.clip(V_LOW + (v - 0.35) * (V_HIGH - V_LOW) / (0.95 - 0.35), 0.0, 1.0)
    h = h + HUE_SHIFT
    vmean = np.bincount(labels.ravel(), v.ravel(), count) / np.maximum(np.bincount(labels.ravel(), None, count), 1)
    jit = k == 0
    v = np.where(jit, v * (1.0 + 0.06 * nn), v); h = np.where(jit, h + 0.006 * nn, h)
    br = k == 1
    v = np.where(br, v * (1.12 + 0.10 * rr), v); s = np.where(br, s * 0.85, s)
    dp = k == 2
    v = np.where(dp, np.maximum(v * (0.84 - 0.06 * rr), 0.50), v); s = np.where(dp, s * 1.12, s)
    gl = k == 3
    v = np.where(gl, 0.88 + 0.10 * rr + (v - vmean[labels]) * 0.3, v); s = np.where(gl, s * 0.25, s)
    vi = k == 4
    h = np.where(vi, 0.72 + 0.06 * rr, h); s = np.where(vi, np.clip(s * 0.9, 0.2, 0.45), s)
    v = np.where(vi, 0.66 + 0.10 * rr + (v - vmean[labels]) * 0.5, v)
    out = hsv_to_rgb(np.stack([h, s, v], -1))
    out[keep] = rgb[keep]
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), kind


def m548_facets(doc, binary, size):
    mesh = next(m for m in doc['meshes'] if m['name'] == 'CrystalDragon'); p = mesh['primitives'][0]
    pos = accessor(doc, binary, p['attributes']['POSITION']); uv = accessor(doc, binary, p['attributes']['TEXCOORD_0'])
    tri = accessor(doc, binary, p['indices']).reshape(-1, 3)
    P = pos[tri]; nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    key = np.round(pos / 1e-5).astype(np.int64)
    _, weld = np.unique(key, axis=0, return_inverse=True); weld = weld.ravel()[tri]
    edges = {}
    parent = np.arange(len(tri))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    cos = np.cos(np.radians(FACET_DEG))
    for t, (a, b, c) in enumerate(weld):
        for e in ((a, b), (b, c), (c, a)):
            e = (min(e), max(e))
            if e in edges:
                o = edges[e]
                if np.dot(nrm[t], nrm[o]) > cos:
                    parent[find(t)] = find(o)
            else:
                edges[e] = t
    root = np.array([find(i) for i in range(len(tri))])
    _, facet = np.unique(root, return_inverse=True)
    canvas = Image.new('I', (size, size), -1); draw = ImageDraw.Draw(canvas)
    for t in np.argsort(-np.abs(np.cross(uv[tri][:, 1] - uv[tri][:, 0], uv[tri][:, 2] - uv[tri][:, 0]))):
        draw.polygon([(u * size, v * size) for u, v in uv[tri[t]]], fill=int(facet[t]))
    labels = np.asarray(canvas).copy()
    empty = labels < 0
    idx = ndimage.distance_transform_edt(empty, return_distances=False, return_indices=True)
    labels = labels[idx[0], idx[1]]
    return labels, int(facet.max()) + 1

SUBTLE_FACET_DEG = 3.0         # flat facets: coplanar neighbours only
SUPERSAMPLE = 4                # tone field rasterised at 4x and area-averaged: anti-aliased triangle edges
QUIET = (0.03, 0.06)           # metres from the eyes and the mouth: no variation inside, full beyond


def node_world(doc, name):
    nodes = doc['nodes']; parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}

    def local(n):
        t = np.eye(4); t[:3, 3] = n.get('translation', [0, 0, 0]); x, y, z, w = n.get('rotation', [0, 0, 0, 1])
        r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        m = np.eye(4); m[:3, :3] = r @ np.diag(n.get('scale', [1, 1, 1])); return t @ m
    i = next(k for k, n in enumerate(nodes) if n.get('name') == name); m = local(nodes[i])
    while i in parent:
        i = parent[i]; m = local(nodes[i]) @ m
    return m[:3, 3]


def m548_subtle(doc, binary, base, eyes):
    """review 2 ("what is this white stuff?"): no painted glints; a subtle per-facet value / faint lavender variation
    that follows the triangles exactly (supersampled coverage, area-averaged, gutters filled from the nearest
    covered texel), none within 3 cm of the eyes and the mouth, then the native-matched colour transform"""
    mesh = next(m for m in doc['meshes'] if m['name'] == 'CrystalDragon'); p = mesh['primitives'][0]
    pos = accessor(doc, binary, p['attributes']['POSITION']); uv = accessor(doc, binary, p['attributes']['TEXCOORD_0'])
    tri = accessor(doc, binary, p['indices']).reshape(-1, 3)
    P = pos[tri]; nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    _, weld = np.unique(np.round(pos / 1e-5).astype(np.int64), axis=0, return_inverse=True); weld = weld.ravel()[tri]
    parent = np.arange(len(tri)); edges = {}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    cos = np.cos(np.radians(SUBTLE_FACET_DEG))
    for t, (a, b, c) in enumerate(weld):
        for e in ((a, b), (b, c), (c, a)):
            e = (min(e), max(e))
            if e in edges and np.dot(nrm[t], nrm[edges[e]]) > cos:
                parent[find(t)] = find(edges[e])
            edges.setdefault(e, t)
    _, facet = np.unique([find(i) for i in range(len(tri))], return_inverse=True); count = facet.max() + 1
    rng = np.random.default_rng(548)
    u = rng.random(count); r = rng.random(count); n = np.clip(rng.normal(0, 1, count), -2, 2)
    dv = np.select([u < 0.15, u < 0.30], [0.06 + 0.04 * r, -(0.06 + 0.04 * r)], 0.03 * n)
    lav = np.where((u >= 0.30) & (u < 0.315), 1.0, 0.0)
    # quiet zone: eye triangles (amber under the UV centroid) and the mouth socket
    size = base.shape[0]; c = uv[tri].mean(1)
    px = np.clip((c * size).astype(int), 0, size - 1)
    eye_tri = eyes[px[:, 1], px[:, 0]]
    centres = P.mean(1)
    anchors = np.vstack([centres[eye_tri], node_world(doc, 'Socket_Mouth')[None]])
    dist = np.min(np.linalg.norm(centres[:, None, :] - anchors[None], axis=2), axis=1)
    amp = np.clip((dist - QUIET[0]) / (QUIET[1] - QUIET[0]), 0, 1); amp = amp * amp * (3 - 2 * amp)
    S = size * SUPERSAMPLE
    fields = {k: Image.new('F', (S, S), 0.0) for k in ('cov', 'dv', 'lav')}
    draws = {k: ImageDraw.Draw(v) for k, v in fields.items()}
    for t in range(len(tri)):
        poly = [(x * S, y * S) for x, y in uv[tri[t]]]
        draws['cov'].polygon(poly, fill=1.0)
        draws['dv'].polygon(poly, fill=float(dv[facet[t]] * amp[t]))
        draws['lav'].polygon(poly, fill=float(lav[facet[t]] * amp[t]))
    arr = {k: np.asarray(v, np.float64).reshape(size, SUPERSAMPLE, size, SUPERSAMPLE).sum((1, 3))
           for k, v in fields.items()}
    cov = arr['cov']; covered = cov > 0
    tone_dv = np.where(covered, arr['dv'] / np.maximum(cov, 1e-9), 0.0)
    tone_lav = np.where(covered, arr['lav'] / np.maximum(cov, 1e-9), 0.0)
    idx = ndimage.distance_transform_edt(~covered, return_distances=False, return_indices=True)
    tone_dv = tone_dv[idx[0], idx[1]]; tone_lav = tone_lav[idx[0], idx[1]]
    rgb = base.astype(np.float64) / 255.0
    h, s_, v = np.moveaxis(rgb_to_hsv(rgb), -1, 0)
    s_ = s_ * (SATURATION / 0.42); h = h + HUE_SHIFT
    v = np.clip(V_LOW + (v - 0.35) * (V_HIGH - V_LOW) / (0.95 - 0.35), 0.0, 1.0)
    v = v * (1.0 + tone_dv)
    hh = np.where(h < 0.5, h + 1.0, h); hh = hh - tone_lav * 0.25 * (hh - 0.75); h = hh % 1.0
    v = v * (1.0 + 0.03 * tone_lav)
    out = hsv_to_rgb(np.stack([h, s_, v], -1)); out[eyes] = rgb[eyes]
    print('m548 subtle facets', count, 'bright/deep/lavender', int((u < 0.15).sum()), int(((u >= 0.15) & (u < 0.30)).sum()),
          int(lav.sum()), 'quiet triangles', int((amp < 1).sum()))
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def main():
    src, dst, creature, variant = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    doc, binary = read_glb(src)
    mat = doc['materials'][0]; pbr = mat['pbrMetallicRoughness']; extras = mat.setdefault('extras', {})
    extras['openyamm_specular'] = SPECULAR[creature]; extras['openyamm_edge_darkening'] = EDGE[creature]
    replacements = {}
    if creature == 'm596':
        pbr['metallicFactor'] = 0.0; pbr['roughnessFactor'] = ROUGHNESS
        if variant == 'full':
            tex = pbr['baseColorTexture']['index']
            base = np.asarray(image_of(doc, binary, tex).convert('RGB'))
            yy, xx = np.mgrid[0:base.shape[0], 0:base.shape[1]]
            labels = (yy // (base.shape[0] // 8)) * 8 + xx // (base.shape[1] // 8)
            new, kind = apply_lut(base, labels, 64, 596, np.zeros(labels.shape, bool))
            replacements[doc['images'][doc['textures'][tex]['source']]['bufferView']] = png_bytes(new)
            print('m596 swatch tones', np.bincount(kind, minlength=5).tolist())
    else:
        tex_b = pbr['baseColorTexture']['index']; tex_o = pbr['metallicRoughnessTexture']['index']
        orm = np.asarray(image_of(doc, binary, tex_o).convert('RGB')).copy()
        if variant == 'gloss':
            orm[..., 1] = round(ROUGHNESS * 255)
        elif variant == 'subtle':
            base = np.asarray(image_of(doc, binary, tex_b).convert('RGB'))
            hsv = np.asarray(Image.fromarray(base).convert('HSV')).astype(float) / 255.0
            eyes = (hsv[..., 0] > 20 / 360) & (hsv[..., 0] < 60 / 360) & (hsv[..., 1] > 0.45)
            eyes = ndimage.binary_dilation(eyes, iterations=2)
            replacements[doc['images'][doc['textures'][tex_b]['source']]['bufferView']] = png_bytes(
                m548_subtle(doc, binary, base, eyes))
            orm[..., 1] = round(ROUGHNESS * 255); orm[..., 0] = 255   # uniform gloss; glints come from the specular
        else:
            base = np.asarray(image_of(doc, binary, tex_b).convert('RGB'))
            labels, count = m548_facets(doc, binary, base.shape[0])
            hsv = np.asarray(Image.fromarray(base).convert('HSV')).astype(float) / 255.0
            eyes = (hsv[..., 0] > 20 / 360) & (hsv[..., 0] < 60 / 360) & (hsv[..., 1] > 0.45)
            eyes = ndimage.binary_dilation(eyes, iterations=2)
            new, kind = apply_lut(base, labels, count, 548, eyes)
            replacements[doc['images'][doc['textures'][tex_b]['source']]['bufferView']] = png_bytes(new)
            # ORM at its own resolution: per-facet roughness 0.10-0.20 (glints 0.08) and specular mask 0.75-1.0
            s = orm.shape[0] / base.shape[0]
            lab_o = labels[(np.arange(orm.shape[0]) / s).astype(int)][:, (np.arange(orm.shape[1]) / s).astype(int)]
            rng = np.random.default_rng(5480)
            rough = 0.10 + 0.10 * rng.random(count); rough[kind == 3] = 0.08
            spec = 0.75 + 0.25 * rng.random(count); spec[kind == 3] = 1.0
            orm[..., 1] = np.round(rough[lab_o] * 255); orm[..., 0] = np.round(spec[lab_o] * 255)
            print('m548 facets', count, 'tones', np.bincount(kind, minlength=5).tolist(), 'eye texels', int(eyes.sum()))
        replacements[doc['images'][doc['textures'][tex_o]['source']]['bufferView']] = png_bytes(orm)
    out = replace_views(doc, binary, replacements) if replacements else binary
    write_glb(dst, doc, out)
    print('CRYSTAL', creature, variant, src.name, '->', dst.name, f'{len(out) / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
