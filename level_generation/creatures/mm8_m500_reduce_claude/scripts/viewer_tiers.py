#!/usr/bin/env python3
"""Browser review GLBs for the three Water Elemental tiers: each tier material's own region ramps (material extras,
as the engine applies them) baked into the GLB's own base-colour atlas with its own region mask; LOD/shadow meshes and
the variant mappings dropped so only full detail renders. manifest.json lists installed and reduced side by side,
clips and native anchors from the production viewer (mm8_m500_claude/review/viewer/manifest.json), with sha256 and
?v= rewritten on every build. Usage: [VIEWER_DIR=review/viewer] [VIEWER_REVISION=reduce-1] viewer_tiers.py <glb> <tag> ..."""
import copy, hashlib, io, json, os, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]; PROD = HERE.parent / 'mm8_m500_claude'
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
OUT = HERE / os.environ.get('VIEWER_DIR', 'review/viewer'); OUT.mkdir(parents=True, exist_ok=True)
REV = os.environ.get('VIEWER_REVISION', 'reduce-1')
LABELS = {'A': 'Water Elemental A', 'B': 'Water Elemental B', 'C': 'Water Elemental C'}


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


def image(doc, binary, tex):
    v = doc['bufferViews'][doc['images'][doc['textures'][tex]['source']]['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))


models = []
for glb, tag in zip(sys.argv[1::2], sys.argv[2::2]):
    src, srcbin = read_glb(Path(glb))
    for mi, mat in enumerate(src['materials']):
        tier = mat['name'][-1]
        doc, binary = copy.deepcopy(src), bytearray(srcbin)
        node = next(n for n in doc['nodes'] if n.get('name') == 'Body')
        mesh = doc['meshes'][node['mesh']]; mesh.pop('extras', None); doc['meshes'] = [mesh]; node['mesh'] = 0
        for p in mesh['primitives']:
            p.pop('extensions', None); p['material'] = mi
        doc.pop('extensions', None); doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
        m = doc['materials'][mi]; info = m['pbrMetallicRoughness']['baseColorTexture']
        base = image(doc, binary, info['index']).convert('RGB'); lb = lin(np.asarray(base, np.float32) / 255); lum = lb @ W
        mask = np.stack([np.asarray(ch.resize(base.size, Image.BILINEAR), np.float32) / 255 for ch in
                         image(doc, binary, m['extras']['openyamm_region_mask']['index']).convert('RGBA').split()], -1)
        out = lb.copy()
        for c, reg in enumerate(m['extras']['openyamm_region_ramps']):
            lo, hi = reg['range']
            out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
        buf = io.BytesIO(); Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary += buf.getvalue()
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'water_{tier}_{tag}'})
        doc['textures'].append(dict(doc['textures'][info['index']], source=len(doc['images']) - 1)); info['index'] = len(doc['textures']) - 1
        tris = sum(doc['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives'])
        name = f'mm8_m500_{tier.lower()}_{tag}.glb'; write_glb(OUT / name, doc, binary)
        digest = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
        models.append({'id': f'water_{tier.lower()}_{tag}', 'label': f"{LABELS[tier]} · {'installed' if tag == 'r100' else 'reduced'} · {tris:,} tris",
                       'url': f'{name}?v={digest[:12]}', 'sha256': digest, 'revision': REV})
        print('VIEWER', name, tris)
models.sort(key=lambda m: m['id'])
man = json.loads((PROD / 'review/viewer/manifest.json').read_text())
pick = next(m for m in models if m['id'].startswith('water_a') and not m['id'].endswith('r100'))
man.update(revision=REV, models=models, model=pick['url'], model_sha256=pick['sha256'], default_model=pick['id'],
           feedback='feedback/user_feedback.json')
(OUT / 'manifest.json').write_text(json.dumps(man, indent=2) + '\n')
