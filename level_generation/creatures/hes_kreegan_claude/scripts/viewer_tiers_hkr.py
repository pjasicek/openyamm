#!/usr/bin/env python3
"""hkr review-viewer GLBs: three.js has no region ramps or per-descriptor attachments, so each tier is baked from
export/hes_kreegan_trooper_lod0.glb (body + shell + every rigid part and the carbine in one mesh, before the split):
- the ramps (textures/hkr_ramps.json) baked into the body's and the armour atlas's base colour with the engine rule
  (per region: t = linear luminance over the range, colour = mix(colour, ramp(t), mask channel));
- the glow materials' emissive colour per tier (glow_variants.py);
- tier B's carapace pauldrons (vertices fully on B_*_Carapace) left out of tiers A and C, and the ivory caps (fully
  on B_*_Pauldron; the spikes are on B_*_Spikes) left out of tier B, exactly as the actors.yml attachment lists do;
- clips renamed without the Carbine_ prefix for the shared viewer (Standing, Walking, ...), the Demon_* clips kept.
Writes review/viewer/hes_kreegan_<a|b|c>.glb and work/tier_<variant>_<material>.png. Args: none"""
import io, json, struct, copy
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
GLOW = {'hkr_a': (1.0, 0.42, 0.08), 'hkr_b': (1.0, 0.36, 0.06), 'hkr_c': (1.0, 0.86, 0.55)}


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def acc(doc, binary, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    comp = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(bytes(binary[off:off + a['count'] * comp * np.dtype(dt).itemsize]), dt).reshape(a['count'], comp)


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def image_bytes(doc, binary, idx):
    v = doc['bufferViews'][doc['images'][idx]['bufferView']]
    return bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])


R = json.load(open(ROOT / 'textures' / 'hkr_ramps.json'))
src = ROOT / 'export' / 'hes_kreegan_trooper_lod0.glb'      # the Trooper caste (skinned shell) before the split
for variant in R['variants']:
    doc, binary = read_glb(src)
    names = [n.get('name') for n in doc['nodes']]
    joints = doc['skins'][0]['joints']
    cara = {joints.index(names.index(f'B_{s}_Carapace')) for s in 'LR'}
    cap = {joints.index(names.index(f'B_{s}_Pauldron')) for s in 'LR'}
    for mat in doc['materials']:
        name = mat['name'].split('.')[0]
        entry = next((m for m in R['materials'] if m['base'] == name), None)
        if entry is not None:
            ti = mat['pbrMetallicRoughness']['baseColorTexture']['index']
            img = Image.open(io.BytesIO(image_bytes(doc, binary, doc['textures'][ti]['source']))).convert('RGBA')
            rgba = np.asarray(img, np.float32) / 255; base = lin(rgba[..., :3])
            mk = Image.open(ROOT / 'textures' / entry['mask']).convert('RGBA')
            mask = np.stack([np.asarray(ch.resize(img.size, Image.BILINEAR), np.float32) / 255 for ch in mk.split()], -1)
            lum = base @ W; out = base.copy()
            for c, reg in enumerate(entry['ramps'][variant]):
                lo, hi = reg['range']
                out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
            im = Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + 0.5).astype(np.uint8))
            im.save(ROOT / 'work' / f'tier_{variant}_{name}.png')
            buf = io.BytesIO(); im.save(buf, 'PNG'); binary += b'\0' * (-len(binary) % 4)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary += buf.getvalue()
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{name}_{variant}'})
            doc['textures'].append(dict(doc['textures'][ti], source=len(doc['images']) - 1))
            mat['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures']) - 1
        if name in ('HKR_Glow', 'Rifle_Glow'):
            mat['emissiveFactor'] = list(GLOW[variant]); mat.setdefault('pbrMetallicRoughness', {})['baseColorFactor'] = [*GLOW[variant], 1.0]
    drop = cara if variant != 'hkr_b' else cap      # A and C: no carapace; B: the carapace replaces the ivory cap
    if True:
        for mesh in doc['meshes']:
            for p in mesh['primitives']:
                mname = doc['materials'][p['material']]['name']
                if not mname.startswith('HKR_'):
                    continue
                J = acc(doc, binary, p['attributes']['JOINTS_0']); Wt = acc(doc, binary, p['attributes']['WEIGHTS_0']).astype(np.float32)
                if doc['accessors'][p['attributes']['WEIGHTS_0']].get('normalized'): Wt = Wt / 255.0
                on = np.zeros(len(J), bool)
                for c in drop: on |= ((J == c) & (Wt > 0.999)).any(1)
                idx = acc(doc, binary, p['indices']).reshape(-1, 3)
                keep = ~on[idx].all(1)
                if keep.all(): continue
                newi = idx[keep].astype(np.uint32).ravel()
                binary += b'\0' * (-len(binary) % 4)
                doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': newi.nbytes, 'target': 34963}); binary += newi.tobytes()
                doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5125, 'count': int(newi.size), 'type': 'SCALAR'})
                p['indices'] = len(doc['accessors']) - 1
    for a in doc['animations']:
        if a['name'].startswith('Carbine_'): a['name'] = a['name'][len('Carbine_'):]
    out = ROOT / 'review' / 'viewer' / f'hes_kreegan_{variant[-1]}.glb'
    write_glb(out, doc, binary)
    print('VIEWER', out.name, round(out.stat().st_size / 1e6, 1), 'MB')
