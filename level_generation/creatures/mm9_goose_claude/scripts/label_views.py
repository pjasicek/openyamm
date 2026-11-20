"""Weight views: 'Body' coloured by its weights (palette per bone name) next to the MM9 source mesh coloured by its
dominant bone (from the fit/rig source blend), front/left/q34/top. Args: <rig blend> <mm9 rig blend> <out dir> [size]"""
import bpy, sys, os, hashlib
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
RIG, SRC, OUT = argv[:3]
SIZE = int(argv[3]) if len(argv) > 3 else 700
os.makedirs(OUT, exist_ok=True)


def colour(name):
    h = hashlib.md5(name.encode()).digest()
    return np.array([0.15 + 0.85 * h[0] / 255, 0.15 + 0.85 * h[1] / 255, 0.15 + 0.85 * h[2] / 255])


bpy.ops.wm.open_mainfile(filepath=RIG)
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != body:
        bpy.data.objects.remove(o)
me = body.data
col = me.color_attributes.get('lab') or me.color_attributes.new('lab', 'FLOAT_COLOR', 'POINT')
gn = {g.index: g.name for g in body.vertex_groups}
for v in me.vertices:
    c = sum((g.weight * colour(gn[g.group]) for g in v.groups), np.zeros(3))
    col.data[v.index].color = (*c, 1)
me.color_attributes.active_color = col
with bpy.data.libraries.load(SRC) as (src, dst):
    dst.objects = [n for n in src.objects if n != 'MM9_Rig']
span = max(o.dimensions.x for o in [body]) * 1.6
for o in dst.objects:
    if o is None or o.type != 'MESH':
        continue
    bpy.context.scene.collection.objects.link(o)
    o.parent = None
    o.modifiers.clear()
    o.location.x += span
    c2 = o.data.color_attributes.new('lab', 'FLOAT_COLOR', 'POINT')
    gn2 = {g.index: g.name for g in o.vertex_groups}
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        c2.data[v.index].color = (*colour(gn2[g.group]), 1)
    o.data.color_attributes.active_color = c2
rig = bpy.data.objects['MM9_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_backface_culling = False
sc.render.resolution_x = SIZE * 2; sc.render.resolution_y = SIZE
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(b) for o in sc.objects if o.type == 'MESH' for b in o.bound_box]
c = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
cd.ortho_scale = max(ext[0], 2 * ext[1], 2 * ext[2]) * 1.05
dirs = {'front': Vector((0, -1, 0.05)), 'left': Vector((1, 0, 0.05)), 'q34': Vector((-1.0, -1.25, 0.55)),
        'top': Vector((0, 0.0001, 1)), 'back': Vector((0, 1, 0.05)), 'bottom': Vector((0, 0.0001, -1))}
for k, d in dirs.items():
    cam.location = c + d.normalized() * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f'lab_{k}.png')
    bpy.ops.render.render(write_still=True)
print('LABELS done')
