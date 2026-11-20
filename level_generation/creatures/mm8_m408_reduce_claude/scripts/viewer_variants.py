#!/usr/bin/env python3
"""Review-viewer GLBs for the reduction: three.js has no region ramps, so each tier is baked into the base colour with
the engine rule of mm8_m408_claude/scripts/viewer_tiers.py (ramps and mask from ../mm8_m408_claude/textures).
Usage: viewer_variants.py <glb> <tag> [tier,...] -> review/viewer/mm8_m408_<tier>_<tag>.glb; then refreshes the
sha256/url of every model listed in review/viewer/manifest.json."""
import hashlib, io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]; TEX = HERE.parent / 'mm8_m408_claude' / 'textures'
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


src, tag = Path(sys.argv[1]), sys.argv[2]
R = json.load(open(TEX / 'm408_ramps.json'))
tiers = sys.argv[3].split(',') if len(sys.argv) > 3 else R['variants']
entry = next(m for m in R['materials'] if m['base'] == 'Couatl_A')
image = Image.open(TEX / 'm408_basecolor.png').convert('RGBA')
base = lin(np.asarray(image, np.float32)[..., :3] / 255)
mask = np.stack([np.asarray(ch.resize(image.size, Image.BILINEAR), np.float32) / 255
                 for ch in Image.open(TEX / entry['mask']).convert('RGBA').split()], -1)
lum = base @ W
for variant in tiers:
    doc, binary = read_glb(src)
    out = base.copy()
    for c, reg in enumerate(entry['ramps'][variant]):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    buf = io.BytesIO(); Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary += buf.getvalue()
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'Couatl_{variant}'})
    for mat in doc['materials']:
        info = mat['pbrMetallicRoughness']['baseColorTexture']
        doc['textures'].append(dict(doc['textures'][info['index']], source=len(doc['images']) - 1))
        info['index'] = len(doc['textures']) - 1
    doc.get('extensionsUsed', []).count('KHR_materials_variants') and doc['extensionsUsed'].remove('KHR_materials_variants')
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    for m in doc['meshes']:
        for p in m['primitives']:
            p.pop('extensions', None)
    write_glb(HERE / 'review' / 'viewer' / f'mm8_m408_{variant}_{tag}.glb', doc, binary)
    print('VIEWER', f'mm8_m408_{variant}_{tag}.glb')

manifest_path = HERE / 'review' / 'viewer' / 'manifest.json'
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    for model in manifest['models']:
        path = HERE / 'review' / 'viewer' / model['url'].split('?')[0]
        if path.exists():
            model['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            model['url'] = path.name + '?v=' + model['sha256'][:12]
    manifest['model_sha256'] = manifest['models'][0]['sha256']
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
