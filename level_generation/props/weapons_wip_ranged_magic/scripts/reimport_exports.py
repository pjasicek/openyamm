"""Reimport all accepted source exports; compare linked LODs at review distance."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]

spec = importlib.util.spec_from_file_location('builder', HERE / 'scripts/build_weapons.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def main():
    ledger = json.loads((HERE / 'ledger.json').read_text())
    reports = {}
    image = bpy.data.images.new('UV checker', width=512, height=512)
    y, x = np.indices((512, 512))
    values = ((x // 16 + y // 16) % 2) * .6 + .15
    pixels = np.stack([values, values, values, np.ones_like(values)], axis=2).astype(np.float32)
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(HERE / 'textures/uv_checker.png')
    image.file_format = 'PNG'
    image.save()
    folder = HERE / 'work/lod_preview'
    folder.mkdir(exist_ok=True)
    for icon, entry in ledger.items():
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.data.orphans_purge(do_recursive=True)
        path = HERE / entry['source_export']
        bpy.ops.import_scene.gltf(filepath=str(path))
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        assert len(objects) == 1
        points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
        assert abs(min(v.z for v in points)) < 1e-5
        assert max(v.y for v in points) - min(v.y for v in points) > .99
        obj = objects[0]
        assert obj.data.uv_layers and len(obj.data.materials) == 1
        reports[icon] = {'reimported': True, 'triangles': len(obj.data.polygons)}
        if icon in builder.PILOTS:
            checker = bpy.data.materials.new('UV inspection')
            checker.use_nodes = True
            bsdf = checker.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Roughness'].default_value = .8
            tex = checker.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = bpy.data.images.load(str(HERE / 'textures/uv_checker.png'))
            checker.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
            bpy.context.scene.view_layers[0].material_override = checker
            builder.render(icon + '_checker')
    subprocess.run(['python3', str(HERE / 'scripts/make_lod_previews.py')], check=True)
    for icon, files in json.loads((folder / 'previews.json').read_text()).items():
        for label, out in files.items():
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
            bpy.data.orphans_purge(do_recursive=True)
            bpy.ops.import_scene.gltf(filepath=str(out))
            builder.render(f'{icon}_{label}_reimport', resolution=896, views=['top', 'low'])
    (HERE / 'receipts/reimport.json').write_text(json.dumps(reports, indent=2) + '\n')
    print(f'Reimported {len(reports)} grounded, UV-mapped, single-material source models')


if __name__ == '__main__':
    main()
