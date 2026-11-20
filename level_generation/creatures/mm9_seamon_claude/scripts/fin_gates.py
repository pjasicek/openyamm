"""Fin gap gate: every tail fin piece's base edge against the tail surface, in the bind pose and every clip at 48 fps.
Args: <glb> <label blend (same body; its 'piece' attribute)> <out json>

Fins = piece-2 components behind the head (bind), all on the tail's top. Base edge = the lowest vertex
of every 2 cm slice along the tail among the lowest 35 % of the fin's height (bind), so the whole base length counts. Gap per base vertex = its distance outside
the main body surface (0 when inside, by the surface normal at the nearest point); a fin's gap is the largest over
its whole base edge, so a base that touches at one corner and lifts at the other still fails.
"""
import bpy, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, LABB, OUT = argv[:3]
FPS = 48
bpy.ops.wm.open_mainfile(filepath=LABB)
me = bpy.data.objects['Body'].data
P = np.array([v.co[:] for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
kd = KDTree(len(P))
for i, p in enumerate(P):
    kd.insert(p, i)
kd.balance()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
mesh = next(o for o in sc.objects if o.type == 'MESH' and o.name == 'Sea')
gm = mesh.data
gm.calc_loop_triangles()
bind = np.array([(mesh.matrix_world @ v.co)[:] for v in gm.vertices])
gp = np.array([piece[kd.find(Vector(p))[1]] for p in bind])
tris = np.array([t.vertices[:] for t in gm.loop_triangles])
# welded components
key = {}
wid = np.array([key.setdefault(tuple(np.round(p, 5)), len(key)) for p in bind])
parent = list(range(len(key)))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for t in tris:
    a, b, c = (find(wid[i]) for i in t)
    parent[b] = a
    parent[find(c)] = a
root = np.array([find(w) for w in wid])
roots, counts = np.unique(root, return_counts=True)
main = roots[np.argmax(counts)]
body_tris = tris[root[tris[:, 0]] == main]
fins = []
for r in roots:
    ids = np.nonzero(root == r)[0]
    c = bind[ids].mean(0)
    if r == main or gp[ids[0]] != 2 or c[1] < -1.3 or c[2] < 0.0:
        continue
    fins.append((ids, c))


def bvh_of(p):
    return BVHTree.FromPolygons([Vector(x) for x in p], body_tris.tolist())


bt = bvh_of(bind)
bases = []
for ids, c in fins:
    z = bind[ids][:, 2]
    zcut = z.min() + 0.35 * np.ptp(z)
    slices = {}
    for i in ids:
        if bind[i][2] > zcut:
            continue
        k = int(bind[i][1] // 0.02)
        if k not in slices or bind[i][2] < bind[slices[k]][2]:
            slices[k] = i
    bases.append(np.array(list(slices.values())))


def gaps(p):
    tree = bvh_of(p)
    out = []
    for base in bases:
        g = 0.0
        for i in base:
            q = Vector(p[i])
            co, nrm, _, dist = tree.find_nearest(q)
            if co is not None and (q - co).dot(nrm) > 0:
                g = max(g, dist)
        out.append(g)
    return out


dg = bpy.context.evaluated_depsgraph_get()


def posed():
    dg.update()
    ev = mesh.evaluated_get(dg)
    m = ev.to_mesh()
    p = np.array([(mesh.matrix_world @ v.co)[:] for v in m.vertices])
    ev.to_mesh_clear()
    return p


rep = {'fins': [[round(x, 3) for x in c] for _, c in fins], 'bind_gap_m': [round(g, 4) for g in gaps(bind)], 'clips': {}}
fps = sc.render.fps / sc.render.fps_base
arm.animation_data_create()
worst_all = [0.0] * len(fins)
for act in bpy.data.actions:
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    worst, at = [0.0] * len(fins), [0.0] * len(fins)
    for k in range(int((f1 - f0) / fps * FPS) + 1):
        f = f0 + k / FPS * fps
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        for j, g in enumerate(gaps(posed())):
            if g > worst[j]:
                worst[j], at[j] = g, k / FPS
    rep['clips'][act.name] = {'worst_gap_m': [round(g, 4) for g in worst], 'at_s': [round(t, 3) for t in at]}
    worst_all = [max(a, b) for a, b in zip(worst_all, worst)]
rep['worst_gap_any_clip_m'] = [round(g, 4) for g in worst_all]
json.dump(rep, open(OUT, 'w'), indent=1)
print('FINGATE ' + json.dumps({'fins': rep['fins'], 'bind': rep['bind_gap_m'], 'worst': rep['worst_gap_any_clip_m']}))
