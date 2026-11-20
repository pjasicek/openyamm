"""Combine the two authored resolutions, ready for the existing static LOD linker."""
from pathlib import Path
import sys

import bpy

P = Path(__file__).resolve().parents[1]
for icon in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(P / 'work/finished' / f'scroll_{icon}_export.glb'))
    base = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    base.name = 'scroll_' + icon
    bpy.ops.import_scene.gltf(filepath=str(P / 'work/lod' / f'scroll_{icon}_export.glb'))
    lod = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o != base)
    lod.name = base.name + '_LOD1'
    lod.data.materials.clear()
    lod.data.materials.append(base.data.materials[0])
    for face in lod.data.polygons:
        face.material_index = 0
    out = P / 'work/lod_stage'
    out.mkdir(exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(out / f'{icon}.glb'), export_format='GLB',
                              export_animations=False, export_yup=True)
