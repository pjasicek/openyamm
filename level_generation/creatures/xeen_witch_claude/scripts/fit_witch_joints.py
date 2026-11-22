"""G3 joints for the witch: Meshy's auto-rig (work/meshy_joints.json) for the axial joints, clavicles, shoulders, hips
and knees; the limbs re-derived from her own shells:
- arms are separate shells (P08 right, P09 left) ending under the hand shells (P03 bare right hand, P02 left
  gauntlet). Arm centreline = ring centres of the arm shell alone, cut perpendicular to the shoulder -> hand line
  (two passes, the second perpendicular to the smoothed first centreline). WRIST = centre of the arm shell's distal
  open boundary loop moved to the hand shell's proximal end along the arm (the hand shell overlaps the forearm tip);
  ELBOW = Meshy's elbow t along shoulder -> wrist, centred on the ring centreline (natm rule: the ring line fits
  latch onto muscle bulges).
- ankles: the boot shells (P05 right, P06 left) are closed; the ankle is the centre of the narrowest horizontal boot
  ring between 8 and 22 cm, at Meshy's ankle height.
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
ARM, HAND, BOOT = {'R': 8, 'L': 9}, {'R': 3, 'L': 2}, {'R': 5, 'L': 6}


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


def boundary_loops(bm):
    edges = [e for e in bm.edges if e.is_boundary]
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
        out.append(np.array([tuple(x.co) for x in comp]))
    return out


J = {k: v.copy() for k, v in M.items()}
CL, report = {}, {}
for s in ('R', 'L'):
    S, Wm = M[f'{s}_UpperArm'], M[f'{s}_Hand']
    A = shell({ARM[s]})
    loops = boundary_loops(A)
    d0 = (Wm - S) / np.linalg.norm(Wm - S)
    distal = max(loops, key=lambda l: (l.mean(0) - S) @ d0)
    wr_loop = distal.mean(0)
    hand = CO[pv == HAND[s]]
    # hand shell's proximal end along the arm: 5th percentile of its projection
    hp = (hand - S) @ d0
    prox = np.percentile(hp, 3)
    ts = np.linspace(0.08, 0.98, 50)
    L0 = float((wr_loop - S) @ d0)
    c1 = []
    for t in ts:
        q = S + d0 * L0 * t
        rs = [r for r in rings(A, q, d0) if np.linalg.norm(r[0] - q) < 0.07]
        if rs:
            c1.append((t, min(rs, key=lambda r: np.linalg.norm(r[0] - q))))
    tt = np.array([c[0] for c in c1]); cc = np.array([c[1][0] for c in c1]); per = np.array([c[1][1] for c in c1])
    CL[f'{s}_arm'] = cc.tolist()
    # wrist: on the centreline extrapolated to the hand shell's proximal end (or the loop if the hand starts beyond)
    tw = min(prox, L0) / L0 if L0 > 0 else 1.0
    o = np.argsort(tt)
    fa = cc[(tt > 0.6)]
    fa_c = fa.mean(0); fa_u = np.linalg.svd(fa - fa_c)[2][0]
    if fa_u @ d0 < 0:
        fa_u = -fa_u
    wr = fa_c + fa_u * float((S + d0 * L0 * tw - fa_c) @ fa_u)
    # the hand shell starts with a 3-5 cm wrist band (wrap / gauntlet cuff): the wrist is its narrowest ring beyond
    # the band, 3-9 cm past the shell's proximal end (hand_profile.py: 23-24 cm against the 26-42 cm cuff and palm)
    Hs = shell({HAND[s]}); dd = (wr - S) / np.linalg.norm(wr - S)
    cand = []
    for k in np.arange(0.03, 0.0901, 0.005):
        q = wr + dd * k
        rs = [r for r in rings(Hs, q, dd) if np.linalg.norm(r[0] - q) < 0.05]
        if rs:
            r = max(rs, key=lambda r: r[1]); cand.append((r[1], k, r[0]))
    Hs.free()
    pmin, kmin, cmin = min(cand, key=lambda c: c[0])
    wr = cmin
    report_wrist = {'band_k_cm': round(float(kmin) * 100, 1), 'perimeter_cm': round(float(pmin) * 100, 1)}
    L_ = np.linalg.norm(wr - S); dw = (wr - S) / L_
    tm = float((M[f'{s}_Forearm'] - S) @ dw / L_)
    tproj = (cc - S) @ dw / L_
    o = np.argsort(tproj)
    el = np.array([np.interp(tm, tproj[o], cc[o][:, k]) for k in range(3)])
    J[f'{s}_Forearm'], J[f'{s}_Hand'] = el, wr
    report[s] = {'wrist_loop': np.round(wr_loop, 3).tolist(), 'hand_prox_t': round(float(prox / L0), 3),
                 'wrist': np.round(wr, 3).tolist(), 'meshy_wrist_off_cm': round(float(np.linalg.norm(wr - Wm)) * 100, 1),
                 'elbow_t': round(tm, 3), 'meshy_elbow_off_cm': round(float(np.linalg.norm(el - M[f'{s}_Forearm'])) * 100, 1),
                 'upper_m': round(float(np.linalg.norm(el - S)), 3), 'fore_m': round(float(np.linalg.norm(wr - el)), 3),
                 'wrist_ring': report_wrist}
    print('ARM', s, json.dumps(report[s]))
    A.free()
    # ankle
    Am = M[f'{s}_Foot']
    B = shell({BOOT[s]})
    best = None
    for z in np.arange(0.08, 0.225, 0.01):
        for r in rings(B, (Am[0], Am[1], z), (0, 0, 1)):
            if np.linalg.norm(r[0][:2] - Am[:2]) < 0.09 and (best is None or r[1] < best[1]):
                best = (np.array([r[0][0], r[0][1], z]), r[1])
    B.free()
    ank = np.array([best[0][0], best[0][1], Am[2]])
    J[f'{s}_Foot'] = ank
    print('ANKLE', s, np.round(ank, 3).tolist(), 'narrowest z', round(float(best[0][2]), 3), 'perimeter cm',
          round(best[1] * 100, 1), 'meshy', np.round(Am, 3).tolist())
json.dump({'height_m': float(CO[:, 2].max() - CO[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': report}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
json.dump(CL, open(os.path.join(HERE, 'work', 'centrelines.json'), 'w'))
