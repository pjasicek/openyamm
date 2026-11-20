"""G3 joints for the m270 lich (built mirrored, see README), from its pieces against Meshy's auto-rig estimate
(work/meshy_joints.json). Meshy keeps the axial joints, clavicles, shoulders, elbows, hips, knees and ankles (the legs
are a piece under the skirt). Replaced: the WRIST - narrowest ring of the arm piece (P01 left, P02 right: chain sleeve
and bony hand in one piece) cut perpendicular to the elbow -> hand line, between 55 % and the first slice where the
fingers separate. Writes work/joints_final.json. Args: -- <blend>"""
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
SIDE = {'L': {'glove': 1}, 'R': {'glove': 2}}


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
    el = M[f'{s}_Forearm']
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
    print('PROFILE', s, ' '.join(f'{t:.2f}:{p*100:.0f}/{k}' for t, c, p, k in prof))
    # m270: the sleeve keeps an inner loop all along (k = 2), so the finger split is not the loop count: the bony
    # wrist is the narrowest ring above 5 cm perimeter between 50 and 70 % (the carpal bones beyond are 1-2 cm loops)
    split = 0.73
    cand = [x for x in prof if 0.5 < x[0] < 0.70 and x[2] > 0.05]
    w = min(cand, key=lambda x: x[2])
    G.free()
    J[f'{s}_Hand'] = w[1]
    rep[s] = {'wrist_t': round(w[0], 3), 'wrist_perimeter_cm': round(w[2] * 100, 1), 'finger_split_t': round(split, 3),
              'wrist_meshy_off_cm': round(float(np.linalg.norm(w[1] - M[f'{s}_Hand'])) * 100, 1)}
    print('JOINTS', s, json.dumps(rep[s]))
for a, b in (('Forearm', None), ('Hand', None), ('Calf', None), ('Foot', None), ('UpperArm', None), ('Thigh', None)):
    l, r = J[f'L_{a}'], J[f'R_{a}']
    print('SYM', a, 'L', np.round(l, 3).tolist(), 'R', np.round(r, 3).tolist(), 'mirror diff cm',
          round(float(np.linalg.norm(l - r * np.array([-1, 1, 1]))) * 100, 1))
json.dump({'height_m': float(co[:, 2].max() - co[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': rep}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
