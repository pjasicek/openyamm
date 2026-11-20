"""Part-coloured render with back faces magenta (a flipped twin: with culling, the twin shows wherever the view meets a mesh's back face, i.e.
looks into an opening). Args: <npz> <out prefix> <centre x,y,z> <ortho> <size> <views name=dx,dy,dz:...>"""
import bpy, sys, colorsys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co, tri, comp = D['co'], D['tri'], D['comp']
bpy.ops.wm.read_factory_settings(use_empty=True)
for flip in (0, 1):
    t = tri[:, ::-1] if flip else tri
    me = bpy.data.meshes.new('m%d' % flip); me.from_pydata(co.tolist(), [], t.tolist()); me.update()
    vc = me.color_attributes.new('c', 'FLOAT_COLOR', 'POINT')
    cols = np.array([(1.0, 0.0, 1.0, 1.0) if flip else (*colorsys.hsv_to_rgb((c * 0.381) % 1, 0.45, 0.85), 1.0) for c in comp])
    vc.data.foreach_set('color', cols.ravel())
    o = bpy.data.objects.new('m%d' % flip, me); bpy.context.scene.collection.objects.link(o)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'
sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = int(a[4]); sc.world = bpy.data.worlds.new('W'); sc.world.color = (.3, .3, .33)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[3]); cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
ce = Vector([float(x) for x in a[2].split(',')])
for v in a[5].split(':'):
    nm, d = v.split('='); d = Vector(tuple(float(x) for x in d.split(','))).normalized()
    cam.location = ce + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{nm}.png'; bpy.ops.render.render(write_still=True)
