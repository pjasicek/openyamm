"""Clay renders of npz meshes (co, tri; optional 'part' per vertex coloured). Args: <out prefix> <size> <ortho> <cx,cy,cz> <views csv> <npz>..."""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
out, size, ortho, ctr, views = a[0], int(a[1]), float(a[2]), [float(x) for x in a[3].split(',')], a[4].split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
cols = [(.75, .72, .7, 1), (.8, .35, .3, 1), (.35, .45, .8, 1), (.4, .75, .4, 1), (.8, .75, .3, 1), (.6, .4, .7, 1)]
for k, f in enumerate(a[5:]):
    D = np.load(f); co, tri = D['co'], D['tri']
    me = bpy.data.meshes.new('m%d' % k); me.from_pydata(co.tolist(), [], tri.tolist()); me.update()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new('o%d' % k, me); bpy.context.collection.objects.link(ob)
    if 'part' in D.files:
        part = D['part']; ca = me.color_attributes.new('c', 'FLOAT_COLOR', 'POINT')
        for i, p in enumerate(part): ca.data[i].color = cols[int(p) % len(cols)]
    elif 'comp' in D.files:
        part = D['comp']; ca = me.color_attributes.new('c', 'FLOAT_COLOR', 'POINT')
        for i, p in enumerate(part): ca.data[i].color = cols[int(p) % len(cols)]
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_backface_culling = False; sh.show_cavity = False
import os
if os.environ.get('XRAY'): sh.show_xray = True; sh.xray_alpha = float(os.environ['XRAY'])
sc.render.resolution_x = sc.render.resolution_y = size
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, 0.05), 'back': (0, 1, 0.05), 'left': (-1, 0, 0.05), 'right': (1, 0, 0.05), 'top': (0, 0.001, 1), 'q34': (-1, -1.2, 0.4), 'qback': (1, 1.2, 0.4), 'below': (0.3, -0.5, -1)}
c = Vector(ctr)
for v in views:
    d = Vector(D[v]).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'; bpy.ops.render.render(write_still=True)
