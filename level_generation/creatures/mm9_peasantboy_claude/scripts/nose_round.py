"""Round the nose bridge (second pass: under side light the knife-edged bridge left by the mirrored Meshy face threw
one side of the nose into a dark brown band). Face-shell vertices in the bridge zone (|x| < 1.4 cm, rest z 0.712-0.752,
front) get weighted Laplacian steps (weight falls off over |x| and the zone's ends); the midline stays at x = 0 and the
nose tip below 0.712 is not touched. Positions only. Args: <in blend> <out blend> [iters 8]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
IT = int(a[2]) if len(a) > 2 else 8
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
hl = bm.faces.layers.int['head']


def w(p):
    if p.y > -0.05 or not (0.708 < p.z < 0.756) or abs(p.x) > 0.014:
        return 0.0
    ez = min((p.z - 0.708) / 0.006, (0.756 - p.z) / 0.006, 1.0)
    return max(0.0, ez) * (1 - abs(p.x) / 0.014)


headv = {v for f in bm.faces if f[hl] for v in f.verts}
from collections import defaultdict
twins = defaultdict(list)
for v in headv:
    twins[tuple(round(c, 5) for c in v.co)].append(v)
W = {v: w(v.co) for v in headv}
W = {v: x for v, x in W.items() if x > 0}
for _ in range(IT):
    global_twins = None
    new = {}
    for v, x in W.items():
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in headv]
        if len(nb) < 3:
            continue
        avg = sum((n.co for n in nb), Vector()) / len(nb)
        p = v.co.lerp(avg, 0.5 * x)
        if abs(v.co.x) < 1e-6:
            p.x = 0.0
        new[v] = p
    for v, p in new.items():
        v.co = p
    # coincident vertices (an unwelded seam at the bridge top) move together: a gap opened there (a dark notch)
    for k, vs in twins.items():
        if len(vs) > 1 and any(v in new for v in vs):
            m = sum((v.co for v in vs), Vector()) / len(vs)
            for v in vs:
                v.co = m.copy()
    twins = defaultdict(list, {tuple(round(c, 5) for c in vs[0].co): vs for vs in twins.values()})
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('NOSEROUND', len(W))
