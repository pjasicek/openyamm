"""Lower-lid fold under the right eye (PeasantM5 viewer r2; Markel's 'speck', mm9_markel README): face 3801 (11 mm2) is folded
46 deg against its neighbour and faces down (normal z -0.43), so in the viewer's top light it shades as a dark triangle whatever
the paint. Its three vertices (and only them) move halfway to the mean of their ring neighbours, 3 passes, each move capped at
CAP; positions only (UVs, weights, topology unchanged). Not near the nose or mouth.
Args: -- <in blend> <out blend> [face 3801] [cap 0.0015]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
F = int(a[2]) if len(a) > 2 else 3801; CAP = float(a[3]) if len(a) > 3 else 0.0015
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
f = bm.faces[F]; vs = list(f.verts); orig = {v.index: v.co.copy() for v in vs}
def worst():
    return max(f.normal.angle(g.normal) for e in f.edges for g in e.link_faces if g is not f)
before = worst()
for _ in range(3):
    new = {}
    for v in vs:
        nb = [e.other_vert(v).co for e in v.link_edges]
        c = sum(nb, v.co * 0) / len(nb); new[v.index] = v.co + 0.5 * (c - v.co)
    for v in vs:
        d = new[v.index] - orig[v.index]
        if d.length > CAP: d = d.normalized() * CAP
        v.co = orig[v.index] + d
    bm.normal_update()
after = worst()
bm.to_mesh(me); me.update(); bpy.ops.wm.save_as_mainfile(filepath=a[1])
import math
print('LID_FOLD worst angle deg', round(math.degrees(before)), '->', round(math.degrees(after)), 'normal', [round(x, 2) for x in f.normal],
      'moves mm', [round((v.co - orig[v.index]).length * 1000, 2) for v in vs])
