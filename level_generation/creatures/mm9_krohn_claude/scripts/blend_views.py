"""Workbench renders of a .blend's Body (+ props) at rest: views around a centre. Args: blend outprefix size ortho cx,cy,cz [views]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
out, size, ortho = a[1], int(a[2]), float(a[3])
c = Vector([float(x) for x in a[4].split(',')])
views = (a[5] if len(a) > 5 else 'front,q34,left,back').split(',')
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'ARMATURE' and o.animation_data:
        o.animation_data.action = None
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'
sh.color_type = os.environ.get('COLOR', 'SINGLE'); sh.show_backface_culling = bool(os.environ.get('CULL'))
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'front': Vector((0, -1, 0.05)), 'q34': Vector((-1, -1.25, 0.4)), 'left': Vector((1, 0, 0.05)), 'back': Vector((0, 1, 0.05)),
        'right': Vector((-1, 0, 0.05)), 'top': Vector((0, -0.2, 1)), 'low': Vector((-0.5, -1, -0.5)), 'under': Vector((0.3, 0.2, -1))}
for v in views:
    d = dirs[v].normalized(); cam.location = c + d * 20
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'; bpy.ops.render.render(write_still=True)
print('VIEWS', out)
