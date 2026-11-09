"""Step D: triangle budget per part, after weights (weights interpolate in the collapse). Parts 0+10 stay connected and share one pass, face and hands protected by a vertex group.
Args: <rig blend> <out blend> [json targets]"""
import bpy, bmesh, sys, json
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
T = {'skin': 2200, 'hands': 1100, 10: 3300, 1: 1400, 2: 520, 3: 240, 4: 240, 5: 460, 11: 520, 12: 760, 13: 96}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
me = body.data
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
objs = []


def extract(ids, name):
    o = body.copy(); o.data = me.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    ids = set(ids)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in ids], context='VERTS')
    bm.to_mesh(o.data); bm.free()
    return o


def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)


def decimate(o, target, vg=None, f=1.0, inv=False):
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects: x.select_set(x is o)
    r0 = tris(o)
    m = o.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = min(1.0, target / r0); m.use_collapse_triangulate = True
    if vg: m.vertex_group = vg; m.vertex_group_factor = f; m.invert_vertex_group = inv
    # keep it on top of the armature modifier order for apply
    bpy.ops.object.modifier_move_to_index(modifier='d', index=0)
    bpy.ops.object.modifier_apply(modifier='d')
    print('DEC', o.name, r0, '->', tris(o))


# parts 0 and 10 reduce apart (the bridge faces go) and are bridged again below
fc = extract(np.nonzero(pa == 10)[0], 'face')
vf = fc.vertex_groups.new(name='protect')
for v in fc.data.vertices: vf.add([v.index], 1.0 if v.co.z < 0.815 else 0.0, 'REPLACE')
decimate(fc, T[10], 'protect', 1.0, True); fc.vertex_groups.remove(fc.vertex_groups['protect']); objs.append(fc)
ske = extract(np.nonzero(pa == 0)[0], 'skin')
def group_of(fn):
    g = ske.vertex_groups.new(name='protect')
    n_prot = 0
    for v in ske.data.vertices:
        hand = sum(q.weight for q in v.groups if any(k in ske.vertex_groups[q.group].name for k in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) and q.group != g.index)
        w = 1.0 if fn(v, hand) else 0.0
        n_prot += w > 0
        g.add([v.index], w, 'REPLACE')
    return g


def fcount(g):
    idx = g.index
    pv = set(v.index for v in ske.data.vertices if any(q.group == idx and q.weight > 0.5 for q in v.groups))
    return sum(1 for p in ske.data.polygons if all(x in pv for x in p.vertices))


g = group_of(lambda v, h: not (h > 0.3))
keep = fcount(g); print('protected tris', keep)
decimate(ske, keep + T['hands'], 'protect', 1.0, True); ske.vertex_groups.remove(ske.vertex_groups['protect'])
objs.append(ske)
for k in (1, 2, 3, 4, 5, 11, 12, 13):
    ids = np.nonzero(pa == k)[0]
    if not len(ids): continue
    o = extract(ids, f'p{k}')
    decimate(o, T[k]); objs.append(o)
for o in bpy.data.objects: o.select_set(o in objs)
bpy.data.objects.remove(body)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
b = objs[0]; b.name = 'Body'; me = b.data; me.name = 'Body'
# strip degenerate slivers
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=2e-4)
lay = bm.verts.layers.int['part']


def all_loops(k):
    es = {e for e in bm.edges if e.is_boundary and e.verts[0][lay] == k and e.verts[1][lay] == k}
    out = []
    while es:
        st = [es.pop()]; cur = [st[0]]
        while st:
            e = st.pop()
            for v in e.verts:
                for f in v.link_edges:
                    if f in es: es.remove(f); cur.append(f); st.append(f)
        out.append(cur)
    return out


def stat(l):
    c = np.array([v.co[:] for e in l for v in e.verts]); return c.mean(0).round(3), np.ptp(c, 0).round(3), len(l)


l0 = [l for l in all_loops(0) if stat(l)[0][2] > 0.7]
l1 = [l for l in all_loops(10) if stat(l)[0][2] < 0.84]
print('RINGS', [stat(l) for l in l0][:6], [stat(l) for l in l1][:8])
r0 = max(l0, key=len)
r1 = max(l1, key=lambda l: min(stat(l)[1][:2]))
print('BRIDGE', len(bmesh.ops.bridge_loops(bm, edges=r0 + r1)['faces']))
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
print('REDUCED tris', tris(b), 'verts', len(me.vertices))
for k in sorted(T, key=str):
    pass
bpy.ops.wm.save_as_mainfile(filepath=OUT)
