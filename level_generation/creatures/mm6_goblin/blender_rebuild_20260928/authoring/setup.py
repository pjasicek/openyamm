"""Create the owned authoring scene and load read-only shape references through Blender MCP."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT.parent / 'meshy_restart_20260923'
SCENE_NAME = 'MM6 Goblin - Authored 15K'


def setup():
    if bpy.data.scenes.get(SCENE_NAME):
        raise RuntimeError('Authoring scene already exists; inspect it before rebuilding.')
    scene = bpy.data.scenes.new(SCENE_NAME)
    bpy.context.window.scene = scene
    scene['gb_owner'] = str(ROOT)
    scene.unit_settings.system = 'METRIC'
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 960
    scene.render.resolution_y = 1120
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.render.fps = 48
    scene.world = bpy.data.worlds.new('GB15 Studio world')
    scene.world.use_nodes = True
    background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (.13, .16, .19, 1)
    background.inputs['Strength'].default_value = .35
    for name in ['GB15 Reference', 'GB15 Character', 'GB15 Studio']:
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
    ref = bpy.data.collections['GB15 Reference']
    before = set(scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(HISTORY / 'repaired_master/mm6_goblin_repaired_master.glb'))
    sources = [o for o in scene.objects if o not in before and o.type == 'MESH']
    bounds = [o.matrix_world @ Vector(p) for o in sources for p in o.bound_box]
    z_min, z_max = min(p.z for p in bounds), max(p.z for p in bounds)
    factor = 1.7 / (z_max - z_min)
    for obj in sources:
        world = obj.matrix_world.copy()
        for v in obj.data.vertices:
            p = world @ v.co
            v.co = (p.x * factor, p.y * factor, (p.z - z_min) * factor)
        obj.matrix_world.identity()
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        ref.objects.link(obj)
        obj['gb_role'] = 'reference'
        obj.hide_render = True
        obj.hide_set(True)
    main = max(sources, key=lambda o: len(o.data.vertices))
    main.name = 'GB15 Dense shape guide'
    for label, angle, location in [('front', math.pi / 2, (0, .5, .85)),
                                    ('left', math.pi / 2, (.7, 0, .85)),
                                    ('back', math.pi / 2, (0, .6, .85)),
                                    ('right', math.pi / 2, (-.7, 0, .85))]:
        obj = bpy.data.objects.new('GB15 Reference ' + label, None)
        obj.empty_display_type = 'IMAGE'
        obj.data = bpy.data.images.load(str(HISTORY / 'references' / (label + '.png')), check_existing=True)
        obj.empty_display_size = 2.0
        obj.location = location
        obj.rotation_euler = (angle, 0, 0)
        obj.hide_render = True
        obj['gb_role'] = 'reference'
        ref.objects.link(obj)
        bpy.context.view_layer.update()
        obj.hide_set(True)
    studio = bpy.data.collections['GB15 Studio']
    for name, location, power, size in [('Key', (-3, -4, 5), 600, 4),
                                        ('Fill', (3, -2, 2.5), 360, 3),
                                        ('Rim', (1, 3, 4), 650, 3)]:
        light = bpy.data.lights.new('GB15 ' + name, 'AREA')
        light.energy, light.shape, light.size = power, 'DISK', size
        obj = bpy.data.objects.new(light.name, light)
        obj.location = location
        obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
        studio.objects.link(obj)
    camera = bpy.data.cameras.new('GB15 Review camera')
    obj = bpy.data.objects.new(camera.name, camera)
    studio.objects.link(obj)
    obj.location = (0, -4, .87)
    obj.rotation_euler = (Vector((0, 0, .87)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    camera.type, camera.ortho_scale = 'ORTHO', 1.98
    scene.camera = obj
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.region_3d.view_distance = 3.2
            area.spaces.active.region_3d.view_location = (0, 0, .9)
    for folder in ['review', 'checkpoints', 'delivery']:
        (ROOT / folder).mkdir(exist_ok=True)
    report = {'source': str(HISTORY / 'repaired_master/mm6_goblin_repaired_master.glb'),
              'source_scale': factor, 'source_z_min': z_min, 'working_height_m': 1.7,
              'scene': scene.name, 'guide_object': main.name, 'blender': bpy.app.version_string}
    (ROOT / 'authoring/source_alignment.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    setup()
