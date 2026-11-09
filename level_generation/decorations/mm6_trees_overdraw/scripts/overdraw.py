#!/usr/bin/env python3
"""Leaf overdraw gate: card layers per covered pixel, per LOD and view, from an exported GLB (the cut cards the engine
draws). CPU orthographic rasteriser (numpy): every alpha-tested (MASK, not billboard) triangle is scanned, its texture
alpha sampled at each pixel (nearest texel of the full-size image, cutoff 0.5), and the passing fragments counted.

- layers: fragments per covered pixel with no depth test (the cost without a prepass);
- front: only fragments in front of the opaque depth (bark, crown shells) - what remains once the engine draws opaque
  parts into the depth prepass first and alpha-tested cards behind them are rejected.
Covered = at least one passing card fragment. Views: front (looking down -z in glTF), three-quarter (45 deg), side.
Copied from ../../mm8_3d/trees_other/scripts/overdraw.py; only the heat-map output differs (both counts, the
no-depth-test layers as <prefix>_all_*, the layers in front of the opaque depth as <prefix>_front_*).
Usage: overdraw.py <model.glb> [--res 384] [--heat out_prefix]   (prints one line per LOD and view, JSON at the end)"""
import argparse, io, json, math, struct, sys
import numpy as np
from PIL import Image

COMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
DT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}


def read_glb(path):
    data = open(path, 'rb').read()
    jl = struct.unpack('<I', data[12:16])[0]
    doc = json.loads(data[20:20 + jl])
    binary = data[20 + jl + 8:]
    return doc, binary


def accessor(doc, binary, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    n = COMP[a['type']]; dt = np.dtype(DT[a['componentType']])
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    out = np.frombuffer(binary[off:off + a['count'] * n * dt.itemsize], dt).reshape(a['count'], n)
    if a.get('normalized') and dt != np.float32:
        out = out.astype(np.float32) / np.iinfo(dt).max
    return out


def image_alpha(doc, binary, material):
    tex = material['pbrMetallicRoughness']['baseColorTexture']['index']
    im = doc['images'][doc['textures'][tex]['source']]
    v = doc['bufferViews'][im['bufferView']]
    raw = binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]
    return np.asarray(Image.open(io.BytesIO(raw)).convert('RGBA'))[..., 3] >= 128


def lod_meshes(doc):
    base = next(n for n in doc['nodes'] if n['name'] == 'Tree')
    return [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']


def rotate(p, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    x = p[:, 0] * c + p[:, 2] * s
    z = -p[:, 0] * s + p[:, 2] * c
    return np.stack([x, p[:, 1], z], 1)


def raster(tris, uvs, alphas, frame, res, depth_buffer=None, count=None, opaque=False):
    """tris: (n, 3, 3) view space (x right, y up, z toward the viewer). Accumulates passing fragments into `count`
    (no depth test) and, for opaque triangles, the nearest z into depth_buffer; returns per-fragment lists for the
    front test when depth_buffer is given and not opaque."""
    x0, y0, scale = frame
    frags = []
    for k in range(len(tris)):
        t = tris[k]
        px = (t[:, 0] - x0) * scale; py = (y0 - t[:, 1]) * scale
        xmin, xmax = int(max(math.floor(px.min()), 0)), int(min(math.ceil(px.max()), res - 1))
        ymin, ymax = int(max(math.floor(py.min()), 0)), int(min(math.ceil(py.max()), res - 1))
        if xmin > xmax or ymin > ymax:
            continue
        gx, gy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        d = (py[1] - py[2]) * (px[0] - px[2]) + (px[2] - px[1]) * (py[0] - py[2])
        if abs(d) < 1e-9:
            continue
        w0 = ((py[1] - py[2]) * (gx - px[2]) + (px[2] - px[1]) * (gy - py[2])) / d
        w1 = ((py[2] - py[0]) * (gx - px[2]) + (px[0] - px[2]) * (gy - py[2])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        z = w0 * t[0, 2] + w1 * t[1, 2] + w2 * t[2, 2]
        ix = gx[inside].astype(int); iy = gy[inside].astype(int); zz = z[inside]
        if opaque:
            np.minimum.at(depth_buffer, (iy, ix), -zz)
            continue
        uv = uvs[k]; alpha = alphas
        u = w0[inside] * uv[0, 0] + w1[inside] * uv[1, 0] + w2[inside] * uv[2, 0]
        v = w0[inside] * uv[0, 1] + w1[inside] * uv[1, 1] + w2[inside] * uv[2, 1]
        th, tw = alpha.shape
        tx = np.clip((np.mod(u, 1.0) * tw).astype(int), 0, tw - 1)
        ty = np.clip((np.mod(v, 1.0) * th).astype(int), 0, th - 1)
        ok = alpha[ty, tx]
        np.add.at(count, (iy[ok], ix[ok]), 1)
        frags.append((iy[ok], ix[ok], -zz[ok]))
    return frags


def analyse(path, res=384, heat=None, lods=(0, 1, 2)):
    doc, binary = read_glb(path)
    chain = lod_meshes(doc)
    mats = doc['materials']
    alpha_cache = {}
    # one frame for every LOD and view: the LOD0 bounds' largest extent
    allpos = np.concatenate([accessor(doc, binary, p['attributes']['POSITION'])
                             for p in doc['meshes'][chain[0]]['primitives']])
    ext = np.abs(allpos[:, [0, 2]]).max()
    hmax = allpos[:, 1].max()
    size = max(2 * ext, hmax) * 1.04
    frame = (-size / 2, hmax + 0.02 * size, res / size)
    out = {}
    for lod in lods:
        if lod >= len(chain):
            continue
        for view, yaw in (('front', 0.0), ('three_quarter', math.radians(45)), ('side', math.radians(90))):
            count = np.zeros((res, res), np.int32)
            depth = np.full((res, res), np.inf, np.float32)
            frags = []
            for p in doc['meshes'][chain[lod]]['primitives']:
                m = mats[p['material']]
                pos = rotate(accessor(doc, binary, p['attributes']['POSITION']).astype(np.float64), yaw)
                idx = accessor(doc, binary, p['indices']).reshape(-1, 3)
                tris = pos[idx]
                if m.get('extras', {}).get('openyamm_billboard'):
                    continue
                if m.get('alphaMode') == 'MASK':
                    key = p['material']
                    if key not in alpha_cache:
                        alpha_cache[key] = image_alpha(doc, binary, m)
                    uv = accessor(doc, binary, p['attributes']['TEXCOORD_0']).astype(np.float64)[idx]
                    frags += raster(tris, uv, alpha_cache[key], frame, res, count=count)
                else:
                    raster(tris, None, None, frame, res, depth_buffer=depth, opaque=True)
            front = np.zeros_like(count)
            for iy, ix, dz in frags:
                keep = dz < depth[iy, ix] - 1e-4
                np.add.at(front, (iy[keep], ix[keep]), 1)
            cov = count > 0
            fcov = front > 0
            r = {'covered_px': int(cov.sum()), 'opaque_only_px': int(((count == 0) & np.isfinite(depth)).sum()),
                 'opaque_seen_px': int((np.isfinite(depth) & (front == 0)).sum()),
                 'layers_mean': round(float(count[cov].mean()), 2) if cov.any() else 0.0,
                 'layers_p95': float(np.percentile(count[cov], 95)) if cov.any() else 0.0,
                 'front_mean': round(float(front[fcov].mean()), 2) if fcov.any() else 0.0,
                 'front_p95': float(np.percentile(front[fcov], 95)) if fcov.any() else 0.0}
            out[f'LOD{lod}_{view}'] = r
            print(f"OVERDRAW LOD{lod} {view:13s} covered {r['covered_px']:6d} layers mean {r['layers_mean']:5.2f} "
                  f"p95 {r['layers_p95']:4.0f}   in front of opaque mean {r['front_mean']:5.2f} p95 {r['front_p95']:4.0f}")
            if heat:                     # MM6 copy: both maps, <prefix>_{front,all}_LOD<n>_<view>.png
                for name, cnt in (('front', front), ('all', count)):
                    hm = np.clip(cnt / 8.0, 0, 1)
                    rgb = np.stack([hm, np.clip(1.5 - np.abs(hm - 0.5) * 3, 0, 1) * (hm > 0), 1 - hm], -1) * (cnt > 0)[..., None]
                    img = (rgb * 255).astype(np.uint8)
                    img[(cnt == 0) & np.isfinite(depth)] = (60, 60, 60)
                    Image.fromarray(img).save(f'{heat}_{name}_LOD{lod}_{view}.png')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('glb'); ap.add_argument('--res', type=int, default=384); ap.add_argument('--heat')
    ap.add_argument('--json')
    a = ap.parse_args()
    res = analyse(a.glb, a.res, a.heat)
    if a.json:
        json.dump(res, open(a.json, 'w'), indent=1)
