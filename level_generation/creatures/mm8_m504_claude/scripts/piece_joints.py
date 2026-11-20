"""G3 joints for the m398 skeleton warrior from its separate pieces, against Meshy's auto-rig estimate
(work/meshy_joints.json). Meshy keeps the axial joints, clavicles, shoulders and hips (the shoulder balls P23/P24 and
the femoral heads agree with it). Replaced from the pieces:
- ELBOW: centre of the elbow knob between the humerus and the gauntlet (P19 left, P20 right);
- WRIST: narrowest ring of the gauntlet shell (P02 left, P01 right) cut perpendicular to the elbow -> hand line,
  between 55 % and the first slice where the fingers separate;
- KNEE: centre of the femur/tibia piece (P12 left, P13 right) ring at the kneecap height (P22 left, P21 right),
  moved back by 25 % of the kneecap depth (the hinge sits behind the patella);
- ANKLE: narrowest horizontal ring of the boot shell (P05 left, P06 right) between 8 and 22 cm, centre.
Writes work/joints_final.json. Args: -- <blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
co = np.array([tuple(v.co) for v in ob.data.vertices])
pv = np.zeros(len(co), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
M = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints'].items()}
SIDE = {'L': {'elbow': 19, 'glove': 2, 'leg': 12, 'patella': 22, 'boot': 5},
        'R': {'elbow': 20, 'glove': 1, 'leg': 13, 'patella': 21, 'boot': 6}}


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
        a, b = e.verts; adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
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
rep = {}
for s, P in SIDE.items():
    el = co[pv == P['elbow']].mean(0)
    hand = M[f'{s}_Hand']
    d = (hand - el) / np.linalg.norm(hand - el)
    G = shell({P['glove']})
    gl = co[pv == P['glove']]
    L = float(((gl - el) @ d).max())
    prof = []
    for t in np.linspace(0.3, 0.95, 40):
        q = el + d * L * t
        rs = rings(G, q, d)
        near = [r for r in rs if np.linalg.norm(r[0] - q) < 0.08]
        if near:
            r = min(near, key=lambda r: np.linalg.norm(r[0] - q)); prof.append((t, r[0], r[1], len(near)))
    split = next((t for t, c, p, k in prof if t > 0.5 and k > 1), 0.9)
    cand = [x for x in prof if 0.5 < x[0] < split - 0.03]
    w = min(cand, key=lambda x: x[2])
    print('PROFILE', s, ' '.join(f'{t:.2f}:{p*100:.0f}/{k}' for t, c, p, k in prof))
    G.free()
    # knee: ring of the leg piece at the patella height
    pat = co[pv == P['patella']]; pc = pat.mean(0)
    LG = shell({P['leg']})
    rs = rings(LG, (pc[0], pc[1], pc[2]), (0, 0, 1)); LG.free()
    rs = [r for r in rs if np.linalg.norm(r[0][:2] - pc[:2]) < 0.08]
    kc = min(rs, key=lambda r: np.linalg.norm(r[0][:2] - pc[:2]))[0] if rs else pc
    depth = pat[:, 1].max() - pat[:, 1].min()
    knee = np.array([kc[0], kc[1] + 0.25 * depth, pc[2]])
    # ankle: narrowest boot ring
    BT = shell({P['boot']}); best = None
    bc = co[pv == P['boot']]
    for z in np.arange(0.08, 0.22, 0.005):
        for c, per in rings(BT, (bc[:, 0].mean(), bc[:, 1].mean(), z), (0, 0, 1)):
            if best is None or per < best[1]:
                best = (np.array([c[0], c[1], z]), per, z)
    BT.free()
    J[f'{s}_Forearm'], J[f'{s}_Hand'], J[f'{s}_Calf'], J[f'{s}_Foot'] = el, w[1], knee, best[0]
    rep[s] = {'elbow_meshy_off_cm': round(float(np.linalg.norm(el - M[f'{s}_Forearm'])) * 100, 1),
              'wrist_t': round(w[0], 3), 'wrist_perimeter_cm': round(w[2] * 100, 1), 'finger_split_t': round(split, 3),
              'wrist_meshy_off_cm': round(float(np.linalg.norm(w[1] - M[f'{s}_Hand'])) * 100, 1),
              'knee_meshy_off_cm': round(float(np.linalg.norm(knee - M[f'{s}_Calf'])) * 100, 1),
              'ankle_meshy_off_cm': round(float(np.linalg.norm(best[0] - M[f'{s}_Foot'])) * 100, 1),
              'ankle_z': round(float(best[2]), 3), 'ankle_perimeter_cm': round(best[1] * 100, 1)}
    print('JOINTS', s, json.dumps(rep[s]))
for a, b in (('Forearm', None), ('Hand', None), ('Calf', None), ('Foot', None), ('UpperArm', None), ('Thigh', None)):
    l, r = J[f'L_{a}'], J[f'R_{a}']
    print('SYM', a, 'L', np.round(l, 3).tolist(), 'R', np.round(r, 3).tolist(), 'mirror diff cm',
          round(float(np.linalg.norm(l - r * np.array([-1, 1, 1]))) * 100, 1))
json.dump({'height_m': float(co[:, 2].max() - co[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': rep}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
