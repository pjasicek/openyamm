#!/usr/bin/env python3
"""Review viewer for the texture pass: each tier of each given runtime GLB with its own region ramps baked into its
base-colour atlas (as the engine applies them), LOD/shadow meshes and variant mappings dropped. Clips and native
anchors come from the reduction project's Cast v2 viewer (the installed motion).
Usage: texpass_viewer.py <out dir> <revision> <glb> <tag> <label> [<glb> <tag> <label> ...]
Model ids are <tag>_<tier>, e.g. before_a / after_a.
"""
import copy
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as R  # noqa: E402

TEMPLATE = P.parent / 'mm8_m500_reduce_claude/review/viewer_cast/manifest.json'
# Page and script of the sibling Troll texture pass viewer (the MM8 projects' own viewer pages are not kept).
PAGE = P.parent / 'mm8_m480_texpass_claude/review/viewer'
RENAMES = [('Troll texture pass: MM8 Troll Peasant (mm8_m480) / MM7 Troll (mm7_m461) (mm8_m480_texpass_claude)',
            'Water Elemental texture pass: MM8 Water Elemental (mm8_m500) / MM7 Water Elemental (mm7_m210)'),
           ('Troll texture pass review', 'Water Elemental texture pass review'), ('Troll texpass', 'Water texpass'),
           ('mm8:m480-texpass', 'mm8:m500-texpass'), ('mm8_m480_texpass_claude', 'mm8_m500_claude')]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)


def srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def ramp(colors, t):
    c = np.array(colors, np.float32)
    x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2)
    f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def image(doc, binary, texture):
    view = doc['bufferViews'][doc['images'][doc['textures'][texture]['source']]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[start:start + view['byteLength']])))


def tier_glb(src, srcbin, material_index, out_path, name):
    doc, binary = copy.deepcopy(src), bytearray(srcbin)
    node = next(n for n in doc['nodes'] if n.get('name') == 'Body')
    mesh = doc['meshes'][node['mesh']]
    mesh.pop('extras', None)
    doc['meshes'] = [mesh]
    node['mesh'] = 0
    for p in mesh['primitives']:
        p.pop('extensions', None)
        p['material'] = material_index
    doc.pop('extensions', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
    m = doc['materials'][material_index]
    info = m['pbrMetallicRoughness']['baseColorTexture']
    base = image(doc, binary, info['index']).convert('RGB')
    linear = R.srgb_to_linear(np.asarray(base, np.float32) / 255)
    lum = linear @ W
    mask = np.stack([np.asarray(ch.resize(base.size, Image.BILINEAR), np.float32) / 255 for ch in
                     image(doc, binary, m['extras']['openyamm_region_mask']['index']).convert('RGBA').split()], -1)
    out = linear.copy()
    for c, region in enumerate(m['extras']['openyamm_region_ramps']):
        lo, hi = region['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(region['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    buf = io.BytesIO()
    Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary += buf.getvalue()
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    doc['textures'].append(dict(doc['textures'][info['index']], source=len(doc['images']) - 1))
    info['index'] = len(doc['textures']) - 1
    R.write_glb(out_path, doc, bytes(binary))
    return sum(doc['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives'])


def main():
    out_dir, revision = Path(sys.argv[1]), sys.argv[2]
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ('index.html', 'review.js'):
        text = (PAGE / name).read_text()
        for old, new in RENAMES:
            text = text.replace(old, new)
        (out_dir / name).write_text(text)
    models = []
    args = sys.argv[3:]
    for glb, tag, label in zip(args[0::3], args[1::3], args[2::3]):
        src, srcbin = R.read_glb(Path(glb))
        tiers = [(i, m['name'][-1].lower()) for i, m in enumerate(src['materials']) if m['name'][-2] == '_']
        for index, tier in tiers:
            name = f'm500_{tag}_{tier}.glb'
            tris = tier_glb(src, srcbin, index, out_dir / name, f'{tag}_{tier}')
            digest = hashlib.sha256((out_dir / name).read_bytes()).hexdigest()
            models.append({'id': f'{tag}_{tier}', 'label': f'{label} · tier {tier.upper()} · {tris:,} tris',
                           'url': f'{name}?v={digest[:12]}', 'sha256': digest, 'revision': revision})
            print('VIEWER', name, tris)
    manifest = json.loads(TEMPLATE.read_text())
    pick = models[-1]
    manifest.update(revision=revision, models=models, model=pick['url'], model_sha256=pick['sha256'],
                    default_model=pick['id'], feedback='feedback/user_feedback.json')
    (out_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
