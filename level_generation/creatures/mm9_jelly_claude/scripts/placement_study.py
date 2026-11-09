"""Placement study: MM9 lobber hanging on its claw tips vs flipped upright (rotated 180 deg about the forward axis),
both on a floor plane, a few StandAir/Rattack1 frames. Args: glb out.png"""
import bpy, sys, math, os
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def load(dx, flip):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    for o in new:
        if o.name.startswith('Icosphere'):
            o.hide_render = True
    arm.rotation_mode = 'XYZ'
    if flip:
        arm.rotation_euler = (0, math.pi, 0)
        arm.location = (dx, 0, 0.7926)
    else:
        arm.location = (dx, 0, 0.80)
    return arm
a = load(-0.9, False)
b = load(0.9, True)
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = 900; sc.render.resolution_y = 560
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 3.6
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, 0.8)); d = Vector((-0.8, -1.4, 0.35)).normalized()
cam.location = c + d * 10; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
os.makedirs(out, exist_ok=True)
for clip, frames in (('StandAir', (0, 18)), ('Rattack1', (8,)), ('winceAir1', (12,))):
    for arm in (a, b):
        act = bpy.data.actions[clip] if clip in bpy.data.actions else None
        arm.animation_data_create(); arm.animation_data.action = act
        try:
            arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, f'{clip}_{f:02d}.png')
        bpy.ops.render.render(write_still=True)
print('STUDY done')
