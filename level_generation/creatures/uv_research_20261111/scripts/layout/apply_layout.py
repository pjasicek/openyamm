"""Write a packed layout (npz: uv per triangle corner, glTF v-down, same face order as the trial blend's mesh) onto a
seam trial's saved blend and export the neutral static upload GLB (as uv_atlas_v8.py) and the skinned measurement GLB.

blender.sh apply_layout.py <log> <trial .blend> <layout npz> <out dir> <name> mesh=<name>
"""
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
BLEND, LAYOUT, OUT, NAME = argv[:4]
opts = dict(a.split('=', 1) for a in argv[4:])
bpy.ops.wm.open_mainfile(filepath=BLEND)
OUT = os.path.abspath(OUT)
for im in bpy.data.images:     # blends saved by a trial run with a relative out dir: the exporter needs real paths
    if im.filepath and not im.filepath.startswith('//') and not os.path.isabs(im.filepath):
        im.filepath = os.path.abspath(im.filepath)
count = len(np.load(LAYOUT)['uv'])
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.polygons) == count
            and (o.name == opts.get('mesh') or o.data.name == opts.get('mesh') or 'mesh' not in opts))
rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
me = mesh.data
uv = np.load(LAYOUT)['uv'].astype(np.float64)
assert len(uv) == len(me.polygons), (len(uv), len(me.polygons))
uv[..., 1] = 1.0 - uv[..., 1]
flat = np.zeros((len(me.loops), 2), np.float32)
for p in me.polygons:
    flat[list(p.loop_indices)] = uv[p.index]
me.uv_layers['UVMap'].data.foreach_set('uv', flat.ravel())
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != mesh:
        bpy.data.objects.remove(o)
dup = mesh.copy()
dup.data = mesh.data.copy()
dup.modifiers.clear()
dup.parent = None
dup.matrix_world = mesh.matrix_world
dup.data.materials.clear()
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_upload.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
bpy.data.objects.remove(dup)
for o in bpy.data.objects:
    o.select_set(o == mesh or o == rig)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_measure.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_skins=True, export_animations=False, export_materials='EXPORT',
                          export_attributes=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}.blend'))
print('APPLY done', NAME)
