"""Restore the source icon's ivory forehead stone inside the existing gold setting."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import bpy

project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project / '../projectiles_claude/scripts'))
import projlib as pl

name = 'equipment_6helm4'
path = project / 'work/codex_tex' / f'{name}_export.glb'
backup = project / 'work/repairs' / f'{name}_before_pearl_export.glb'
assert not backup.exists()
shutil.copyfile(path, backup)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(path))
body = next(obj for obj in bpy.context.scene.objects if obj.type == 'MESH')
# Blender import restores the author's Z-up axes; the small stone sits inside the measured oval setting.
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, location=(-0.018, -0.292, 0.541))
pearl = bpy.context.object
pearl.scale = (0.027, 0.018, 0.040)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
material = bpy.data.materials.new('ivory_forehead_stone')
material.use_nodes = True
shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
shader.inputs['Base Color'].default_value = (0.72, 0.69, 0.59, 1)
shader.inputs['Metallic'].default_value = 0
shader.inputs['Roughness'].default_value = 0.2
pearl.data.materials.append(material)
for face in pearl.data.polygons:
    face.use_smooth = True
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = name
bpy.ops.wm.save_as_mainfile(filepath=str(project / 'work/codex_tex' / f'{name}_finished.blend'))
pl.WORK = str(project / 'work/codex_tex')
pl.export(body, name)
status = {'baked': True, 'export_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'finishing': 'Source-icon ivory stone added within existing oval setting; separately dielectric material',
          'source_export_sha256': hashlib.sha256(backup.read_bytes()).hexdigest()}
(project / 'review' / f'{name}_bake_status.json').write_text(json.dumps(status, indent=2) + '\n')
(project / 'review/defender_forehead_stone.json').write_text(json.dumps(status, indent=2) + '\n')
