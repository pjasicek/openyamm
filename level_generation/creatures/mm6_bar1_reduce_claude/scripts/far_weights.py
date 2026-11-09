"""Hand skin vertices of work/source.blend weighted mainly to a finger bone far from them: distance to the dominant bone's
rest segment more than FAR (2 cm) beyond the nearest hand/finger bone segment (a patch beside the left ring finger
was 100 % on the thumb tip bone and swung into a spike whenever the thumb curled). REA_FIX=1 refills those vertices
from their good neighbours (flood fill: mean weights of neighbours already good, repeated until all are set) and
saves work/source.blend."""
import os, bpy, bmesh
from mathutils import Vector
from mathutils.geometry import intersect_point_line
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAR = float(os.environ.get('REA_FAR', '.02'))
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = o.data
names = {g.index: g.name for g in o.vertex_groups}
segs = {b.name: (rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local) for b in rig.data.bones
        if '_Hand' in b.name or '_Finger' in b.name}
def dist(p, s):
    a, b = segs[s]; q, t = intersect_point_line(p, a, b); t = min(max(t, 0), 1)
    return (p - (a + (b - a) * t)).length
W = [{names[g.group]: g.weight for g in v.groups if names[g.group] != 'ReduceProtect'} for v in me.vertices]
bad = set()
for v in me.vertices:
    w = W[v.index]
    if not w: continue
    dom = max(w, key=w.get)
    if dom not in segs or '_Finger' not in dom: continue  # palm skin near the knuckles is rightly on the hand bone
    p = o.matrix_world @ v.co; near = min(segs, key=lambda s: dist(p, s))
    if dist(p, dom) > dist(p, near) + FAR:
        bad.add(v.index); print('FAR', v.index, dom, '%.0f mm' % (dist(p, dom) * 1000), 'nearest', near, '%.0f mm' % (dist(p, near) * 1000))
print('BAD', len(bad))
if os.environ.get('REA_FIX') and bad:
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    todo = set(bad)
    while todo:
        done = {}
        for i in todo:
            good = [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges if e.other_vert(bm.verts[i]).index not in todo]
            if not good: continue
            acc = {}
            for n in good:
                for g, x in W[n].items(): acc[g] = acc.get(g, 0) + x / len(good)
            tot = sum(acc.values()); done[i] = {g: x / tot for g, x in acc.items()}
        if not done: print('STUCK', len(todo)); break
        for i, w in done.items(): W[i] = w
        todo -= set(done)
    for i in bad:
        for g in o.vertex_groups:
            if g.name != 'ReduceProtect': g.remove([i])
        for g, x in W[i].items():
            if x > 1e-4: o.vertex_groups[g].add([i], x, 'REPLACE')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend')); print('FIXED', len(bad))
