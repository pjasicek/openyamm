"""G6 for hvf's legs against the coat-dress (user review 2026-10-22: "feet leak through the coat", the stepping thigh
came out through the front panel): on every frame of every clip, each trouser-leg vertex of the thigh and knee
(garment 15, rest z in ZRANGE) against the coat's outer surface (garments 1 and 2, faces whose rest normal points away
from the body axis, n . radial > 0.3). The coat is an open shell for this test: proximity to the nearest outer face,
signed by that face's normal; a leg vertex is IN FRONT of the panel when its signed distance exceeds LEAK and the
offset is along the normal (tangential part < TANG: the vertex lies over the panel, not beside its edge, so the legs
showing through the front split do not count). Faces turned down (posed normal z < -0.5: the underside of
the coat lying on the floor in Death) are not a panel front. Leg vertices already in front of the coat at rest (the split shows
them) are left out. Prints per clip the frames with leaks, the count and the worst depth; writes
review/g6_legs_<tag>.json. Args: -- <blend> <tag> [clip ...]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag, clips = a[0], a[1], a[2:]
LEAK, TANG = float(os.environ.get('LEAK', '0.005')), float(os.environ.get('TANG', '0.003'))
ZRANGE = (0.33, 1.00)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
gv = np.array([x.value for x in me.attributes['garment'].data])
R0 = np.array([v.co[:] for v in me.vertices])
pel = np.array(rig.data.bones['B_Pelvis'].head_local)
coat_faces = []
for p in me.polygons:
    if all(gv[i] in (1, 2) for i in p.vertices):
        c = np.array(p.center); rad = c[:2] - pel[:2]; rn = np.linalg.norm(rad)
        if rn > 1e-6 and (np.array(p.normal[:2]) @ (rad / rn)) > 0.3 and c[2] < 1.15:
            coat_faces.append(tuple(p.vertices))
legs = np.where((gv == 15) & (R0[:, 2] > ZRANGE[0]) & (R0[:, 2] < ZRANGE[1]))[0]


def leaks(P):
    tree = BVHTree.FromPolygons(P, coat_faces)
    out = []
    for i in legs:
        loc, n, idx, d = tree.find_nearest(P[i], 0.08)
        if loc is None:
            continue
        off = P[i] - loc; s = off.dot(n)
        if n.z < -0.5:                                  # the underside of cloth lying on the floor faces nobody
            continue
        if s > LEAK and (off - n * s).length < TANG:
            out.append((int(i), s, int(idx)))
    return out


rest = {i for i, _, _ in leaks([Vector(x) for x in R0])}
acts = [x for x in bpy.data.actions if (not clips or x.name in clips) and x.name in ('Standing', 'Walking', 'Hit', 'Death', 'Fidget')]
report = {'rest_excluded': len(rest), 'leg_vertices': int(len(legs))}
for act in acts:
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    frames, worst, most = [], 0.0, 0
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m2 = ev.to_mesh()
        P = [v.co.copy() for v in m2.vertices]; ev.to_mesh_clear()
        L = [(i, s, k) for i, s, k in leaks(P) if i not in rest]
        if os.environ.get('DETAIL') and L and len(L) == max(most, len(L)):
            fc = coat_faces[max(L, key=lambda x: x[1])[2]]
            print('G6LEGS detail', act.name, f, 'n', len(L), 'worst leg rest', np.round(R0[max(L, key=lambda x: x[1])[0]], 3).tolist(),
                  'coat face rest centre', np.round(R0[list(fc)].mean(0), 3).tolist(), 'garment', int(gv[fc[0]]))
        if L:
            frames.append(f); worst = max(worst, max(x[1] for x in L)); most = max(most, len(L))
    report[act.name] = {'leak_frames': f'{len(frames)}/{f1 - f0 + 1}', 'frames': frames[:40],
                        'max_vertices': most, 'worst_mm': round(worst * 1000, 1)}
    print('G6LEGS', act.name, json.dumps(report[act.name]))
print('G6LEGS rest excluded', len(rest), 'of', len(legs))
json.dump(report, open(os.path.join(HERE, 'review', f'g6_legs_{tag}.json'), 'w'), indent=1)
