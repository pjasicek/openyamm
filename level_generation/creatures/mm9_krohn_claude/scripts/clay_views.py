"""Clay renders of a GLB (all meshes, studio light, grey): views front, q34, left, back, right. Args: glb outprefix size"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, size = a[0], a[1], int(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
pts = [o.matrix_world @ v.co for o in sc.objects if o.type == 'MESH' for v in o.data.vertices]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
c = (lo + hi) / 2; ext = max(hi - lo) * 1.05
print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi], 'tris', sum(len(p.vertices) - 2 for o in sc.objects if o.type == 'MESH' for p in o.data.polygons), 'parts', sum(1 for o in sc.objects if o.type == 'MESH'))
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = os.environ.get('COLOR', 'SINGLE')
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(os.environ.get('ORTHO', ext)); cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
if os.environ.get('CENTER'):
    c = Vector([float(x) for x in os.environ['CENTER'].split(',')])
dirs = {'front': Vector((0, -1, 0.05)), 'q34': Vector((-1, -1.25, 0.4)), 'left': Vector((1, 0, 0.05)), 'back': Vector((0, 1, 0.05)), 'right': Vector((-1, 0, 0.05))}
for v in os.environ.get('VIEWS', 'front,q34,left,back,right').split(','):
    d = dirs[v].normalized(); cam.location = c + d * 20
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'; bpy.ops.render.render(write_still=True)
