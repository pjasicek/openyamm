"""Textured right-hand close-ups from the textured master (what the review viewer shows: no dagger, the runtime
attaches it). Front, outer side (from her right), inner side (from her left, body hidden), at given clip frames.
Args: -- <blend> <out prefix> <action>:<frame> [...]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.3, 0.32, 0.35)
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.4
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_start = 0.01; cd.clip_end = 10
for spec in a[2:]:
    name, f = spec.split(':'); act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(f))
    c = rig.matrix_world @ rig.pose.bones['B_R_Hand'].head
    for view, d, near in (('front', Vector((0, -1, 0)), 2.0), ('outer', Vector((-1, 0, 0)), 2.0), ('inner', Vector((1, 0, 0)), 0.2)):
        cam.location = c + d * near; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        cd.clip_start = 0.01 if near > 1 else 0.05
        sc.render.filepath = f'{out}_{name}{int(f):03d}_{view}.png'; bpy.ops.render.render(write_still=True)
