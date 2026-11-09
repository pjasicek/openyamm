"""Foot flatness probe on the skinned mesh: per action and foot, the tilt of the sole while the foot is on the floor.
Sole = the foot vertices (weighted > 0.5 to Foot/Toe) within 2 cm of the foot's lowest rest point. Per frame the
deformed sole is fitted with a plane; roll = tilt across the foot (+ = standing on the outer edge), pitch = tilt
along it (+ = toe up). A foot counts as planted while its lowest sole point is below PLANT (default 3 cm).
Prints per action and foot: planted frames, roll range and pitch range on them, and the frames with |roll| > LIMIT.
Args: -- <blend> <action> [...]  (env PLANT=0.03 LIMIT=8)"""
import bpy, sys, os, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); acts = a[1:]
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
names = [g.name for g in body.vertex_groups]
PLANT = float(os.environ.get('PLANT', '0.03')); LIMIT = float(os.environ.get('LIMIT', '8'))
rest = np.array([body.matrix_world @ v.co for v in me.vertices])
SOLE, AX = {}, {}
for s in 'LR':
    foot = np.array([sum(e.weight for e in v.groups if names[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > 0.5
                     for v in me.vertices])
    idx = np.where(foot)[0]; idx = idx[rest[idx, 2] < rest[idx, 2].min() + 0.02]
    SOLE[s] = idx
    P = rest[idx] - rest[idx].mean(0)
    f0 = np.linalg.svd(P[:, :2], full_matrices=False)[2][0]     # long axis of the sole (horizontal)
    if f0[1] > 0:
        f0 = -f0                                                  # character faces -Y: forward = toe
    AX[s] = np.array([f0[0], f0[1], 0.0])
for an in acts:
    act = bpy.data.actions.get(an)
    if act is None:
        print(f"FLAT {an}: no such action"); continue
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0_, f1_ = int(act.frame_range[0]), int(act.frame_range[1])
    res = {s: [] for s in 'LR'}
    for f in range(f0_, f1_ + 1):
        sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
        co = co.reshape(-1, 3) @ np.array(body.matrix_world.to_3x3()).T + np.array(body.matrix_world.translation)
        for s in 'LR':
            P = co[SOLE[s]]
            if P[:, 2].min() > PLANT:
                continue
            c = P.mean(0); n = np.linalg.svd(P - c, full_matrices=False)[2][2]
            if n[2] < 0:
                n = -n
            # deformed forward: the rest forward carried by the best rigid fit of the sole
            R0 = rest[SOLE[s]] - rest[SOLE[s]].mean(0)
            U, _, Vt = np.linalg.svd(R0.T @ (P - c)); Rm = (U @ Vt).T
            if np.linalg.det(Rm) < 0:
                Vt[2] *= -1; Rm = (U @ Vt).T
            fw = Rm @ AX[s]; fw -= n * (fw @ n); fw /= np.linalg.norm(fw)
            right = np.cross(fw, np.array([0, 0, 1.0])); right /= np.linalg.norm(right)
            out = right if s == 'R' else -right                      # outward side of this foot
            # the inner edge raised (standing on the outer edge) tilts the sole normal outward
            roll = math.degrees(math.atan2(n @ out, n[2]))
            pitch = math.degrees(math.asin(np.clip(fw[2], -1, 1)))
            res[s].append((f, roll, pitch))
            if os.environ.get('VERBOSE'):
                print(f'FLATF {an} {s} f{f}: low {P[:, 2].min() * 100:.1f} cm roll {roll:+.1f} pitch {pitch:+.1f}')
    for s in 'LR':
        r = np.array(res[s])
        if not len(r):
            print(f'FLAT {an} {s}: never planted'); continue
        bad = [int(x) for x in r[np.abs(r[:, 1]) > LIMIT, 0]]
        print(f'FLAT {an} {s}: planted {len(r)}/{f1_ - f0_ + 1} roll {r[:, 1].min():+.1f}..{r[:, 1].max():+.1f} '
              f'(mean {r[:, 1].mean():+.1f}) pitch {r[:, 2].min():+.1f}..{r[:, 2].max():+.1f} deg; '
              f'|roll|>{LIMIT:g}: {bad[:16]}{" ..." if len(bad) > 16 else ""}')
