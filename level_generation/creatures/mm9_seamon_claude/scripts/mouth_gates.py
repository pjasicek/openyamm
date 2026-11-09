"""Mouth gates on an exported GLB, every clip at 48 fps (LOD0 'Sea' mesh, skinned by Blender):
  teeth   - intersecting triangle pairs: lower teeth x upper exterior skin, upper teeth x lower exterior skin, and
            lower x upper exterior skin (lips through each other)
  cavity  - cavity triangles x exterior skin (the mouth lining showing through the head)
  stretch - cavity triangles: largest edge length ratio posed / bind, and texel stretch (3D length per texel over
            the head skin's median at bind: 1 = as sharp as the head), max and p99 per clip
  hinge   - triangles within HINGE_R of a mouth corner (bind) that are slivers (aspect L^2/2A > 12) or whose edges
            stretch past 2x / shrink below 0.35x; the worst frame per clip
Labels come from a blend with the same body (by bind position): mouth_rebuild.py's 'mlab' attribute, or for the old
body the 'piece' teeth (upper/lower by jaw weight) and an interior flag per loop triangle (mouth_open_probe.py npy)
so the old mouth interior does not count as exterior skin.

Args: <glb> <label blend> <out json> [interior npy|-] [corners json (mouth_rebuild report)]
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, LABB, OUT = argv[:3]
INTERIOR = argv[3] if len(argv) > 3 and argv[3] != '-' else None
CORNERS = json.load(open(argv[4]))['corners'] if len(argv) > 4 else None
FPS = 48
HINGE_R = 0.15
HEAD_Y = -1.2

# ---------------------------------------------------------------- labels from the blend
bpy.ops.wm.open_mainfile(filepath=LABB)
ob = bpy.data.objects.get('Body') or bpy.data.objects.get('Sea')
me = ob.data
n = len(me.vertices)
P = np.array([v.co[:] for v in me.vertices])
gi = {g.name: g.index for g in ob.vertex_groups}
jaw = np.zeros(n)
for v in me.vertices:
    for g in v.groups:
        if g.group == gi.get('Bone08'):
            jaw[v.index] = g.weight
cls = np.zeros(n, int)          # 0 upper skin, 1 lower skin, 2 cavity, 3 upper teeth, 4 lower teeth, 5 eye, 6 other
if 'mlab' in me.attributes:
    ml = np.array([d.value for d in me.attributes['mlab'].data])
    cls = np.where(jaw >= 0.5, 1, 0)
    cls[ml == 1] = 2
    cls[ml == 2] = 3
    cls[ml == 3] = 4
    cls[ml == 4] = 5
else:
    piece = np.array([d.value for d in me.attributes['piece'].data])
    cls = np.where(jaw >= 0.5, 1, 0)
    adj = [[] for _ in range(n)]
    for e in me.edges:
        a, b = e.vertices
        adj[a].append(b); adj[b].append(a)
    seen = np.zeros(n, bool)
    for s in range(n):
        if seen[s] or piece[s] != 2:
            continue
        st, ids = [s], [s]
        seen[s] = True
        while st:
            x = st.pop()
            for y in adj[x]:
                if not seen[y]:
                    seen[y] = True; st.append(y); ids.append(y)
        c = P[ids].mean(0)
        if c[1] > -1.3 or c[2] > 0.9:
            cls[ids] = 6
        elif c[2] > 0.58 and np.ptp(P[ids], 0).max() < 0.1 and jaw[ids].mean() < 0.5 and abs(c[0]) > 0.12:
            cls[ids] = 5
        else:
            cls[ids] = 4 if jaw[ids].mean() >= 0.5 else 3
    if INTERIOR:
        me.calc_loop_triangles()
        op = np.load(INTERIOR)
        for t, o in zip(me.loop_triangles, op):
            if o < 0.35:
                for i in t.vertices:
                    if cls[i] in (0, 1):
                        cls[i] = 2
kd = KDTree(n)
for i, p in enumerate(P):
    kd.insert(p, i)
kd.balance()

# ---------------------------------------------------------------- the GLB
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
mesh = next(o for o in sc.objects if o.type == 'MESH' and o.name.split('.')[0] == 'Sea' and 'LOD' not in o.name
            and o.find_armature() is not None) if any(o.name.startswith('Sea') for o in sc.objects) else None
if mesh is None:
    mesh = max((o for o in sc.objects if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
gm = mesh.data
gm.calc_loop_triangles()
gv = np.array([v.co[:] for v in gm.vertices])
gcls = np.array([cls[kd.find(Vector(p))[1]] for p in (mesh.matrix_world @ Vector(q) for q in gv)])
tris = np.array([t.vertices[:] for t in gm.loop_triangles])
uvl = gm.uv_layers.active.data
tuv = np.array([[uvl[l].uv[:] for l in t.loops] for t in gm.loop_triangles])
tc = np.array([np.bincount(gcls[t], minlength=7).argmax() if len(set(gcls[t])) > 1 else gcls[t[0]] for t in tris])
bind_w = np.array([(mesh.matrix_world @ Vector(q))[:] for q in gv])
head = bind_w[tris].mean(1)[:, 1] < HEAD_Y
groups = {k: np.nonzero((tc == c) & head)[0] for k, c in (('up', 0), ('lo', 1), ('cav', 2), ('ut', 3), ('lt', 4))}
# exterior skin away from the lip line only: faces touching cavity/teeth vertices are the lip itself
lipv = set(np.nonzero(np.isin(gcls, (2, 3, 4)))[0])
for k in ('up', 'lo'):
    groups[k] = np.array([t for t in groups[k] if not (set(tris[t]) & lipv)], int)
corner_ids = np.zeros(len(tris), bool)
if CORNERS:
    cen = bind_w[tris].mean(1)
    for c in CORNERS:
        corner_ids |= np.linalg.norm(cen - np.array(c), axis=1) < HINGE_R
    corner_ids &= np.isin(tc, (0, 1, 2))      # skin and cavity (teeth are slender by design)


def tri_geom(p):
    a, b, c = p[tris[:, 0]], p[tris[:, 1]], p[tris[:, 2]]
    e = np.stack([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1), np.linalg.norm(a - c, axis=1)], 1)
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    return e, area


def sigma_max(p, sel):
    """Largest singular value of the map UV (texels at 2048) -> 3D per triangle."""
    a, b, c = p[tris[sel, 0]], p[tris[sel, 1]], p[tris[sel, 2]]
    uv = tuv[sel] * 2048
    du1, du2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    det = du1[:, 0] * du2[:, 1] - du2[:, 0] * du1[:, 1]
    ok = np.abs(det) > 1e-9
    e1, e2 = b - a, c - a
    inv = np.stack([np.stack([du2[:, 1], -du2[:, 0]], 1), np.stack([-du1[:, 1], du1[:, 0]], 1)], 1) / \
        np.where(ok, det, 1)[:, None, None]
    J = np.einsum('tki,tij->tkj', np.stack([e1, e2], 2), inv)
    s = np.linalg.svd(J, compute_uv=False)[:, 0]
    return np.where(ok, s, np.nan)


bind_e, bind_a = tri_geom(bind_w)
cav = groups['cav']
bind_sig = sigma_max(bind_w, cav) if len(cav) else np.zeros(0)
skin_sig = sigma_max(bind_w, np.concatenate([groups['up'], groups['lo']]))
sig_med = float(np.nanmedian(skin_sig))          # texel stretch is measured against the head skin's density
fps_scene = sc.render.fps / sc.render.fps_base
report = {'groups': {k: int(len(v)) for k, v in groups.items()}, 'corner_tris': int(corner_ids.sum()),
          'cavity_bind_texels_per_m': round(1 / float(np.nanmedian(bind_sig)), 1) if len(cav) else None,
          'head_skin_texels_per_m': round(1 / sig_med, 1), 'clips': {}}
dg = bpy.context.evaluated_depsgraph_get()
arm.animation_data_create()


def posed():
    dg.update()
    ev = mesh.evaluated_get(dg)
    m = ev.to_mesh()
    p = np.array([(mesh.matrix_world @ v.co)[:] for v in m.vertices])
    ev.to_mesh_clear()
    return p


def overlaps(p, a, b):
    if len(a) == 0 or len(b) == 0:
        return 0
    verts = [Vector(x) for x in p]
    ta = BVHTree.FromPolygons(verts, tris[a].tolist())
    tb = BVHTree.FromPolygons(verts, tris[b].tolist())
    # neighbours that only touch at a shared vertex are not a crossing
    return sum(1 for i, j in ta.overlap(tb) if not set(tris[a[i]]) & set(tris[b[j]]))


def lip_pairs(p):
    verts = [Vector(x) for x in p]
    ta = BVHTree.FromPolygons(verts, tris[groups['lo']].tolist())
    tb = BVHTree.FromPolygons(verts, tris[groups['up']].tolist())
    return [(np.round(bind_w[tris[groups['lo'][i]]].mean(0), 3).tolist(),
             np.round(bind_w[tris[groups['up'][j]]].mean(0), 3).tolist()) for i, j in ta.overlap(tb)
            if not set(tris[groups['lo'][i]]) & set(tris[groups['up'][j]])]


def frame_vals(p):
    e, area = tri_geom(p)
    vals = {'lt_up': overlaps(p, groups['lt'], groups['up']), 'ut_lo': overlaps(p, groups['ut'], groups['lo']),
            'lips': overlaps(p, groups['lo'], groups['up']),
            'cavity_skin': overlaps(p, groups['cav'], np.concatenate([groups['up'], groups['lo']]))}
    if corner_ids.any():
        rr = e[corner_ids] / np.maximum(bind_e[corner_ids], 1e-9)
        L = e[corner_ids].max(1)
        asp = L * L / np.maximum(2 * area[corner_ids], 1e-12)
        vals['hinge_bad'] = int(((asp > 12) | (rr.max(1) > 2.0) | (rr.min(1) < 0.35)).sum())
    return vals


report['bind'] = frame_vals(bind_w)
for act in bpy.data.actions:
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    dur = (f1 - f0) / fps_scene
    worst = {'lt_up': 0, 'ut_lo': 0, 'lips': 0, 'cavity_skin': 0, 'stretch_max': 0.0, 'texel_max': 0.0,
             'hinge_bad': 0}
    at = {}
    frames_pen = 0
    texels = []
    for k in range(int(math.floor(dur * FPS + 1e-6)) + 1):
        t = k / FPS
        f = f0 + t * fps_scene
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        p = posed()
        vals = frame_vals(p)
        if os.environ.get('LIPS_DEBUG') == act.name and abs(t - float(os.environ.get('LIPS_T', 0))) < 1e-3:
            print('LIPS', lip_pairs(p))
        frames_pen += (vals['lt_up'] + vals['ut_lo']) > 0
        e, area = tri_geom(p)
        if len(cav):
            r = (e[cav] / np.maximum(bind_e[cav], 1e-9)).max(1)
            s = sigma_max(p, cav) / sig_med
            texels.append(s)
            vals['stretch_max'] = float(r.max())
            vals['texel_max'] = float(np.nanmax(s))
        for key, v in vals.items():
            if v > worst[key]:
                worst[key] = v
                at[key] = round(t, 3)
    rec = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in worst.items()}
    rec['at_s'] = at
    rec['frames_with_teeth_penetration'] = int(frames_pen)
    rec['frames'] = int(math.floor(dur * FPS + 1e-6)) + 1
    if texels:
        allt = np.concatenate(texels)
        rec['texel_p99'] = round(float(np.nanpercentile(allt, 99)), 3)
    report['clips'][act.name] = rec
json.dump(report, open(OUT, 'w'), indent=1)
print('GATES ' + json.dumps({k: {kk: v[kk] for kk in ('lt_up', 'ut_lo', 'lips', 'cavity_skin', 'stretch_max',
                                                      'texel_max', 'hinge_bad')}
                             for k, v in report['clips'].items()}))
