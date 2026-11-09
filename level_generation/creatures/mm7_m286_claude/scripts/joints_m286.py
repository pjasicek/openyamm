"""G3 joint composition for the m286 minotaur (after joints_m190.py). Meshy's auto-rig (work/meshy_joints.json) gives
the axial joints, clavicles, shoulders and hips. The Smart Topology body shell P00 holds the skin of the arms, hands
and legs in one piece (wrist bands P05 right / P06 left are separate), so every limb joint is centred on a
cross-section ring of P00 alone:
- ELBOW = Meshy's elbow parameter t along shoulder -> wrist, centred on the arm ring perpendicular to that line;
- WRIST = the first local minimum of the arm ring perimeter past t 0.85 of shoulder -> Meshy hand;
- KNEE, ANKLE = the midpoint across the leg through Meshy's joint along the bend's in-plane direction (Meshy put the knee
  on the front surface and the hock on the back surface of the bent goat leg; a horizontal ring is oblique there);
- TOE   = Meshy's toe, moved to the hoof's front third at the sole.
The rest is Meshy's. Writes work/joints_final.json and work/centrelines.json. Args: -- <blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
CO = np.array([tuple(v.co) for v in ob.data.vertices])
M = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints'].items()}


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
        out.append((np.array([tuple(x.co) for x in comp]).mean(0), per))
    bm.free()
    return out


def nearest_ring(base, p, n, radius):
    rs = [r for r in rings(base, p, n) if np.linalg.norm(r[0] - p) < radius]
    return min(rs, key=lambda r: np.linalg.norm(r[0] - p)) if rs else None


SKIN = shell({0})
BVH = BVHTree.FromBMesh(SKIN)
J = {k: v.copy() for k, v in M.items()}
CL, report = {}, {}
for s in ('L', 'R'):
    sh, mh = M[f'{s}_UpperArm'], M[f'{s}_Hand']
    L_ = np.linalg.norm(mh - sh); d = (mh - sh) / L_
    cl = []
    for t in np.linspace(0.12, 1.2, 55):
        q = sh + d * L_ * t
        r = nearest_ring(SKIN, q, d, 0.07)
        if r is not None:
            cl.append((t, r[0], r[1]))
    tt = np.array([c[0] for c in cl]); cc = np.array([c[1] for c in cl]); pp = np.array([c[2] for c in cl])
    # the wrist: the first local minimum of the perimeter past t 0.85 (the palm widens again after it)
    wsel = [i for i in range(1, len(tt) - 1) if tt[i] >= 0.85 and pp[i] <= pp[i - 1] and pp[i] <= pp[i + 1]]
    k = wsel[0] if wsel else int(np.argmin(np.where(tt >= 0.85, pp, 1e9)))
    wr = cc[k]
    tm = float((M[f'{s}_Forearm'] - sh) @ d / L_)
    el = np.array([np.interp(tm, tt, cc[:, i]) for i in range(3)])
    CL[f'{s}_arm'] = cc.tolist()
    J[f'{s}_Hand'], J[f'{s}_Forearm'] = wr, el
    rep = {'meshy_elbow_t': round(tm, 3), 'elbow_move_cm': round(float(np.linalg.norm(el - M[f'{s}_Forearm'])) * 100, 2),
           'wrist_t': round(float(tt[k]), 3), 'wrist_perimeter_cm': round(float(pp[k]) * 100, 1),
           'wrist_off_meshy_cm': round(float(np.linalg.norm(wr - mh)) * 100, 2)}
    print('WRISTPROFILE', s, [(round(float(a), 2), round(float(b) * 100, 1)) for a, b in zip(tt, pp) if a > 0.6])
    chain = [M[f'{s}_Thigh'], M[f'{s}_Calf'], M[f'{s}_Foot'], M[f'{s}_Toe0']]
    for idx, (jn, key) in enumerate((('Calf', 'knee'), ('Foot', 'ankle')), start=1):
        A = chain[idx]
        up = chain[idx - 1] - A; dn = chain[idx + 1] - A
        b = up / np.linalg.norm(up) + dn / np.linalg.norm(dn)          # into the bend, in the leg's plane
        b /= np.linalg.norm(b)
        hits = []
        for sgn in (1, -1):
            loc = BVH.ray_cast(Vector(A - sgn * b * 0.4), Vector(sgn * b), 0.8)[0]
            hits.append(np.array(loc) if loc is not None else None)
        # the first surface met from each side across the leg: the joint is their midpoint
        J[f'{s}_{jn}'] = (hits[0] + hits[1]) / 2
        rep[f'{key}_thickness_cm'] = round(float(np.linalg.norm(hits[0] - hits[1])) * 100, 1)
        rep[f'{key}_move_cm'] = round(float(np.linalg.norm(J[f'{s}_{jn}'] - A)) * 100, 2)
    # toe: the hoof's front third at the sole
    foot = CO[(pv == 0) & (CO[:, 2] < 0.12) & (np.sign(CO[:, 0]) == np.sign(M[f'{s}_Foot'][0])) &
              (np.abs(CO[:, 0] - M[f'{s}_Foot'][0]) < 0.2)]
    y0, y1 = foot[:, 1].min(), foot[:, 1].max()
    J[f'{s}_Toe0'] = np.array([foot[:, 0].mean(), y0 + (y1 - y0) / 3, 0.04])
    rep['hoof_len_cm'] = round(float(y1 - y0) * 100, 1)
    rep.update({'upper_m': round(float(np.linalg.norm(el - sh)), 3), 'fore_m': round(float(np.linalg.norm(wr - el)), 3),
                'thigh_m': round(float(np.linalg.norm(J[f'{s}_Calf'] - J[f'{s}_Thigh'])), 3),
                'shin_m': round(float(np.linalg.norm(J[f'{s}_Foot'] - J[f'{s}_Calf'])), 3)})
    report[s] = rep
    print('JOINTS', s, json.dumps(rep))
SKIN.free()
sym = {k: round(float(J['L_' + k][0] + J['R_' + k][0]) * 100, 2)
       for k in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot', 'Toe0')}
print('SYMMETRY x(L)+x(R) cm', sym)
json.dump({'height_m': float(CO[:, 2].max() - CO[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': report}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
json.dump(CL, open(os.path.join(HERE, 'work', 'centrelines.json'), 'w'))
