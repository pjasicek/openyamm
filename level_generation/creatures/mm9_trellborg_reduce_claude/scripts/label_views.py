"""Workbench renders of work/source.blend Body coloured by a per-face label array (LABELS npz key KEY, or a bool .npy) ->
review/labels/<tag>_<view>.png. Env: LABELS, KEY, TAG, ZOOM=head|body."""
import os, bpy, numpy as np, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
body = bpy.data.objects['Body']; me = body.data; me.calc_loop_triangles()
src = os.environ['LABELS']; lab = np.load(src)[os.environ['KEY']] if src.endswith('.npz') else np.load(src)
lab = lab.astype(int)
assert len(lab) == len(me.loop_triangles) == len(me.polygons)
pal = np.array([[.5, .5, .5], [.85, .75, .6], [.9, .3, .3], [.3, .6, .9], [.2, .8, .2], [.6, .3, .8], [.9, .9, .2], [1, 1, 1], [.4, .25, .1], [0, 1, 1]])
col = me.color_attributes.new('lab', 'FLOAT_COLOR', 'CORNER')
cs = np.zeros((len(me.loops), 4)); cs[:, 3] = 1
for p in me.polygons:
    for l in p.loop_indices: cs[l, :3] = pal[lab[p.index] % len(pal)]
col.data.foreach_set('color', cs.reshape(-1))
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
body.modifiers.clear()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'VERTEX'; sc.display.shading.light = 'STUDIO'
sc.display.shading.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('RES', 800))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
mw = body.matrix_world
pts = np.array([mw @ v.co for v in me.vertices])
if os.environ.get('ZOOM', 'head') == 'head':
    sel = pts[:, 2] > pts[:, 2].max() - 0.55; ctr = pts[sel].mean(0); ctr[2] = pts[:, 2].max() - 0.27; scale = 0.6
elif os.environ.get('ZOOM') in ('handR', 'handL'):
    sg = -1 if os.environ['ZOOM'] == 'handR' else 1
    loc = np.array([v.co[:] for v in me.vertices])
    sel = (loc[:, 0] * sg > 0.48) & (loc[:, 2] < -0.1) & (loc[:, 2] > -0.4); ctr = pts[sel].mean(0); scale = 0.4
    print('HAND center', ctr, sel.sum(), np.array(mw))
else:
    ctr = (pts.min(0) + pts.max(0)) / 2; scale = 2.5
cam.data.ortho_scale = float(os.environ.get('SCALE', scale))
views = {'front': (0, -1, 0), 'side': (1, 0, 0), 'back': (0, 1, 0), 'q34': (0.7, -0.7, 0), 'lside': (-1, 0, 0), 'top': (0.001, -0.3, 1), 'low': (0.4, -0.8, -0.45)}
# glTF import: which way does the figure face? figure faces -y (creature frame)
for name, dv in views.items():
    dv = Vector(dv).normalized(); cam.location = Vector(ctr) + dv * 5
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', 'labels', f"{os.environ.get('TAG', 'lab')}_{name}.png")
    bpy.ops.render.render(write_still=True)
print('RENDERED')
