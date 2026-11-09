"""Render owned source models only; retain measurements for the replacement handoff."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]


def main():
    entries = json.loads((PROJECT / 'ownership.json').read_text())
    assert len(entries) == len({entry['icon'] for entry in entries}) == 95
    output = PROJECT / 'review' / 'baseline'
    output.mkdir(parents=True, exist_ok=True)
    measurements = {}
    for entry in entries:
        icon = entry['icon']
        report = output / f'{icon}.json'
        if report.exists() and all((output / f'{icon}_{view}.png').exists() for view in ('above', 'low')):
            measurements[icon] = json.loads(report.read_text())
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path = REPO / 'assets_source' / entry['model']
        bpy.ops.import_scene.gltf(filepath=str(path))
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        assert meshes, path
        points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
        lo = Vector([min(point[i] for point in points) for i in range(3)])
        hi = Vector([max(point[i] for point in points) for i in range(3)])
        centre = (lo + hi) / 2
        extent = max(hi - lo)
        triangles = 0
        missing_uvs = []
        for obj in meshes:
            obj.data.calc_loop_triangles()
            triangles += len(obj.data.loop_triangles)
            if not obj.data.uv_layers:
                missing_uvs.append(obj.name)
            for slot in obj.material_slots:
                if slot.material:
                    slot.material.use_backface_culling = True
        measurement = {'source': str(path.relative_to(REPO)), 'triangles': triangles,
                       'bounds_blender': [list(lo), list(hi)], 'missing_uvs': missing_uvs,
                       'materials': sorted({slot.material.name for obj in meshes for slot in obj.material_slots
                                            if slot.material}),
                       'binding_length': entry['length']}
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = 8
        scene.render.resolution_x = scene.render.resolution_y = 256
        scene.render.film_transparent = True
        scene.view_settings.view_transform = 'Standard'
        world = bpy.data.worlds.new('review_world')
        scene.world = world
        world.use_nodes = True
        world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.6, 0.65, 0.75, 1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
        light = bpy.data.objects.new('review_sun', bpy.data.lights.new('review_sun', 'SUN'))
        light.data.energy = 2.0
        scene.collection.objects.link(light)
        light.rotation_euler = (0.4, -0.3, 0.6)
        camera = bpy.data.objects.new('review_camera', bpy.data.cameras.new('review_camera'))
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = extent * 1.4
        scene.collection.objects.link(camera)
        scene.camera = camera
        for view, elevation in (('above', 85), ('low', 18)):
            a, e = math.radians(55), math.radians(elevation)
            direction = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
            camera.location = centre + direction * extent * 4
            camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(output / f'{icon}_{view}.png')
            bpy.ops.render.render(write_still=True)
        report.write_text(json.dumps(measurement, indent=2) + '\n')
        measurements[icon] = measurement
        print('AUDITED', icon, triangles, flush=True)
    (output / 'measurements.json').write_text(json.dumps(measurements, indent=2) + '\n')


main()
