"""Step D: triangle budget per part, after weights. Args: <rig blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
T = {'skin': 3300, 'hands': 1300, 10: 3000, 3: 300, 11: 900, 12: 700, 13: 120}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
objs = []


def extract(ids, name):
    o = body.copy(); o.data = me.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    ids = set(ids.tolist())
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in ids], context='VERTS')
    bm.to_mesh(o.data); bm.free()
    return o


def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)


def decimate(o, target, vg=None):
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects: x.select_set(x is o)
    r0 = tris(o)
    m = o.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = min(1.0, target / r0); m.use_collapse_triangulate = True
    if vg: m.vertex_group = vg; m.vertex_group_factor = 1.0; m.invert_vertex_group = True
    bpy.ops.object.modifier_move_to_index(modifier='d', index=0)
    bpy.ops.object.modifier_apply(modifier='d')
    print('DEC', o.name, r0, '->', tris(o))


ske = extract(np.nonzero(pa == 0)[0], 'skin')
g = ske.vertex_groups.new(name='protect')
for v in ske.data.vertices: g.add([v.index], 0.0 if abs(v.co.x) > 0.68 else 1.0, 'REPLACE')
pv = set(v.index for v in ske.data.vertices if abs(v.co.x) <= 0.68)
keep = sum(1 for p in ske.data.polygons if all(x in pv for x in p.vertices))
print('protected', keep, 'hand tris', tris(ske) - keep)
decimate(ske, keep + T['hands'], 'protect'); ske.vertex_groups.remove(ske.vertex_groups['protect'])
g2 = ske.vertex_groups.new(name='protect')
for v in ske.data.vertices: g2.add([v.index], 1.0 if abs(v.co.x) > 0.68 else 0.0, 'REPLACE')
decimate(ske, T['skin'] + T['hands'], 'protect'); ske.vertex_groups.remove(ske.vertex_groups['protect'])
objs.append(ske)
for k in (10, 3, 6, 7, 11, 12, 13):
    ids = np.nonzero(pa == k)[0]
    if not len(ids): continue
    o = extract(ids, f'p{k}')
    if k in T: decimate(o, T[k])
    objs.append(o)
for o in bpy.data.objects: o.select_set(o in objs)
bpy.data.objects.remove(body)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
b = objs[0]; b.name = 'Body'; me = b.data; me.name = 'Body'
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=2e-4)
# the reductions are not symmetric: the right half is kept and mirrored, parts included
for v in bm.verts:
    if abs(v.co.x) < 0.007: v.co.x = 0
g_ = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g_, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-4)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1.5e-3)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
lay_ = bm.verts.layers.int['part']
for pid_ in (0, 3, 6, 7, 10, 11, 12, 13):
    fs_ = [f for f in bm.faces if all(v[lay_] == pid_ for v in f.verts)]
    if fs_: bmesh.ops.recalc_face_normals(bm, faces=fs_)
for v in bm.verts:
    if v[lay_] not in (0, 3, 6, 7, 10, 11, 12, 13): v[lay_] = 0
# stray shards
seen = set(); dead = []
for f0 in bm.faces:
    if f0 in seen: continue
    st = [f0]; seen.add(f0); cc = [f0]
    while st:
        f = st.pop()
        for e in f.edges:
            for h in e.link_faces:
                if h not in seen: seen.add(h); st.append(h); cc.append(h)
    if len(cc) < 5: dead += cc
bmesh.ops.delete(bm, geom=dead, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
print('REDUCED tris', tris(b), 'verts', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
