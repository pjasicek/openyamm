#!/usr/bin/env python3
"""Sandro's heart jar (D-62, DD-21): MM7's shipped vase (`mm7_deco_dec97.glb`, row dec97) recast as translucent green
glass with Sandro's heart inside.

- Glass (alpha BLEND, `xeen_heartjar_glass`): the vase's own mesh and LODs (positions, normals, UVs and its baked
  normal map kept). Each LOD's glass primitive holds an inner wall first (the shell pulled 0.006 model units inward
  along its normals, winding and normals reversed: the far wall seen through the near one) and then the outer shell.
  Blended primitives keep their authored triangle order, which is their draw order, so the far wall is always drawn
  before the near one. A new base colour (bottle green, alpha 0.36 in the belly, thicker at the foot, shoulder and
  lip), glossy metallic-roughness and an emissive green glow brightest in the belly.
- Heart (opaque, `xeen_heartjar_heart`): a small anatomical heart (a tapered, slightly lopsided ovoid with its apex
  tilted down, an aortic arch and two vessel stubs), dark red-brown with darker grooves and faint veins, a faint red
  emission with `openyamm_pulse` (a heartbeat). One heart mesh (accessors shared) in all three LODs.

    build.py <repo> <out.glb>"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / 'level_generation/decorations/xeen_planedevices_claude/scripts'))
from lib import Mesh, ellipsoid, mr_map, noise, normal_map, ramp, smoothstep, tube, u8  # noqa: E402

raw = (repo / 'assets_source/engine/models/mm7_deco_dec97.glb').read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
src = json.loads(raw[20:20 + n])
bl = struct.unpack_from('<I', raw, 20 + n)[0]
sbin = raw[28 + n:28 + n + bl]
TYPES = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read(i):
    a = src['accessors'][i]
    bv = src['bufferViews'][a['bufferView']]
    dt = np.dtype(TYPES[a['componentType']])
    w = WIDTH[a['type']]
    o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(sbin, dt, a['count'] * w, o).reshape(a['count'], w).copy()


def src_image(i):
    bv = src['bufferViews'][src['images'][i]['bufferView']]
    o = bv.get('byteOffset', 0)
    return sbin[o:o + bv['byteLength']]


# ------------------------------------------------------------------ the new GLB
doc = {'asset': {'version': '2.0', 'generator': 'xeen_heartjar_claude build.py'}, 'buffers': [{'byteLength': 0}],
       'bufferViews': [], 'accessors': [], 'images': [], 'textures': [], 'samplers': [
           {'magFilter': 9729, 'minFilter': 9987}], 'materials': [], 'meshes': [], 'nodes': [],
       'scenes': [{'name': 'Scene', 'nodes': [0]}], 'scene': 0}
binary = bytearray()


def view(data, target=None):
    binary.extend(b'\0' * (-len(binary) % 4))
    v = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}
    if target:
        v['target'] = target
    binary.extend(data)
    doc['bufferViews'].append(v)
    return len(doc['bufferViews']) - 1


def accessor(a, kind, comp, target, bounds=False):
    a = np.ascontiguousarray(a)
    acc = {'bufferView': view(a.tobytes(), target), 'componentType': comp, 'count': int(a.shape[0]), 'type': kind}
    if bounds:
        acc['min'] = a.min(axis=0).tolist()
        acc['max'] = a.max(axis=0).tolist()
    doc['accessors'].append(acc)
    return len(doc['accessors']) - 1


def texture_png(data, name):
    doc['images'].append({'bufferView': view(data), 'mimeType': 'image/png', 'name': name})
    doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0})
    return len(doc['textures']) - 1


def texture(arr, name):
    buf = io.BytesIO()
    mode = 'RGBA' if arr.shape[2] == 4 else 'RGB'
    Image.fromarray(u8(arr), mode).save(buf, 'PNG', optimize=True)
    return texture_png(buf.getvalue(), name)


def primitive(P, N, UV, T, material):
    return {'attributes': {'POSITION': accessor(P.astype(np.float32), 'VEC3', 5126, 34962, bounds=True),
                           'NORMAL': accessor(N.astype(np.float32), 'VEC3', 5126, 34962),
                           'TEXCOORD_0': accessor(UV.astype(np.float32), 'VEC2', 5126, 34962)},
            'indices': accessor(T.astype(np.uint16).ravel(), 'SCALAR', 5123, 34963), 'material': material}


# ------------------------------------------------------------------ glass textures (the vase's cylindrical UVs)
rng = np.random.default_rng(4047)
src_mat = src['materials'][0]
base_src = np.asarray(Image.open(io.BytesIO(src_image(
    src['textures'][src_mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']))).convert('RGB'), float)
h, w = base_src.shape[:2]
lum = (0.299 * base_src[..., 0] + 0.587 * base_src[..., 1] + 0.114 * base_src[..., 2]) / 255.0
lo, hi = np.percentile(lum, [2, 98])
t = np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1)
v = np.linspace(0, 1, h)[:, None] * np.ones((1, w))
# V runs from the lip (v 0.2) down the neck (to 0.5), the shoulder (0.5-0.55), the belly (0.55-0.8) to the foot (0.85+).
streak = noise(rng, h, w, 40, 1.5)                    # vertical draw streaks of blown glass
thick = np.maximum.reduce([smoothstep(0.80, 0.90, v),                       # the foot
                           1 - smoothstep(0.50, 0.58, v),                   # shoulder, neck and lip
                           0 * v])
k = np.clip(0.5 + 0.12 * (t - 0.5) + 0.08 * streak, 0, 1)
glass = ramp(k, [(0.0, (20, 82, 44)), (0.5, (38, 128, 66)), (1.0, (70, 170, 96))])
glass = glass * (1 - 0.25 * thick[..., None])         # thicker glass reads deeper green
alpha = np.clip(0.36 + 0.26 * thick + 0.05 * streak, 0.3, 0.7)
glow = 0.25 + 0.4 * np.exp(-((v - 0.66) / 0.14) ** 2)   # s14: lower belly peak, so the heart reads red
emissive = np.array([30, 150, 60], float) * glow[..., None] * (0.85 + 0.15 * k[..., None])
mr = mr_map(np.full((h, w), 0.07))

nrm_idx = src_mat['normalTexture']['index']
t_nrm = texture_png(src_image(src['textures'][nrm_idx]['source']), 'heartjar_glass_normal')
t_base = texture(np.concatenate([glass, alpha[..., None] * 255], axis=2), 'heartjar_glass_base')
t_mr = texture(mr, 'heartjar_glass_mr')
t_em = texture(emissive, 'heartjar_glass_emissive')
doc['materials'].append({'name': 'xeen_heartjar_glass', 'alphaMode': 'BLEND', 'doubleSided': False,
                         'normalTexture': {'index': t_nrm},
                         'pbrMetallicRoughness': {'baseColorTexture': {'index': t_base},
                                                  'metallicRoughnessTexture': {'index': t_mr}},
                         'emissiveTexture': {'index': t_em}, 'emissiveFactor': [1.0, 1.0, 1.0],
                         'extras': {'openyamm_specular': 1.0}})


# ------------------------------------------------------------------ heart textures and mesh
def heart_tex(s):
    n1, n2, n3 = noise(rng, s, s, 18), noise(rng, s, s, 4), noise(rng, s, s, 1.2)
    vein_field = noise(rng, s, s, 26, 9)
    veins = np.exp(-(vein_field / 0.06) ** 2)
    groove = np.exp(-((np.linspace(0, 1, s)[None, :] - 0.37) / 0.025) ** 2) * np.ones((s, 1))   # the front groove
    k = np.clip(0.5 + 0.18 * n1 + 0.1 * n2 + 0.06 * n3, 0, 1)
    rgb = ramp(k, [(0.0, (60, 20, 18)), (0.5, (98, 30, 24)), (1.0, (128, 44, 34))])
    fat = smoothstep(0.9, 1.8, noise(rng, s, s, 10)) * 0.35                            # waxy pale patches
    rgb = rgb * (1 - fat[..., None]) + np.array([118, 88, 62]) * fat[..., None]
    dark = np.clip(0.55 * veins + 0.6 * groove, 0, 1)
    rgb = rgb * (1 - dark[..., None]) + np.array([38, 14, 14]) * dark[..., None]
    height = 0.5 * n1 + 0.3 * n2 + 0.15 * n3 - 1.2 * veins - 2.0 * groove
    em = np.array([150, 14, 10], float) * (0.35 + 0.65 * veins + 0.4 * groove)[..., None] * 0.9
    rough = np.clip(0.45 + 0.1 * n2, 0, 1)
    return np.maximum(rgb, 31), mr_map(rough), normal_map(height * 2.0, 1.0), em


hb, hm, hn, he = heart_tex(256)
doc['materials'].append({'name': 'xeen_heartjar_heart', 'normalTexture': {'index': texture(hn, 'heart_normal')},
                         'pbrMetallicRoughness': {'baseColorTexture': {'index': texture(hb, 'heart_base')},
                                                  'metallicRoughnessTexture': {'index': texture(hm, 'heart_mr')}},
                         'emissiveTexture': {'index': texture(he, 'heart_emissive')},
                         'emissiveFactor': [1.0, 1.0, 1.0],
                         'extras': {'openyamm_specular': 0.6, 'openyamm_pulse': [0.7, 0.9]}})

heart = Mesh()
ellipsoid(heart, 'h', (0, 0, 0), (1.0, 1.0, 1.0), 9, 12, uv_tiles=(1.0, 1.0))


def shape(p):
    q = p.copy()
    y = p[:, 1]
    taper = 0.42 + 0.58 * smoothstep(-1.0, 0.35, y)    # the apex narrows below
    q[:, 0] = p[:, 0] * taper * (1.0 + 0.12 * np.clip(-p[:, 0], 0, 1))   # the left ventricle bulges
    q[:, 2] = p[:, 2] * taper * 0.8
    q[:, 1] = y * 1.15 - 0.15 * np.clip(-y, 0, 1) ** 2
    q[:, 0] += 0.18 * np.clip(-y, 0, 1) ** 2           # the apex swings to one side
    return q * [0.078, 0.085, 0.078]


heart.transform(shape)
# The aortic arch and two vessel stubs on top (model units; the heart's top is about y 0.098 here).
arch = np.array([[0.012, 0.07, 0.0], [0.018, 0.115, 0.004], [0.0, 0.142, 0.006], [-0.03, 0.135, 0.004],
                 [-0.045, 0.105, 0.0]])
tube(heart, 'h', arch, np.linspace(0.022, 0.016, len(arch)), 7, u_tiles=1.0, v_scale=2.0)
tube(heart, 'h', np.array([[-0.025, 0.07, 0.02], [-0.03, 0.11, 0.03], [-0.026, 0.13, 0.045]]), 0.014, 6, v_scale=2.0)
tube(heart, 'h', np.array([[0.035, 0.06, -0.02], [0.05, 0.095, -0.03], [0.058, 0.112, -0.028]]), 0.012, 6,
     v_scale=2.0)


def tilt(p):                                          # leaning back on its side, a quarter turn to show the arch
    a, b = np.radians(-18.0), np.radians(35.0)
    q = p.copy()
    q[:, 0], q[:, 1] = p[:, 0] * np.cos(a) - p[:, 1] * np.sin(a), p[:, 0] * np.sin(a) + p[:, 1] * np.cos(a)
    r = q.copy()
    r[:, 0], r[:, 2] = q[:, 0] * np.cos(b) + q[:, 2] * np.sin(b), -q[:, 0] * np.sin(b) + q[:, 2] * np.cos(b)
    return r


heart.transform(tilt)
hlo, hhi = heart.bounds()
heart.transform(lambda p: (p - (hlo + hhi) / 2) * 1.25 + [0.0, 0.34, 0.0])   # the belly's middle, 0.33 tall
HP, HN, HUV, HT = heart.arrays('h')
hlo, hhi = heart.bounds()
heart_prim = primitive(HP, HN, HUV, HT, 1)

# ------------------------------------------------------------------ glass primitives per LOD
INSET = 0.006
lod_tris = []
for mi, m in enumerate(src['meshes']):
    pr = m['primitives'][0]
    P = read(pr['attributes']['POSITION']).astype(float)
    N = read(pr['attributes']['NORMAL']).astype(float)
    UV = read(pr['attributes']['TEXCOORD_0']).astype(float)
    T = read(pr['indices']).reshape(-1, 3).astype(int)
    inner_p = P - N * INSET
    inner_p[:, 1] = np.maximum(inner_p[:, 1], INSET)  # keep the inner floor above the foot
    allP = np.vstack([inner_p, P])
    allN = np.vstack([-N, N])
    allUV = np.vstack([UV, UV])
    allT = np.vstack([T[:, ::-1], T + len(P)])        # the inner wall first: it is the far one
    mesh = {'name': m['name'], 'primitives': [primitive(allP, allN, allUV, allT, 0), dict(heart_prim)]}
    if 'extras' in m:
        mesh['extras'] = m['extras']
    doc['meshes'].append(mesh)
    lod_tris.append((m['name'], len(allT), len(HT)))
doc['nodes'].append({'name': 'Base', 'mesh': 0})
doc['buffers'][0]['byteLength'] = len(binary) + (-len(binary) % 4)

enc = json.dumps(doc, separators=(',', ':')).encode()
enc += b' ' * (-len(enc) % 4)
binary.extend(b'\0' * (-len(binary) % 4))
out.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a)
                + enc + struct.pack('<II', len(binary), 0x004e4942) + bytes(binary))
print('WROTE', out)
for name, g, hh in lod_tris:
    print(f'  {name}: glass {g} triangles (inner + outer), heart {hh}')
print('  heart bounds', np.round(hlo, 3).tolist(), np.round(hhi, 3).tolist())
