"""Close renders of named rest-space spots of a blend's Body (optionally another object), clay and textured:
review/<dir>/<label>_<spot>_<view>_<mode>.png. Usage: blender -b -P spot_renders.py -- <blend> <label> <dir> [Object]"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; blend, label, out = a[0], a[1], a[2]; name = a[3] if len(a) > 3 else 'Body'
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o.name != name
SPOTS = {'mouth': ((-0.01, -0.15, 1.41), .16, {'front': (0, -1, 0), 'side': (1, -.4, .05), 'below': (.2, -1, -.35)}),
         'shins': ((0, -0.05, 0.33), .62, {'front': (0, -1, .1), 'q34l': (.8, -.6, .15), 'q34r': (-.8, -.6, .15)}),
         'whole': ((0, 0, .85), 1.95, {'front': (0, -1, .1), 'side': (1, 0, .1), 'back': (0, 1, .1)})}
cam = bpy.data.objects.new('CamS', bpy.data.cameras.new('CamS')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('SunS', bpy.data.lights.new('SunS', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('WS'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 520
os.makedirs(os.path.join(HERE, 'review', out), exist_ok=True)
modes = os.environ.get('SPOT_MODES', 'clay,tex').split(',')
for spot, (c, size, views) in SPOTS.items():
    c = Vector(c); cam.data.ortho_scale = size
    for view, d in views.items():
        dv = Vector(d).normalized(); cam.location = c + dv * 4
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        for mode in modes:
            if mode == 'clay':
                sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
                sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_cavity = True
            else:
                sc.render.engine = 'BLENDER_EEVEE'
            sc.render.filepath = os.path.join(HERE, 'review', out, f'{label}_{spot}_{view}_{mode}.png')
            bpy.ops.render.render(write_still=True)
