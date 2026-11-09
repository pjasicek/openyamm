"""Installed vs head set, tier GLBs from review/viewer: head close-ups (Fly, Hit, Attack and Death peaks, Dead) from
the side, front and three-quarter. Usage: blender -b -P compare_views.py -- <glb> <label> -> review/compare/<label>_*.png"""
import bpy, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
def use(name):
    act = bpy.data.actions[name]; ad = rig.animation_data; ad.action = act
    if act.slots: ad.action_slot = act.slots[0]
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 420; sc.render.engine = 'BLENDER_EEVEE'
os.makedirs(os.path.join(HERE, 'review', 'compare'), exist_ok=True)
fps = sc.render.fps
for clip, sec in [('Fly', 0.0), ('Hit', 0.2), ('Attack', 0.4), ('Death', 0.3), ('Dead', 0.0)]:
    use(clip); sc.frame_set(int(round(sec * fps)))
    head = next(b for b in rig.pose.bones if b.name == 'Head')
    c = rig.matrix_world @ head.tail
    size = 0.9 if clip in ('Attack', 'Death') else 0.45
    # the creature faces -Y after import (its snout points to -Y)
    for view, dv in [('side', Vector((1, 0, .15))), ('front', Vector((0, -1, .1))), ('q34', Vector((.7, -.7, .3))),
                     ('back', Vector((0, 1, .3)))]:
        dv.normalize(); cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(HERE, 'review', 'compare', f'{label}_{clip}_{view}.png'); bpy.ops.render.render(write_still=True)
