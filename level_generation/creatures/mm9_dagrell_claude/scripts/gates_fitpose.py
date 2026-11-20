"""Dagrell deformation gate against its natural shape: edge length ratio of 'Body' in every role clip (sampled at
30 Hz) relative to the FitPose (the MM9 pose fitted to the Meshy skeleton, i.e. Meshy's own geometry), since its bind
(crouch) pose has pieces spanning joints pulled apart. Args: <anim blend> <uv blend with FitPose> <report json>"""
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
ANIM, UV, REP = argv
bpy.ops.wm.open_mainfile(filepath=ANIM)
with bpy.data.libraries.load(UV) as (src, dst):
    dst.actions = ['FitPose']
fit = dst.actions[0]
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent is rig)
E = np.array([tuple(e.vertices) for e in body.data.edges])


def pose(act, frame):
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    sc.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    P = np.array([tuple(v.co) for v in me.vertices])
    body.evaluated_get(dg).to_mesh_clear()
    return P


P0 = pose(fit, 0)
L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1)
keep = L0 > 1e-4
rep = {}
for act in bpy.data.actions:
    if act.name in ('FitPose',) or act.name.startswith('Xx'):
        continue
    f0, f1 = (int(x) for x in act.frame_range)
    r1, r99, rmax, rmin = [], [], 0, 9
    for f in range(f0, f1 + 1):
        P = pose(act, f)
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)[keep] / L0[keep]
        r1.append(np.percentile(r, 1)); r99.append(np.percentile(r, 99)); rmax = max(rmax, r.max()); rmin = min(rmin, r.min())
    rep[act.name] = {'p1': round(float(min(r1)), 3), 'p99': round(float(max(r99)), 3), 'min': round(float(rmin), 3),
                     'max': round(float(rmax), 3)}
    print('GATE', act.name, rep[act.name])
json.dump(rep, open(REP, 'w'), indent=1)
