"""MM9 clip contact sheet frames (Workbench): Args: <glb> <outdir> <clip:frame,...>"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, spec = argv[0], argv[1], argv[2]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
print([a.name for a in bpy.data.actions][:30])
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get("RES","420"))
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(os.environ.get("ORTHO","2.6")); cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
d = Vector(eval(os.environ.get("DIR","(-1,-1,0.3)"))).normalized(); c = Vector(eval(os.environ.get("CEN","(0,0,0.1)")))
cam.location = c + d * 10; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
for it in spec.split(','):
    nm, fr = it.split(':')
    a = next(x for x in bpy.data.actions if x.name.lower().startswith(nm.lower()))
    arm.animation_data_create(); arm.animation_data.action = a
    try: arm.animation_data.action_slot = a.slots[0]
    except Exception: pass
    sc.frame_set(int(fr)); bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(outdir, f'{nm}_{fr}.png'); bpy.ops.render.render(write_still=True)
print('DONE')
