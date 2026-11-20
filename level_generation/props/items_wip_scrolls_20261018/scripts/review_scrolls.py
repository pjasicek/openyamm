"""Re-import exports and render the above, low, underside and optional checker views."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    mode = args[0] if args else 'finished'
    only = set(args[1:])
    out = P / 'review' / mode
    out.mkdir(exist_ok=True)
    for entry in json.loads((P / 'audit.json').read_text()):
        icon = entry['icon']
        if entry['status'] != 'rebuild' or (only and icon not in only):
            continue
        path = (P / 'baseline' / f'item_{icon}.glb' if mode == 'baseline'
                else P / ('work/lod' if mode == 'lod' else 'work/finished') / f'scroll_{icon}_export.glb')
        if not path.exists() and mode == 'lod':
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        for obj in objects:
            for mat in obj.data.materials:
                mat.use_backface_culling = True
        if mode == 'checker':
            mat = bpy.data.materials.new('UV checker')
            mat.use_nodes = True
            uv = mat.node_tree.nodes.new('ShaderNodeTexCoord')
            checker = mat.node_tree.nodes.new('ShaderNodeTexChecker')
            checker.inputs['Scale'].default_value = 24
            mat.node_tree.links.new(uv.outputs['UV'], checker.inputs['Vector'])
            mat.node_tree.links.new(checker.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
            for obj in objects:
                obj.data.materials.clear()
                obj.data.materials.append(mat)
                for face in obj.data.polygons:
                    face.material_index = 0
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 16
        scene.cycles.use_denoising = True
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = 8
        scene.render.resolution_x = scene.render.resolution_y = 384
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.view_settings.view_transform = 'Standard'
        scene.world = bpy.data.worlds.new('Review world')
        scene.world.use_nodes = True
        scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.65, .7, .8, 1)
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
        points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
        low = Vector([min(v[i] for v in points) for i in range(3)])
        high = Vector([max(v[i] for v in points) for i in range(3)])
        centre, extent = (low + high) / 2, max(high - low)
        for name, position, energy in [('Key', (1, -2, 4), 160), ('Fill', (-3, 1, 2), 80)]:
            light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
            light.location = centre + Vector(position) * extent
            light.rotation_euler = (centre - light.location).to_track_quat('-Z', 'Y').to_euler()
            light.data.energy = energy * extent ** 2
            light.data.size = 3 * extent
            scene.collection.objects.link(light)
        camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = extent * 1.27
        scene.collection.objects.link(camera)
        scene.camera = camera
        for view, direction in [('above', (0, 0, 1)), ('low', (1.5, -.5, .8)), ('underside', (-1, -.6, -.7))]:
            camera.location = centre + Vector(direction).normalized() * extent * 4
            camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(out / f'{icon}_{view}.png')
            bpy.ops.render.render(write_still=True)
        print('REVIEWED', mode, icon, flush=True)


if __name__ == '__main__':
    main()
