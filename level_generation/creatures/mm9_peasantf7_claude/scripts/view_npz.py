"""Clay or part-coloured views of a mesh npz (co, tri, optional comp per vertex). Args: <npz> <out prefix> <centre x,y,z> <ortho> <size> <views a:b:c or name=dx,dy,dz> [color]"""
import bpy, sys, colorsys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co, tri = D['co'], D['tri']
if 'keep' in D.files: pass
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('m'); me.from_pydata(co.tolist(), [], tri.tolist()); me.update()
import os as _os, bmesh as _bm
if _os.environ.get('WELD'):
    _b = _bm.new(); _b.from_mesh(me); _bm.ops.remove_doubles(_b, verts=_b.verts, dist=1e-5); _b.to_mesh(me); _b.free()
for p in me.polygons: p.use_smooth = True
o = bpy.data.objects.new('m', me); bpy.context.scene.collection.objects.link(o)
col = len(a) > 6 and 'comp' in D.files
if col:
    c = D['comp']; vc = me.color_attributes.new('c', 'FLOAT_COLOR', 'POINT')
    for i in range(len(co)):
        r, g, b = colorsys.hsv_to_rgb((c[i] * 0.381) % 1, 0.55, 0.9); vc.data[i].color = (r, g, b, 1)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_backface_culling = False
sh.color_type = 'VERTEX' if col else 'SINGLE'; sh.single_color = (.72, .72, .72)
sc.render.resolution_x = sc.render.resolution_y = int(a[4]); sc.world = bpy.data.worlds.new('W'); sc.world.color = (.3, .3, .33)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[3]); cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
ce = Vector([float(x) for x in a[2].split(',')])
DIR = {'front': (0, -1, 0.05), 'back': (0, 1, .05), 'left': (1, 0, .05), 'right': (-1, 0, .05), 'q34': (-1, -1.25, .4), 'q34l': (1, -1.25, .4), 'q34b': (1, 1.2, .3), 'top': (0, -.01, 1), 'bottom': (0, -.01, -1), 'below': (.4, -.7, -1)}
for v in a[5].split(':'):
    if '=' in v: nm, d = v.split('='); d = tuple(float(x) for x in d.split(','))
    else: nm, d = v, DIR[v]
    d = Vector(d).normalized(); cam.location = ce + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{nm}.png'; bpy.ops.render.render(write_still=True)
