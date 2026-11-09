#!/usr/bin/env python3
"""(Copied from ../mm9_skeletonwarrior_claude; reduction review: textures from that project; Usage: viewer_tiers.py <glb> <suffix>
-> review/viewer/<variant>_<suffix>.glb.)
Review-viewer GLBs (from mm9_dagrell_claude): three.js has no region ramps, so the Warrior tier's ramps are baked into its base
colours with the engine rule and written into a copy of the delivered GLB; the Master tier is the paint itself (no ramps).
The scimitar keeps its material. Writes review/viewer/skelwar_b.glb, skelwar_c.glb."""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT

TX = HERE.parent / 'mm9_skeletonwarrior_claude' / 'textures'
R = json.load(open(TX / 'skelwar_ramps.json'))
SOURCES = {'SkelWar': 'skelwar_basecolor_final.png', 'SkelWarHead': 'skelwar_head_basecolor_final.png'}
GLB = Path(sys.argv[1]); SUFFIX = sys.argv[2]
VIEW = HERE / 'review' / 'viewer'


def read_glb(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode()
    enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc
                     + struct.pack('<II', len(binary), 0x004e4942) + binary)


baked = {}
for entry in R['materials']:
    base = np.asarray(Image.open(TX / SOURCES[entry['base']]).convert('RGB'), np.float64) / 255
    # per channel: resizing an RGBA image premultiplies by alpha (the mouth channel), zeroing the other regions
    mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                     for ch in Image.open(TX / entry['mask']).convert('RGBA').split()], -1)
    for variant in R['variants']:
        if variant == 'skelwar_c':
            continue
        out = TT.apply(base, mask, entry['ramps'][variant])
        img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        baked[(variant, entry['prefix'])] = buf.getvalue()
for variant in R['variants']:
    doc, binary = read_glb(GLB)
    suffix = variant.split('_')[1].upper()
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            mname = doc['materials'][prim['material']]['name']
            if mname == 'Scimitar':
                continue
            prefix = mname.rsplit('_', 1)[0]
            prim['material'] = names[f'{prefix}_{suffix}']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    for (v, prefix), data in baked.items():
        if v != variant:
            continue
        mat = doc['materials'][names[f'{prefix}_{suffix}']]
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary += data
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                              'name': f'{prefix}_{variant}'})
        doc['textures'].append({'source': len(doc['images']) - 1,
                                'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
                                .get('sampler', 0)})
        mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    if 'extensionsUsed' in doc:
        doc['extensionsUsed'] = [e for e in doc['extensionsUsed'] if e != 'KHR_materials_variants']
        if not doc['extensionsUsed']:
            doc.pop('extensionsUsed')
    VIEW.mkdir(parents=True, exist_ok=True); out = VIEW / f'{variant}_{SUFFIX}.glb'
    write_glb(out, doc, binary)
    print('viewer', out.name)
