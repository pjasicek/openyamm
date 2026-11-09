"""Meshy return: connected parts and clay views. Args: <glb> <out prefix>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
obs = [o for o in sc.objects if o.type == 'MESH']
print('OBJS', [(o.name, len(o.data.vertices), len(o.data.polygons), [round(x, 3) for x in o.matrix_world.to_translation()], [round(x, 3) for x in o.dimensions]) for o in obs])
o = obs[0]
M = np.array(o.matrix_world)
P = np.array([v.co for v in o.data.vertices]) @ M[:3, :3].T + M[:3, 3]
print('BOUNDS', P.min(0).round(3), P.max(0).round(3))
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
for i, ids in enumerate(parts[:60]):
    Q = P[ids]
    print('PART', i, len(ids), Q.min(0).round(3).tolist(), Q.max(0).round(3).tolist())
print('NPARTS', len(parts), 'verts', len(P), 'faces', len(bm.faces), 'non-manifold', sum(1 for e in bm.edges if not e.is_manifold), 'boundary', sum(1 for e in bm.edges if e.is_boundary))
bm.free()
for p in o.data.polygons: p.use_smooth = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True; sh.show_shadows = False
sc.render.resolution_x = 700; sc.render.resolution_y = 900
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = (P.min(0) + P.max(0)) / 2; h = np.ptp(P[:, 2])
views = {'front': (0, -1, 0), 'left': (1, 0, 0), 'back': (0, 1, 0), 'right': (-1, 0, 0), 'q34': (-1, -1.2, 0.3)}
for n, d in views.items():
    d = Vector(d).normalized(); cd.ortho_scale = h * 1.08
    cam.location = Vector(c) + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
zt = P[:, 2].max()
for n, d, cc, sz in (('headf', (0, -1, 0), (c[0], c[1], zt - 0.15 * h / 1.88 * 1.0), .42 * h), ('headq', (-1, -1.2, 0.1), (c[0], c[1], zt - .15 * h / 1.88), .42 * h)):
    d = Vector(d).normalized(); cd.ortho_scale = sz
    cam.location = Vector(cc) + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = sc.render.resolution_y = 700
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
