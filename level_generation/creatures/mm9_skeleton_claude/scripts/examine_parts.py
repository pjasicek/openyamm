"""Loose parts of a Meshy Smart Topology return: labels, bboxes (scaled to the MM9 height), a part-coloured render.
Args: <glb> <out blend> <out png prefix> <report json>"""
import bpy, bmesh, sys, json, colorsys, math
import numpy as np
from mathutils import Vector
GLB, BLEND, PNG, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in ms:
    o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1:
    bpy.ops.object.join()
o = bpy.context.active_object
for x in list(bpy.data.objects):
    if x is not o and x.type != 'MESH':
        pass
m = o.matrix_world.copy(); o.parent = None; o.matrix_world = m
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o.name = 'Meshy'; me = o.data
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
co = np.array([tuple(v.co) for v in bm.verts])
tris = np.zeros(cid, int)
for f in bm.faces: tris[comp[f.verts[0].index]] += len(f.verts) - 2
bm.free()
print('verts', len(co), 'faces', tris.sum(), 'parts', cid, 'bounds', co.min(0), co.max(0))
order = np.argsort(-tris)
rep = []
for c in order:
    idx = comp == c; rep.append(dict(part=int(c), tris=int(tris[c]), lo=np.round(co[idx].min(0), 3).tolist(), hi=np.round(co[idx].max(0), 3).tolist()))
json.dump(rep, open(REP, 'w'), indent=0)
for r in rep[:60]: print(r)
ca = me.color_attributes.new('part', 'BYTE_COLOR', 'POINT')
hue = {int(c): (i * 0.618) % 1 for i, c in enumerate(order)}
for i, c in enumerate(comp):
    ca.data[i].color = (*colorsys.hsv_to_rgb(hue[int(c)], .75, .95), 1)
me.attributes.active_color = ca
a = me.attributes.new('part', 'INT', 'POINT'); a.data.foreach_set('value', comp.tolist())
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x, sc.render.resolution_y = 800, 1100
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (.05, .05, .05); sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(max(co.max(0) - co.min(0))) * 1.08; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((co.min(0) + co.max(0)) / 2)
for name, d in dict(front=(0, -1, 0), back=(0, 1, 0), left=(1, 0, 0), right=(-1, 0, 0), q34=(-.7, -1, .2)).items():
    cam.location = c + Vector(d).normalized() * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{PNG}_{name}.png'
    bpy.ops.render.render(write_still=True)
