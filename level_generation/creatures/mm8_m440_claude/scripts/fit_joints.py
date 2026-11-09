"""G3 / H3: joint centres from the mesh's own cross-sections (no auto-rig).

The rest mesh (A-pose, soles at z=0, facing -Y, character left = +X) is sliced perpendicular to each limb; every
slice is split into closed loops and the loop nearest the limb line gives a ring centre and perimeter.
- arm: centreline from the shoulder seed to the hand's far end; WRIST = narrowest ring in the distal third,
  ELBOW = largest deviation of the centreline from the shoulder-wrist line if the A-pose bend is > 8 mm, otherwise
  the source upper-arm : forearm ratio; SHOULDER = one upper-arm radius inside the top of the deltoid along the
  upper-arm axis; the mesh's own elbow hinge axis = normal of (shoulder, elbow, wrist) when the bend is measurable.
- leg: HIP from the source hip height/width scaled to this body, KNEE = largest deviation or the source ratio,
  ANKLE = narrowest ring above the foot.
- spine/neck/head: torso ring centres at the source's relative heights.
Seeds come from work/proportions.json (source). Writes work/joints.json and prints ring residuals.
Args: -- <blend> <mesh object>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
blend, mesh_name = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects[mesh_name]
BASE = bmesh.new(); BASE.from_mesh(ob.data); BASE.transform(ob.matrix_world)
BASE.verts.ensure_lookup_table()
pieces=ob.data.attributes['piece']
bmesh.ops.delete(BASE,geom=[v for v in BASE.verts if pieces.data[v.index].value not in (0,1,2,3,4,5)],context='VERTS')
co = np.array([tuple(v.co) for v in BASE.verts])
from mathutils.bvhtree import BVHTree
TREE = BVHTree.FromBMesh(BASE)
H = 1.7
SRC = json.load(open(os.path.join(HERE, 'work', 'proportions.json')))['source']


def rings(p, n):
    """Closed loops of the mesh cut by the plane (p, n): list of (centroid, perimeter, points)."""
    bm = BASE.copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(p), plane_no=Vector(n))
    edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for v in adj:
        if v in seen:
            continue
        comp, stack = [], [v]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); stack.extend(adj[x])
        pts = np.array([tuple(x.co) for x in comp])
        if len(pts) < 4:
            continue
        ordered = [comp[0]]; left = set(comp[1:])
        while left:
            nxt = next((y for y in adj[ordered[-1]] if y in left), None)
            if nxt is None:
                break
            ordered.append(nxt); left.discard(nxt)
        op = np.array([tuple(x.co) for x in ordered])
        per = float(np.linalg.norm(np.diff(np.vstack([op, op[:1]]), axis=0), axis=1).sum())
        out.append((pts.mean(0), per, pts))
    bm.free()
    return out


def nearest_ring(p, n, target):
    rs = rings(p, n)
    if not rs:
        return None
    return min(rs, key=lambda r: np.linalg.norm(r[0] - target))


def line_dev(pts, a, b):
    d = (b - a) / np.linalg.norm(b - a)
    v = pts - a
    return np.linalg.norm(v - np.outer(v @ d, d), axis=1)


J, report = {}, {}
CENTRE = {}
for side, sg in (('R', -1), ('L', 1)):
    # ---- arm
    sh_seed = np.array([sg * SRC['shoulder_width'] / 2 * H, 0.0, SRC['shoulder_height'] * H])
    # the hand is the most lateral part of an A-pose body at hand height; the tip is the lowest point of that hand
    band = co[(co[:, 2] > 0.36 * H) & (co[:, 2] < 0.62 * H) & (co[:, 0] * sg > 0)]
    outer = band[np.argmax(band[:, 0] * sg)]
    hand_v = co[np.linalg.norm(co[:, :2] - outer[:2], axis=1) < 0.06 * H]
    hand_v = hand_v[hand_v[:, 2] < outer[2] + 0.08 * H]
    tip = hand_v[np.argmin(hand_v[:, 2])]
    axis = (tip - sh_seed) / np.linalg.norm(tip - sh_seed)
    cl = []
    for t in np.linspace(0.12, 0.97, 44):
        q = sh_seed + (tip - sh_seed) * t
        r = nearest_ring(q, axis, q)
        if r is not None and np.linalg.norm(r[0] - q) < 0.08 * H:
            cl.append((t, r[0], r[1]))
    ts = np.array([c[0] for c in cl]); cs = np.array([c[1] for c in cl]); per = np.array([c[2] for c in cl])
    if os.environ.get('JDEBUG'):
        print('ARMDBG', side, 'seed', np.round(sh_seed, 3), 'tip', np.round(tip, 3), [(round(float(t), 2), np.round(c, 3).tolist(), round(float(p), 3)) for t, c, p in zip(ts, cs, per)])
    CENTRE[f'{side}_arm'] = cs.tolist()
    distal = (ts > 0.55) & (ts < 0.85)
    wi = np.where(distal)[0][np.argmin(per[distal])]
    wrist = cs[wi]
    # upper arm axis from the free (separated) upper-arm rings, then the deltoid top along it
    up_idx = (ts > 0.18) & (ts < ts[wi] * 0.5)
    ua = cs[up_idx]
    ua_dir = np.linalg.svd(ua - ua.mean(0))[2][0]
    if np.dot(ua_dir, axis) < 0:
        ua_dir = -ua_dir
    r_up = float(np.median(per[up_idx])) / (2 * math.pi)
    # the glenohumeral joint sits where the upper-arm axis meets the side of the ribcage: torso half-width from a
    # horizontal slice below the armpit (the ring around the body centre), joint on the axis at that width minus a
    # third of the upper-arm radius (garment shells make a surface ray stop at the skin under the sleeve)
    tz = SRC['shoulder_height'] * H - 0.09 * H
    around = [r for r in rings((0, 0, tz), (0, 0, 1)) if r[2][:, 0].min() < 0 < r[2][:, 0].max()]
    torso = max(around, key=lambda r: r[1]) if around else None      # outermost shell (garments over the skin)
    tw = float(np.abs(torso[2][:, 0]).max()) if torso is not None else SRC['shoulder_width'] / 2 * H * 0.7
    report[f'{side}_torso_halfwidth_cm'] = round(tw * 100, 1)
    a0 = ua.mean(0)
    k = ((tw - r_up / 3) * sg - a0[0]) / (-ua_dir[0]) if abs(ua_dir[0]) > 1e-3 else 0.0
    shoulder = a0 - ua_dir * k
    dev = line_dev(cs, shoulder, wrist)
    mid = (ts > ts[wi] * 0.3) & (ts < ts[wi] * 0.75)
    bend_mm = float(dev[mid].max()) * 1000
    if bend_mm > 8:
        elbow = cs[np.where(mid)[0][np.argmax(dev[mid])]]
        hinge = np.cross(elbow - shoulder, wrist - elbow); hinge /= np.linalg.norm(hinge)
    else:
        f = SRC['upper_arm_R'] / (SRC['upper_arm_R'] + SRC['forearm_R'])
        elbow_t = shoulder + (wrist - shoulder) * f
        elbow = cs[np.argmin(np.linalg.norm(cs - elbow_t, axis=1))]
        hinge = None
    J[f'{side}_UpperArm'], J[f'{side}_Forearm'], J[f'{side}_Hand'] = shoulder, elbow, wrist
    report[f'{side}_arm'] = {'bend_mm': round(bend_mm, 1), 'upper_radius_cm': round(r_up * 100, 2),
                             'wrist_perimeter_cm': round(float(per[wi]) * 100, 1),
                             'hinge_from_mesh': None if hinge is None else [round(float(x), 3) for x in hinge],
                             'upper_arm_len': round(float(np.linalg.norm(elbow - shoulder) / H), 4),
                             'forearm_len': round(float(np.linalg.norm(wrist - elbow) / H), 4)}
    # ---- leg
    hip = np.array([sg * SRC['hip_width'] / 2 * H, 0.0, SRC['hip_height'] * H])
    leg_v = co[(co[:, 0] * sg > 0.01 * H) & (co[:, 2] < 0.5 * H)]
    ankle_seed = np.array([np.median(leg_v[leg_v[:, 2] < 0.08 * H][:, 0]), 0.0, 0.05 * H])
    lcl = []
    for t in np.linspace(0.08, 0.95, 40):
        q = hip + (ankle_seed - hip) * t
        r = nearest_ring(q, (0, 0, 1), q)
        if r is not None:
            lcl.append((t, r[0], r[1]))
    lt = np.array([c[0] for c in lcl]); lc = np.array([c[1] for c in lcl]); lp = np.array([c[2] for c in lcl])
    hip_ring = lc[np.argmin(np.abs(lt - 0.1))]
    hip = np.array([hip_ring[0], hip_ring[1], hip[2]])
    low = lt > 0.7
    ai = np.where(low)[0][np.argmin(lp[low])]
    ankle = lc[ai]
    ldev = line_dev(lc, hip, ankle)
    lmid = (lt > 0.35) & (lt < 0.65)
    kb = float(ldev[lmid].max()) * 1000
    if kb > 8:
        knee = lc[np.where(lmid)[0][np.argmax(ldev[lmid])]]
    else:
        f = SRC['thigh_R'] / (SRC['thigh_R'] + SRC['shin_R'])
        kt = hip + (ankle - hip) * f
        knee = lc[np.argmin(np.linalg.norm(lc - kt, axis=1))]
    J[f'{side}_Thigh'], J[f'{side}_Calf'], J[f'{side}_Foot'] = hip, knee, ankle
    report[f'{side}_leg'] = {'bend_mm': round(kb, 1), 'thigh_len': round(float(np.linalg.norm(knee - hip) / H), 4),
                             'shin_len': round(float(np.linalg.norm(ankle - knee) / H), 4)}
# ---- spine and head: torso ring centres at the source's relative heights
for name, frac in (('Pelvis', SRC['pelvis_height']), ('Neck', SRC['shoulder_height'] + 0.03)):
    q = np.array([0.0, 0.0, frac * H])
    r = nearest_ring(q, (0, 0, 1), q)
    J[name] = r[0] if r is not None else q
J['Head'] = J['Neck'] + np.array([0, 0, SRC['neck_to_head'] * H])
out = {'height_m': float(H), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()}, 'report': report}
json.dump(out, open(os.path.join(HERE, 'work', 'joints.json'), 'w'), indent=1)
json.dump(CENTRE, open(os.path.join(HERE, 'work', 'centrelines.json'), 'w'))
for k, v in report.items():
    print('JOINTS', k, json.dumps(v))
