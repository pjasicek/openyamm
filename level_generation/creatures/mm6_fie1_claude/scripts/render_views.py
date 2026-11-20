"""Review renders of a work blend: a row per action, columns = sampled times x views. Run under Blender:

    blender --background work/<file>.blend --python scripts/render_views.py -- <out.png> [--actions A,B]
        [--samples N] [--views front,side,back,three] [--size 360] [--engine workbench|eevee] [--hide name,...]
        [--span 2.9] [--centre z] [--background r,g,b] [--hide_materials name,...] [--only mesh-object]

Each cell is rendered at an orthographic camera framing the 2.7-unit-tall creature (the sprite canvas), so cells line
up with the restored frames. Workbench shows clay shapes; eevee shows the materials (alpha blend, emission).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
out = os.path.abspath(args[0])
opts = {'actions': '', 'samples': '1', 'views': 'front,side', 'size': '360', 'engine': 'workbench', 'hide': '',
        'span': '2.9', 'background': '0.04,0.04,0.05',
        'hide_materials': ''}
for key, value in zip(args[1::2], args[2::2]):
    opts[key.lstrip('-')] = value
scene = bpy.context.scene
size = int(opts['size'])
VIEWS = {'front': 0.0, 'three': 45.0, 'side': 90.0, 'back': 180.0, 'left': -90.0}
views = opts['views'].split(',')
hidden = set(filter(None, opts['hide'].split(',')))
if opts.get('only'):
    # One mesh object only (e.g. a single LOD).
    hidden |= {o.name for o in scene.objects if o.type == 'MESH' and o.name != opts['only']}
for obj in scene.objects:
    if obj.name in hidden or (not opts.get('only') and any(obj.name.startswith(h) for h in hidden)):
        obj.hide_render = True
rig = next((o for o in scene.objects if o.type == 'ARMATURE'), None)
actions = [a for a in opts['actions'].split(',') if a] or [None]

if opts['engine'] == 'workbench':
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'OBJECT'
    for obj in scene.objects:
        obj.color = (0.75, 0.42, 0.32, 1.0)
else:
    for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new('World')
    scene.world.use_nodes = True
    background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs[0].default_value = tuple(float(x) for x in opts['background'].split(',')) + (1.0,)
    background.inputs[1].default_value = 1.0
    scene.view_settings.view_transform = 'Standard'
    # As in game: unlit (texture colour only), blended where the texture has alpha, single-sided.
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        tree = material.node_tree
        bsdf = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        texture = next((n for n in tree.nodes if n.type == 'TEX_IMAGE'), None)
        if bsdf is None or texture is None:
            continue
        for link in list(bsdf.inputs['Base Color'].links):
            tree.links.remove(link)
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
        tree.links.new(texture.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
        if bsdf.inputs['Alpha'].links:
            material.surface_render_method = 'BLENDED'
            material.use_backface_culling = True
        if material.name in opts['hide_materials'].split(','):
            for link in list(bsdf.inputs['Alpha'].links):
                tree.links.remove(link)
            bsdf.inputs['Alpha'].default_value = 0.0
            material.surface_render_method = 'BLENDED'
scene.render.resolution_x = size
scene.render.resolution_y = int(size * 1.0)
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

camera_data = bpy.data.cameras.new('ReviewCam')
camera_data.type = 'ORTHO'
camera_data.ortho_scale = float(opts['span'])
camera = bpy.data.objects.new('ReviewCam', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
target = Vector((0.0, 0.0, float(opts['centre']) if 'centre' in opts else float(opts['span']) / 2 - 0.1))

tiles = []
tmp = out + '.tmp.png'
for action_name in actions:
    row = []
    action = bpy.data.actions.get(action_name) if action_name else None
    if action is not None and rig is not None:
        rig.animation_data_create()
        rig.animation_data.action = action
        if getattr(action, 'slots', None) is not None and len(action.slots):
            rig.animation_data.action_slot = action.slots[0]
        start, end = action.frame_range
    else:
        start, end = scene.frame_current, scene.frame_current
    samples = int(opts['samples'])
    for sample in range(samples):
        frame = start + (end - start) * (sample / max(samples - 1, 1) if samples > 1 else 0.0)
        scene.frame_set(int(math.floor(frame)), subframe=frame - math.floor(frame))
        for view in views:
            angle = math.radians(VIEWS[view])
            # View angle 0 looks at the creature's face (it faces -Y).
            direction = Vector((math.sin(angle), -math.cos(angle), 0.0))
            camera.location = target + direction * 10.0
            camera.rotation_euler = (math.radians(90), 0.0, angle)
            scene.render.filepath = tmp
            bpy.ops.render.render(write_still=True)
            image = bpy.data.images.load(tmp)
            row.append(list(image.pixels))
            bpy.data.images.remove(image)
    tiles.append(row)
os.remove(tmp)
columns = max(len(r) for r in tiles)
sheet = bpy.data.images.new('sheet', columns * size, len(tiles) * size, alpha=True)
pixels = [0.0] * (columns * size * len(tiles) * size * 4)
for r, row in enumerate(tiles):
    # Blender images are bottom-up: the first row goes on top.
    oy = (len(tiles) - 1 - r) * size
    for c, tile in enumerate(row):
        ox = c * size
        for y in range(size):
            src = y * size * 4
            dst = ((oy + y) * columns * size + ox) * 4
            pixels[dst:dst + size * 4] = tile[src:src + size * 4]
sheet.pixels = pixels
sheet.filepath_raw = out
sheet.file_format = 'PNG'
sheet.save()
print('WROTE', out, len(tiles), 'rows', columns, 'columns')
