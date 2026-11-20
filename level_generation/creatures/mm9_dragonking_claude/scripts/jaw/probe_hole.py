"""Delete the lip faces in a copy of Body and render the mouth hole (clay, parts coloured: shell grey, teeth white,
eyes yellow, frills green), bind pose, plus boundary loop stats. Args: -- <blend> <out prefix>"""
import bpy, sys, bmesh, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
rig = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body:
        o.hide_render = True
for m in list(body.modifiers):
    if m.type == 'ARMATURE':
        m.show_render = True
me = body.data
bm = bmesh.new(); bm.from_mesh(me)
lip = bm.faces.layers.bool.get('lip') or bm.faces.layers.int.get('lip')
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lip]], context='FACES')
bm.edges.ensure_lookup_table()
bnd = [e for e in bm.edges if e.is_boundary]
print('BOUNDARY edges', len(bnd))
# loops
left = set(bnd); loops = []
while left:
    e = left.pop(); chain = [e.verts[0], e.verts[1]]
    while True:
        v = chain[-1]; nxt = [x for x in v.link_edges if x in left]
        if not nxt: break
        x = nxt[0]; left.discard(x); chain.append(x.other_vert(v))
    loops.append(chain)
for L in loops:
    P = np.array([tuple(v.co) for v in L])
    print('LOOP', len(L), 'closed', L[0] == L[-1], 'lo', P.min(0).round(3), 'hi', P.max(0).round(3))
# components after delete
comp = {}
bm.verts.ensure_lookup_table()
bm.to_mesh(me); bm.free()
# colour parts
vg = {g.index: g.name for g in body.vertex_groups}
cols = [(0.6, 0.6, 0.6, 1), (0.95, 0.95, 0.9, 1), (0.9, 0.8, 0.1, 1), (0.2, 0.7, 0.3, 1), (0.9, 0.2, 0.2, 1)]
me.materials.clear()
for i, c in enumerate(cols):
    m = bpy.data.materials.new(f'c{i}'); m.diffuse_color = c; me.materials.append(m)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = {}
cid = 0
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen[y.index] = cid; st.append(y)
    cid += 1
size = {}
for k in seen.values(): size[k] = size.get(k, 0) + 1
big = max(size, key=size.get)
for f in bm.faces:
    c = seen[f.verts[0].index]; n = size[c]
    f.material_index = 0 if c == big else (1 if n < 60 else (2 if n < 30 else 3))
bm.to_mesh(me); bm.free()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = sc.render.resolution_y = 700
sc.display.shading.show_backface_culling = False
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.3, 0.3, 0.35)
hc = Vector((0, -4.0, 15.2))
cd = bpy.data.cameras.new('c'); cd.lens = 85; cd.clip_start = 0.01; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, d in (('sideL', (-1, -0.2, 0.1)), ('sideR', (1, -0.2, 0.1)), ('frontlow', (0.25, -1, -0.5)), ('below', (0.15, -0.3, -1)), ('top', (0.1, -0.3, 1))):
    cam.location = hc + Vector(d).normalized() * 9
    cam.rotation_euler = (hc - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{nm}.png'; bpy.ops.render.render(write_still=True)
