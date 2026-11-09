"""G3 arm joints for the goblin from the SKIN shell only (piece 0; bracers and pauldrons are separate shells that
fooled the generic ring fit), seeded by Meshy's auto-rig shoulder and hand joints.

Per side: the arm tip = the skin vertex farthest from the shoulder along the Meshy shoulder -> hand direction; a
centreline of ring centres is cut perpendicular to the LOCAL arm direction (two passes: first along the straight
seed axis, then perpendicular to the smoothed first-pass centreline). WRIST = narrowest ring between 55 % and 85 %
of the shoulder -> tip length; ELBOW = closest approach of two line fits (upper-arm rings 15-42 %, forearm rings
60-92 % of shoulder -> wrist). Ankles from the narrowest skin/foot ring above the foot.
Writes work/joints.json (Meshy joints with ring wrist/elbow/ankle replaced) and work/centrelines.json.
Args: -- <blend>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
M = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints'].items()}


def shell(pieces):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if pv[v.index] not in pieces], context='VERTS')
    return bm


SKIN = shell({0})
co_skin = np.array([tuple(v.co) for v in SKIN.verts])


def rings(base, p, n):
    bm = base.copy()
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
        out.append((op.mean(0), per))
    bm.free()
    return out


def centreline(base, a, b, ts, dirs=None, maxoff=0.07):
    out = []
    for i, t in enumerate(ts):
        q = a + (b - a) * t
        n = dirs[i] if dirs is not None else (b - a)
        rs = [r for r in rings(base, q, n) if np.linalg.norm(r[0] - q) < maxoff]
        if rs:
            r = min(rs, key=lambda r: np.linalg.norm(r[0] - q))
            out.append((t, r[0], r[1]))
    return out


def line_fit(p, d):
    c = p.mean(0); u = np.linalg.svd(p - c)[2][0]
    return c, (u if u @ d > 0 else -u)


J = {k: v.copy() for k, v in M.items()}
CL, report = {}, {}
for s in ('R', 'L'):
    S, Wm = M[f'{s}_UpperArm'], M[f'{s}_Hand']
    d = (Wm - S) / np.linalg.norm(Wm - S)
    far = co_skin[(co_skin - S) @ d > np.linalg.norm(Wm - S)]
    far = far[np.linalg.norm((far - S) - np.outer((far - S) @ d, d), axis=1) < 0.12]
    tip = far[np.argmax((far - S) @ d)]
    ts = np.linspace(0.06, 0.97, 60)
    c1 = centreline(SKIN, S, tip, ts)
    tt = np.array([c[0] for c in c1]); cc = np.array([c[1] for c in c1])
    # second pass: slice perpendicular to the local centreline direction (smoothed finite differences)
    dirs = []
    for t in ts:
        i = np.argmin(np.abs(tt - t)); j0, j1 = max(i - 3, 0), min(i + 3, len(cc) - 1)
        dirs.append(cc[j1] - cc[j0])
    pts = [cc[np.argmin(np.abs(tt - t))] for t in ts]
    c2 = []
    for t, p, n in zip(ts, pts, dirs):
        allr = rings(SKIN, p, n)
        rs = [r for r in allr if np.linalg.norm(r[0] - p) < 0.05]
        near = [r for r in allr if np.linalg.norm(r[0] - p) < 0.09]
        if rs:
            r = min(rs, key=lambda r: np.linalg.norm(r[0] - p)); c2.append((t, r[0], r[1], len(near)))
    t2 = np.array([c[0] for c in c2]); cs = np.array([c[1] for c in c2]); per = np.array([c[2] for c in c2])
    nl = np.array([c[3] for c in c2])
    print('PROFILE', s, ' '.join(f'{t:.2f}:{p*100:.0f}/{k}' for t, p, k in zip(t2, per, nl)))
    # fingers separate where a slice first holds several loops near the axis (beyond mid-arm): the wrist lies before
    split = next((t for t, k in zip(t2, nl) if t > 0.5 and k > 1), 0.85)
    CL[f'{s}_arm'] = cs.tolist()
    m = (t2 > 0.5) & (t2 < split - 0.04)
    wi = np.where(m)[0][np.argmin(per[m])]
    wr = cs[wi]
    L_ = np.linalg.norm(wr - S); dw = (wr - S) / L_
    tw = (cs - S) @ dw / L_
    ca, ua = line_fit(cs[(tw > 0.15) & (tw < 0.42)], dw)
    cb, ub = line_fit(cs[(tw > 0.60) & (tw < 0.92)], dw)
    w0 = ca - cb; a_, b_, c_, d_, e_ = ua @ ua, ua @ ub, ub @ ub, ua @ w0, ub @ w0
    den = a_ * c_ - b_ * b_
    s1, s2 = (b_ * e_ - c_ * d_) / den, (a_ * e_ - b_ * d_) / den
    el = ((ca + ua * s1) + (cb + ub * s2)) / 2
    J[f'{s}_Forearm'], J[f'{s}_Hand'] = el, wr
    report[s] = {'wrist_t_tip': round(float(t2[wi]), 3), 'wrist_perimeter_cm': round(float(per[wi]) * 100, 1),
                 'elbow_t': round(float((el - S) @ dw / L_), 3), 'bend_deg': round(float(np.degrees(np.arccos(np.clip(ua @ ub, -1, 1)))), 1),
                 'line_gap_mm': round(float(np.linalg.norm((ca + ua * s1) - (cb + ub * s2))) * 1000, 1),
                 'upper_m': round(float(np.linalg.norm(el - S)), 3), 'fore_m': round(float(np.linalg.norm(wr - el)), 3),
                 'meshy_wrist_off_cm': round(float(np.linalg.norm(wr - Wm)) * 100, 1),
                 'meshy_elbow_off_cm': round(float(np.linalg.norm(el - M[f'{s}_Forearm'])) * 100, 1)}
    print('ARM', s, json.dumps(report[s]))
    # ankle: narrowest horizontal ring of the foot/shin skin between 6 and 25 cm, near the Meshy ankle
    A = M[f'{s}_Foot']
    feet = {p for p in set(pv.tolist()) if p in (4, 5)}
    FOOT = shell(feet | {0})
    best = None
    for z in np.arange(0.06, 0.26, 0.01):
        rs = [r for r in rings(FOOT, (A[0], A[1], z), (0, 0, 1)) if np.linalg.norm(r[0][:2] - A[:2]) < 0.08]
        for r in rs:
            if best is None or r[1] < best[1]:
                best = (np.array([r[0][0], r[0][1], z]), r[1])
    FOOT.free()
    assert best is not None, f'No ankle ring for {s}'
    J[f'{s}_Foot'] = best[0]
    report[s]['ankle_off_meshy_cm'] = round(float(np.linalg.norm(best[0] - A)) * 100, 1)
    print('ANKLE', s, np.round(best[0], 3).tolist(), 'perimeter cm', round(best[1] * 100, 1), 'meshy', np.round(A, 3).tolist())
# A shallow 6-9 degree elbow bend makes the two fitted lines ill-conditioned. Use their bilateral mean
# fraction, then interpolate EACH arm's measured ring centres to keep the joints inside the actual sleeves.
et=sum(report[s]['elbow_t'] for s in ('R','L'))/2
for s in ('R','L'):
 sh,wr=J[f'{s}_UpperArm'],J[f'{s}_Hand']
 d=wr-sh; cs=np.array(CL[f'{s}_arm']); ts=(cs-sh)@d/(d@d); order=np.argsort(ts)
 el=np.array([np.interp(et,ts[order],cs[order,k]) for k in range(3)])
 J[f'{s}_Forearm']=el
 report[s]['bilateral_elbow_t']=round(et,3)
 print('ELBOW constrained',s,np.round(el,4).tolist(),'fraction',round(et,3))
co = np.array([tuple(v.co) for v in ob.data.vertices])
json.dump({'height_m': float(co[:, 2].max() - co[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': report}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
json.dump(CL, open(os.path.join(HERE, 'work', 'centrelines.json'), 'w'))
