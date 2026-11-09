"""Step D: triangle budget per part, after weights. Skin (body, face, hands) is one connected piece: face and hands are protected by a vertex group. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
T = {'skin': 3000, 'face': 2800, 1: 820, 3: 360, 5: 360, 6: 180, 11: 640, 13: 120}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
me = body.data
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
def extract(ids, name):
    o = body.copy(); o.data = me.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); ids = set(ids)
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
    bpy.ops.object.modifier_move_to_index(modifier='d', index=0)
    bpy.ops.object.modifier_apply(modifier='d')
    print('DEC', o.name, r0, '->', tris(o))
objs = []
ske = extract(np.nonzero(np.isin(pa, (0, 10)))[0], 'skin')
# two passes on the connected skin: body with face and hands fixed, then the face with the rest fixed
fingers = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Hand')
def pgroup(fn):
    sa = np.zeros(len(ske.data.vertices), int); ske.data.attributes['part'].data.foreach_get('value', sa)
    names = {x.index: x.name for x in ske.vertex_groups}
    g = ske.vertex_groups.new(name='protect')
    for v in ske.data.vertices:
        hand = sum(q.weight for q in v.groups if any(k in names.get(q.group, '') for k in fingers))
        g.add([v.index], 1.0 if fn(sa[v.index], hand > 0.3) else 0.0, 'REPLACE')
    pv = set(v.index for v in ske.data.vertices if any(q.group == g.index and q.weight > 0.5 for q in v.groups))
    return g, sum(1 for p in ske.data.polygons if all(x in pv for x in p.vertices))
g, keep = pgroup(lambda p, h: p == 10 or h)
print('protected tris', keep); decimate(ske, keep + T['skin'], 'protect', 1.0, True); ske.vertex_groups.remove(ske.vertex_groups['protect'])
g, keep = pgroup(lambda p, h: p != 10)
print('protected tris', keep); decimate(ske, keep + T['face'], 'protect', 1.0, True); ske.vertex_groups.remove(ske.vertex_groups['protect'])
objs.append(ske)
for k in (1, 3, 5, 6, 11, 13):
    ids = np.nonzero(pa == k)[0]
    o = extract(ids, f'p{k}')
    decimate(o, T[k]); objs.append(o)
for o in bpy.data.objects: o.select_set(o in objs)
bpy.data.objects.remove(body)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
b = objs[0]; b.name = 'Body'; me = b.data; me.name = 'Body'
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=2e-4)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
print('REDUCED tris', tris(b), 'verts', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
