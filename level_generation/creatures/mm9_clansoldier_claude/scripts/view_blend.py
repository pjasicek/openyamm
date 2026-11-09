"""Diagnosis renders of a blend's Body in part colours. Args: <blend> <out prefix> [cx cy cz ortho] [views]"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body': bpy.data.objects.remove(o)
o = bpy.data.objects['Body']; me = o.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
col = me.color_attributes.new('c', 'BYTE_COLOR', 'CORNER')
rng = np.random.RandomState(5); pal = {k: (*rng.rand(3) * .75 + .2, 1) for k in range(40)}
for p in me.polygons:
    for li in p.loop_indices: col.data[li].color = pal[int(fp[p.index]) % 40]
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_backface_culling = False; sh.show_cavity = True
sc.render.resolution_x = 900; sc.render.resolution_y = 900
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.2, 0.22)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[2:5]]) if len(a) > 4 else Vector((0, 0, 0)); cd.ortho_scale = float(a[5]) if len(a) > 5 else 2.2
views = {'front': (0, -1, 0.05), 'back': (0, 1, 0.05), 'left': (1, 0, 0.05), 'q34': (-1, -1.2, 0.3), 'under': (0, -0.4, -1)}
for n in (a[6].split(',') if len(a) > 6 else views):
    d = Vector(views[n]).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
