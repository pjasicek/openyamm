"""Workbench renders of the head parts (bind): shell grey, listed parts coloured. Normal + x-ray.
Args: -- <blend> <out prefix>"""
import bpy, sys, bmesh
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
body = bpy.data.objects['Body']; me = body.data
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body: o.hide_render = True
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), int); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
bm.free()
cols = {0: (0.55, 0.55, 0.55, 1), 1: (0.9, 0.1, 0.1, 1), 18: (0.9, 0.1, 0.9, 1), 9: (0.1, 0.3, 0.95, 1), 4: (0.2, 0.7, 0.3, 1)}
me.materials.clear()
mats = {}
for k, c in list(cols.items()) + [('tooth', (1, 0.9, 0.2, 1)), ('lip', (1, 0.5, 0.0, 1))]:
    m = bpy.data.materials.new(str(k)); m.diffuse_color = c; me.materials.append(m); mats[k] = len(me.materials) - 1
lip = np.zeros(len(me.polygons), bool); me.attributes['lip'].data.foreach_get('value', lip)
for p in me.polygons:
    c = comp[p.vertices[0]]
    p.material_index = mats['lip'] if lip[p.index] else mats.get(c, mats['tooth'] if c not in (0,) else 0)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = sc.render.resolution_y = 800
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.9, 0.9, 0.92)
hc = Vector((0, -3.9, 15.35))
cd = bpy.data.cameras.new('c'); cd.lens = 85; cd.clip_start = 0.01; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for xr in (False, True):
    sc.display.shading.show_xray = xr; sc.display.shading.xray_alpha = 0.35
    for nm, d in (('sideR', (1, -0.15, 0.1)), ('frontlow', (0.3, -1, -0.35)), ('below', (0.1, -0.2, -1))):
        cam.location = hc + Vector(d).normalized() * 6.5
        cam.rotation_euler = (hc - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{nm}_{"xray" if xr else "solid"}.png'; bpy.ops.render.render(write_still=True)
