"""Clean the Meshy return: join, MIRROR in x (Codex drew the stance with the other foot forward; mirrored, the forward
leg and the forward hand are on the same side as MM9's), scale to the MM9 height, ground, flip winding, face attribute
`part` (loose parts by lowest vertex index of the ORIGINAL mesh), stray strap removed.
Args: meshy glb, mm9 glb, out blend, report json"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
MESHY, MM9, OUT, REP = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MESHY)
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
for x in list(sc.objects):
    if x is not o and x.type != 'MESH':
        m = o.matrix_world.copy(); o.parent = None; o.matrix_world = m; bpy.data.objects.remove(x)
for x in sc.objects:
    x.select_set(True)
bpy.context.view_layer.objects.active = o
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o.name = 'Body'; o.data.name = 'Body'; o.data.materials.clear()
co = np.array([v.co for v in o.data.vertices])
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
new = [x for x in bpy.data.objects if x not in existing]
ms = [x for x in new if x.type == 'MESH' and 'd_lich' in x.name]
dg = bpy.context.evaluated_depsgraph_get()
mp = np.array([ms[0].matrix_world @ v.co for v in ms[0].data.vertices])
for x in new:
    bpy.data.objects.remove(x)
H = mp[:, 2].max() - mp[:, 2].min()
s = H / (co[:, 2].max() - co[:, 2].min())
co = co * s
co[:, 0] = -co[:, 0]
co[:, 2] += mp[:, 2].min() - co[:, 2].min()
co[:, 0] -= 0.5 * (co[:, 0].min() + co[:, 0].max()) - 0.5 * (mp[:, 0].min() + mp[:, 0].max())
for v, c in zip(o.data.vertices, co):
    v.co = Vector(c)
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
seen = np.full(len(bm.verts), -1, np.int32); k = 0
for v in bm.verts:
    if seen[v.index] >= 0:
        continue
    st = [v]; seen[v.index] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if seen[y.index] < 0:
                seen[y.index] = k; st.append(y)
    k += 1
lay = bm.faces.layers.int.new('part')
for f in bm.faces:
    f[lay] = int(seen[f.verts[0].index])
# part 0: a thin strap Meshy strung from the belt to a sleeve
gone = [f for f in bm.faces if f[lay] == 0]
bmesh.ops.delete(bm, geom=gone, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# a thin ribbon runs from each hand part's palm up into the sleeve: faces far from the forearm's axis, above the palm
ribbon = 0
for pid in (3, 10):
    fs = []
    for f in bm.faces:
        if f[lay] != pid:
            continue
        ls = sorted(e.calc_length() for e in f.edges)
        if ls[2] > 0.07 and 2 * f.calc_area() / ls[2] < 0.016:
            fs.append(f)
    ribbon += len(fs)
    bmesh.ops.delete(bm, geom=fs, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# small holes left by the cut
for e in list(bm.edges):
    if e.is_valid and e.is_boundary and e.link_faces[0][lay] in (3, 10):
        lp, st, sn = [], [e], set()
        while st:
            x = st.pop()
            if x in sn:
                continue
            sn.add(x); lp.append(x)
            for v in x.verts:
                st += [y for y in v.link_edges if y.is_boundary and y not in sn]
        if len(lp) < 9:
            pid = lp[0].link_faces[0][lay]
            ns = bmesh.ops.holes_fill(bm, edges=lp, sides=0)['faces']
            for f in bmesh.ops.triangulate(bm, faces=ns)['faces']:
                f[lay] = pid
# fragments left by the cut
bm.verts.ensure_lookup_table()
seen = {}
for v in bm.verts:
    if v in seen:
        continue
    st = [v]; seen[v] = v; c = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen:
                seen[y] = v; st.append(y); c.append(y)
    if len(c) < 12 and c[0].link_faces and c[0].link_faces[0][lay] in (3, 10):
        bmesh.ops.delete(bm, geom=c, context='VERTS')
bm.to_mesh(o.data); bm.free(); o.data.update()
print('RIBBON', ribbon)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump({'scale': float(s), 'height': float(H), 'parts': k, 'removed_faces': len(gone)}, open(REP, 'w'), indent=1)
print('STEP1', s, H, k, len(gone))
