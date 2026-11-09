"""Quick three-quarter preview of a .blend or .glb (Workbench, textured if a texture exists, else clay).
Usage: blender --background --python scripts/preview.py -- <in.blend|in.glb> <out.png> [yaw_deg] [eevee]
With eevee: a warm sun and grey sky instead of Workbench, so normal maps and roughness show."""
import bpy, sys, math
from mathutils import Vector

src, out = sys.argv[sys.argv.index('--') + 1:][:2]
yaw = float(sys.argv[sys.argv.index('--') + 3]) if len(sys.argv) > sys.argv.index('--') + 3 else 35.0
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
objs = [o for o in scene.objects if o.type == 'MESH']
lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
center = (lo + hi) / 2; size = max(hi - lo)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 1.3
a = math.radians(yaw)
d = Vector((math.sin(a) * math.cos(math.radians(30)), -math.cos(a) * math.cos(math.radians(30)), math.sin(math.radians(30))))
cam.location = center + d * size * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
cam.data.clip_end = size * 20
scene.camera = cam
if 'eevee' in sys.argv:
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scene.collection.objects.link(sun)
    sun.data.energy = 3.0; sun.data.color = (1.0, 0.95, 0.85)
    sun.rotation_euler = (math.radians(40), 0, math.radians(30))
    world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.35, 0.36, 0.4, 1); bg.inputs['Strength'].default_value = 0.8
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.view_settings.view_transform = 'Standard'
else:
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'TEXTURE'
    scene.display.shading.show_cavity = False
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.film_transparent = False
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
