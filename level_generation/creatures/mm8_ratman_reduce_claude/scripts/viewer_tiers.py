#!/usr/bin/env python3
"""Browser review GLBs for the three Ratman tiers: the engine's trouser ramps (mm8_m448_claude/textures/ratman_ramps.json)
baked into the GLB's own merged head atlas (base colour and region mask embedded in the file), LOD/shadow meshes
dropped so only full detail renders. Usage: [VIEWER_DIR=review/viewer_neckfix] viewer_tiers.py <glb> <tag> ... -> <dir>/mm8_ratman_<tier>_<tag>.glb,
then manifest.json lists installed and reduced side by side."""
import copy, hashlib, io, json, os, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]; ROOT = HERE.parent / 'mm8_m448_claude'
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


def image(doc, binary, name):
    im = next(i for i in doc['images'] if name in i['name']); v = doc['bufferViews'][im['bufferView']]
    return Image.open(io.BytesIO(bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])))


R = json.load(open(ROOT / 'textures' / 'ratman_ramps.json')); entry = R['materials'][0]
OUT = HERE / os.environ.get('VIEWER_DIR', 'review/viewer'); OUT.mkdir(parents=True, exist_ok=True)
LABELS = {'ratman_a': 'Ratman (green)', 'ratman_b': 'Wererat (blue)', 'ratman_c': 'Greater Wererat (maroon)'}
models = []
for glb, tag in zip(sys.argv[1::2], sys.argv[2::2]):
    src, srcbin = read_glb(Path(glb))
    base = image(src, srcbin, 'basecolor').convert('RGBA'); rgba = np.asarray(base, np.float32) / 255
    mask = np.stack([np.asarray(ch.resize(base.size, Image.BILINEAR), np.float32) / 255
                     for ch in image(src, srcbin, 'region_mask').convert('RGBA').split()], -1)
    lb = lin(rgba[..., :3]); lum = lb @ W
    tris = 0
    for variant in R['variants']:
        doc, binary = copy.deepcopy(src), bytearray(srcbin)
        node = next(n for n in doc['nodes'] if n.get('name') == 'Ratman')
        mesh = doc['meshes'][node['mesh']]; mesh.pop('extras', None)
        for n in doc['nodes']:
            n.pop('mesh', None) if n is not node else None
        doc['meshes'] = [mesh]; node['mesh'] = 0
        tris = sum(doc['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives'])
        out = lb.copy()
        for c, reg in enumerate(entry['ramps'][variant]):
            lo, hi = reg['range']
            out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
        buf = io.BytesIO(); Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + 0.5).astype(np.uint8)).save(buf, 'PNG')
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
        binary += buf.getvalue()
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'Ratman_{variant}'})
        for mat in doc['materials']:
            info = mat['pbrMetallicRoughness']['baseColorTexture']
            doc['textures'].append(dict(doc['textures'][info['index']], source=len(doc['images']) - 1))
            info['index'] = len(doc['textures']) - 1
        name = f'mm8_{variant}_{tag}.glb'; write_glb(OUT / name, doc, binary)
        digest = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
        models.append({'id': f'{variant}_{tag}', 'label': f"{LABELS[variant]} · {'installed' if tag == 'r100' else 'reduced, head, shoulder and neck fix' if 'nf' in tag else 'reduced, head and shoulder fix' if 'fix' in tag else 'reduced'} · {tris:,} tris",
                       'url': f'{name}?v={digest[:12]}', 'sha256': digest, 'revision': os.environ.get('VIEWER_REVISION', 'reduce-2-headfix')})
        print('VIEWER', name, tris)
models.sort(key=lambda m: m['id'])
m = json.loads((ROOT / 'review/viewer/manifest.json').read_text())
m.update(revision=os.environ.get('VIEWER_REVISION', 'reduce-2-headfix'), models=models, issues=[], feedback='../feedback/user_feedback.json')
m = json.loads(json.dumps(m).replace('"../../source/', '"../../../mm8_m448_claude/source/'))
pick = next(x for x in models if x['id'] != models[0]['id'] and x['id'].startswith('ratman_a')) if len(models) > 1 else models[0]
m.update(model=pick['url'], model_sha256=pick['sha256'], default_model=pick['id'])
(OUT / 'manifest.json').write_text(json.dumps(m, indent=2) + '\n')
