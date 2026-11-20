"""Legs onto the MM9 leg chains (after fit_chicken.py's global fit of the symmetrised Meshy bird).

Args: <fit blend> <out blend> <report json> [shift_y_fraction]
1. Landmarks per side from horizontal slices of the Meshy leg: the floor contact (lowest toe point), the ankle (lowest
   narrow slice above the toe spread), the leg's exit from the body (highest narrow slice below the thigh feathers).
2. The whole body moves along y so the legs' exits meet MM9's Xleg joints (times shift_y_fraction, default 1): the
   legs carry the body, the head is replaced by the graft and the neck lofted onto MM9's neck chain.
3. Each shank cross-section moves (no rotation) onto MM9's leg polyline Xfoot -> Xlowrleg -> Xleg by its height
   fraction between our ankle and our exit; the foot below the ankle moves rigidly with the ankle (toes kept flat,
   on the floor). Above the exit the displacement fades out over FADE (height) and with distance from the leg axis.
Separate pieces follow their nearest main-body vertex.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
SHIFT_FRAC = float(a[3]) if len(a) > 3 else 1.0
FADE = 0.05
RAD0, RAD1 = 0.035, 0.07
SIDES = {'r': (-1, ['Xfoot', 'Xlowrleg', 'Xleg']), 'l': (1, ['Xfoot01', 'Xlowrleg01', 'Xleg01'])}
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
ob = bpy.data.objects['Body']; me = ob.data
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
rep = {}


def slices(s):
    out = []
    for z in np.arange(0.0, 0.35, 0.005):
        m = (np.abs(P[:, 2] - z) < 0.003) & (s * P[:, 0] > 0.01) & (piece == 0)
        if m.sum() < 3:
            out.append((z, None, None)); continue
        ext = max(np.ptp(P[m, 0]), np.ptp(P[m, 1]))
        out.append((z, ext, P[m].mean(0)))
    return out


land = {}
for side, (s, chain) in SIDES.items():
    sl = slices(s)
    floor = P[(s * P[:, 0] > 0.01) & (P[:, 2] < 0.15), 2].min()
    narrow = [(z, c) for z, e, c in sl if e is not None and e < 0.046 and z > floor + 0.01]
    za = narrow[0][0]                      # lowest narrow slice: just above the toe spread
    # exit: walk up while the slice stays narrow (contiguous)
    zs = [z for z, _ in narrow]
    k = 0
    while k + 1 < len(zs) and zs[k + 1] - zs[k] < 0.0075:
        k += 1
    ze = zs[k]
    cen = {round(z, 4): c for z, c in narrow}
    land[side] = {'floor': float(floor), 'ankle_z': float(za), 'exit_z': float(ze),
                  'ankle': cen[round(za, 4)].tolist(), 'exit': cen[round(ze, 4)].tolist()}
rep['landmarks'] = land
dy = SHIFT_FRAC * np.mean([J[SIDES[sd][1][2]][1] - land[sd]['exit'][1] for sd in SIDES])
rep['shift_y'] = float(dy)
D = np.zeros_like(P); D[:, 1] = dy
P1 = P + D
for side, (s, chain) in SIDES.items():
    L = land[side]
    za, ze = L['ankle_z'], L['exit_z']
    ank = np.array(L['ankle']) + [0, dy, 0]; ext = np.array(L['exit']) + [0, dy, 0]
    floor = L['floor']
    # our centreline by height (slice centroids, shifted)
    zs = np.arange(za, ze + 1e-6, 0.005)
    cl = []
    for z in zs:
        m = (np.abs(P1[:, 2] - z) < 0.003) & (s * P1[:, 0] > 0.01) & (piece == 0) & \
            (np.hypot(P1[:, 0] - ank[0], P1[:, 1] - ank[1]) < 0.06)
        cl.append(P1[m].mean(0) if m.sum() else (cl[-1] if cl else ank))
    cl = np.array(cl)
    # MM9 polyline: Xfoot (lifted to our new ankle height) -> Xlowrleg -> Xleg (at our exit height)
    new_ankle_z = za - floor            # toes onto the floor
    F, Lw, K = J[chain[0]].copy(), J[chain[1]].copy(), J[chain[2]].copy()
    F[2] = new_ankle_z
    K[2] = ze
    Lw[2] = max(min(Lw[2], ze - 0.01), new_ankle_z + 0.01)
    poly = [F, Lw, K]
    segl = [np.linalg.norm(poly[i + 1] - poly[i]) for i in range(2)]
    tot = sum(segl)

    def on_poly(u):
        x = u * tot
        if x <= segl[0]:
            return poly[0] + (poly[1] - poly[0]) * (x / segl[0])
        return poly[1] + (poly[2] - poly[1]) * ((x - segl[0]) / segl[1])
    disp_cl = np.array([on_poly((z - za) / max(ze - za, 1e-6)) - c for z, c in zip(zs, cl)])
    foot_disp = disp_cl[0].copy()
    exit_disp = disp_cl[-1].copy()
    sidem = (s * P1[:, 0] > 0) & (piece == 0)
    for i in np.nonzero(sidem)[0]:
        z = P1[i, 2]
        r = np.hypot(P1[i, 0] - cl[-1][0], P1[i, 1] - cl[-1][1])
        if z < za:
            if np.hypot(P1[i, 0] - ank[0], P1[i, 1] - ank[1]) > 0.15:
                continue
            D[i] += foot_disp
        elif z <= ze:
            rr = np.hypot(P1[i, 0] - ank[0], P1[i, 1] - ank[1])
            k = min(len(zs) - 1, int(round((z - za) / 0.005)))
            if np.hypot(P1[i, 0] - cl[k][0], P1[i, 1] - cl[k][1]) > 0.05:
                continue
            D[i] += disp_cl[k]
        else:
            wz = max(0.0, 1 - (z - ze) / FADE)
            wr = np.clip((RAD1 - r) / (RAD1 - RAD0), 0, 1)
            w = wz * wr
            w = w * w * (3 - 2 * w)
            D[i] += w * exit_disp
    rep[side] = {'foot_disp': foot_disp.tolist(), 'exit_disp': exit_disp.tolist(),
                 'mm9_poly': [p.tolist() for p in poly]}
Pn = P + D
# feet yaw: the toes' median direction (horizontal, from the ankle) turned onto MM9's toes' median direction, about
# the vertical through the new ankle; the lowest shank blends in over YAW_BLEND above the ankle
YAW_BLEND = 0.015
TOES9 = {'r': ['Xtoe', 'Xtoe01', 'Xtoe02'], 'l': ['Xtoe03', 'Xtoe04', 'Xtoe05']}
for side, (s_, chain) in SIDES.items():
    L = land[side]
    F = J[chain[0]]
    ank = np.array(L['ankle']) + rep[side]['foot_disp'] + [0, dy, 0]
    za = L['ankle_z'] - L['floor']
    foot = (s_ * Pn[:, 0] > 0) & (Pn[:, 2] < za) & (piece == 0) & (np.hypot(Pn[:, 0] - ank[0], Pn[:, 1] - ank[1]) < 0.15)
    d = Pn[foot, :2] - ank[:2]
    r = np.linalg.norm(d, axis=1)
    th = np.arctan2(d[:, 0], -d[:, 1])
    fwd = (np.abs(th) < np.radians(100)) & (r > 0.02)
    d9 = np.array([J[t][:2] - F[:2] for t in TOES9[side]])
    th9 = np.arctan2(d9[:, 0], -d9[:, 1])
    yaw = float(np.median(th9) - np.median(th[fwd]))
    rep[side]['foot_yaw_deg'] = float(np.degrees(yaw))
    sel = (s_ * Pn[:, 0] > 0) & (piece == 0) & (Pn[:, 2] < za + YAW_BLEND) & \
        (np.hypot(Pn[:, 0] - ank[0], Pn[:, 1] - ank[1]) < 0.15)
    for i in np.nonzero(sel)[0]:
        w = 1.0 if Pn[i, 2] < za else 1 - (Pn[i, 2] - za) / YAW_BLEND
        a_ = yaw * w
        c, sn = np.cos(a_), np.sin(a_)
        x, y = Pn[i, 0] - ank[0], Pn[i, 1] - ank[1]
        # rotate (x, y) so the angle atan2(x, -y) grows by a_
        Pn[i, 0] = ank[0] + x * c - y * sn
        Pn[i, 1] = ank[1] + y * c + x * sn
D = Pn - P
# separate pieces follow their nearest main-body vertex
main = np.nonzero(piece == 0)[0]
kd = KDTree(len(main))
for j, i in enumerate(main):
    kd.insert(Vector(P[i]), j)
kd.balance()
for i in np.nonzero(piece != 0)[0]:
    Pn[i] = P[i] + D[main[kd.find(Vector(P[i]))[1]]]
for v, p in zip(me.vertices, Pn):
    v.co = Vector(p)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('LEGFIT ' + json.dumps(rep))
