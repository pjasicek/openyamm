#!/usr/bin/env python3
"""(Banshee reduction copy: Usage viewer_tiers.py <glb> <suffix>, run from mm9_banshee_claude, writes into the reduce project's review/viewer/banshee_<tier>_<suffix>.glb.)
Review-viewer GLBs: three.js has no region ramps, so each tier's ramps are baked into its colour, keeping the see-through alpha; KHR_materials_specular 0 as the game's specular off. Run from the project."""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, '../claude_shared')
import tier_textures as TT, region_variants as RV
OUT = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
R = json.load(open('textures/banshee_ramps.json'))
base_rgba = np.asarray(Image.open('textures/banshee_basecolor_rgba.png').convert('RGBA'), np.float64) / 255
mask = np.stack([np.asarray(c.resize((2048, 2048), Image.BILINEAR), np.float64) / 255 for c in Image.open('textures/banshee_region_mask.png').convert('RGBA').split()], -1)
hair_rgba = np.asarray(Image.open('textures/banshee_hair_rgba.png').convert('RGBA'), np.float64) / 255
hm = np.zeros(hair_rgba.shape[:2] + (4,)); hm[..., 0] = 1


def add(doc, binary, arr, name):
    buf = io.BytesIO(); Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA').save(buf, 'PNG'); data = buf.getvalue()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    doc['textures'].append({'source': len(doc['images']) - 1})
    return len(doc['textures']) - 1


for k, sfx in (('banshee_a', 'A'), ('banshee_b', 'B'), ('banshee_c', 'C')):
    doc, binary = RV.read_glb(Path(sys.argv[1]))
    binary = bytearray(binary)
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            pre = doc['materials'][p['material']]['name'].rsplit('_', 1)[0]
            p['material'] = names[f'{pre}_{sfx}']
            p.get('extensions', {}).pop('KHR_materials_variants', None)
            if not p.get('extensions'):
                p.pop('extensions', None)
    for role, pres in (('body', ('Banshee', 'BansheeArmL', 'BansheeArmR')), ('skirt', ('BansheeSkirt',))):
        if k in R[role]:
            out = TT.apply(base_rgba[..., :3], mask, R[role][k])
            t = add(doc, binary, np.dstack([out, base_rgba[..., 3]]), f'tier_{role}_{sfx}')
            for pre in pres:
                doc['materials'][names[f'{pre}_{sfx}']]['pbrMetallicRoughness']['baseColorTexture'] = {'index': t}
                doc['materials'][names[f'{pre}_{sfx}']].get('extras', {}).pop('openyamm_region_mask', None)
    out = TT.apply(hair_rgba[..., :3], hm, R['hair'][k])
    t = add(doc, binary, np.dstack([out, hair_rgba[..., 3]]), f'tier_hair_{sfx}')
    for pre in ('BansheeHairL', 'BansheeHairR'):
        doc['materials'][names[f'{pre}_{sfx}']]['pbrMetallicRoughness']['baseColorTexture'] = {'index': t}
        doc['materials'][names[f'{pre}_{sfx}']].get('extras', {}).pop('openyamm_region_mask', None)
    for m in doc['materials']:
        m.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc['extensionsUsed'] = sorted((set(doc.get('extensionsUsed', [])) | {'KHR_materials_specular'}) - {'KHR_materials_variants'})
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    RV.write_glb(Path(OUT) / f'{k}_{sys.argv[2]}.glb', doc, binary)
    print('viewer', k)
