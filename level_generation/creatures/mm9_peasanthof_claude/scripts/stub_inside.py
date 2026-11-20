"""HOF2 wrists, r2: keep the grafted hand's stub inside the sleeve at rest (see-through gate: from behind/above, the left
wrist showed the BACK of a long stub triangle that passed out through the cuff top; one ray met nothing else). The fitted
forearm joint axis runs ~3 cm off the sleeve's centre, so this measures from the sleeve's own centre line: slices every
5 mm along the forearm axis, centre = bounding-box centre of the sleeve vertices in the slice. Every stub vertex (all its
faces `hand`) behind S_MAX (from the hand joint) whose distance from the centre line exceeds K x the sleeve's inner wall
along the same perpendicular ray moves in to K x that distance (axial position kept). Before/after: stub faces that cross
the sleeve faces (BVH overlap). Positions only. Args: <in blend> <out blend> [k 0.85] [s_max -0.004]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
K = float(a[2]) if len(a) > 2 else 0.85
S_MAX = float(a[3]) if len(a) > 3 else -0.004
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = ob.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
dl = bm.verts.layers.deform.verify()
gname = {g.index: g.name for g in ob.vertex_groups}
rep = {}
def bvh_of(faces):
    vs = []; fs = []
    for f in faces:
        b = len(vs); vs += [mw @ v.co for v in f.verts]; fs.append(list(range(b, b + len(f.verts))))
    return BVHTree.FromPolygons(vs, fs)
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    arm = {i for i, n in gname.items() if f' {tok} ' in n and any(k in n for k in ('Forearm', 'Hand', 'UpperArm', 'Finger'))}
    def s_of(p): return float((np.array(p) - a1) @ ax)
    sf = [f for f in bm.faces if not f[lh] and not f[lk] and -0.22 < s_of(mw @ f.calc_center_median()) < 0.03
          and np.mean([sum(w for g, w in v[dl].items() if g in arm) for v in f.verts]) > 0.5
          and np.linalg.norm(np.cross(np.array(mw @ f.calc_center_median()) - a1, ax)) < 0.12]
    stub_f = [f for f in bm.faces if f[lh] and -0.2 < s_of(mw @ f.calc_center_median()) < 0.03
              and np.linalg.norm(np.cross(np.array(mw @ f.calc_center_median()) - a1, ax)) < 0.12]
    sv = {v for f in sf for v in f.verts}
    SP = np.array([tuple(mw @ v.co) for v in sv]); SS = (SP - a1) @ ax
    ks = np.arange(-0.2, 0.031, 0.005); cents = []
    for s in ks:
        m = np.abs(SS - s) < 0.006
        cents.append(0.5 * (SP[m].min(0) + SP[m].max(0)) if m.sum() >= 4 else None)
    good = [i for i, c in enumerate(cents) if c is not None]
    def centre(s):
        i = int(np.clip(np.searchsorted(ks, s), 1, len(ks) - 1))
        lo = max([g for g in good if g <= i - 1], default=good[0]); hi = min([g for g in good if g >= i], default=good[-1])
        if lo == hi: return cents[lo]
        t = (s - ks[lo]) / (ks[hi] - ks[lo]); return cents[lo] * (1 - t) + cents[hi] * t
    sb = bvh_of(sf)
    before = len(sb.overlap(bvh_of(stub_f)))
    moved = 0; worst = 0.0
    for _ in range(3):
        for v in {v for f in stub_f for v in f.verts if all(g[lh] for g in v.link_faces)}:
            p = np.array(mw @ v.co); s = s_of(p)
            if s > S_MAX: continue
            c = centre(s); c = c + ax * (s - float((c - a1) @ ax))   # centre on the vertex's slice plane
            d = p - c; d = d - (d @ ax) * ax; r = np.linalg.norm(d)
            if r < 1e-4: continue
            d /= r
            h = sb.ray_cast(Vector(c.tolist()), Vector(d.tolist()), 0.15)
            if h[0] is None: continue
            hd = (np.array(h[0]) - c) @ d
            if r > K * hd:
                worst = max(worst, r - K * hd)
                v.co = mwi @ Vector((c + d * K * hd + ax * 0).tolist()); moved += 1
    after = len(sb.overlap(bvh_of(stub_f)))
    rep[tok] = {'sleeve_faces': len(sf), 'stub_faces': len(stub_f), 'moved': moved, 'worst_mm': round(worst * 1000, 1),
                'crossings_before': before, 'crossings_after': after}
bm.to_mesh(ob.data); ob.data.update()
print('STUB_INSIDE', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
