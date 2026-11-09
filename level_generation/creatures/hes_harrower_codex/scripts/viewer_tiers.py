#!/usr/bin/env python3
"""Bake four viewer-only assemblies from the final authoring GLBs.
Three.js needs baked region ramps and explicit attachment selection; runtime exports retain shared textures.
"""
import io, json, struct, copy
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
GLOW = {'hhw_a': (1,.12,.008), 'hhw_b': (1,.46,.04), 'hhw_c': (1,.12,.008), 'hhw_boss': (1,.55,.12)}


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


R = json.load(open(ROOT / 'textures' / 'hhw_ramps.json'))
(ROOT/'review/viewer').mkdir(parents=True,exist_ok=True)
for variant in R['variants']:
    src=ROOT/'work'/('assembly_'+('vreth' if variant=='hhw_boss' else 'family')+'_lod0.glb')
    doc, binary = read_glb(src)
    names = [n.get('name') for n in doc['nodes']]
    joints = doc['skins'][0]['joints']
    trophies={joints.index(names.index('Harrower_Trophies'))}
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
            im = Image.fromarray((np.dstack([np.clip(srgb(out),0,1),rgba[...,3]])*255+.5).astype(np.uint8),'RGBA')
            im.save(ROOT / 'work' / f'tier_{variant}_{name}.png')
            buf = io.BytesIO(); im.save(buf, 'PNG'); binary += b'\0' * (-len(binary) % 4)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary += buf.getvalue()
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{name}_{variant}'})
            doc['textures'].append(dict(doc['textures'][ti], source=len(doc['images']) - 1))
            mat['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures']) - 1
        if name in ('HHW_Glow','HHW_ClothGlow','HHW_MantleGlow','Demon_Iris'):
            mat.setdefault('extensions',{})['KHR_materials_emissive_strength']={'emissiveStrength':.65 if name in ('HHW_ClothGlow','HHW_MantleGlow') else 3.5}
            if 'KHR_materials_emissive_strength' not in doc.setdefault('extensionsUsed',[]):doc['extensionsUsed'].append('KHR_materials_emissive_strength')
            mat['emissiveFactor'] = list(GLOW[variant]); mat.setdefault('pbrMetallicRoughness', {})['baseColorFactor'] = [*GLOW[variant], 1.0]
        if name.startswith('HHW_Mantle'):
            mat.setdefault('pbrMetallicRoughness',{}).setdefault('baseColorFactor',[1,1,1,1])[3]=1 if variant=='hhw_boss' else 0
            mat['alphaMode']='MASK';mat['alphaCutoff']=.5
        if name=='HHW_Cloth':mat['alphaMode']='MASK';mat['alphaCutoff']=.5
        if name.startswith(('HHW_Cloth','HHW_Mantle')):mat['doubleSided']=True
    drop = (cap if variant in ('hhw_a','hhw_b') else set()) | (trophies if variant in ('hhw_a','hhw_c') else set())
    if drop:
        for mesh in doc['meshes']:
            for p in mesh['primitives']:
                mname = doc['materials'][p['material']]['name']
                if not mname.startswith('HHW_'):
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
    doc['animations']=[a for a in doc['animations'] if a['name'].startswith('Harrower_')]
    for a in doc['animations']:a['name']=a['name'].removeprefix('Harrower_')
    doc.pop('extensions',None)
    for mesh in doc['meshes']:
        for p in mesh['primitives']:p.pop('extensions',None)
    out = ROOT / 'review' / 'viewer' / f'hes_harrower_{variant.removeprefix("hhw_")}.glb'
    import sys
    sys.path.insert(0,str(ROOT.parents[2]/'tools'))
    from merge_head_material import compact
    doc,binary=compact(doc,binary)
    write_glb(out,doc,bytearray(binary))
    print('VIEWER', out.name, round(out.stat().st_size / 1e6, 1), 'MB')
