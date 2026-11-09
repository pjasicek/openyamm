"""Identical-camera stills of review GLBs for the texture-quality pass (before/after sheets): Eevee, one sun from
above-front plus a grey sky, rest pose (Standing frame 0), the user's close-up framing (head, left arm and claw from the
creature's left side, close) plus full-body front and three-quarter.

Args: <in.glb> <out prefix> [image_substring=override.png ...]
Writes <prefix>_close.png, <prefix>_front.png, <prefix>_q34.png (1200 x 800). Overrides replace a material image
whose name contains the substring (texel-density heatmaps)."""
import bpy, sys, math
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
overrides = dict(a.split('=', 1) for a in args[2:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data and 'Standing' in bpy.data.actions:
    rig.animation_data.action = bpy.data.actions['Standing']
sc = bpy.context.scene
sc.frame_set(0)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:                                   # LOD0 only
    o.hide_render = any(t in o.name for t in ('LOD', 'Shadow'))
for mat in bpy.data.materials:
    if not mat.node_tree:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            for key, path in overrides.items():
                if key in node.image.name:
                    node.image = bpy.data.images.load(path)
                    node.image.colorspace_settings.name = 'sRGB'
                    node.interpolation = 'Closest'
bpy.context.view_layer.update()


def bone(name):
    return rig.matrix_world @ rig.pose.bones[name].head


head, claw, root = bone('Bone36'), bone('Bone15'), bone('Bone37')
corners = [rig.matrix_world @ p for b in rig.pose.bones for p in (b.head, b.tail)]   # skinned bounds: the bones
lo = Vector([min(c[i] for c in corners) for i in range(3)])
hi = Vector([max(c[i] for c in corners) for i in range(3)])
centre = (lo + hi) / 2
size = max(hi - lo)
up = Vector((0, 0, 1))
forward = (head - root)
forward.z = 0
forward.normalize()
side = forward.cross(up).normalized()
if (claw - root).dot(side) < 0:
    side = -side                                    # the camera on the side of the left (Bone39) arm
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1200, 800
sc.render.film_transparent = False
world = bpy.data.worlds.new('w')
sc.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.32, 0.33, 0.35, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.2
sc.collection.objects.link(sun)
sun.rotation_euler = (forward * 0.6 + up * 1.0).to_track_quat('Z', 'Y').to_euler()
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 50


def shoot(name, target, direction, distance):
    cam.location = target + direction.normalized() * distance
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{name}.png'
    bpy.ops.render.render(write_still=True)


focus = (head + claw) / 2
shoot('close', focus, side * 1.0 + forward * 0.25 + up * 0.08, (head - claw).length * 2.6 + size * 0.15)
shoot('front', centre, forward + up * 0.25, size * 1.5)
shoot('q34', centre, forward + side + up * 0.45, size * 1.5)
print('VIEWS', out)
