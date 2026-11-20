#!/usr/bin/env python3
"""(Ghost reduction copy: usage viewer_tiers.py <glb> <suffix>, run from mm9_ghost_claude; writes the reduce project's
review/viewer/ghost_<tier>_<suffix>.glb.) Review-viewer GLBs: three.js has no region ramps, so each tier's ramps are baked into its colour, keeping the see-through alpha; KHR_materials_specular 0 as the game's specular off. Run from the project."""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, '../claude_shared')
import tier_textures as TT, region_variants as RV
OUT = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
R = json.load(open('textures/ghost_ramps.json'))
base_rgba = np.asarray(Image.open('textures/ghost_basecolor_rgba.png').convert('RGBA'), np.float64) / 255
mask = np.stack([np.asarray(c.resize((2048, 2048), Image.BILINEAR), np.float64) / 255 for c in Image.open('textures/ghost_region_mask.png').convert('RGBA').split()], -1)
for k, sfx in (('ghost_a', 'A'), ('ghost_b', 'B'), ('ghost_c', 'C')):
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
    if k in R:
        out = TT.apply(base_rgba[..., :3], mask, R[k])
        rgba = np.dstack([np.clip(out, 0, 1), base_rgba[..., 3]])
        buf = io.BytesIO(); Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(buf, 'PNG'); data = buf.getvalue()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary += data
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': 'tier_' + sfx})
        doc['textures'].append({'source': len(doc['images']) - 1})
        for pre in ('Ghost', 'GhostArmL', 'GhostArmR'):
            doc['materials'][names[f'{pre}_{sfx}']]['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
            doc['materials'][names[f'{pre}_{sfx}']].get('extras', {}).pop('openyamm_region_mask', None)
    for m in doc['materials']:
        m.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
    doc['extensionsUsed'] = sorted((set(doc.get('extensionsUsed', [])) | {'KHR_materials_specular'}) - {'KHR_materials_variants'})
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    RV.write_glb(OUT / f'{k}_{sys.argv[2]}.glb', doc, binary)
    print('viewer', k)
