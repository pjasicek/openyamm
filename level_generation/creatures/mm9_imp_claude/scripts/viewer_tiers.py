#!/usr/bin/env python3
"""Review-viewer GLBs: three.js has no region ramps, so each tier's ramps are baked into its base colours with the
engine rule (claude_shared/tier_textures.py) and written into a copy of the delivered export GLB (same mesh, clips and
floor pass). Usage: viewer_tiers.py -> review/viewer/<tier>.glb; also work/tier_<variant>_<material>.png."""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT

R = json.load(open(HERE / 'textures' / 'imp_ramps.json'))
SOURCES = {'Imp': 'imp_basecolor_graded.png', 'ImpHead': 'imp_head_basecolor_graded.png'}
GLB = 'mm9_imp_full.glb'
# parts only one tier wears (attachments in the game): their triangles leave the other tiers' viewer GLBs
ONLY = {'imp_a': (), 'imp_b': ('Xwrap L', 'Xwrap R'), 'imp_c': ('Xtongue',)}
PARTS = ('Xwrap L', 'Xwrap R', 'Xtongue')
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
    base = np.asarray(Image.open(HERE / 'textures' / SOURCES[entry['base']]).convert('RGB'), np.float64) / 255
    # per channel: resizing an RGBA image premultiplies by alpha (the mouth channel), zeroing the other regions
    mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                     for ch in Image.open(HERE / 'textures' / entry['mask']).convert('RGBA').split()], -1)
    for variant in R['variants']:
        out = TT.apply(base, mask, entry['ramps'][variant])
        img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
        img.save(HERE / 'work' / f'tier_{variant}_{entry["base"]}.png')
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        baked[(variant, entry['prefix'])] = buf.getvalue()
for variant in R['variants']:
    doc, binary = read_glb(HERE / 'export' / GLB)
    suffix = variant.split('_')[1].upper()
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            mname = doc['materials'][prim['material']]['name']
            if mname.startswith('TridentProps'):
                prim.get('extensions', {}).pop('KHR_materials_variants', None)
                if not prim.get('extensions'):
                    prim.pop('extensions', None)
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
    # hide the parts of the other tiers: scale their helper joint's skin to nothing by removing their triangles
    jnames = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
    hide = [jnames.index(p) for p in PARTS if p not in ONLY[variant]]
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            if not doc['materials'][prim['material']]['name'].startswith('TridentProps'):
                continue
            a = doc['accessors'][prim['attributes']['JOINTS_0']]; bv = doc['bufferViews'][a['bufferView']]
            n = {5121: 1, 5123: 2}[a['componentType']]
            st = bv.get('byteStride', 4 * n)
            dt = {1: np.uint8, 2: np.uint16}[n]
            off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            J = np.frombuffer(bytes(binary), np.uint8, a['count'] * st, off).reshape(a['count'], st)[:, :4 * n].copy().view(dt).reshape(a['count'], 4)
            W_ = doc['accessors'][prim['attributes']['WEIGHTS_0']]
            bw = doc['bufferViews'][W_['bufferView']]
            ow = bw.get('byteOffset', 0) + W_.get('byteOffset', 0)
            ww = np.frombuffer(bytes(binary), np.float32 if W_['componentType'] == 5126 else np.uint8, W_['count'] * 4, ow).reshape(W_['count'], 4).astype(np.float64)
            top = J[np.arange(len(J)), ww.argmax(1)]
            bad = np.isin(top, hide)
            ia = doc['accessors'][prim['indices']]; bi = doc['bufferViews'][ia['bufferView']]
            ti = {5123: np.uint16, 5125: np.uint32}[ia['componentType']]
            oi = bi.get('byteOffset', 0) + ia.get('byteOffset', 0)
            idx = np.frombuffer(bytes(binary), ti, ia['count'], oi).reshape(-1, 3)
            keep = idx[~bad[idx].any(1)].astype(ti).ravel()
            data = keep.tobytes()
            binary += b'\0' * (-len(binary) % 4)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
            binary += data
            doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': ia['componentType'], 'count': int(len(keep)), 'type': 'SCALAR'})
            prim['indices'] = len(doc['accessors']) - 1
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    if 'extensionsUsed' in doc:
        doc['extensionsUsed'] = [e for e in doc['extensionsUsed'] if e != 'KHR_materials_variants']
        if not doc['extensionsUsed']:
            doc.pop('extensionsUsed')
    out = VIEW / f'{variant}.glb'
    write_glb(out, doc, binary)
    print('viewer', out.name)
