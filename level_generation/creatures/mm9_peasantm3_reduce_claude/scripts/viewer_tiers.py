#!/usr/bin/env python3
"""Review-viewer GLBs (PeasantM3 reduction; after ../mm9_peasantm3_claude/scripts/viewer_tiers.py): three.js has no region
ramps, so each tier's ramps are baked into its body base colour with the engine rule (tier_textures.apply), in copies of the
given GLB; the head keeps its tier material (tier B has its own head image). Tone image, region mask and ramps are read from the
GLB itself (as tex_extract.py), so the installed and the reduced file are baked the same way.
Usage: viewer_tiers.py <glb> <prefix> -> work/viewer_<prefix>_th_{a,b}.glb"""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT  # noqa: E402
import region_variants as RV  # noqa: E402
GLB = Path(sys.argv[1]); PREFIX = sys.argv[2]
VARIANTS = ['pm3_a', 'pm3_b']; BODY = {'pm3_a': 'PeasantM3_A', 'pm3_b': 'PeasantM3_B'}
for idx, variant in enumerate(VARIANTS):
    doc, binary = RV.read_glb(GLB); binary = bytearray(binary)
    assert [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']] == VARIANTS

    def image(i):
        im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
        return Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    mat = doc['materials'][names[BODY[variant]]]
    tone = np.asarray(image(doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB'),
                      np.float64) / 255
    mimg = image(doc['textures'][mat['extras']['openyamm_region_mask']['index']]['source']).convert('RGBA')
    mask = np.stack([np.asarray(ch.resize((tone.shape[1], tone.shape[0]), Image.BILINEAR), np.float64) / 255
                     for ch in mimg.split()], -1)
    img = Image.fromarray((np.clip(TT.apply(tone, mask, mat['extras']['openyamm_region_ramps']), 0, 1) * 255).astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if idx in mp['variants']:
                    prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
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
    d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(HERE / 'work' / f"viewer_{PREFIX}_th_{variant.split('_')[1]}.glb", d2, b2)
    print('viewer', variant)
