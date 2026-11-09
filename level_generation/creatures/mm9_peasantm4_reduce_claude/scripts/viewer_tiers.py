#!/usr/bin/env python3
"""PeasantDM2 reduction copy of ../mm9_peasantdm2_claude/scripts/viewer_tiers.py (ramps, tone image and mask read in place from
that project): args <glb> <prefix> -> work/viewer_<prefix>_th_{a,b}.glb. Original docstring:
Review-viewer GLBs (after mm9_nobleman_claude/scripts/viewer_tiers.py): three.js has no region ramps, so each tier's
ramps are baked into its body base colour with the engine rule, in copies of the delivered GLB; the head keeps its
tier material (tier B has its own head image). Writes review/viewer/pdm2_a.glb, pdm2_b.glb. Args: [glb]"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
NB = HERE.parent / 'mm9_peasantdm2_claude'
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
R = json.load(open(NB / 'textures' / 'pdm2_ramps.json'))
GLB = Path(sys.argv[1]).resolve(); PREFIX = sys.argv[2]; ONLY = None
OUT = HERE / 'work'
OUT.mkdir(parents=True, exist_ok=True)
e = R['materials'][0]
base = np.asarray(Image.open(NB / 'textures' / 'pdm2_tp_basecolor_graded.png').convert('RGB'), np.float64) / 255
mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                 for ch in Image.open(NB / 'textures' / e['mask']).convert('RGBA').split()], -1)
for idx, variant in enumerate(R['variants']):
    if ONLY and variant not in ONLY:
        continue
    vm = R.get('variant_masks', {}).get(variant)
    vmask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                      for ch in Image.open(NB / 'textures' / vm).convert('RGBA').split()], -1) if vm else mask
    img = Image.fromarray((np.clip(TT.apply(base, vmask, e['ramps'][variant]), 0, 1) * 255).astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if idx in mp['variants']:
                    prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    mat = doc['materials'][names[f"{e['prefix']}_{variant.split('_')[1].upper()}"]]
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'body_{variant}'})
    doc['textures'].append({'source': len(doc['images']) - 1,
                            'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
    mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [x for x in doc.get('extensionsUsed', []) if x != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(OUT / f"viewer_{PREFIX}_th_{variant.split('_')[1]}.glb", d2, b2)
    print('viewer', variant)
