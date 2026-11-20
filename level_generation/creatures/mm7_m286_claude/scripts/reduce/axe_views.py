"""Axe GLBs side by side: flat view (along the blade normal, glTF +Z = Blender -Y), edge view, three-quarter and a grip
close-up, textured (EEVEE) and clay (workbench). Usage: blender -b -P axe_views.py -- <out.png> <label=glb,...>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; items = [x.split('=') for x in a[1].split(',')]
VIEWS = [('flat', (0, -1, 0), (0, 0, 0.28), 1.55), ('edge', (1, 0, 0), (0, 0, 0.28), 1.55),
         ('q34', (0.6, -0.6, 0.5), (0, 0, 0.28), 1.6), ('head', (0.3, -1, 0.25), (0, 0, 0.72), 0.75),
         ('grip', (0.5, -1, 0.3), (0, 0, 0.0), 0.32)]
tiles = []
for label, glb in items:
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and 'LOD' in o.name:
            o.hide_render = True
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 360
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.8, .78, .74)
    for name, d, c, size in VIEWS:
        c = Vector(c); cam.location = c + Vector(d).normalized() * 3
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            try:
                sc.render.engine = eng
            except TypeError:
                sc.render.engine = 'BLENDER_EEVEE_NEXT'
            p = os.path.join(HERE, 'work', f'_axe_{label}_{name}_{mode}.png'); sc.render.filepath = p
            bpy.ops.render.render(write_still=True); tiles.append((label, name, mode, p))
import json
json.dump(tiles, open(os.path.join(HERE, 'work', '_axe_tiles.json'), 'w'))
print('AXEVIEWS', len(tiles), out)
