"""Export one 50% static LOD for complex items; link with tools/link_static_model_lods.py afterwards."""
import json
import sys
from pathlib import Path

import bmesh
import bpy

HERE = Path(__file__).resolve().parents[1]
DESIGNS = json.loads((HERE / 'designs.json').read_text())
sys.path.insert(0, str(HERE.parent / 'projectiles_claude/scripts'))
import projlib as pl


for icon in sys.argv[sys.argv.index('--') + 1:]:
    if not DESIGNS[icon].get('lod_enabled', True):
        # shortcut: retain the woven glove at LOD0; hand-build its LOD if distant draw cost becomes measurable.
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = HERE / 'work/finished' / (icon + '_export.glb')
    bpy.ops.import_scene.gltf(filepath=str(source))
    base = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    count = len(base.data.polygons)
    objects, counts = [base], [count]
    for level, ratio in [(1, DESIGNS[icon].get('lod_ratio', .5))]:
        lod = base.copy()
        lod.data = base.data.copy()
        lod.name = base.name + '_LOD' + str(level)
        bpy.context.collection.objects.link(lod)
        bm = bmesh.new()
        bm.from_mesh(lod.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-9)
        bm.to_mesh(lod.data)
        bm.free()
        bpy.context.view_layer.objects.active = lod
        decimate = lod.modifiers.new('silhouette_lod', 'DECIMATE')
        decimate.ratio = ratio
        decimate.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=decimate.name)
        counts.append(len(lod.data.polygons))
        assert counts[-1] < counts[-2]
        pl.WORK = str(HERE / 'work' / ('lod' + str(level)))
        pl.export(lod, icon)
        objects.append(lod)
    for obj in bpy.context.scene.objects:
        obj.select_set(obj in objects)
    folder = HERE / 'work/lod_stage'
    folder.mkdir(exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(folder / (icon + '.glb')), use_selection=True,
                              export_format='GLB', export_yup=True, export_normals=True,
                              export_animations=False, export_skins=False, export_morph=False, export_apply=True)
    (HERE / 'receipts' / ('lods_' + icon + '.json')).write_text(json.dumps({'icon': icon, 'triangles': counts}, indent=2) + '\n')
    print('STATIC LODS', icon, counts)
