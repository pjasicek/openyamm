"""Contact sheet: the four installed tiers side by side at the same scale, three-quarter view, textured.
Usage: blender --background --python scripts/render_sheet.py -- [out.png] [lod]
Default output review/tiers.png at LOD0; with lod 1..3 the given level's node is shown instead (link removes the LOD
nodes, so this reads the work/t<N>_lods.blend objects)."""
import bpy, sys, os, math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import ROOT, REPO

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(args[0]) if args else os.path.join(ROOT, 'review', 'tiers.png')
LOD = int(args[1]) if len(args) > 1 else 0

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
x = 0.0
for n in (1, 2, 3, 4, 5, 6):
    if not os.path.exists(os.path.join(REPO, 'assets_dev', 'engine', 'models', f'loot_satchel_t{n}.glb')):
        continue
    before = set(bpy.data.objects)
    if LOD == 0:
        bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, 'assets_dev', 'engine', 'models', f'loot_satchel_t{n}.glb'))
        objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    else:
        with bpy.data.libraries.load(os.path.join(ROOT, 'work', f't{n}_lods.blend')) as (src, dst):
            dst.objects = [f'LootSatchelT{n}_LOD{LOD}']
        objs = [o for o in dst.objects]
        for o in objs:
            scene.collection.objects.link(o)
    o = objs[0]
    w = o.dimensions.x
    tallest = max(globals().get('tallest', 0.0), max(o.dimensions))
    x += w / 2
    o.location = (x, 0, 0)
    x += w / 2 + 0.12
    o.rotation_mode = 'XYZ'

total = x - 0.12
center = Vector((total / 2, 0, tallest * 0.45))
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = max(total * 1.08, tallest * 1.5 / 0.35)
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam)
d = Vector((0, -math.cos(math.radians(30)), math.sin(math.radians(30))))
cam.location = center + d * 4
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
next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.18, 0.2, 0.12, 1)
ground.data.materials.append(gm)
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 2000; scene.render.resolution_y = 700
scene.view_settings.view_transform = 'Standard'
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('SHEET', OUT)
