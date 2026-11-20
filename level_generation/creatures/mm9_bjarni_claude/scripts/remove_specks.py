"""Delete tiny loose specks of the Meshy body (mm9_bjarni, 2026-11-02: the detached-parts audit found a 1-triangle sliver
floating 5 mm off the belt and a 6-triangle chip that leaves the thigh in Cower). Loose parts are taken after welding by
position (UV seams do not split them); a part with at most MAX faces is deleted. UVs of the rest are unchanged.
Only the parts whose centre lies within 1 cm of one of AT (x,y,z;...) when given: the studs on the belt and trouser seams are
small loose parts too, and stay. Args: -- <in blend> <out blend> [max faces 8] [AT]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
MAX = int(a[2]) if len(a) > 2 else 8
AT = [tuple(float(c) for c in p.split(',')) for p in a[3].split(';')] if len(a) > 3 else None
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(ob.data)
key = {}
for v in bm.verts:
    key.setdefault(tuple(round(c, 5) for c in v.co), []).append(v)
parent = {}
def find(x):
    while parent.get(x, x) != x:
        parent[x] = parent.get(parent[x], parent[x]); x = parent[x]
    return x
def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry: parent[rx] = ry
for vs in key.values():
    for v in vs[1:]: union(vs[0].index, v.index)
for f in bm.faces:
    ids = [v.index for v in f.verts]
    for i in ids[1:]: union(ids[0], i)
groups = {}
for f in bm.faces:
    groups.setdefault(find(f.verts[0].index), []).append(f)
dead = []
for g, fs in groups.items():
    if len(fs) <= MAX:
        c = sum((f.calc_center_median() for f in fs), fs[0].normal * 0) / len(fs)
        if AT is not None and not any((c - c.__class__(q)).length < 0.01 for q in AT):
            continue
        print('SPECK', len(fs), [round(x, 3) for x in c])
        dead += fs
bmesh.ops.delete(bm, geom=dead, context='FACES')
bm.to_mesh(ob.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('SPECKS removed faces', len(dead))
