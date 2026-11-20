"""Posed clay shots of a clip GLB. Args: glb outprefix size cam(front|side|q34|back) spec... spec = Clip:time"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, pre, size, cam_ = a[0], a[1], int(a[2]), a[3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
body = [o for o in sc.objects if o.type == 'MESH']
for o in body:
    for p in o.data.polygons: p.use_smooth = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.72, 0.7, 0.64); sh.show_cavity = True; sh.show_backface_culling = True; sh.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.12, 0.13, 0.15); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam; cd.clip_end = 100; cd.ortho_scale = float(__import__("os").environ.get("ORTHO", 2.5))
D = {'front': (0, -1, 0.05), 'side': (1, 0, 0.05), 'q34': (-1, -1.2, 0.4), 'back': (0, 1, 0.05)}
arm.animation_data_create()
fps = sc.render.fps
for i, s in enumerate(a[4:]):
    clip, t = s.rsplit(':', 1)
    act = bpy.data.actions[next(k.name for k in bpy.data.actions if k.name == clip or k.name.startswith(clip + '_') or clip in k.name)]
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    sc.frame_float = float(t) * fps; sc.frame_set(int(float(t) * fps), subframe=(float(t) * fps) % 1)
    bpy.context.view_layer.update()
    hip = arm.matrix_world @ arm.pose.bones['Bip01 Spine1'].head
    c = Vector((hip.x, hip.y, max(hip.z, 0.75))) if not __import__("os").environ.get("HIPC") else (arm.matrix_world @ arm.pose.bones["Bip01 Pelvis"].head) + Vector((0, 0, float(__import__("os").environ["HIPC"])))
    if float(sc.frame_current) < 0: pass
    d = Vector(D[cam_]).normalized(); cam.location = c + d * 10; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{pre}_{i:02d}.png'; bpy.ops.render.render(write_still=True)
