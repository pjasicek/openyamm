#!/usr/bin/env python3
"""hkr attachment far LODs vs atlas gaps: per attachment GLB (export/hes_kreegan_<part>.glb, not the body) and per
primitive with a base colour texture, each LOD level's area-weighted mean base colour (sRGB luminance) and its share
of dark texels (luminance < 0.12; the plates' inner surfaces map to a dark block, so the share is compared with
LOD0's, not with zero), sampled at 7 barycentric points per triangle with world-area weights. A LOD whose triangles
reach into gutters or the dark block reads darker than LOD0 at distance. Pass per level: mean luminance drop <= 0.04
and, for light materials (LOD0 mean > 0.25; the black carapace sits on the threshold), dark share +<= 0.04. Writes review/lod_atlas_check.json. Args: [glb ...] (default: every attachment)"""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
BARY = np.array([[1 / 3, 1 / 3, 1 / 3], [0.6, 0.2, 0.2], [0.2, 0.6, 0.2], [0.2, 0.2, 0.6], [0.45, 0.45, 0.1],
                 [0.1, 0.45, 0.45], [0.45, 0.1, 0.45]])
SKIP = ('far', 'glow', 'lod0', 'lods', 'near', 'runtime_lod0', 'shadows', 'split', 'variants', 'carbine_drop')


def read(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw[28 + n:]


def acc(doc, binb, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    dt = COMP[a['componentType']]; nc = NCOMP[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', 0)
    if stride and stride != nc * np.dtype(dt).itemsize:
        arr = np.ndarray((a['count'], nc), dt, binb, off, (stride, np.dtype(dt).itemsize))
    else:
        arr = np.frombuffer(binb, dt, a['count'] * nc, off).reshape(a['count'], nc)
    return arr.astype(np.float64) if dt == np.float32 else arr


def image(doc, binb, tex):
    src = doc['textures'][tex]['source']; v = doc['bufferViews'][doc['images'][src]['bufferView']]
    o = v.get('byteOffset', 0)
    return np.asarray(Image.open(io.BytesIO(binb[o:o + v['byteLength']])).convert('RGB'), np.float64) / 255.0


def stats(doc, binb, prim, img):
    P = acc(doc, binb, prim['attributes']['POSITION']); UV = acc(doc, binb, prim['attributes']['TEXCOORD_0'])
    I = acc(doc, binb, prim['indices']).reshape(-1, 3).astype(int)
    area = 0.5 * np.linalg.norm(np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]), axis=1)
    h, w, _ = img.shape
    uv = np.einsum('kj,tjc->tkc', BARY, UV[I])                       # tris x 7 x 2
    x = np.clip((uv[..., 0] % 1.0) * w, 0, w - 1).astype(int); y = np.clip((uv[..., 1] % 1.0) * h, 0, h - 1).astype(int)
    lum = img[y, x] @ np.array([0.2126, 0.7152, 0.0722])
    wts = np.repeat(area[:, None], 7, 1); wts /= wts.sum()
    return {'tris': int(len(I)), 'lum': float((lum * wts).sum()), 'dark': float(((lum < 0.12) * wts).sum())}


files = [Path(p) for p in sys.argv[1:]] or [ROOT/'export'/f'{name}.glb' for name in
    ('hes_ion_lance', 'hes_ion_lance_twin', 'hes_lancer_graft')]
rep, bad = {}, []
for f in files:
    doc, binb = read(f)
    m0 = doc['meshes'][doc['nodes'][0]['mesh']]
    levels = [doc['nodes'][0]['mesh']] + m0.get('extras', {}).get('openyamm_lods', [])
    for pi, prim in enumerate(m0['primitives']):
        mat = doc['materials'][prim['material']]
        t = mat.get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if t is None: continue
        img = image(doc, binb, t['index'])
        rows = [stats(doc, binb, doc['meshes'][mi]['primitives'][pi], img) for mi in levels]
        key = f'{f.stem}:{mat["name"]}'; rep[key] = rows
        for li, r in enumerate(rows[1:], 1):
            dl, dd = r['lum'] - rows[0]['lum'], r['dark'] - rows[0]['dark']
            # brighter is no gap; the dark-share test only for light plates (the black carapace sits on the threshold)
            if dl < -0.04 or (dd > 0.04 and rows[0]["lum"] > 0.25): bad.append(f'{key} LOD{li} lum {dl:+.3f} dark {dd:+.3f} tris {r["tris"]}')
        print('LODATLAS', key, ' '.join(f"L{i}:{r['tris']}t lum {r['lum']:.3f} dark {r['dark']:.3f}" for i, r in enumerate(rows)))
json.dump(rep, open(ROOT / 'review' / 'lod_atlas_check.json', 'w'), indent=1)
print('LODATLAS', 'FAIL' if bad else 'PASS', len(bad))
for b in bad: print('  ', b)

assert not bad, "Attachment LOD atlas gate failed; see report"
