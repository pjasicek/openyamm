"""Clay renders of the head set from our own mesh, the geometry the Codex paints go on. Args: <uv blend> <out dir>"""
import bpy, bmesh, sys
from mathutils import Vector
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
for m in list(body.modifiers): body.modifiers.remove(m)
body.parent = None
me = body.data
mat = np.zeros(len(me.polygons), int); me.attributes['mat'].data.foreach_get('value', mat)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if mat[f.index] != 2], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free()
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
for p in me.polygons: p.use_smooth = True
P = np.array([v.co[:] for v in me.vertices]); print('HEADBOX', P.min(0).round(3), P.max(0).round(3))
c = Vector(((P[:, 0].min() + P[:, 0].max()) / 2, (P[:, 1].min() + P[:, 1].max()) / 2, (P[:, 2].min() + P[:, 2].max()) / 2))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .76, .72); sh.show_cavity = True; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 1254; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 0.8; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1), '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}/clay_{v}.png'; bpy.ops.render.render(write_still=True)
print('HEADCLAY', tuple(c))
