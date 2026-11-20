"""Clay (or textured) views of a GLB or a .blend's meshes for diagnosis. Workbench, studio light, grey background.
Args: -- <glb|blend> <out png> <cx,cy,cz> <ortho> <views: front,q34,left,right,back,below,q34low,top> [textured]
Writes one row of square 768 px tiles. The creature faces -Y (Blender)."""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, c, ortho, views = a[0], a[1], Vector([float(x) for x in a[2].split(',')]), float(a[3]), a[4].split(',')
tex = len(a) > 5 and a[5] == 'textured'
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'ARMATURE':
        if o.animation_data:
            o.animation_data.action = None
        for pb in o.pose.bones:
            pb.matrix_basis.identity()
    if o.type == 'MESH' and o.name.startswith('MM9_'):
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = os.environ.get('LIGHT', 'STUDIO')
sh.color_type = 'TEXTURE' if tex else 'SINGLE'
sh.single_color = (0.75, 0.72, 0.68)
sh.show_backface_culling = False
sh.show_cavity = not tex
RW, RH = [int(x) for x in os.environ.get('RES', '768x768').split('x')]
sc.render.resolution_x, sc.render.resolution_y = RW, RH
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.35, 0.35, 0.37)
sc.render.film_transparent = bool(os.environ.get('ALPHA'))
sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': (-1.0, -1.25, 0.35), 'front': (0, -1, 0.02), 'left': (1, 0, 0.02), 'back': (0, 1, 0.02),
        'right': (-1, 0, 0.02), 'below': (0, -1, -0.6), 'q34low': (-0.8, -1, -0.45), 'top': (0, -0.0001, 1),
        'q34r': (1.0, -1.25, 0.35)}
tiles = []
for v in views:
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    p = out + f'.{v}.png'
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    tiles.append(p)
if os.environ.get('KEEP_TILES'):
    print('CLAY tiles', tiles); sys.exit(0)
img = bpy.data.images.new('sheet', 768 * len(tiles), 768)
px = [0.0] * (768 * len(tiles) * 768 * 4)
for k, p in enumerate(tiles):
    im = bpy.data.images.load(p)
    src_px = list(im.pixels)
    for y in range(768):
        row = src_px[y * 768 * 4:(y + 1) * 768 * 4]
        o = (y * 768 * len(tiles) + k * 768) * 4
        px[o:o + 768 * 4] = row
    os.remove(p)
img.pixels = px
img.filepath_raw = out
img.file_format = 'PNG'
img.save()
print('CLAY', out)
