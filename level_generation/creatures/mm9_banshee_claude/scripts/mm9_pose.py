"""MM9 frames, textured. Args: glb outprefix ortho cx,cy,cz spec... (spec = action@frame:view)"""
import bpy, sys
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=A[0])
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in sc.objects:
    if o.name.startswith('Icosphere'):
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = 500; sc.render.resolution_y = 500
ortho = float(A[2]); c0 = A[3]
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
arm.animation_data_create()
D = {'front': (0, -1, .02), 'side': (1, 0, .02), 'q34': (.7, -1, .2), 'back': (0, 1, .1)}
bone = None
if c0.startswith('bone:'):
    bone = c0[5:]
else:
    c = Vector([float(x) for x in c0.split(',')])
for i, s in enumerate(A[4:]):
    spec, view = s.split(':')
    act, f = spec.split('@')
    a = next((x for x in bpy.data.actions if x.name.startswith(act)), None)
    arm.animation_data.action = a
    try:
        arm.animation_data.action_slot = a.slots[0]
    except Exception:
        pass
    sc.frame_set(0); sc.frame_set(int(round(float(f) * 24)))
    bpy.context.view_layer.update()
    if bone:
        c = arm.matrix_world @ arm.pose.bones[bone].head
    d = Vector(D[view]).normalized(); cam.location = c + d * 8
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{A[1]}_{i:02d}.png'; bpy.ops.render.render(write_still=True)
print('ACTIONS', [a.name for a in bpy.data.actions][:5])
