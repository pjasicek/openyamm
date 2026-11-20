"""Two-sided patch (PeasantDM4 see-through gate, 2026-11-02: from behind the right elbow the view reached the back of the
undersleeve's faces 1615/1616 through a gap, 58-141 px in every clip): body faces whose centre lies within R of each
point (Blender rest frame) get a flipped twin OFF behind them along the face normal, with the same UVs (their own paint),
attributes and weights. Faces added only. Args (Blender): <in blend> <out blend> <x,y,z;x,y,z...> [r 0.03] [off 0.0005] [flip 1|0] [heads 0|1]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
PTS = [Vector([float(t) for t in s.split(',')]) for s in a[2].split(';')]
R = float(a[3]) if len(a) > 3 else 0.03; OFF = float(a[4]) if len(a) > 4 else 0.0005
FLIP = (a[5] != '0') if len(a) > 5 else True
HEADS = (a[6] == '1') if len(a) > 6 else False   # 1: head-set faces too (the neck cap seen from below through the collar gap)   # 0: an unflipped copy OFF below a crack in the outer surface (seen through it)
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
hl, kl = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
dl = bm.verts.layers.deform.active; uvs = list(bm.loops.layers.uv.values()); ints = list(bm.faces.layers.int.values())
sel = [f for f in bm.faces if (HEADS or not f[hl]) and not f[kl] and any((f.calc_center_median() - p).length < R for p in PTS)]
vn = {}
for f in sel:
    for v in f.verts:
        vn.setdefault(v, Vector()); vn[v] += f.normal * f.calc_area()
vmap = {}
for v, n in vn.items():
    nv = bm.verts.new(v.co - n.normalized() * OFF); nv[dl] = v[dl]; vmap[v] = nv
for f in sel:
    nf = bm.faces.new([vmap[v] for v in (reversed(f.verts) if FLIP else f.verts)])
    nf.material_index = f.material_index; nf.smooth = f.smooth
    for L in ints: nf[L] = f[L]
    for nl, ol in zip(nf.loops, reversed(f.loops) if FLIP else f.loops):
        for U in uvs: nl[U].uv = ol[U].uv
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('TWIN_PATCH faces', len(sel))
