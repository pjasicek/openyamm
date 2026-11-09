"""G3 joint composition for the m410 thief (after mm7_m190_claude). Meshy's auto-rig (work/meshy_joints.json)
gives the axial joints, clavicles, shoulders, hips and knees. The Smart Topology torso shell P00 carries the arms and
hands; the boots are P05 (left) and P04 (right):
- WRIST = centre of the narrowest arm ring within 5 cm of Meshy's wrist along the arm;
- ELBOW = Meshy's elbow parameter t along shoulder -> wrist, centred on the arm cross-section at that t;
- ANKLE = centre of the narrowest horizontal ring of the boot shell between 7 and 15 cm, near Meshy's ankle.
Writes work/joints_final.json and work/centrelines.json. Args: -- <blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
CO = np.array([tuple(v.co) for v in ob.data.vertices])
M = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints'].items()}
SIDE = {'L': {'fore': (0,), 'leg': 5}, 'R': {'fore': (0,), 'leg': 4}}


def shell(pieces):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if pv[v.index] not in pieces], context='VERTS')
    return bm


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
        pts = np.array([tuple(x.co) for x in comp])
        ordered = [comp[0]]; left = set(comp[1:])
        while left:
            nxt = next((y for y in adj[ordered[-1]] if y in left), None)
            if nxt is None:
                break
            ordered.append(nxt); left.discard(nxt)
        op = np.array([tuple(x.co) for x in ordered])
        per = float(np.linalg.norm(np.diff(np.vstack([op, op[:1]]), axis=0), axis=1).sum())
        out.append((pts.mean(0), per))
    bm.free()
    return out


def boundary_loop_centre(piece):
    bm = shell({piece})
    bv = {v for e in bm.edges if e.is_boundary for v in e.verts}
    c = np.array([tuple(v.co) for v in bv]).mean(0)
    bm.free()
    return c


J = {k: v.copy() for k, v in M.items()}
CL, report = {}, {}
for s, ids in SIDE.items():
    sh = M[f'{s}_UpperArm']; mw = M[f'{s}_Hand']
    d_ = (mw - sh) / np.linalg.norm(mw - sh)
    ARM0 = shell(set(ids['fore'])); best = None
    for off in np.arange(-0.05, 0.051, 0.005):
        q = mw + d_ * off
        for r in rings(ARM0, q, d_):
            if np.linalg.norm(r[0] - q) < 0.05 and (best is None or r[1] < best[1]):
                best = (r[0], r[1])
    ARM0.free()
    wr = np.array(best[0])
    L_ = np.linalg.norm(wr - sh); d = (wr - sh) / L_
    tm = float((M[f'{s}_Forearm'] - sh) @ d / L_)
    ARM = shell(set(ids['fore']))
    cl = []
    for t in np.linspace(0.12, 0.95, 40):
        q = sh + d * L_ * t
        rs = [r for r in rings(ARM, q, d) if np.linalg.norm(r[0] - q) < 0.06]
        if rs:
            cl.append((t, min(rs, key=lambda r: np.linalg.norm(r[0] - q))[0]))
    ARM.free()
    tt = np.array([c[0] for c in cl]); cc = np.array([c[1] for c in cl])
    el = np.array([np.interp(tm, tt, cc[:, k]) for k in range(3)])
    CL[f'{s}_arm'] = cc.tolist()
    J[f'{s}_Hand'], J[f'{s}_Forearm'] = wr, el
    # ankle
    A = M[f'{s}_Foot']
    LEG = shell({ids['leg']})
    best = None
    for z in np.arange(0.07, 0.15, 0.005):                  # m410: the boot shaft narrows again at 18 cm, above the ankle
        for r in rings(LEG, (A[0], A[1], z), (0, 0, 1)):
            if np.linalg.norm(r[0][:2] - A[:2]) < 0.08 and (best is None or r[1] < best[1]):
                best = (np.array([r[0][0], r[0][1], z]), r[1])
    LEG.free()
    J[f'{s}_Foot'] = best[0]
    report[s] = {'meshy_elbow_t': round(tm, 3), 'elbow_move_cm': round(float(np.linalg.norm(el - M[f'{s}_Forearm'])) * 100, 2),
                 'wrist_off_meshy_cm': round(float(np.linalg.norm(wr - M[f'{s}_Hand'])) * 100, 2),
                 'upper_m': round(float(np.linalg.norm(el - sh)), 3), 'fore_m': round(float(np.linalg.norm(wr - el)), 3),
                 'ankle_perimeter_cm': round(best[1] * 100, 1),
                 'ankle_off_meshy_cm': round(float(np.linalg.norm(best[0] - A)) * 100, 2)}
    print('JOINTS', s, json.dumps(report[s]))
sym = {k: round(float(J['L_' + k][0] + J['R_' + k][0]) * 100, 2) for k in ('UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot')}
print('SYMMETRY x(L)+x(R) cm', sym)
json.dump({'height_m': float(CO[:, 2].max() - CO[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': report}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
json.dump(CL, open(os.path.join(HERE, 'work', 'centrelines.json'), 'w'))
