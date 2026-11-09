#!/usr/bin/env python3
"""Bake native palette ramps for the three.js review; runtime tiers share the original four maps."""
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


R = json.load(open(ROOT / 'textures/m500_ramps.json'))
for variant in R['variants']:
    doc, binary = read_glb(ROOT / 'export/mm8_m500_runtime_lod0.glb')
    for M in R['materials']:
        material = next(m for m in doc['materials'] if m['name'] == M['base'])
        material.setdefault('extensions',{})['KHR_materials_specular']={'specularFactor':.33}
        if 'KHR_materials_specular' not in doc.setdefault('extensionsUsed',[]):doc['extensionsUsed'].append('KHR_materials_specular')
        img = doc['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
        bview = doc['bufferViews'][doc['images'][img]['bufferView']]; start = bview.get('byteOffset',0)
        base = lin(np.asarray(Image.open(io.BytesIO(binary[start:start+bview['byteLength']])).convert('RGB'),np.float32)/255)
        mask = np.stack([np.asarray(ch.resize(base.shape[1::-1],Image.Resampling.BILINEAR),np.float32)/255 for ch in Image.open(ROOT/'textures'/M['mask']).convert('RGBA').split()],-1)
        lum=base@W;out=base.copy()
        for c,reg in enumerate(M['ramps'][variant]):
            lo,hi=reg['range'];out=out*(1-mask[...,c:c+1])+ramp(reg['colors'],(lum-lo)/(hi-lo))*mask[...,c:c+1]
        buf=io.BytesIO();Image.fromarray((np.clip(srgb(out),0,1)*255+.5).astype(np.uint8)).save(buf,'PNG')
        binary+=b'\0'*(-len(binary)%4);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(buf.getvalue())});binary+=buf.getvalue()
        doc['images'][img]={'bufferView':len(doc['bufferViews'])-1,'mimeType':'image/png','name':variant+'_'+M['base']}
    write_glb(ROOT/'review/viewer'/f'mm8_m500_{variant[-1]}.glb',doc,binary)
    print('VIEWER',variant)
