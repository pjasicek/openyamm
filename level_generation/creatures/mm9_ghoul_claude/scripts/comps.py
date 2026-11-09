"""Component report and colour-coded views. Args: <glb> <out prefix>"""
import bpy, sys, bmesh, colorsys, os
from mathutils import Vector
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
glb, pre = argv[:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
seen = {}; cid = 0
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen[y.index] = cid; st.append(y)
    cid += 1
vid = np.array([seen[i] for i in range(len(bm.verts))])
co = np.array([v.co for v in bm.verts])
order = np.argsort([-(vid == c).sum() for c in range(cid)])
oe = {}
for e in bm.edges:
    if len(e.link_faces) == 1: oe[seen[e.verts[0].index]] = oe.get(seen[e.verts[0].index], 0) + 1
for r, c in enumerate(order[:40]):
    q = co[vid == c]
    print('COMP', r, 'id', c, 'v', len(q), 'open', oe.get(c, 0), 'min', np.round(q.min(0), 3), 'max', np.round(q.max(0), 3))
rank = {c: r for r, c in enumerate(order)}
ca = me.color_attributes.new('C', 'FLOAT_COLOR', 'POINT') if False else None
mats = []
for r in range(12):
    m = bpy.data.materials.new(f'm{r}'); m.diffuse_color = (*colorsys.hsv_to_rgb((r * 0.381) % 1, 0.75, 1), 1); mats.append(m)
me.materials.clear()
for m in mats: me.materials.append(m)
for p in me.polygons:
    p.material_index = min(rank[seen[p.vertices[0]]], 11); p.use_smooth = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.1, 0.1, 0.1); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((co.min(0) + co.max(0)) / 2); cd.ortho_scale = float(np.ptp(co, 0).max()) * 1.08; cd.clip_end = 100
for n, d in (('front', (0, -1, 0.05)), ('left', (1, 0, 0.05)), ('q34', (-1, -1.2, 0.4)), ('back', (0, 1, 0.05))):
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{pre}_{n}.png'; bpy.ops.render.render(write_still=True)
