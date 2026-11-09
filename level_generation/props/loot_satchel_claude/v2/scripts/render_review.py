"""Review renders of the installed v2 satchels, side by side at true relative scale, three-quarter view, textured.
Usage: blender --background --python v2/scripts/render_review.py -- <tiers|distance>
tiers    -> review/tiers.png: large, grey-green ground.
distance -> review/distance.png: the same row seen small on a grass-green ground (about 10 m in game), to judge
            whether each tier reads by colour and size at range."""
import bpy, sys, os, math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import ROOT, REPO

MODE = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
x = 0.0; tallest = 0.0; gap = 0.25
for n in range(1, 7):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, 'assets_dev', 'engine', 'models', f'loot_satchel_t{n}.glb'))
    o = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0]
    o.rotation_mode = 'XYZ'; o.rotation_euler = (0, 0, math.radians(-35))   # three-quarter turn (import is Z-up)
    bpy.context.view_layer.update()
    w = max(o.dimensions.x, o.dimensions.y); tallest = max(tallest, o.dimensions.z)
    x += w / 2; o.location = (x, 0, 0); x += w / 2 + gap
total = x - gap
center = Vector((total / 2, 0, tallest * 0.45))
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'
cam_data.ortho_scale = total * (1.06 if MODE == 'tiers' else 3.5)
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam)
d = Vector((0, -math.cos(math.radians(30)), math.sin(math.radians(30))))
cam.location = center + d * 20; cam_data.clip_end = 100
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.0; sun.data.color = (1.0, 0.95, 0.85); sun.rotation_euler = (math.radians(40), 0, math.radians(30))
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.35, 0.36, 0.4, 1); bg.inputs['Strength'].default_value = 0.8
bpy.ops.mesh.primitive_plane_add(size=cam_data.ortho_scale * 6, location=(total / 2, 0, 0))
ground = bpy.context.active_object
gm = bpy.data.materials.new('ground'); gm.use_nodes = True
colour = (0.18, 0.2, 0.12, 1) if MODE == 'tiers' else (0.09, 0.2, 0.05, 1)
next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = colour
ground.data.materials.append(gm)
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = (2000, 600) if MODE == 'tiers' else (1600, 500)
scene.view_settings.view_transform = 'Standard'
scene.render.filepath = os.path.join(ROOT, 'review', f'{MODE}.png')
bpy.ops.render.render(write_still=True)
print('REVIEW', scene.render.filepath)
