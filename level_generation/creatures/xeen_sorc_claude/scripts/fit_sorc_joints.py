"""G3 joints for the sorceress: Meshy's auto-rig (work/meshy_joints.json) for the axial joints, clavicles, shoulders,
hips and knees; the arm and ankle joints re-derived from her own skin shell (P00: skin, gloves and boots in one shell):
- arm centreline = ring centres of P00 cut perpendicular to the shoulder -> Meshy wrist line (only rings within 7 cm
  of the line, so the torso is never taken).
- WRIST = narrowest ring between 7 cm before and 4 cm past Meshy's wrist along the forearm (the glove narrows at the
  wrist below its flared cuff), ELBOW = Meshy's elbow t along shoulder -> wrist, centred on the ring centreline
  (natm rule: ring line fits latch onto muscle bulges).
- ANKLE = centre of the narrowest horizontal boot ring between 8 and 22 cm near Meshy's ankle, at Meshy's height.
Writes work/joints_final.json and work/centrelines.json. Args: -- <step1 blend>"""
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
BASE = bmesh.new(); BASE.from_mesh(ob.data); BASE.verts.ensure_lookup_table()
bmesh.ops.delete(BASE, geom=[v for v in BASE.verts if pv[v.index] != 0], context='VERTS')


def rings(p, n):
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
        out.append((op.mean(0), per))
    bm.free()
    return out


J = {k: v.copy() for k, v in M.items()}
CL, report = {}, {}
for s in ('R', 'L'):
    S, Wm, Em = M[f'{s}_UpperArm'], M[f'{s}_Hand'], M[f'{s}_Forearm']
    L0 = float(np.linalg.norm(Wm - S)); d0 = (Wm - S) / L0
    cl = []
    for t in np.linspace(0.12, 1.0, 45):
        q = S + d0 * L0 * t
        rs = [r for r in rings(q, d0) if np.linalg.norm(r[0] - q) < 0.07]
        if rs:
            r = min(rs, key=lambda r: np.linalg.norm(r[0] - q)); cl.append((t, r[0], r[1]))
    tt = np.array([c[0] for c in cl]); cc = np.array([c[1] for c in cl])
    CL[f'{s}_arm'] = cc.tolist()
    df = (Wm - Em) / np.linalg.norm(Wm - Em)
    cand = []
    for k in np.arange(-0.07, 0.0401, 0.005):
        q = Wm + df * k
        rs = [r for r in rings(q, df) if np.linalg.norm(r[0] - q) < 0.05]
        if rs:
            r = min(rs, key=lambda r: np.linalg.norm(r[0] - q)); cand.append((r[1], k, r[0]))
    pmin, kmin, wr = min(cand, key=lambda c: c[0])
    L_ = np.linalg.norm(wr - S); dw = (wr - S) / L_
    tm = float((Em - S) @ dw / L_)
    tproj = (cc - S) @ dw / L_
    o = np.argsort(tproj)
    el = np.array([np.interp(tm, tproj[o], cc[o][:, k]) for k in range(3)])
    J[f'{s}_Forearm'], J[f'{s}_Hand'] = el, wr
    report[s] = {'wrist': np.round(wr, 3).tolist(), 'wrist_k_cm': round(float(kmin) * 100, 1),
                 'wrist_perimeter_cm': round(float(pmin) * 100, 1),
                 'meshy_wrist_off_cm': round(float(np.linalg.norm(wr - Wm)) * 100, 1),
                 'elbow_t': round(tm, 3), 'meshy_elbow_off_cm': round(float(np.linalg.norm(el - Em)) * 100, 1),
                 'upper_m': round(float(np.linalg.norm(el - S)), 3), 'fore_m': round(float(np.linalg.norm(wr - el)), 3),
                 'ring_profile': [(round(float(c[1]) * 100, 1), round(float(c[0]), 1)) for c in sorted(cand, key=lambda c: c[1])]}
    print('ARM', s, json.dumps(report[s]))
    Am = M[f'{s}_Foot']
    best = None
    for z in np.arange(0.08, 0.225, 0.01):
        for r in rings((Am[0], Am[1], z), (0, 0, 1)):
            if np.linalg.norm(r[0][:2] - Am[:2]) < 0.09 and (best is None or r[1] < best[1]):
                best = (np.array([r[0][0], r[0][1], z]), r[1])
    ank = np.array([best[0][0], best[0][1], Am[2]])
    J[f'{s}_Foot'] = ank
    print('ANKLE', s, np.round(ank, 3).tolist(), 'narrowest z', round(float(best[0][2]), 3), 'perimeter cm',
          round(best[1] * 100, 1), 'meshy', np.round(Am, 3).tolist())
json.dump({'height_m': float(CO[:, 2].max() - CO[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': report}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
json.dump(CL, open(os.path.join(HERE, 'work', 'centrelines.json'), 'w'))
