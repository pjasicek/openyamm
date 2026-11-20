"""Close renders of the head following Xheadpiv: <anim blend> <outdir> <clip@frame,...> [ortho]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
ortho = float(argv[3]) if len(argv) > 3 else 0.7
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
for m in bpy.data.materials:
    m.diffuse_color = (0.8, 0.8, 0.8, 1)
sc.render.resolution_x = sc.render.resolution_y = 384
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(argv[1], exist_ok=True)
for spec in argv[2].split(','):
    name, frame = spec.split('@')
    act = bpy.data.actions[name]
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    sc.frame_set(int(frame)); bpy.context.view_layer.update()
    c = rig.matrix_world @ rig.pose.bones['Xheadpiv'].head + Vector((0, -0.15, -0.05))
    for vn, d in (('side', Vector((-1, -0.3, 0.2))), ('front', Vector((-0.5, -1, 0.2)))):
        d.normalize(); cam.location = c + d * 5
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(argv[1], f'{name}_{frame}_{vn}.png'); bpy.ops.render.render(write_still=True)
