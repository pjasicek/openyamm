"""Close renders of a rigged blend: ACTION@FRAME list, one view, ortho, centre on a bone. Args: blend outdir view
ortho bone poses(comma) [size] [color]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir, view, ortho, bone, poses = argv[:6]
size = int(argv[6]) if len(argv) > 6 else 420
color = argv[7] if len(argv) > 7 else 'VERTEX'
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in sc.objects:
    if o.type == 'MESH' and os.environ.get('SHOWMM9') != '1' and (o.name.startswith('MM9') or o.name.endswith('.mesh') or o.name == 'MeshyPosed'):
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = color; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
sc.world = bpy.data.worlds.new('w')
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(ortho); cd.clip_end = 1000
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.55)), 'front': Vector((0, -1, 0)), 'left': Vector((1, 0, 0)),
        'right': Vector((-1, 0, 0)), 'top': Vector((0, 0.0001, 1)), 'back': Vector((0, 1, 0)),
        'below': Vector((0.3, -0.5, -1)), 'q34l': Vector((1.0, -1.25, 0.55))}
for pose in poses.split(','):
    name, f = pose.split('@')
    act = bpy.data.actions[name]
    arm.animation_data_create(); arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    sc.frame_set(int(f))
    c = (arm.matrix_world @ arm.pose.bones[bone].head)
    d = dirs[view].normalized()
    cam.location = c + d * 80
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{name}_{f}_{view}_{bone}.png')
    bpy.ops.render.render(write_still=True)
