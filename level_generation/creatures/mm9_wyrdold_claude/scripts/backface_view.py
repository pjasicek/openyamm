"""Mesh npz with every back face shown red (a flipped red twin behind each face, back faces culled): where the view meets the back of a
one-sided sheet. Args: <npz> <out prefix> <centre x,y,z> <ortho> <size> <views name=dx,dy,dz:...> [parts comma]"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co, tri = D['co'], D['tri']
if len(a) > 6:
    names = [str(x) for x in D['names']]; ks = [names.index(p) for p in a[6].split(',')]; tri = tri[np.isin(D['comp'][tri[:, 0]], ks)]
bpy.ops.wm.read_factory_settings(use_empty=True)
def obj(name, c, t, col):
    me = bpy.data.meshes.new(name); me.from_pydata(c.tolist(), [], t.tolist()); me.update()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new(name); m.diffuse_color = col; me.materials.append(m); return o
obj('front', co, tri, (.75, .75, .72, 1)); obj('back', co, tri[:, ::-1], (1, 0, 0, 1))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = int(a[4]); sc.world = bpy.data.worlds.new('W'); sc.world.color = (.1, .3, .1)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[3]); cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
ce = Vector([float(x) for x in a[2].split(',')])
for v in a[5].split(':'):
    nm, d = v.split('='); d = Vector(tuple(float(x) for x in d.split(','))).normalized()
    cam.location = ce + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{nm}.png'; bpy.ops.render.render(write_still=True)
