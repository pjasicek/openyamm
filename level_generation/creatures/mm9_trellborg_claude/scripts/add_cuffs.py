"""Rigid flared cuffs over the wrist join, one per arm: closed double wall, 100 % on Forearm. UVs from the end of the bracer on the shared body layout, per quad: corners by the bracer surface at the same angle, ring's free edge = the bracer's rim, so each tier's own paint reads as part of the bracer. Quads straddling a chart seam stay inside one source triangle. Writes work/cuff.json (rings in the forearm frame). Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
HERE = '/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_trellborg_claude/'
C = json.load(open(HERE + 'scripts/cuff_config.json'))
RINGS = C['rings']; N = C['sides']; WALL = C['wall']          # outer rings [al, r]; the wall comes back inside
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
gi = body.vertex_groups
FR = json.load(open(HERE + 'work/hands_v1.json'))['frames']
unit = lambda v: v / np.linalg.norm(v)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv['PartUV']; lay = bm.verts.layers.int['part']; mt = bm.faces.layers.int['mat']; dv = bm.verts.layers.deform.verify()
out = {}
for S, sg in (('R', -1), ('L', 1)):
    W = np.array(FR[S]['W']); d = unit(np.array(FR[S]['d'])); U = unit(np.cross(d, [0, 0, 1.0])); V = np.cross(d, U)
    fg = gi[f'Bip01 {S} Forearm'].index
    src = []
    for f in bm.faces:
        if f[mt] != 0: continue
        c = np.array(f.calc_center_median()[:]) - W; a = c @ d
        if np.sign(c[0] + W[0]) == sg and -0.17 < a < C['src_end'] and np.linalg.norm(c - d * a) < 0.11: src.append(f)
    vs = [list(l.vert.co) for f in src for l in f.loops]; tr = [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(src))]
    bvh = BVHTree.FromPolygons(vs, tr, all_triangles=True)
    n = len(RINGS)
    als = [r[0] for r in RINGS]; a0, a1 = als[0], als[-1]
    sa = lambda a: C['src_start'] + (a - a0) / (a1 - a0) * (C['src_end'] - 0.002 - C['src_start'])
    rings = [(a, r) for a, r in RINGS] + [(a1 + 0.004, RINGS[-1][1] - WALL * 0.5)] + [(a, r - WALL) for a, r in reversed(RINGS[1:])]
    P = lambda a, r, j: W + d * a + (U * np.cos(2 * np.pi * j / N) + V * np.sin(2 * np.pi * j / N)) * r
    grid = [[bm.verts.new(P(a, r, j).tolist()) for j in range(N)] for a, r in rings]
    for rw in grid:
        for v in rw: v[lay] = 30; v[dv][fg] = 1.0
    def src_of(a, j):
        q = W + d * sa(a) + (U * np.cos(2 * np.pi * j / N) + V * np.sin(2 * np.pi * j / N)) * 0.074
        loc, nor, idx, dist = bvh.find_nearest(Vector(q)); return np.array(loc[:]), idx
    def uv_in(f, p, clamp):
        vv = [np.array(l.vert.co[:]) for l in f.loops]; uv = [np.array(l[uvl].uv[:]) for l in f.loops]
        e1, e2 = vv[1] - vv[0], vv[2] - vv[0]; A = np.c_[e1, e2]; x = np.linalg.lstsq(A, p - vv[0], rcond=None)[0]
        b = np.array([1 - x.sum(), x[0], x[1]])
        if clamp: b = np.clip(b, 0, 1); b /= b.sum()
        return b[0] * uv[0] + b[1] * uv[1] + b[2] * uv[2]
    seam = 0; used = 0
    for i in range(len(rings)):
        i2 = (i + 1) % len(rings); ai, aj = rings[i][0], rings[i2][0]
        # rings past the free edge fold back: the source runs back too
        for j in range(N):
            k = (j + 1) % N
            flip = i >= n                                   # inner wall
            q = (grid[i][j], grid[i][k], grid[i2][k], grid[i2][j])
            if flip: pass
            cor = [(ai, j), (ai, j + 1), (aj, j + 1), (aj, j)]
            pts = [src_of(a, jj) for a, jj in cor]; uvs = [uv_in(src[p[1]], p[0], True) for p in pts]
            e = max(np.linalg.norm(uvs[x] - uvs[(x + 1) % 4]) for x in range(4))
            cen, ci = src_of(0.5 * (ai + aj), j + 0.5)
            if e > C['seam_uv']:
                seam += 1; uvs = [uv_in(src[ci], pp[0], True) for pp in pts]
            f = bm.faces.new(q); f.smooth = True; f[mt] = 0; used += 1
            for l, u in zip(f.loops, uvs): l[uvl].uv = (float(u[0]), float(u[1]))
    # orient: outer wall normals out
    cf = list({f for rw in grid for v in rw for f in v.link_faces}); bmesh.ops.recalc_face_normals(bm, faces=cf)
    print('CUFF', S, 'rings', len(rings), 'quads', used, 'seam quads', seam, 'src faces', len(src))
    out[S] = dict(rings=RINGS, wall=WALL)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free()
json.dump(out, open(HERE + 'work/cuff.json', 'w'))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CUFF done')
