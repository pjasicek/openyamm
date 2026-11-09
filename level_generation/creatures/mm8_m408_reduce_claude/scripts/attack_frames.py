"""Attack frames for the native comparison: a .blend master (Couatl_Rig) or a creature GLB, the Attack action at the
clip times matched to the native m408aa-ah phases, front (native view 0) and side (native view 2: head right),
textured workbench, fixed orthographic framing with the ground line.
Usage: blender -b -P attack_frames.py -- <in.blend|in.glb> <out_dir> <tag>"""
import math, os, sys
import bpy
from mathutils import Vector
src, out, tag = sys.argv[sys.argv.index('--') + 1:][:3]
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene; scene.render.fps = 24
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
for o in scene.objects:
    if o.type == 'MESH' and o.hide_render is False and not any(m.type == 'ARMATURE' for m in o.modifiers):
        o.hide_render = True
rig.animation_data_create(); rig.animation_data.action = bpy.data.actions['Attack']
if rig.animation_data.action_slot is None and bpy.data.actions['Attack'].slots:
    rig.animation_data.action_slot = bpy.data.actions['Attack'].slots[0]
scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False
scene.world = bpy.data.worlds.new('W'); scene.world.color = (.09, .1, .12)
scene.render.resolution_x, scene.render.resolution_y = 360, 420
scene.render.film_transparent = False
bpy.ops.mesh.primitive_plane_add(size=0.004, location=(0, 0, 0))
line = bpy.context.object; bpy.ops.transform.resize(value=(800, 0.25, 1)); line.color = (.5, .5, .5, 1)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'
# native frame ms -> clip seconds: start, full rear (ad) at the end of the rear hold, low point (af) at the 0.9 s
# impact marker, recovery after it
NATIVE = [0, 125, 250, 375, 500, 625, 750, 875]
CLIP = [0., .2, .4, .6, .75, .9, 1.05, 1.2]
views = {'front': (Vector((0, -6, .55)), 1.6), 'side': (Vector((-6, -.1, .55)), 1.9)}
for name, (pos, scale) in views.items():
    cam.data.ortho_scale = scale
    target = Vector((pos.x * 0, pos.y * 0 + (-.1 if name == 'side' else 0), .55))
    cam.location = pos if name == 'front' else Vector((-6, -.1, .55))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for ms, t in zip(NATIVE, CLIP):
        f = t * 24; scene.frame_set(int(f), subframe=f - int(f))
        scene.render.filepath = os.path.join(out, f'{tag}_{name}_{ms:03d}.png')
        bpy.ops.render.render(write_still=True)
print('DONE', tag)
