"""Rest-pose close renders of a viewer GLB (Eevee): mouth, shins, both hands, whole body from 3 sides ->
review/<dir>/<label>_<spot>_<view>.png. Usage: blender -b -P glb_spots.py -- <glb> <label> <dir> [spot,...]"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]; glb, label, out = args[:3]
only = args[3].split(',') if len(args) > 3 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if o.animation_data:
            o.animation_data.action = None
        for b in o.pose.bones:
            b.matrix_basis.identity()
if os.environ.get('SPOT_NO_NORMAL'):            # diagnostic: shading without the normal maps
    for mat in bpy.data.materials:
        if mat.node_tree:
            for link in list(mat.node_tree.links):
                if link.to_socket.name == 'Normal':
                    mat.node_tree.links.remove(link)
bpy.context.view_layer.update()
SPOTS = {'torso': ((0.0, -0.05, 1.08), .62, {'front': (0, -1, .05), 'q34l': (.7, -.7, .1), 'side': (1, -.1, .05)}),
         'arm': ((0.42, -0.02, 1.0), .55, {'front': (0, -1, .05), 'out': (1, -.3, .1)}),
         'face': ((0.0, -0.12, 1.50), .34, {'front': (0, -1, .05), 'q34l': (.7, -.7, .1), 'q34r': (-.7, -.7, .1), 'left': (1, -.1, .05), 'right': (-1, -.1, .05), 'top': (0, -.4, 1)}),
         'mouth': ((-0.01, -0.15, 1.41), .17, {'front': (0, -1, 0), 'side': (1, -.4, .05), 'below': (.2, -1, -.35)}),
         'shins': ((0, -0.05, 0.33), .62, {'front': (0, -1, .1), 'q34l': (.8, -.6, .15), 'q34r': (-.8, -.6, .15)}),
         'hands': ((0, -0.02, 0.82), 1.45, {'front': (0, -1, .05), 'back': (0, 1, .05)}),
         'whole': ((0, 0, .85), 1.95, {'front': (0, -1, .1), 'side': (1, 0, .1), 'back': (0, 1, .1)})}
cam = bpy.data.objects.new('CamS', bpy.data.cameras.new('CamS')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('SunS', bpy.data.lights.new('SunS', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('WS'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 520
sc.render.engine = 'BLENDER_EEVEE'
os.makedirs(os.path.join(HERE, 'review', out), exist_ok=True)
for spot, (c, size, views) in SPOTS.items():
    if only and spot not in only:
        continue
    c = Vector(c); cam.data.ortho_scale = size
    for view, d in views.items():
        dv = Vector(d).normalized(); cam.location = c + dv * 4
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(HERE, 'review', out, f'{label}_{spot}_{view}.png'); bpy.ops.render.render(write_still=True)
