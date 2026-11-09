"""Step D: triangle budget per region, after weights. The skin is one closed piece: body, head and hands take a pass each with the rest protected by a vertex group. Teeth and eyes keep a share. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
T = {'body': 4600, 'head': 3100, 'hands': 1900, 13: 160, 14: 700}
C = np.array([0.0, -0.03, 0.755]); N = np.array([0.0, -0.35, 0.937]); N /= np.linalg.norm(N)
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
ske = extract(np.nonzero(pa == 0)[0], 'skin')
def pgroup(fn):
    names = {x.index: x.name for x in ske.vertex_groups}
    g = ske.vertex_groups.new(name='protect')
    for v in ske.data.vertices:
        hand = sum(q.weight for q in v.groups if 'Hand' in names.get(q.group, ''))
        head = (np.array(v.co[:]) - C) @ N > -0.01
        g.add([v.index], 1.0 if fn(head, hand > 0.5) else 0.0, 'REPLACE')
    pv = set(v.index for v in ske.data.vertices if any(q.group == g.index and q.weight > 0.5 for q in v.groups))
    return g, sum(1 for p in ske.data.polygons if all(x in pv for x in p.vertices))
for name, fn in (('body', lambda a, h: a or h), ('head', lambda a, h: not a), ('hands', lambda a, h: not h)):
    g, keep = pgroup(fn)
    print('protected tris', keep); decimate(ske, keep + T[name], 'protect', 1.0, True); ske.vertex_groups.remove(ske.vertex_groups['protect'])
objs.append(ske)
for k in (13, 14):
    o = extract(np.nonzero(pa == k)[0], f'p{k}')
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
