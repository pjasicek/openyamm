"""Tune existing demon material factors while preserving every geometry and animation byte."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct

import bpy

stage = Path(__file__).resolve().parent
repo = stage.parents[3]
record_dir = repo / 'output/creature_3d_rendering_review/material_tuning'
record_dir.mkdir(parents=True, exist_ok=True)
factors = {'Demon_Meshy_Body': {'metallicFactor': 0.0},
           'Demon_Red_Iris': {'roughnessFactor': 0.22},
           'Demon_Black_Pupil': {'roughnessFactor': 0.18}}

source = stage / 'mm6_demon_textured.glb'
data = source.read_bytes()
json_length = struct.unpack_from('<I', data, 12)[0]
document = json.loads(data[20:20+json_length])
original = copy.deepcopy(document)
for name, values in factors.items():
    material = next(material for material in document['materials'] if material['name'] == name)
    material['pbrMetallicRoughness'].update(values)
# Factors alone change; texture, geometry, bind, morph and animation data are untouched.
assert {key: value for key, value in document.items() if key != 'materials'} == {
    key: value for key, value in original.items() if key != 'materials'}
encoded = json.dumps(document, separators=(',', ':')).encode()
encoded += b' ' * (-len(encoded) % 4)
binary_chunk = data[20+json_length:]
result = struct.pack('<III', 0x46546c67, 2, 20+len(encoded)+len(binary_chunk))
result += struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + binary_chunk
assert result[20+len(encoded):] == binary_chunk
backup = record_dir / source.name
if not backup.exists():
    shutil.copy2(source, backup)
source.write_bytes(result)

for name in ('authored_checkpoint.blend', 'mm6_demon_textured.blend'):
    path = stage / name
    if not (record_dir / name).exists():
        shutil.copy2(path, record_dir / name)
    bpy.ops.wm.open_mainfile(filepath=str(path))
    changed = set()
    for material in bpy.data.materials:
        for prefix, values in factors.items():
            if material.name != prefix and not material.name.startswith(prefix + '.'):
                continue
            shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
            for factor, value in values.items():
                input_name = 'Metallic' if factor == 'metallicFactor' else 'Roughness'
                for link in list(shader.inputs[input_name].links):
                    material.node_tree.links.remove(link)
                shader.inputs[input_name].default_value = value
            changed.add(prefix)
    assert changed == set(factors), (name, changed)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)

record = {'factor_changes': factors, 'original_sha256': hashlib.sha256(backup.read_bytes()).hexdigest(),
          'updated_sha256': hashlib.sha256(result).hexdigest(),
          'binary_chunk_sha256': hashlib.sha256(binary_chunk).hexdigest(),
          'geometry_bind_morph_animation_bytes_unchanged': True,
          'base_colour_and_normal_images_unchanged': True}
(record_dir / 'record.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record, indent=2), flush=True)
