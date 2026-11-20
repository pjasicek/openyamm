"""Poke-through gate for Yrsa's rooted boots (root_shoes.py, 2026-10-30): the stretched thigh band must stay inside the
dress in every clip frame.

Args (Blender): <glb> <report json> [fps 48] [min height m 0.5] [lowest ray elevation deg -10]
The boot pieces are the loose LOD0 parts weighted mostly to a Foot joint; their faces with a vertex higher than
`min height` above the floor at rest are the thigh band. In every frame of every clip (and the bind pose) rays leave
points on those faces (centre and three inner points) in 80 directions from 10 deg below the horizon to 50 deg above
(where a standing or party camera can be). A ray that leaves the model without hitting anything is a point seen from
outside: the band pokes through the skirt there. Reports the visible points per clip and the worst frame.
"""
import bpy, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
GLB, REP = a[0], a[1]
FPS = float(a[2]) if len(a) > 2 else 48.0
MINH = float(a[3]) if len(a) > 3 else 0.5
MINEL = float(a[4]) if len(a) > 4 else -10.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name
            and 'Shadow' not in o.name)
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not mesh:
        bpy.data.objects.remove(o)
me = mesh.data
names = [g.name for g in mesh.vertex_groups]
# loose parts by position-welded connectivity (glTF splits vertices on UV seams)
key = {}
weld = np.array([key.setdefault(tuple(np.round(v.co, 5)), len(key)) for v in me.vertices])
parent = list(range(len(key)))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x


for p in me.polygons:
    vs = [find(weld[i]) for i in p.vertices]
    for v in vs[1:]:
        parent[find(v)] = find(vs[0])
comp = np.array([find(weld[i]) for i in range(len(me.vertices))])
foot = {}
for c in np.unique(comp):
    ids = np.nonzero(comp == c)[0]
    if len(ids) > 600:
        continue
    acc = {}
    for i in ids:
        for g in me.vertices[i].groups:
            acc[names[g.group]] = acc.get(names[g.group], 0) + g.weight
    top = max(acc, key=acc.get)
    if top.endswith('Foot'):
        foot[c] = top
assert len(foot) == 2, foot
rest = [mesh.matrix_world @ v.co for v in me.vertices]
floor = min(p.z for p in rest)
band = [p.index for p in me.polygons if comp[p.vertices[0]] in foot and max(rest[i].z for i in p.vertices) - floor > MINH]
dirs = [Vector((math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(az))
                * math.cos(math.radians(el)), math.sin(math.radians(el))))
        for el in (-10, 0, 15, 30, 50) if el >= MINEL for az in range(0, 360, 360 // 16)]
sc = bpy.context.scene
frames = [('bind', None, 0.0)]
for act in bpy.data.actions:
    lo, hi = act.frame_range
    dur = (hi - lo) / 24.0                    # glTF import keys at 24 fps
    frames += [(act.name, act, t) for t in np.arange(0, dur + 1e-6, 1.0 / FPS)]
rep = {'min_elevation_deg': MINEL, 'band_faces': len(band), 'boots': sorted(foot.values()), 'clips': {}}
rig.animation_data_create()
for clip, act, t in frames:
    if act is None:
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        f = act.frame_range[0] + t * 24.0
        sc.frame_set(int(f), subframe=f % 1.0)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    em = ev.to_mesh()
    P = [ev.matrix_world @ v.co for v in em.vertices]
    bvh = BVHTree.FromPolygons(P, [p.vertices[:] for p in em.polygons])
    seen = 0
    for fi in band:
        vs = em.polygons[fi].vertices
        cen = sum((P[i] for i in vs), Vector()) / len(vs)
        pts = [cen] + [cen.lerp(P[i], 0.6) for i in vs]
        for q in pts:
            for d in dirs:
                hit = bvh.ray_cast(q + d * 0.001, d, 10.0)
                if hit[0] is None:
                    seen += 1
                    break
    ev.to_mesh_clear()
    r = rep['clips'].setdefault(clip, {'frames': 0, 'frames_seen': 0, 'worst_points': 0, 'worst_time': None})
    r['frames'] += 1
    if seen:
        r['frames_seen'] += 1
        if seen > r['worst_points']:
            r['worst_points'], r['worst_time'] = seen, round(float(t), 4)
rep['total_frames_seen'] = sum(r['frames_seen'] for r in rep['clips'].values())
json.dump(rep, open(REP, 'w'), indent=1)
print('POKE_GATE', json.dumps(rep))
