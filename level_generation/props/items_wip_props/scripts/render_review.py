"""Re-import owned ground-item GLBs and render icon comparisons from above and low angles."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    mode = args[0]
    only = set(args[1:])
    entries = json.loads((PROJECT / 'ownership.json').read_text())
    out = PROJECT / 'review' / mode
    out.mkdir(parents=True, exist_ok=True)
    stats = json.loads((out / 'stats.json').read_text()) if (out / 'stats.json').exists() else {}
    for entry in entries:
        icon = entry['icon']
        if only and icon not in only:
            continue
        path = (ROOT / 'assets_source' / entry['model'] if mode == 'baseline'
                else PROJECT / 'work' / 'exports' / f'props_{icon}_export.glb')
        if not path.exists():
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        if mode == 'checker':
            mat = bpy.data.materials.new('UV checker')
            mat.use_nodes = True
            uv = mat.node_tree.nodes.new('ShaderNodeTexCoord')
            grid = mat.node_tree.nodes.new('ShaderNodeTexChecker')
            grid.inputs['Scale'].default_value = 12
            grid.inputs['Color1'].default_value = (.1, .1, .1, 1)
            grid.inputs['Color2'].default_value = (.8, .8, .8, 1)
            mat.node_tree.links.new(uv.outputs['UV'], grid.inputs['Vector'])
            mat.node_tree.links.new(grid.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
            for obj in objects:
                for i in range(len(obj.data.materials)):
                    obj.data.materials[i] = mat
        points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
        lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
        hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
        centre = (lo + hi) / 2
        extent = max(hi - lo)
        stats[icon] = {'bounds_blender': [list(lo), list(hi)], 'triangles': sum(
            len(p.vertices) - 2 for o in objects for p in o.data.polygons)}
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 8
        scene.cycles.use_denoising = True
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = 6
        scene.render.resolution_x = scene.render.resolution_y = 192
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.view_settings.view_transform = 'Standard'
        scene.world = bpy.data.worlds.new('Review world')
        scene.world.use_nodes = True
        scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.65, .7, .8, 1)
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .7
        for name, location, energy, size in [('Key', (1, -2, 4), 180, 4), ('Fill', (-3, 1, 2), 80, 3)]:
            light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
            light.location = centre + Vector(location) * extent
            light.rotation_euler = (centre - light.location).to_track_quat('-Z', 'Y').to_euler()
            light.data.energy = energy * extent * extent
            light.data.shape = 'DISK'
            light.data.size = size * extent
            scene.collection.objects.link(light)
        camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = extent * 1.5
        scene.collection.objects.link(camera)
        scene.camera = camera
        for name, direction in [('above', (.05, -.05, 1)), ('low', (1, -1.4, .85))]:
            target = out / f'{icon}_{name}.png'
            if target.exists() and not only:
                continue
            camera.location = centre + Vector(direction).normalized() * extent * 4
            camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(target)
            bpy.ops.render.render(write_still=True)
        print('REVIEWED', icon, stats[icon], flush=True)
    (out / 'stats.json').write_text(json.dumps(stats, indent=2) + '\n')


if __name__ == '__main__':
    main()
