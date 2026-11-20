"""Clay renders of a rigged master blend (rest pose): views q34, front, left, back, right. Args: blend outdir prefix size ortho [center z]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, outdir, prefix, size, ortho = argv[0], argv[1], argv[2], int(argv[3]), float(argv[4])
cz = float(argv[5]) if len(argv) > 5 else None
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
o = next(o for o in sc.objects if o.type == 'MESH')
for m in o.modifiers: m.show_render = m.show_viewport = False
for p in o.data.polygons: p.use_smooth = True
pts = [o.matrix_world @ v.co for v in o.data.vertices]
c = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
if cz is not None: c = Vector((0, 0, cz))
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.8, 0.78, 0.75)
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.55)), 'front': Vector((0, -1, 0.08)), 'left': Vector((1, 0, 0.08)),
        'back': Vector((0, 1, 0.08)), 'right': Vector((-1, 0, 0.08))}
for v, d in dirs.items():
    d = d.normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png'); bpy.ops.render.render(write_still=True)
