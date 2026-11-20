"""Render the Meshy return's loose parts in distinct colours, scaled to the MM9 height, with the MM9 skeleton joints.
Args: meshy glb, mm9 glb, outdir, prefix. Crops: whole, head, hand L, hand R, feet."""
import bpy, bmesh, sys, os, colorsys
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, mm9, outdir, prefix = argv[:4]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
for x in list(sc.objects):
    if x is not o and x.type != 'MESH':
        m = o.matrix_world.copy(); o.parent = None; o.matrix_world = m; bpy.data.objects.remove(x)
for x in sc.objects:
    x.select_set(True)
bpy.context.view_layer.objects.active = o
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([v.co for v in o.data.vertices])
H = 1.8486
s = H / (co[:, 2].max() - co[:, 2].min())
co = co * s; co[:, 2] -= co[:, 2].min() + 0.0113
for v, c in zip(o.data.vertices, co):
    v.co = Vector(c)
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
print('PARTS', sizes)
for i in range(k):
    q = co[seen == i]; print('PART', i, sizes[i], np.round(q.min(0), 3).tolist(), np.round(q.max(0), 3).tolist())
col = bm.loops.layers.color.new('Col')
for f in bm.faces:
    h = (seen[f.verts[0].index] * 0.381966) % 1
    c = colorsys.hsv_to_rgb(h, 0.65, 0.95)
    for l in f.loops:
        l[col] = (*c, 1)
bm.to_mesh(o.data); bm.free()
for mat in bpy.data.materials:
    pass
o.data.materials.clear()
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_backface_culling = False
sh.show_cavity = True
sc.render.resolution_x = 800; sc.render.resolution_y = 800
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
crops = {'head': ((0, -.02, 1.6), .55), 'handR': ((.28, -.12, .95), .4), 'handL': ((-.28, -.15, .95), .4), 'feet': ((0, -.05, .12), .9),
         'torso': ((0, 0, 1.15), .9)}
for name, (cc, ortho) in crops.items():
    cd.ortho_scale = ortho
    for n, d in {'front': (0, -1, .02), 'side': (1, 0, .02), 'q34': (-1, -1.25, .35)}.items():
        d = Vector(d).normalized(); c = Vector(cc); cam.location = c + d * 10
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(outdir, f'{prefix}_{name}_{n}.png'); bpy.ops.render.render(write_still=True)
# one distinct-colour render of the whole figure per part id, with material colours
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
for i in range(k):
    mt = bpy.data.materials.new(f'p{i}'); mt.diffuse_color = (*colorsys.hsv_to_rgb((i * 0.381966) % 1, 0.7, 0.95), 1)
    o.data.materials.append(mt)
for f in bm.faces:
    f.material_index = int(seen[f.verts[0].index])
# boundary loops per part
seen_e = set()
for e in bm.edges:
    if e.is_boundary and e.index not in seen_e:
        st = [e]; lp = []
        while st:
            x = st.pop()
            if x.index in seen_e:
                continue
            seen_e.add(x.index); lp.append(x)
            for v in x.verts:
                st += [y for y in v.link_edges if y.is_boundary and y.index not in seen_e]
        pts = np.array([tuple(v.co) for x in lp for v in x.verts])
        print('LOOP part', seen[lp[0].verts[0].index], 'edges', len(lp), np.round(pts.min(0), 3).tolist(), np.round(pts.max(0), 3).tolist())
bm.to_mesh(o.data); bm.free()
sh.color_type = 'MATERIAL'; sc.render.resolution_x = 1200; sc.render.resolution_y = 1500
cd.ortho_scale = 2.0
for n, d in {'front': (0, -1, .02), 'side': (1, 0, .02), 'back': (0, 1, .02), 'q34': (-1, -1.25, .35)}.items():
    d = Vector(d).normalized(); c = Vector((0, 0, .9)); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_all_{n}.png'); bpy.ops.render.render(write_still=True)
