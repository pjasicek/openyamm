"""Textured (Eevee) and clay (workbench + cavity) views of forearm prop GLBs, LOD0 only, in prop space (glTF +Y along
the forearm = Blender +Y after import... the importer maps glTF (x, y, z) to Blender (x, -z, y)).
Views: whole prop from both sides, the severed hand's back, palm and fingertips, the wound end.
Usage: blender -b -P prop_views.py -- <label=glb,...> -> review/prop/<label>_<view>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'prop'); os.makedirs(out, exist_ok=True)
# (centre in glTF prop space, ortho size, view direction in glTF prop space)
VIEWS = {'whole_x': ((0.02, -0.01, 0), .5, (1, 0, .3)), 'whole_mx': ((0.02, -0.01, 0), .5, (-1, 0, .3)),
         'hand_back': ((0.02, -0.17, 0), .2, (0, 0, 1)), 'palm': ((0.02, -0.17, 0), .2, (0, 0, -1)),
         'fingers': ((0.02, -0.2, 0), .16, (.3, -1, .4)), 'hand_side': ((0.02, -0.17, 0), .2, (1, 0, 0)),
         'wound': ((0.0, 0.19, 0), .16, (.2, 1, .5))}
g2b = lambda v: Vector((v[0], -v[2], v[1]))
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'Sword':
            o.hide_render = True
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 10; sc.render.resolution_x = sc.render.resolution_y = 400
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = True; sc.display.shading.cavity_type = 'BOTH'
    for name, (c, size, d) in VIEWS.items():
        c = g2b(c); d = g2b(Vector(d).normalized())
        cam.location = c + d * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{name}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('PROPVIEWS done')
