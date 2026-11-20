"""Sword GLBs straight from file (own normals): blade face-on both sides, edge-on and grip close-up, textured and
clay -> review/sword/<label>_<view>_<mode>.png. Usage: blender -b -P sword_views.py -- <label=glb,...>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'sword'); os.makedirs(out, exist_ok=True)
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    o = next(x for x in bpy.data.objects if x.type == 'MESH')
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    ctr = (lo + hi) / 2; L = (hi - lo).length
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 520
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.9, 0.2, -0.5); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.8, .78, .74)
    grip = lo + (hi - lo) * Vector((.5, .5, .1))
    for view, c, d, s in (('front', ctr, (0, -1, .05), L * .9), ('back', ctr, (0, 1, .05), L * .9),
                          ('edge', ctr, (1, 0, .05), L * .9), ('grip', grip, (.6, -.8, .2), L * .3),
                          ('guard', lo + (hi - lo) * Vector((.5, .5, .27)), (.5, -.85, .2), L * .3),
                          ('wave', lo + (hi - lo) * Vector((.5, .5, .65)), (.3, -1, .1), L * .35)):
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = s
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{view}_{mode}.png'); bpy.ops.render.render(write_still=True)
print('SWORDVIEWS done')
