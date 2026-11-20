"""Review renders of an exported rock GLB (LOD objects not linked yet), MM6 review lighting (sky + sun):
LOD0..3 from the sprite's view (review yaw, 15 degrees up) and an LOD0 turntable at +0/90/180/270 degrees.
COLOR_0 is multiplied into the base colour, as the engine does. Args: <rock> [glb]. Writes work/<rock>/review/*.png"""
import bpy, json, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scans

args = sys.argv[sys.argv.index('--') + 1:]
rock = args[0]
cfg = json.load(open(os.path.join(scans.HERE, 'rocks.json')))[rock]
glb = args[1] if len(args) > 1 else os.path.join(scans.HERE, 'work', rock, f'{rock}_export.glb')
out = os.path.join(scans.HERE, 'work', rock, 'review'); os.makedirs(out, exist_ok=True)
yaw0 = float(cfg['review_yaw']); el0 = float(cfg.get('review_el', 15))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    nt = mat.node_tree; pb = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if pb is None or not pb.inputs['Base Color'].links:
        continue
    src = pb.inputs['Base Color'].links[0].from_socket
    if src.node.type == 'TEX_IMAGE':                   # importer left COLOR_0 out of the material: multiply it in
        vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(src, mix.inputs['A']); nt.links.new(vc.outputs['Color'], mix.inputs['B'])
        nt.links.new(mix.outputs['Result'], pb.inputs['Base Color'])
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
scene.eevee.taa_render_samples = 32
world = bpy.data.worlds.new('World'); scene.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1.0); bg.inputs['Strength'].default_value = 0.9
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.2
sun.data.angle = math.radians(3); scene.collection.objects.link(sun)
cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera')); scene.collection.objects.link(cam)
scene.camera = cam; cam.data.lens = 50


def bounds(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))


def shoot(target, yaw, path, el=None):
    el = el0 if el is None else el
    lo, hi = bounds(target); centre = (lo + hi) / 2; radius = (hi - lo).length / 2
    fov = 2 * math.atan(cam.data.sensor_width / (2 * cam.data.lens)); dist = radius * 1.08 / math.sin(fov / 2)
    d = Vector((math.sin(math.radians(yaw)) * math.cos(math.radians(el)),
                -math.cos(math.radians(yaw)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    cam.location = centre + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    # sun from the camera's upper left, as in the sprites (fixed relative to the view)
    sun.rotation_euler = (math.radians(40), 0, math.radians(yaw - 35))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


objs.sort(key=lambda o: len(o.name))
for o in objs:
    o.hide_render = True
for level, o in enumerate(objs):
    o.hide_render = False
    shoot(objs[0], yaw0, os.path.join(out, f'render_lod{level}.png'))
    o.hide_render = True
objs[0].hide_render = False
for extra in (0, 90, 180, 270):
    shoot(objs[0], yaw0 + extra, os.path.join(out, f'render_yaw{extra:03d}.png'))
print('REVIEW', rock, [o.name for o in objs])
