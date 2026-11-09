"""Eevee review renders of work/tree.blend (sun + sky, alpha-clipped leaves, Standard view transform).
Args: out_prefix [blend]. Writes <out_prefix>_<object>_<view>.png for every LOD object in the file, all with the same
cameras: 'eye' (eye level, 10.5 m away, like the sprite) and 'three_quarter' (raised, 45 degrees round)."""
import bpy, sys, os, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
prefix = args[0]
blend = args[1] if len(args) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'tree.blend')
views = args[2].split(',') if len(args) > 2 else ['eye', 'three_quarter']
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = True
sc.render.resolution_x = 480; sc.render.resolution_y = 540
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.42, 0.55, 0.75, 1); bg.inputs['Strength'].default_value = 0.55
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86)
sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
lods = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Tree')]
H = max((o.matrix_world @ Vector(c)).z for o in lods for c in o.bound_box)
target = Vector((0, 0, H * 0.5))
CAMS = {'eye': (0.0, 1.0, 1.6), 'three_quarter': (45.0, 1.0, 5.5)}
for o in lods:
    for x in lods:
        x.hide_render = x is not o
    for view in views:
        yaw, scale, height = CAMS[view]
        d = 10.5 * scale
        cam.location = (math.sin(math.radians(yaw)) * d, -math.cos(math.radians(yaw)) * d, height)
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{prefix}_{o.name}_{view}.png'
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)
