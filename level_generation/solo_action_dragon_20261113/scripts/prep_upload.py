"""UV the Meshy foreleg with the shared atlas (TEXTURE_QUALITY_PASS) and write the retexture upload GLB.

blender -b --python prep_upload.py -- <meshy.glb> <upload.glb> <report.json>
"""
import json
import sys

import bpy

sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared')
import uv_atlas  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
source, upload, report_path = argv[:3]
options = dict(item.split('=') for item in argv[3:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=source)
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
kwargs = {'size': 4096, 'margin_px': 4}
if 'charts' in options:
    kwargs['charts'] = options['charts']
if 'threshold' in options:
    kwargs['partuv_threshold'] = float(options['threshold'])
report = uv_atlas.unwrap(obj, **kwargs)
material = bpy.data.materials.new('foreleg')
obj.data.materials.clear()
obj.data.materials.append(material)
for o in list(bpy.context.scene.objects):
    if o is not obj:
        bpy.data.objects.remove(o)
bpy.ops.export_scene.gltf(filepath=upload, export_format='GLB', use_selection=False)
with open(report_path, 'w') as stream:
    json.dump({k: (v if isinstance(v, (int, float, str, list, dict, type(None))) else str(v)) for k, v in report.items()},
              stream, indent=1, default=str)
print('UPLOAD', upload, {k: report.get(k) for k in ('charts_used', 'packer_used', 'fallbacks', 'atlas_use', 'used')})
