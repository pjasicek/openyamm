"""G3: joint centres of the queen from the mesh's own cross-sections (no auto-rig: she has no legs).

Rest mesh: A-pose, abdomen tip at z = 0, facing -Y, her left = +X, 2.4 m from abdomen tip to horn tips.
- Arms (bar1 rule): ring centreline shoulder seed -> fingertip; WRIST = narrowest ring in the distal part, ELBOW =
  closest approach of line fits through the upper-arm and forearm rings, SHOULDER = point of the upper-arm axis 7 cm
  below the shoulder top.
- Torso, from the central slice's half-width per height (arms excluded by |x| < 0.3 m): WAIST (pelvis joint) =
  narrowest between 1.2 and 1.42 m; SHOULDER TOP = highest height with half-width >= 0.2 m, shoulder joints 4 cm
  below it; NECK joint at the neck's base 1 cm above the shoulder top; HEAD joint 8 cm above the narrowest ring within
  15 cm above the shoulder top (the skull base); Spine/Spine1/Spine2 at 1/4, 1/2, 3/4 from the waist to the shoulder joints.
- Abdomen: centreline marched from the waist down the curved body: each step slices perpendicular to the current
  direction and takes the loop nearest the prediction; the march stops at the tip. ABDOMEN joints are spaced evenly
  along it (ABDOMEN_BONES segments).
Input: the latest of work/step3.blend (reduced), step2.blend (head grafted), step1.blend. Writes work/joints.json."""
import bpy, bmesh, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
ABDOMEN_BONES = 6
src = next(P / 'work' / f for f in ('step3.blend', 'step2.blend', 'step1.blend') if (P / 'work' / f).exists())
bpy.ops.wm.open_mainfile(filepath=str(src))
ob = bpy.data.objects['Queen']
BASE = bmesh.new(); BASE.from_mesh(ob.data); BASE.transform(ob.matrix_world)
co = np.array([tuple(v.co) for v in BASE.verts])
H = float(co[:, 2].max())


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
        if len(comp) < 4:
            continue
        ordered = [comp[0]]; left = set(comp[1:])
        while left:
            nxt = next((y for y in adj[ordered[-1]] if y in left), None)
            if nxt is None:
                break
            ordered.append(nxt); left.discard(nxt)
        op = np.array([tuple(x.co) for x in ordered])
        per = float(np.linalg.norm(np.diff(np.vstack([op, op[:1]]), axis=0), axis=1).sum())
        pts = np.array([tuple(x.co) for x in comp])
        out.append((pts.mean(0), per, pts))
    bm.free()
    return out


def nearest_ring(p, n, target, within=None):
    rs = rings(p, n)
    if within is not None:
        rs = [r for r in rs if np.linalg.norm(r[0] - target) < within]
    return min(rs, key=lambda r: np.linalg.norm(r[0] - target)) if rs else None


def torso_ring(z):
    """The horizontal ring around the body centre at height z (arms excluded: the ring that spans x = 0)."""
    rs = [r for r in rings((0, 0, z), (0, 0, 1)) if r[2][:, 0].min() < 0 < r[2][:, 0].max()]
    return max(rs, key=lambda r: r[1]) if rs else None


def march(p, n, step, stop, within=0.1, min_perimeter=0.03, blend=0.4):
    """Centreline along a limb: slice perpendicular to the current direction one step ahead, take the loop nearest the
    prediction, steer toward it. Returns centres and perimeters until no loop is found or stop(p) holds."""
    cs, pr = [p.copy()], [np.nan]
    for i in range(300):
        q = p + n * step
        r = nearest_ring(q, n, q, within=within)
        if r is None or r[1] < min_perimeter:
            break
        nn = r[0] - p
        if np.linalg.norm(nn) < 1e-6:
            break
        nn /= np.linalg.norm(nn)
        n = (1 - blend) * n + blend * nn; n /= np.linalg.norm(n)
        p = r[0]
        cs.append(p.copy()); pr.append(r[1])
        if stop(p):
            break
    return np.array(cs), np.array(pr), n


J, report = {}, {}
# ---- torso profile: half-width of the central slice (|x| < 0.3 m) per height. Arms hang free below the armpits and
# merge into the slice above them, so ring perimeters there measure torso and arms together; the width is robust.
def central_half(z):
    bm = BASE.copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, 0, z)),
                                 plane_no=Vector((0, 0, 1)))
    pts = np.array([tuple(v.co) for v in res['geom_cut'] if isinstance(v, bmesh.types.BMVert)])
    bm.free()
    pts = pts[np.abs(pts[:, 0]) < 0.3] if len(pts) else pts
    return (float(np.abs(pts[:, 0]).max()), pts) if len(pts) else (0.0, pts)


zs = np.arange(1.1, 2.0, 0.01)
half = np.array([central_half(z)[0] for z in zs])
waistband = (zs > 1.2) & (zs < 1.42)
z_waist = float(zs[waistband][np.argmin(half[waistband])])
shoulder_top = float(zs[(zs > 1.6) & (zs < 1.9) & (half >= 0.2)].max())
neckband = (zs > shoulder_top) & (zs < shoulder_top + 0.15)
z_neck = float(zs[neckband][np.argmin(half[neckband])])
z_sh = shoulder_top - 0.04
r = torso_ring(z_waist)
J['Pelvis'] = r[0] if r else np.array([0, 0, z_waist])
r = torso_ring(z_neck)
J['Neck'] = r[0] if r else np.array([0, 0, z_neck])
for name, f in (('Spine', 0.25), ('Spine1', 0.5), ('Spine2', 0.75)):
    z = z_waist + (z_sh - z_waist) * f
    _, pts = central_half(z)
    J[name] = np.array([0.0, (pts[:, 1].min() + pts[:, 1].max()) / 2, z]) if len(pts) else np.array([0, 0, z])
head_col = co[(np.hypot(co[:, 0] - J['Neck'][0], co[:, 1] - J['Neck'][1]) < 0.07) & (co[:, 2] > z_neck)]
skull_top = float(head_col[:, 2].max()) if len(head_col) else H
# The neck bone starts at the base of the neck (just above the shoulder tops), the head at the skull base 8 cm above
# the narrowest neck ring (a central horn sits on the head's axis, so the skull top is not measurable from above).
neck_mid = J['Neck'].copy()
r = torso_ring(shoulder_top + 0.01)
J['Neck'] = np.array([neck_mid[0], neck_mid[1], shoulder_top + 0.01]) if r is None else np.array([r[0][0], r[0][1], shoulder_top + 0.01])
J['Head'] = neck_mid + np.array([0, 0, 0.08])
shoulder_outer = float(half[np.argmin(np.abs(zs - shoulder_top + 0.02))])
report['torso'] = {'shoulder_top_z': shoulder_top, 'shoulder_joint_z': z_sh, 'neck_z': z_neck, 'waist_z': z_waist,
                   'skull_top_z': skull_top, 'waist_halfwidth_cm': round(float(half[waistband].min()) * 100, 1),
                   'shoulder_outer_cm': round(shoulder_outer * 100, 1)}
# ---- arms
CENTRE = {}
for side, sg in (('R', -1), ('L', 1)):
    sh_seed = np.array([sg * (shoulder_outer - 0.06), J['Spine2'][1], z_sh])
    band = co[(co[:, 2] > 0.9) & (co[:, 2] < z_sh - 0.2) & (co[:, 0] * sg > 0.25)]
    tip = band[np.argmin(band[:, 2] - 0.3 * np.abs(band[:, 0]))]          # lowest-outermost fingertip
    axis = (tip - sh_seed) / np.linalg.norm(tip - sh_seed)
    # March from the free forearm (above the hand) up the arm until the loop merges with the torso near the armpit,
    # and down to the hand: the shoulder region itself slices as one loop with the torso.
    fv = co[(np.abs(co[:, 2] - 1.25) < 0.02) & (co[:, 0] * sg > 0.35)]
    f0 = fv.mean(0)
    up, pu, _ = march(f0, np.array([-sg * 0.45, 0.0, 0.89]), 0.02, lambda q: q[2] > z_sh - 0.02, within=0.06)
    med = np.nanmedian(pu[1:6]) if len(pu) > 6 else np.nanmedian(pu[1:])
    keep = [0] + [i for i in range(1, len(up)) if pu[i] < 1.6 * med]
    stop = next((i for i in range(1, len(up)) if pu[i] >= 1.6 * med), len(up))
    up, pu = up[:stop], pu[:stop]
    dn, pd, _ = march(f0, np.array([sg * 0.35, 0.0, -0.94]), 0.015, lambda q: q[2] < tip[2] + 0.1, within=0.06)
    cs = np.vstack([up[::-1], dn[1:]]); pr = np.r_[pu[::-1], pd[1:]]
    pr[np.isnan(pr)] = np.nanmedian(pr)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cs, axis=0), axis=1))]
    ts = arc / arc[-1]
    CENTRE[f'{side}_arm'] = cs.tolist()
    print('ARMDBG', side, 'samples', len(cs), 'top', np.round(cs[0], 3).tolist(), 'bottom', np.round(cs[-1], 3).tolist(),
          [(round(float(t), 2), round(float(p_) * 100, 1)) for t, p_ in zip(ts, pr)])
    distal = (ts > 0.55) & (ts < 0.92)
    wi = np.where(distal)[0][np.argmin(pr[distal])]
    wrist = cs[wi]
    up_idx = (ts > 0.15) & (ts < ts[wi] * 0.45)
    ua = cs[up_idx]
    ua_dir = np.linalg.svd(ua - ua.mean(0))[2][0]
    ua_dir = ua_dir if ua_dir @ axis > 0 else -ua_dir
    r_up = float(np.median(pr[up_idx])) / (2 * math.pi)
    # glenohumeral joint: on the upper-arm axis, 7 cm below the shoulder top (the axis met at the torso width lands
    # under the deltoid on this narrow-shouldered body)
    tw = shoulder_outer - r_up
    a0 = ua.mean(0)
    k = ((shoulder_top - 0.07) - a0[2]) / (-ua_dir[2]) if abs(ua_dir[2]) > 1e-3 else 0.0
    shoulder = a0 - ua_dir * k
    d = (wrist - shoulder) / np.linalg.norm(wrist - shoulder)
    t2 = (cs - shoulder) @ d / np.linalg.norm(wrist - shoulder)

    def fit(mask):
        p_ = cs[mask]; c = p_.mean(0); u = np.linalg.svd(p_ - c)[2][0]
        return c, (u if u @ d > 0 else -u)
    c1, u1 = fit((t2 > 0.12) & (t2 < 0.42)); c2, u2 = fit((t2 > 0.58) & (t2 < 0.92))
    w0 = c1 - c2; a, b, c_, dd, e = u1 @ u1, u1 @ u2, u2 @ u2, u1 @ w0, u2 @ w0
    den = a * c_ - b * b
    s1 = (b * e - c_ * dd) / den if abs(den) > 1e-9 else 0.0
    s2 = (a * e - b * dd) / den if abs(den) > 1e-9 else 0.0
    elbow = ((c1 + u1 * s1) + (c2 + u2 * s2)) / 2
    clav = np.array([sg * 0.035, J['Spine2'][1], z_sh - 0.03])
    J[f'{side}_Clavicle'], J[f'{side}_UpperArm'], J[f'{side}_Forearm'], J[f'{side}_Hand'] = clav, shoulder, elbow, wrist
    report[f'{side}_arm'] = {'upper_arm_m': round(float(np.linalg.norm(elbow - shoulder)), 3),
                             'forearm_m': round(float(np.linalg.norm(wrist - elbow)), 3),
                             'bend_deg': round(float(np.degrees(np.arccos(np.clip(u1 @ u2, -1, 1)))), 1),
                             'wrist_perimeter_cm': round(float(pr[wi]) * 100, 1), 'torso_halfwidth_cm': round(tw * 100, 1),
                             'fingertip': np.round(tip, 3).tolist()}
# ---- abdomen centreline, marched down from the waist
p = J['Pelvis'].copy(); n = np.array([0.0, 0.0, -1.0]); step = 0.03
line = [p.copy()]
for i in range(200):
    q = p + n * step
    r = nearest_ring(q, n, q, within=0.12)
    if r is None or r[1] < 0.05:
        break
    c = r[0]
    nn = c - p; nn /= np.linalg.norm(nn)
    n = 0.6 * n + 0.4 * nn; n /= np.linalg.norm(n)
    p = c
    line.append(c.copy())
line = np.array(line)
# extend to the actual tip: the farthest abdomen vertex along the last direction
low = co[np.linalg.norm(co - line[-1], axis=1) < 0.35]
tipv = low[np.argmax((low - line[-1]) @ n)]
line = np.vstack([line, tipv])
arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
CENTRE['abdomen'] = line.tolist()
# Abdomen joints from the tip (index 0) up to the waist (index ABDOMEN_BONES)
for i in range(ABDOMEN_BONES + 1):
    s = arc[-1] * (1 - i / ABDOMEN_BONES)
    J[f'Abdomen{i:02d}'] = np.array([np.interp(s, arc, line[:, k]) for k in range(3)])
report['abdomen'] = {'length_m': round(float(arc[-1]), 3), 'samples': len(line), 'tip': np.round(tipv, 3).tolist()}
out = {'source': src.name, 'height_m': H, 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
       'report': report}
(P / 'work' / 'joints.json').write_text(json.dumps(out, indent=1))
(P / 'work' / 'centrelines.json').write_text(json.dumps(CENTRE))
for k, v in report.items():
    print('JOINTS', k, json.dumps(v))
