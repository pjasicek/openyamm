"""Staff GLBs straight from file (own normals): close-ups along the shaft (spear head, upper bands, grip, lower band,
butt cap) and the whole staff, textured and clay -> review/staff/<label>_<view>_<mode>.png.
Usage: blender -b -P staff_views.py -- <label=glb,...>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'staff'); os.makedirs(out, exist_ok=True)
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    o = next(x for x in bpy.data.objects if x.type == 'MESH')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 360
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.9, 0.2, -0.5); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.8, .78, .74)
    # the staff's long axis is the import's -Y (glTF +Z); y = position along it
    at = lambda y: o.matrix_world @ Vector((0, y, 0))
    for view, y, s in (('head', 1.2, .16), ('band_hi', 0.9, .14), ('band_mid', 0.41, .14), ('grip', -0.06, .2),
                       ('band_lo', -0.29, .14), ('butt', -0.37, .12), ('whole', 0.43, 1.8)):
        c = at(y); d = Vector((.6, .2, .78)).normalized()
        cam.location = c + d * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = s
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{view}_{mode}.png'); bpy.ops.render.render(write_still=True)
print('STAFFVIEWS done')
