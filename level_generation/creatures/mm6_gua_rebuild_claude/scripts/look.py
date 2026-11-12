"""Workbench renders of a blend's Body (face colour by an int face attribute, or flat grey), front / right side / back / 3/4,
optional rig pose from an action and frame. Args: <blend> <out png> [attr|none] [action:frame] [zoom centre x,y,z,size]"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = a[0], a[1]; ATTR = a[2] if len(a) > 2 else 'part'; POSE = a[3] if len(a) > 3 and a[3] != '-' else None
ZOOM = [float(x) for x in a[4].split(',')] if len(a) > 4 else None
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
body = bpy.data.objects['Body']
rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: o.hide_render = True
if POSE and rig:
    act, fr = POSE.split(':')
    rig.animation_data_create(); rig.animation_data.action = bpy.data.actions[act]
    sc.frame_set(int(fr))
me = body.data
pal = np.array([[.6, .6, .6], [.75, .45, .2], [.95, .75, .6], [.5, .5, .55], [.9, .2, .2], [.2, .45, .5], [.4, .25, .1], [.8, .6, .2],
                [.3, .3, .8], [.3, .15, .05], [.9, .9, .2], [.6, .2, .7], [.2, .8, .3], [.1, .1, .1], [.5, .9, .9], [.9, .5, .9], [.3, .7, .9], [.95, .55, .45]])
if ATTR != 'none' and ATTR in me.attributes:
    v = np.zeros(len(me.polygons), int); me.attributes[ATTR].data.foreach_get('value', v)
    ca = me.color_attributes.new('lk', 'FLOAT_COLOR', 'CORNER')
    cols = np.zeros((len(me.loops), 4)); cols[:, 3] = 1
    for p in me.polygons:
        cols[p.loop_start:p.loop_start + p.loop_total, :3] = pal[v[p.index] % len(pal)]
    ca.data.foreach_set('color', cols.ravel())
    me.color_attributes.active_color = ca
    sc.display.shading.color_type = 'VERTEX'
else:
    sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.7, .7, .7)
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x = 600; sc.render.resolution_y = 900 if not ZOOM else 600
sc.render.film_transparent = False
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg)
q = np.array([tuple(ev.matrix_world @ v.co) for v in ev.to_mesh().vertices]); ev.to_mesh_clear()
cen = Vector(((q.max(0) + q.min(0)) / 2).tolist()); size = float(np.ptp(q[:, 2])) * 1.08
if ZOOM: cen = Vector(ZOOM[:3]); size = ZOOM[3]
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * (1.0 if ZOOM else 1.0)
tiles = []
for k, (az, el) in enumerate([(0, 0), (90, 0), (180, 0), (35, 12)]):
    r = 6.0; th = math.radians(az); ph = math.radians(el)
    d = Vector((math.sin(th) * math.cos(ph), -math.cos(th) * math.cos(ph), math.sin(ph)))
    cam.location = cen + d * r
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = OUT + f'.{k}.png'; bpy.ops.render.render(write_still=True)
print('LOOK', OUT)
