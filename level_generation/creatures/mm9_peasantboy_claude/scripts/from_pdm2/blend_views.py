"""Workbench renders of a blend's 'Body' (rest pose) around a point: diagnostic only.
Args: <blend> <out png> <cx,cy,cz | 'all'> <ortho size> [views: front,back,left,right,q34,below,top] [size px]
Writes one sheet with the views side by side. Faces with the attribute `hand`=1 are tinted blue, `head`=1 red when
COLOR=parts is set; otherwise the material/texture colours (COLOR=tex) or plain clay."""
import bpy, sys, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, out, cen, ortho = argv[0], argv[1], argv[2], float(argv[3])
views = (argv[4] if len(argv) > 4 else 'front,left,back,right').split(',')
size = int(argv[5]) if len(argv) > 5 else 600
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
body = bpy.data.objects['Body']
rig = body.parent
if rig is not None:
    if rig.animation_data:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
for o in sc.objects:
    o.hide_render = o is not body
bpy.context.view_layer.update()
me = body.data
mode = os.environ.get('COLOR', 'clay')
if mode == 'parts':
    import numpy as np
    n = len(me.polygons)
    hd = np.zeros(n, int); hn = np.zeros(n, int)
    if 'head' in me.attributes:
        me.attributes['head'].data.foreach_get('value', hd)
    if 'hand' in me.attributes:
        me.attributes['hand'].data.foreach_get('value', hn)
    base = len(me.materials)
    for nm, c in (('c0', (0.75, 0.75, 0.75, 1)), ('c1', (0.9, 0.35, 0.3, 1)), ('c2', (0.3, 0.5, 0.95, 1))):
        m = bpy.data.materials.new(nm); m.diffuse_color = c; me.materials.append(m)
    me.polygons.foreach_set('material_index', (base + hd + 2 * hn).tolist())
sh = sc.display.shading
sc.render.engine = 'BLENDER_WORKBENCH'
sh.light = 'STUDIO'
sh.color_type = {'parts': 'MATERIAL', 'tex': 'TEXTURE'}.get(mode, 'SINGLE')
sh.single_color = (0.72, 0.7, 0.66)
sh.show_cavity = mode == 'clay'
sc.render.resolution_x = sc.render.resolution_y = size
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.32, 0.34, 0.38)
sh.background_type = 'WORLD'
dg = bpy.context.evaluated_depsgraph_get()
if cen == 'all':
    pts = [body.matrix_world @ v.co for v in body.evaluated_get(dg).to_mesh().vertices]
    c = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
else:
    c = Vector([float(x) for x in cen.split(',')])
dirs = {'front': (0, -1, 0.05), 'back': (0, 1, 0.05), 'left': (1, 0, 0.05), 'right': (-1, 0, 0.05),
        'q34': (-0.8, -1, 0.35), 'q34l': (0.8, -1, 0.35), 'below': (0, -0.3, -1), 'top': (0, -0.01, 1)}
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
files = []
for v in views:
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    f = out[:-4] + f'_{v}.png'
    sc.render.filepath = f
    bpy.ops.render.render(write_still=True)
    files.append(f)
imgs = [bpy.data.images.load(f) for f in files]
W = size * len(imgs)
sheet = bpy.data.images.new('sheet', W, size)
import numpy as np
px = np.zeros((size, W, 4), np.float32)
for k, im in enumerate(imgs):
    px[:, k * size:(k + 1) * size] = np.array(im.pixels[:], np.float32).reshape(size, size, 4)
sheet.pixels = px.ravel()
sheet.filepath_raw = out; sheet.file_format = 'PNG'; sheet.save()
for f in files:
    os.remove(f)
print('VIEWS', out)
