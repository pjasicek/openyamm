"""Review renders (Blender, Cycles) of the cage bird against a stand-in of its wall: grey stone with the cage picture
(xwcage, 160 x 320 from the panel bottom = the origin) and the room floor 64 below. Asset metres x 100 = world units.

Usage: blender -b --factory-startup --python render_review.py -- <out_dir> <anim.glb> [static.glb]
Writes front, q (three-quarter), side, close, the clip sheet frames clip_<frame>.png, and static_front.png."""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir, anim = argv[0], argv[1]
static = argv[2] if len(argv) > 2 else None
os.makedirs(out_dir, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
CAGE = os.path.join(REPO, 'assets_dev/worlds/xeen/textures_x2/xwcage.png')
EYE = -0.64 + 1.6       # the party's eye over the room floor, in the tray's frame


def material(name, colour=None, image=None, alpha=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Roughness'].default_value = 0.9
    if image:
        t = m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(image)
        t.interpolation = 'Closest'
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
        if alpha:
            m.node_tree.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
            for attr, value in (('surface_render_method', 'DITHERED'), ('blend_method', 'CLIP')):
                try:
                    setattr(m, attr, value)
                except (AttributeError, TypeError):
                    pass
    else:
        b.inputs['Base Color'].default_value = colour
    return m


def plane(name, size, location, rotation, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=location, rotation=rotation)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0], size[1], 1)
    o.data.materials.append(mat)
    return o


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 48
    s.cycles.use_denoising = True
    s.view_settings.view_transform = 'Standard'
    s.render.resolution_x, s.render.resolution_y = 900, 700
    s.render.fps = 30
    w = bpy.data.worlds.new('w')
    s.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.20, 0.19, 0.17, 1)
    bg.inputs['Strength'].default_value = 0.8
    for nm, energy, rot, col in (('key', 2.8, (55, 0, -30), (1.0, 0.93, 0.82)),
                                 ('fill', 0.8, (65, 0, 140), (0.8, 0.86, 1.0))):
        sun = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
        sun.data.energy = energy
        sun.data.color = col
        sun.data.angle = math.radians(8)
        sun.rotation_euler = [math.radians(a) for a in rot]
        s.collection.objects.link(sun)
    # the wall (Blender y = 0 plane, the room toward -y: glTF +Z out from the wall is Blender -Y)
    plane('wall', (8, 6), (0, 0.002, 1.5), (math.radians(90), 0, 0), material('stone', (0.36, 0.33, 0.28, 1)))
    cage = plane('cage', (1.6, 3.2), (0, -0.001, 1.6), (math.radians(90), 0, 0), material('cage', image=CAGE, alpha=True))
    cage.data.uv_layers.active.data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    plane('niche', (1.6, 3.2), (0, 0.001, 1.6), (math.radians(90), 0, 0), material('dark', (0.04, 0.035, 0.03, 1)))
    plane('floor', (8, 8), (0, -4, -0.64), (0, 0, 0), material('flags', (0.30, 0.24, 0.18, 1)))
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    s.collection.objects.link(cam)
    s.camera = cam
    return s, cam


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def shoot(s, cam, eye, target, name, lens=40):
    cam.data.lens = lens
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = os.path.join(out_dir, name)
    bpy.ops.render.render(write_still=True)


s, cam = reset()
objs = load(anim)
arm = next(o for o in objs if o.type == 'ARMATURE')
action = arm.animation_data.action if arm.animation_data and arm.animation_data.action else None
if action is None:
    action = next(a for a in bpy.data.actions if a.name.startswith('perch'))
    arm.animation_data_create()
    arm.animation_data.action = action
start, end = (int(round(v)) for v in action.frame_range)
print('ACTION', action.name, start, end)
c = (0, -0.2, 0.25)
s.frame_set(start)
shoot(s, cam, (0, -3.2, EYE), c, 'front.png')
shoot(s, cam, (1.9, -2.6, EYE), c, 'q.png')
shoot(s, cam, (2.4, -0.9, 0.5), (0, -0.25, 0.22), 'side.png', 50)
shoot(s, cam, (-0.5, -1.25, 0.62), (0, -0.25, 0.27), 'close.png', 50)
for k in range(8):
    frame = start + round((end - start) * k / 8)
    s.frame_set(frame)
    shoot(s, cam, (-0.4, -1.4, 0.65), (0, -0.25, 0.25), f'clip_{frame:03d}.png', 45)
if static:
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    load(static)
    shoot(s, cam, (-0.5, -1.25, 0.62), (0, -0.25, 0.27), 'static_close.png', 50)
