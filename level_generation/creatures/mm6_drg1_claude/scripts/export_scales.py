"""Replace only the accepted body/head images, preserving v8 burn metadata and all geometry/motion bytes."""
import copy
import io
import json
import sys
from pathlib import Path
from PIL import Image

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as rv

report = {}
for name in ['mm6_drg1_runtime_lod0.glb', 'mm6_drg1_lods.geometry.glb', 'mm6_drg1_lods.glb',
             'mm6_drg1_shadow.glb', 'mm6_drg1.glb']:
    doc, binary = rv.read_glb(P / 'work/before_scales_v9/export' / name)
    old_doc = copy.deepcopy(doc)
    replacements = {}
    for label in ['body', 'head']:
        material = next(m for m in doc['materials'] if m['name'] == 'Drake' + label.title() + '_A')
        for key, suffix in [('baseColorTexture', 'basecolor_2k'), ('normalTexture', 'normal_2k')]:
            texture = material[key] if key == 'normalTexture' else material['pbrMetallicRoughness'][key]
            image_index = doc['textures'][texture['index']]['source']
            view_index = doc['images'][image_index]['bufferView']
            view = doc['bufferViews'][view_index]
            start = view.get('byteOffset', 0)
            old = Image.open(io.BytesIO(binary[start:start + view['byteLength']]))
            image = Image.open(P / 'textures' / f'drg1_{label}_{suffix}.png').convert('RGB')
            assert image.size == old.size == (2048, 2048), (name, label, key, old.size)
            stream = io.BytesIO()
            image.save(stream, 'PNG')
            replacements[view_index] = stream.getvalue()
    assert len(replacements) == 4
    packed = bytearray()
    for index, view in enumerate(doc['bufferViews']):
        start = view.get('byteOffset', 0)
        data = replacements.get(index, binary[start:start + view['byteLength']])
        packed += b'\0' * (-len(packed) % 4)
        view['byteOffset'] = len(packed)
        view['byteLength'] = len(data)
        packed += data
    # All non-image data and all other textures, including burn maps, must remain byte-identical.
    for index, (old, new) in enumerate(zip(old_doc['bufferViews'], doc['bufferViews'])):
        if index not in replacements:
            assert binary[old.get('byteOffset', 0):][:old['byteLength']] == packed[new['byteOffset']:][:new['byteLength']]
    for key in old_doc.keys() - {'bufferViews', 'buffers'}:
        assert old_doc[key] == doc[key], (name, key)
    rv.write_glb(P / 'export' / name, doc, packed)
    check, data = rv.read_glb(P / 'export' / name)
    for index, expected in replacements.items():
        view = check['bufferViews'][index]
        assert data[view['byteOffset']:][:view['byteLength']] == expected
    report[name] = {'only_four_image_buffers_changed': True, 'all_geometry_skin_uv_animation_bytes_preserved': True,
                    'all_material_variant_lod_and_burn_metadata_preserved': True,
                    'all_other_texture_bytes_preserved': True}
(P / 'review/scales_v9/export.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
