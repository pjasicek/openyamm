"""Meshy return's loose parts in distinct colours (see-through cross sections too). Args: glb outdir prefix"""
import bpy, bmesh, sys, os, colorsys, json
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix = argv[:3]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = np.full(len(bm.verts), -1, np.int32); k = 0; sizes = []
for v in bm.verts:
    if seen[v.index] >= 0:
        continue
    st = [v]; seen[v.index] = k; n = 0
    while st:
        x = st.pop(); n += 1
        for e in x.link_edges:
            y = e.other_vert(x)
            if seen[y.index] < 0:
                seen[y.index] = k; st.append(y)
    k += 1; sizes.append(n)
co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
rep = []
for i in np.argsort(sizes)[::-1]:
    q = co[seen == i]
    be = sum(1 for e in bm.edges if e.is_boundary and seen[e.verts[0].index] == i)
    rep.append({'part': int(i), 'verts': int(sizes[i]), 'min': np.round(q.min(0), 3).tolist(), 'max': np.round(q.max(0), 3).tolist(), 'boundary': be})
    print('PART', rep[-1])
col = o.data.color_attributes.new('C', 'FLOAT_COLOR', 'POINT')
rng = np.random.default_rng(1)
pal = [colorsys.hsv_to_rgb(rng.random(), 0.8, 0.9) for _ in range(k)]
for i, c in enumerate(col.data):
    p = pal[seen[i]]; c.color = (p[0], p[1], p[2], 1)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_backface_culling = True
sc.render.resolution_x = 900; sc.render.resolution_y = 1100
c = Vector((0, 0, 0))
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 1.15; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, d in {'front': (0, -1, .02), 'left': (1, 0, .02), 'back': (0, 1, .02), 'below': (0.0, 0.25, -1)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{n}.png'); bpy.ops.render.render(write_still=True)
# side cut: clip plane through x = 0 by clip_start of a camera looking along +x
cd.clip_start = 10 - 0.002
for n, d in {'cut_x0': (1, 0, 0)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sh.show_backface_culling = False
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{n}.png'); bpy.ops.render.render(write_still=True)
