#!/usr/bin/env python3
"""Review-viewer GLBs per colour variant (three.js has neither KHR_materials_variants selection nor region ramps), as
mm8_m480_reduce_claude/scripts/viewer_variants.py: each primitive takes its variant material and the region ramps are
baked into its base colour with the engine rule. Works for the MM8 and the MM7 Troll.
Usage: viewer_variants.py <glb> <tag> -> review/viewer/<variant>_<tag>.glb"""
import copy
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def image(doc, binary, tex):
    v = doc['bufferViews'][doc['images'][doc['textures'][tex]['source']]['bufferView']]
    s = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[s:s + v['byteLength']])))


def ramp(colors, t):
    c = np.array(colors, np.float32)
    x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2)
    f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def bake(base_rgb, mask_img, ramps):
    base = lin(np.asarray(base_rgb, np.float32) / 255)
    m4 = np.asarray(mask_img.convert('RGBA'))
    mask = np.stack([np.asarray(Image.fromarray(m4[..., k]).resize(base.shape[1::-1], Image.Resampling.BILINEAR))
                     for k in range(4)], -1).astype(np.float32) / 255
    lum = base @ W
    out = base.copy()
    for c, reg in enumerate(ramps):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    return (np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)


def main():
    src, tag = Path(sys.argv[1]), sys.argv[2]
    base_doc, base_bin = read_glb(src)
    if 'KHR_materials_variants' not in base_doc.get('extensions', {}):
        # one look, no variants (zcat): the GLB as it is, model id base_<tag>
        out_path = HERE / 'review/viewer' / f'base_{tag}.glb'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        write_glb(out_path, base_doc, bytes(base_bin))
        print('VIEWER', out_path.name)
        return
    for vi, variant in enumerate(v['name'] for v in base_doc['extensions']['KHR_materials_variants']['variants']):
        doc = copy.deepcopy(base_doc)
        binary = bytearray(base_bin)
        for m in doc['meshes']:
            for p in m['primitives']:
                ext = p.pop('extensions', {}).get('KHR_materials_variants')
                if ext:
                    p['material'] = next(x['material'] for x in ext['mappings'] if vi in x['variants'])
        doc.pop('extensions')
        doc['extensionsUsed'] = [e for e in doc['extensionsUsed'] if e != 'KHR_materials_variants']
        for mi, mat in enumerate(doc['materials']):
            extras = mat.get('extras', {})
            used = any(p['material'] == mi for m in doc['meshes'] for p in m['primitives'])
            if 'openyamm_region_ramps' not in extras or not used:
                continue
            tex = mat['pbrMetallicRoughness']['baseColorTexture']['index']
            out = bake(image(doc, binary, tex).convert('RGB'), image(doc, binary, extras['openyamm_region_mask']['index']),
                       extras['openyamm_region_ramps'])
            buf = io.BytesIO()
            Image.fromarray(out).save(buf, 'PNG')
            binary.extend(b'\0' * (-len(binary) % 4))
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
            binary.extend(buf.getvalue())
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                                  'name': f'{variant}_baked'})
            sampler = {'sampler': doc['textures'][tex]['sampler']} if 'sampler' in doc['textures'][tex] else {}
            doc['textures'].append({'source': len(doc['images']) - 1, **sampler})
            mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        out_path = HERE / 'review/viewer' / f'{variant}_{tag}.glb'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        write_glb(out_path, doc, bytes(binary))
        print('VIEWER', out_path.name)


if __name__ == '__main__':
    main()
