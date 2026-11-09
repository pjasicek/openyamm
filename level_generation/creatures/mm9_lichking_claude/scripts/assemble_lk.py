"""Step 2: raw Meshy parts -> symmetric labelled parts on one figure, Blender frame (faces -Y, z up, raw ABC handedness comes later).
Paired parts: the figure's RIGHT (-x, nearer the three-quarter camera) part is kept and mirrored. Midline parts: bisected, -x half mirrored.
Meshy's human head goes; the approved Lich's skull (work/lich_skull.npz) takes its place inside the crown. Meshy part 0 holds head, chest
medallion, buckle, one hand and thin strings: split by region, strings dropped. Each part reduced to its budget with symmetric collapse.
Args: <body raw npz> <skull npz> <out npz>. env SKULL_S (scale), SKULL_TOP (z of the skull top), SKULL_Y (front y shift)."""
import bpy, bmesh, sys, os
import numpy as np
BODY, SKULL, OUT = sys.argv[sys.argv.index('--') + 1:]
D = np.load(BODY); co, tri, comp = D['co'], D['tri'], D['comp']
tp = comp[tri[:, 0]]; cen = co[tri].mean(1)
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection
def make(name, tmask, src=None, largest=False):
    c, t = (co, tri) if src is None else src
    t = t[tmask]
    if largest:
        # keep the largest edge-connected piece (drops strings that touch the region)
        par = {}
        def f(x):
            while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
            return x
        for a, b, d in t: par[f(b)] = f(a); par[f(d)] = f(a)
        r = np.array([f(a) for a in t[:, 0]]); u, cnt = np.unique(r, return_counts=True); t = t[r == u[cnt.argmax()]]
    used, inv = np.unique(t, return_inverse=True)
    me = bpy.data.meshes.new(name); me.from_pydata(c[used].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o
def mirror_mid(o, keep_positive=False):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=not keep_positive, clear_inner=keep_positive, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.mirror(bm, geom=g, axis='X', merge_dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
def pair(o):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    ret = bmesh.ops.duplicate(bm, geom=g)
    vs = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]; fs = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)]
    for v in vs: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=fs)
    bm.to_mesh(me); bm.free(); return o
T = lambda k: tp == k
# long thin triangles are the strings
el = np.max(np.linalg.norm(co[tri] - co[np.roll(tri, 1, 1)], axis=2), 1)
z, x, y = cen[:, 2], cen[:, 0], cen[:, 1]
parts = {}
# ---- midline parts (bisected, -x half kept)
parts['torso'] = make('torso', T(1))
parts['pants'] = make('pants', T(4))
parts['crown'] = make('crown', T(3) | T(9))
parts['collar'] = make('collar', T(11))
parts['tabard'] = make('tabard', T(10))
parts['buckle'] = make('buckle', T(0) & (z > 0.86) & (z < 1.1) & (el < 0.05), largest=True)
parts['medal'] = make('medal', T(0) & (z > 1.12) & (z < 1.32) & (y < -0.07) & (el < 0.05), largest=True)
for k in ('torso', 'pants', 'crown', 'collar', 'tabard', 'buckle', 'medal'): mirror_mid(parts[k])
# ---- pairs from the -x side
parts['hands'] = pair(make('hands', T(0) & (z < 0.86) & (x < -0.2) & (el < 0.05), largest=True))
parts['uarms'] = pair(make('uarms', T(7)))
parts['bracers'] = pair(make('bracers', T(13)))
parts['boots'] = pair(make('boots', T(6)))
parts['kneemed'] = pair(make('kneemed', T(14)))
parts['medalsF'] = pair(make('medalsF', T(17)))
parts['medalsB'] = pair(make('medalsB', T(19)))
parts['wings'] = pair(make('wings', T(20)))
# ---- skull: the Lich's, scaled into the crown
S = np.load(SKULL); sc, st = S['co'], S['tri']
s = float(os.environ.get('SKULL_S', '0.82'))     # 2026-10-31 r2: 0.88 at top 1.565 left the cranium out of the crown
q = (sc - [0.5 * (sc[:, 0].min() + sc[:, 0].max()), 0, 0]) * s
q[:, 2] += float(os.environ.get('SKULL_TOP', '1.545')) - q[:, 2].max()
q[:, 1] += float(os.environ.get('SKULL_Y', '0.017'))
print('SKULL z', q[:, 2].min().round(3), q[:, 2].max().round(3), 'y', q[:, 1].min().round(3), q[:, 1].max().round(3), 'w', np.ptp(q[:, 0]).round(3))
me = bpy.data.meshes.new('skull'); me.from_pydata(q.tolist(), [], st.tolist()); me.update()
o = bpy.data.objects.new('skull', me); coll.objects.link(o); parts['skull'] = o
for o in parts.values():
    for p in o.data.polygons: p.use_smooth = True
BUDGET = dict(torso=2800, pants=600, crown=850, collar=180, tabard=286, buckle=380, medal=200, hands=1500, uarms=600, bracers=340, boots=900, kneemed=240,
              medalsF=240, medalsB=240, wings=240, skull=3000)
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
total = 0
for nm, o in parts.items():
    t0 = tris(o)
    if not os.environ.get('NOREDUCE') and t0 > BUDGET[nm] * 1.02:
        bpy.context.view_layer.objects.active = o
        for xo in bpy.data.objects: xo.select_set(xo is o)
        m = o.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = BUDGET[nm] / t0; m.use_symmetry = True; m.symmetry_axis = 'X'; m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='d')
    print('PART', nm, t0, '->', tris(o)); total += tris(o)
print('TOTAL tris', total)
names = list(parts); Co = []; Tr = []; Pa = []; base = 0
for k, nm in enumerate(names):
    me = parts[nm].data; me.calc_loop_triangles()
    c = np.array([v.co[:] for v in me.vertices]); t = np.array([lt.vertices[:] for lt in me.loop_triangles])
    Co.append(c); Tr.append(t + base); Pa.append(np.full(len(c), k)); base += len(c)
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names))
print('SAVED', base)
