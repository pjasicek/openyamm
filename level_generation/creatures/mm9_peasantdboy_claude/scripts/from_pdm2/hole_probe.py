"""Which faces does the view meet through a see-through hole? For one clip frame and view (see_through_gate.py's camera
rule), every hole pixel near a target bone is ray cast through all back faces until it leaves the model; reported are
the first back faces hit: count, their rest height relative to the target, their loose part (vertices welded by
position), whether they are lining faces (one texel: all loops share a UV) and their face index sample.
Args (Blender): <glb> <clip> <frame30> <az> <el> <bone[@t]> [radius 0.12] [px_mm 2]"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import Counter

a = sys.argv[sys.argv.index('--') + 1:]
GLB, CLIP, F30, AZ, EL, TGT = a[0], a[1], int(a[2]), float(a[3]), float(a[4]), a[5]
RAD = float(a[6]) if len(a) > 6 else 0.12
PX = (float(a[7]) if len(a) > 7 else 2.0) / 1000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name
            and 'Shadow' not in o.name)
me = mesh.data
uv = me.uv_layers[0].data
lining = np.array([len({tuple(round(x, 6) for x in uv[i].uv) for i in p.loop_indices}) == 1 for p in me.polygons])
bm = bmesh.new(); bm.from_mesh(me)
weld = {}
for v in bm.verts:
    weld.setdefault(tuple(round(x, 5) for x in v.co), []).append(v.index)
par = list(range(len(bm.verts)))
def fnd(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
for vs in weld.values():
    for x in vs[1:]:
        par[fnd(x)] = fnd(vs[0])
for e in bm.edges:
    par[fnd(e.verts[1].index)] = fnd(e.verts[0].index)
part = np.array([fnd(p.vertices[0]) for p in me.polygons])
ids, cnt = np.unique(part, return_counts=True)
rest_c = np.array([tuple(mesh.matrix_world @ p.center) for p in me.polygons])
sc = bpy.context.scene
FPS = sc.render.fps / sc.render.fps_base
act = bpy.data.actions[CLIP]
rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f = act.frame_range[0] + F30 / 30.0 * FPS
sc.frame_set(int(f), subframe=f % 1.0)
dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg); em = ev.to_mesh()
P = [ev.matrix_world @ v.co for v in em.vertices]
polys = [p.vertices[:] for p in em.polygons]
normals = [(ev.matrix_world.to_3x3() @ p.normal).normalized() for p in em.polygons]
bvh = BVHTree.FromPolygons(P, polys)
bn, t = (TGT.split('@') + ['0'])[:2]
pb = rig.pose.bones[bn]
h = rig.matrix_world @ pb.head
T = h.lerp(rig.matrix_world @ (pb.children[0].head if pb.children else pb.tail), float(t))
d = Vector((math.sin(math.radians(AZ)) * math.cos(math.radians(EL)), -math.cos(math.radians(AZ)) * math.cos(math.radians(EL)),
            math.sin(math.radians(EL))))
rot = (-d).to_track_quat('-Z', 'Y').to_matrix()
right, up, fwd = rot.col[0], rot.col[1], -rot.col[2]
n = int(2 * RAD / PX)
names = [g.name for g in mesh.vertex_groups]
def dom_bone(k):
    c = Counter()
    for vi in me.polygons[k].vertices:
        gs = me.vertices[vi].groups
        if len(gs):
            c[names[max(gs, key=lambda g: g.weight).group]] += 1
    return c.most_common(1)[0][0] if c else ''
hole_bones = Counter()
hole_faces = {}
first_back, hole_first = Counter(), Counter()
zs = []
for i in range(n):
    for j in range(n):
        o = T + d * 3 + right * ((j + 0.5) * PX - RAD) + up * ((i + 0.5) * PX - RAD)
        hit = bvh.ray_cast(o, fwd, 10)
        if hit[0] is None:
            continue
        k = hit[2]
        if normals[k].dot(fwd) < 0:          # front face first: not into an opening
            continue
        fb = k
        loc = hit[0]
        front = False
        for _ in range(20):
            hit = bvh.ray_cast(loc + fwd * 1e-4, fwd, 10)
            if hit[0] is None:
                break
            if normals[hit[2]].dot(fwd) < 0:
                front = True; break
            loc = hit[0]
        key = (int(part[fb]), bool(lining[fb]))
        first_back[key] += 1
        if not front:
            hole_first[key] += 1
            zs.append(rest_c[fb][2])
            hole_bones[(dom_bone(fb), int(me.polygons[fb].material_index))] += 1
            hole_faces[fb] = hole_faces.get(fb, 0) + 1
print('HOLEPROBE parts (id: faces)', {int(i): int(c) for i, c in zip(ids, cnt)})
print('HOLEPROBE first back face (part, lining): px', dict(first_back))
print('HOLEPROBE holes by first back face (part, lining): px', dict(hole_first))
print('HOLEPROBE hole first back faces by (dominant bone, material)', dict(hole_bones))
print('HOLEPROBE part sizes of hits', {int(k[0]): int(cnt[list(ids).index(k[0])]) for k in hole_first})
for k, c in sorted(hole_faces.items(), key=lambda kv: -kv[1])[:8]:
    print('HOLEPROBE face', k, 'px', c, 'rest centre', [round(x, 4) for x in rest_c[k]],
          'rest normal', [round(x, 3) for x in (mesh.matrix_world.to_3x3() @ me.polygons[k].normal).normalized()])
if zs:
    print('HOLEPROBE hole first-back-face rest z pct 10/50/90', np.percentile(zs, [10, 50, 90]).round(3).tolist())
