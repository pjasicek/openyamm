#!/usr/bin/env python3
"""Review-viewer GLBs: three.js has no region ramps, so each tier is baked into the base colour with the engine rule
(per region: t = linear luminance normalised over the region's range, colour = mix(colour, ramp(t), mask channel);
 textures/fmp_ramps.json) for the two materials (PeasantF2_A body set, PeasantF2Head_A head set), written to
review/viewer/mm6_bar1_<tier>.glb from export/mm6_fmp_runtime_lod0.glb.
The full baked tier textures are also saved as work/tier_<tier>_<material>.png for previews."""
import io, json, struct
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


R = json.load(open(ROOT / 'textures' / 'fmp_ramps.json'))
SOURCES = {'PeasantF2_A': 'fmp_body_basecolor_1k.png', 'PeasantF2Head_A': 'fmp_head_basecolor_1k.png'}


def load(material):
    image = Image.open(ROOT / 'textures' / SOURCES[material]).convert('RGBA')
    rgba = np.asarray(image, np.float32) / 255
    entry = next(m for m in R['materials'] if m['base'] == material)
    # per channel: resizing an RGBA image premultiplies by alpha, and unused channels are 0
    mask = np.stack([np.asarray(ch.resize(image.size, Image.BILINEAR), np.float32) / 255
                     for ch in Image.open(ROOT / 'textures' / entry['mask']).convert('RGBA').split()], -1)
    return lin(rgba[..., :3]), rgba[..., 3:4], mask, entry


cache = {}
for variant in R['variants']:
    doc, binary = read_glb(ROOT / 'export' / 'mm6_fmp_runtime_lod0.glb')
    for mat in doc['materials']:
        name = mat['name'].split('.')[0]
        if name not in SOURCES:
            continue
        base, alpha, mask, entry = cache.setdefault(name, load(name))
        lum = base @ W; out = base.copy()
        for c, reg in enumerate(entry['ramps'][variant]):
            lo, hi = reg['range']
            out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
        pixels = np.clip(srgb(out), 0, 1)
        im = Image.fromarray((pixels * 255 + 0.5).astype(np.uint8)); im.save(ROOT / 'work' / f'tier_{variant}_{name}.png')
        buf = io.BytesIO(); im.save(buf, 'PNG')
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
        binary += buf.getvalue()
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                              'name': f'{name}_{variant}'})
        info = mat['pbrMetallicRoughness']['baseColorTexture']
        doc['textures'].append(dict(doc['textures'][info['index']], source=len(doc['images']) - 1))
        info['index'] = len(doc['textures']) - 1
    write_glb(ROOT / 'review' / 'viewer' / f'mm6_{variant}.glb', doc, binary)
    print('VIEWER', f'mm6_{variant}.glb')
