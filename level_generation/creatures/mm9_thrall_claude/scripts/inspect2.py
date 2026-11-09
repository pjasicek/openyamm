"""Hands, pelvis under the skirt. Args: <glb> <out prefix>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = set(); parts = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); ids = []
    while st:
        x = st.pop(); ids.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    parts.append(ids)
parts.sort(key=len, reverse=True)
keep = set(parts[0])
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
bm.to_mesh(o.data); bm.free()
for p in o.data.polygons: p.use_smooth = True
M = o.matrix_world
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
P = np.array([M @ v.co for v in o.data.vertices])
print('P', P.min(0), P.max(0))
def shot(n, c, d, sz):
    d = Vector(d).normalized(); cd.ortho_scale = sz
    cam.location = Vector(c) + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
shot('pelv', (0, 0, 0.05), (0, -1, 0), 0.5)
shot('pelvb', (0, 0, 0.05), (0.5, 1, -0.3), 0.5)
xm = P[:, 0].max(); ym = P[P[:, 0] > xm - 0.01].mean(0)
xn = P[:, 0].min(); yn = P[P[:, 0] < xn + 0.01].mean(0)
print('hands', ym, yn)
shot('handL', (xm - 0.04, ym[1], ym[2] + 0.02), (0.6, -1, 0.3), 0.2)
shot('handR', (xn + 0.04, yn[1], yn[2] + 0.02), (-0.6, -1, 0.3), 0.2)
shot('handL2', (xm - 0.04, ym[1], ym[2] + 0.02), (-1, 0.2, 0.2), 0.2)
shot('handR2', (xn + 0.04, yn[1], yn[2] + 0.02), (1, 0.2, 0.2), 0.2)
