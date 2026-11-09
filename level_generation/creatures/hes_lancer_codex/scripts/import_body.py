"""Import the shared export; recover authoring labels from its read-only source master."""
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

P = Path(__file__).resolve().parents[1]
SOURCE = P.with_name('hes_kreegan_claude')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE / 'work/rig_v3t.blend'))
body = bpy.data.objects['Body']
mesh = body.data
thin = np.array([v.vector[:] for v in mesh.attributes['thin_co'].data])
labels = {name: np.array([v.value for v in mesh.attributes[name].data])
          for name in ('piece', 'garment')}
properties = {k: bpy.context.scene[k] for k in ('rig_offsets',) if k in bpy.context.scene}
tree = KDTree(len(thin))
for i, co in enumerate(thin):
    tree.insert(Vector(co), i)
tree.balance()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(P / 'source/hes_kreegan.glb'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = bpy.data.objects['HKR']
for obj in list(bpy.data.objects):
    if obj not in (rig, body):
        bpy.data.objects.remove(obj, do_unlink=True)
rig.name = 'Rig'
body.name = body.data.name = 'Body'
rig.animation_data_clear()
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
bpy.context.view_layer.update()
assert np.max(np.abs(np.array(body.matrix_world) - np.eye(4))) < 1e-5
nearest = [tree.find(v.co) for v in body.data.vertices]
assert max(d for _, _, d in nearest) < 1e-4, 'Source authoring labels do not match the shared export'
for name, values in labels.items():
    attr = body.data.attributes.new(name, 'INT', 'POINT')
    attr.data.foreach_set('value', [int(values[i]) for _, i, _ in nearest])
for key, value in properties.items():
    bpy.context.scene[key] = value
for action in bpy.data.actions:
    action.use_fake_user = True
for material in bpy.data.materials:
    for key in list(material.keys()):
        if key.startswith('openyamm_region'):
            del material[key]
    material.gltf_materials_variants.clear() if hasattr(material, 'gltf_materials_variants') else None
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/imported.blend'))
report = {'source': 'source/hes_kreegan.glb', 'vertices': len(body.data.vertices),
          'triangles': len(body.data.polygons), 'bones': len(rig.data.bones),
          'labels_max_error_m': max(d for _, _, d in nearest),
          'clips': {a.name: list(a.frame_range) for a in bpy.data.actions},
          'materials': [m.name for m in body.data.materials]}
(P / 'review/import.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
