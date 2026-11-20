"""Import a Meshy retexture GLB as one object with this folder's texture set and save work/<name>_tex.blend. The
mesh is grounded and scaled back to the prepared model's height (Meshy may normalise it); the prepared work/<name>_uv
.blend's bounds are printed for comparison.
Usage: blender --background --python import_tex.py -- <name> <retexture glb> <texture prefix> <height metres> [material]"""
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
name, source, prefix, height = args[:4]
material = args[4] if len(args) > 4 else 'Bone'
bpy.ops.wm.read_factory_settings(use_empty=True)
obj = blib.import_mesh(source, name)
obj.data.materials.clear()
blib.ground(obj, float(height))
bm = bmesh.new(); bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)  # glTF splits vertices at UV/normal seams
bm.to_mesh(obj.data); bm.free()
for p in obj.data.polygons:
    p.use_smooth = True
while len(obj.data.uv_layers) > 1:
    obj.data.uv_layers.remove(obj.data.uv_layers[-1])
obj.data.uv_layers[0].name = 'UVMap'
obj.data.materials.append(blib.texture_material(material, prefix))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blib.WORK, f'{name}_tex.blend'))
print('IMPORTED', name, 'tris', len(obj.data.polygons), 'verts', len(obj.data.vertices),
      'dims', [round(d, 3) for d in obj.dimensions])
