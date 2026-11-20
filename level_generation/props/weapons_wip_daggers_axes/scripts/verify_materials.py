"""Inspect embedded PBR images in every owned export and inventory unique texture payloads."""
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from link_static_model_lods import read_glb

owned = json.loads((P / 'ownership.json').read_text())
models, unique = {}, {}
for entry in owned:
    icon = entry['icon']
    doc, binary = read_glb(P / 'work/exports' / f'w02_{icon}_export.glb')
    images = []
    for source in doc['images']:
        view = doc['bufferViews'][source['bufferView']]
        start = view.get('byteOffset', 0)
        payload = binary[start:start + view['byteLength']]
        im = Image.open(io.BytesIO(payload)).convert('RGB')
        pixels = np.asarray(im)
        digest = hashlib.sha256(payload).hexdigest()
        images.append(pixels)
        unique[digest] = {'size': list(im.size), 'png_bytes': len(payload)}
    def texture(index):
        return images[doc['textures'][index]['source']]
    materials = []
    for mat in doc['materials']:
        pbr = mat['pbrMetallicRoughness']
        if 'baseColorTexture' not in pbr:
            assert mat['name'].startswith('jewel_')
            assert pbr['metallicFactor'] == 0 and .2 <= pbr['roughnessFactor'] <= .3
            assert all(.01 <= v <= .9 for v in pbr['baseColorFactor'][:3])
            materials.append({'name': mat['name'], 'untextured_faceted_dielectric': True,
                              'metallic': 0, 'roughness': pbr['roughnessFactor']})
            continue
        base = texture(pbr['baseColorTexture']['index'])
        assert base.min() >= 30 and base.max() <= 243, (icon, 'basecolor range')
        if 'metallicRoughnessTexture' not in pbr:
            assert mat['name'] == 'carved stone'
            assert pbr['metallicFactor'] == 0 and .8 <= pbr['roughnessFactor'] <= .9
            materials.append({'name': mat['name'], 'metallic': 0,
                              'roughness': pbr['roughnessFactor'], 'texture_size': list(base.shape[:2])})
            continue
        mr = texture(pbr['metallicRoughnessTexture']['index'])
        metal = np.unique(mr[:, :, 2]).tolist()
        rough = np.unique(mr[:, :, 1]).tolist()
        assert set(metal) <= {0, 255}, (icon, 'fractional metallic', metal)
        assert min(rough) >= 45 and max(rough) <= 230, (icon, 'roughness range', rough)
        normal = texture(mat['normalTexture']['index'])
        assert normal[:, :, 2].min() >= 128, (icon, 'normal below tangent hemisphere')
        materials.append({'name': mat['name'], 'metallic_values': metal,
                          'roughness_values': rough, 'basecolor_range': [int(base.min()), int(base.max())]})
    models[icon] = materials
assert len(models) == 69
report = {'checked_icons': len(models), 'materials': models, 'unique_textures': unique,
          'unique_texture_count': len(unique),
          'unique_png_bytes': sum(v['png_bytes'] for v in unique.values()),
          'unique_texture_pixels': sum(v['size'][0] * v['size'][1] for v in unique.values())}
(P / 'review/material_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print('PBR PASS', len(models), 'icons;', len(unique), 'unique embedded PNGs')
