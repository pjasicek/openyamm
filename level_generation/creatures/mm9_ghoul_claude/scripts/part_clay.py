"""Views of 'Body' coloured by the part attribute. Args: blend outprefix size then name=cx,cy,cz,dx,dy,dz,ortho ..."""
import bpy, sys, colorsys
from mathutils import Vector
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
pre, size = a[1], int(a[2])
sc = bpy.context.scene
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
me = body.data
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
pal = {0: (0.75, 0.7, 0.62), 1: (0.3, 0.8, 0.3), 2: (0.2, 0.6, 1), 3: (1, 0.9, 0.2), 6: (1, 0.2, 0.2), 7: (0.9, 0.2, 0.9), 10: (0.75, 0.6, 0.5), 11: (0.3, 0.2, 0.15), 12: (1, 1, 0.8), 13: (1, 0.5, 0)}
me.materials.clear()
ks = sorted(pal)
for k in ks:
    m = bpy.data.materials.new(str(k)); m.diffuse_color = (*pal[k], 1); me.materials.append(m)
for p in me.polygons:
    p.material_index = ks.index(pa[p.vertices[0]]) if pa[p.vertices[0]] in pal else 0; p.use_smooth = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.1, 0.1, 0.12); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for s in a[3:]:
    n, v = s.split('='); f = [float(x) for x in v.split(',')]
    d = Vector(f[3:6]).normalized(); c = Vector(f[:3]); cd.ortho_scale = f[6]; cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{pre}_{n}.png'; bpy.ops.render.render(write_still=True)
