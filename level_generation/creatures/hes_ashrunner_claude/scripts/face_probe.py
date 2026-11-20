"""Head-area probe of a rig blend at rest: per piece (head, hood, goggles, eyes) vertex count, bounds and centre, and
workbench renders with one colour per piece (front, three-quarter, left) close on the face.
Args: -- <blend> <out prefix> [object name, default Body]"""
import bpy, sys, os, colorsys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
obj = bpy.data.objects[a[2] if len(a) > 2 else 'Body']
sc = bpy.context.scene
rig = bpy.data.objects['Rig']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = obj.data
co = np.array([tuple(obj.matrix_world @ v.co) for v in me.vertices])
pv = np.array([x.value for x in me.attributes['piece'].data])
for p in (2, 3, 10, 25, 81, 38, 40):
    m = pv == p
    if m.any():
        print('PIECE', p, int(m.sum()), 'lo', np.round(co[m].min(0), 3).tolist(), 'hi', np.round(co[m].max(0), 3).tolist(),
              'c', np.round(co[m].mean(0), 3).tolist())
hb = rig.data.bones['B_Head']
print('HEADBONE', np.round(np.array(rig.matrix_world @ hb.head_local), 3).tolist(),
      np.round(np.array(rig.matrix_world @ hb.tail_local), 3).tolist())
col = me.color_attributes.new('probe', 'BYTE_COLOR', 'POINT')
rng = np.random.default_rng(3)
pal = {}
for i, p in enumerate(pv):
    if p not in pal:
        pal[p] = colorsys.hsv_to_rgb(rng.random(), 0.6, 0.9) + (1.0,)
    col.data[i].color = pal[p]
for p, c in ((2, (0.9, 0.7, 0.6, 1)), (3, (0.5, 0.5, 0.55, 1)), (10, (1, 0.8, 0, 1)), (25, (1, 0, 0, 1)),
             (81, (0, 1, 0, 1)), (38, (0, 0, 1, 1)), (40, (0, 0, 1, 1))):
    for i in np.nonzero(pv == p)[0]:
        col.data[i].color = c
me.color_attributes.active_color = col
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 600
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not obj:
        o.hide_render = True
c = Vector(tuple(co[pv == 2].mean(0))) + Vector((0, 0, 0.03))
for name, d in (('front', (0, -1, 0.05)), ('tq', (-0.6, -0.8, 0.1)), ('left', (-1, 0, 0.05)), ('top', (0, -0.6, 0.8))):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(cam); cam.data.lens = 85
    cam.location = c + Vector(d).normalized() * 0.75; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam; sc.render.filepath = f'{a[1]}_{name}.png'; bpy.ops.render.render(write_still=True)
print('FACEPROBE', a[1])
