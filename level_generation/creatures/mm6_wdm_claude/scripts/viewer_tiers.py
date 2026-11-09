#!/usr/bin/env python3
"""Review-viewer GLBs: three.js has no region ramps, so bake each tier into the base colour with the engine rule
(colour = mix(colour, ramp(t), mask), t = linear luminance normalised over the material's range; textures/wdm_ramps.json)
and write review/viewer/mm6_wdm_<tier>.glb from export/mm6_wdm_lod0.glb (skin, clips and sockets unchanged), per skin
material (body and grafted head)."""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
RAMPS = json.load(open(ROOT / 'textures' / 'wdm_ramps.json'))
SOURCES = {'Demon': 'wdm_basecolor_graded_1k.png', 'DemonHead': 'wdm_head_basecolor.png'}
W = np.array([0.2126, 0.7152, 0.0722], np.float32)


def load(material):
    """Linear base colour, normalised luminance t over the material's range, and the skin mask (red channel)."""
    base = np.asarray(Image.open(ROOT / 'textures' / SOURCES[material]).convert('RGB'), np.float32) / 255
    mask_file = RAMPS['materials'][material]['mask']
    mask = np.asarray(Image.open(ROOT / 'textures' / mask_file).convert('RGBA').resize(
        base.shape[1::-1], Image.BILINEAR), np.float32)[..., 0:1] / 255
    lo, hi = RAMPS['materials'][material]['range']
    L = lin(base)
    return L, np.clip((L @ W - lo) / (hi - lo), 0, 1), mask


def ramp(colors, t):
    """Same rule as the engine shader: linear interpolation between the 16 stops at t * 15."""
    c = np.array(colors, np.float32); x = t * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


cache = {}
for tier, data in RAMPS['tiers'].items():
    doc, binary = read_glb(ROOT / 'export' / 'mm6_wdm_lod0.glb')
    for mat in doc['materials']:
        name = mat['name'].split('.')[0]
        if name not in SOURCES:
            continue
        L, t, mask = cache.setdefault(name, load(name))
        out = srgb(L * (1 - mask) + ramp(data['colors'], t) * mask)
        buf = io.BytesIO(); Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(buf, 'PNG')
        img = doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
        binary += buf.getvalue()
        doc['images'][img] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                              'name': f'{name}_{tier}'}
    out_path = ROOT / 'review' / 'viewer' / f'mm6_wdm_{tier}.glb'
    write_glb(out_path, doc, binary)
    print('VIEWER', out_path.name)
