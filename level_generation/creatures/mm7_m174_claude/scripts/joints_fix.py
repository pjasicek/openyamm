"""Wrists and elbows of the Moon Cleric (after arm_rings.py; edits work/joints_final.json in place).
WRIST: the hand shells (pieces 4 R, 5 L) carry an ~8 cm forearm stub up into the sleeve, so arm_rings' cuff centroid
sits mid-forearm. Slice each hand shell perpendicular to its axis (cuff centroid -> farthest fingertip) and take the
narrowest stretch between 15 and 60 % of that length and keep its distal end (the palm widens after it).
ELBOW: inside the wide bell sleeves the ring centreline sags and Meshy's estimate sits 5 cm off (65 deg rest bend);
the HD masters show a nearly straight A-pose arm, so the elbow goes on the shoulder -> wrist line at the human
upper-arm share UPPER, BACK m behind it (a slight bend that fixes the hinge plane). Args: -- <step1 blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
p = os.path.join(HERE, 'work', 'joints_final.json')
d = json.load(open(p)); J = d['joints']
UPPER, BACK = float(os.environ.get('UPPER', '0.54')), float(os.environ.get('BACK', '0.012'))


def loops(bm, q, n):
    bmc = bm.copy()
    res = bmesh.ops.bisect_plane(bmc, geom=bmc.verts[:] + bmc.edges[:] + bmc.faces[:], plane_co=Vector(q), plane_no=Vector(n))
    es = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in es:
        a, b = e.verts; adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for v in adj:
        if v in seen:
            continue
        comp, st = [], [v]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); st.extend(adj[x])
        pts = np.array([x.co[:] for x in comp])
        if len(pts) >= 4:
            per = sum(e.calc_length() for e in es if e.verts[0] in seen and e.verts[1] in comp)
            out.append((pts.mean(0), len(pts), pts))
    bmc.free()
    return out


for s, piece in (('R', cfg.HANDS['R']), ('L', cfg.HANDS['L'])):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if pv[v.index] != piece], context='VERTS')
    co = np.array([v.co[:] for v in bm.verts])
    cuff = np.array([v.co[:] for v in bm.verts if any(e.is_boundary for e in v.link_edges)]).mean(0)
    tip = co[np.argmax(np.linalg.norm(co - cuff, axis=1))]
    L = float(np.linalg.norm(tip - cuff)); ax = (tip - cuff) / L
    prof = []
    for t in np.linspace(0.05, 0.75, 36):
        q = cuff + ax * L * t
        ls = [l for l in loops(bm, q, ax) if np.linalg.norm(l[0] - q) < 0.05]
        if ls:
            c, n, pts = min(ls, key=lambda l: np.linalg.norm(l[0] - q))
            w = float(np.ptp((pts - c) @ np.linalg.svd(pts - c)[2][0]))      # widest extent of the section
            prof.append((t, c, w, len(ls)))
    bm.free()
    cand = [x for x in prof if 0.15 <= x[0] <= 0.6 and x[3] == 1]
    wmin = min(x[2] for x in cand)
    # the slender gaunt wrist is a 3.5 cm tube over 15-30 %: the joint is where the palm starts to widen (the last
    # section within 10 % of the narrowest)
    t, wc, w, _ = max((x for x in cand if x[2] <= wmin * 1.1), key=lambda x: x[0])
    old = np.array(J[f'{s}_Hand'])
    J[f'{s}_Hand'] = [round(float(x), 5) for x in wc]
    print('WRIST', s, 't', round(t, 2), 'width cm', round(w * 100, 1), 'moved cm', round(float(np.linalg.norm(wc - old)) * 100, 1),
          'profile', ' '.join(f'{x[0]:.2f}:{x[2]*100:.1f}/{x[3]}' for x in prof))
    sh = np.array(J[f'{s}_UpperArm'])
    el = sh + (wc - sh) * UPPER + np.array([0.0, BACK, 0.0])
    J[f'{s}_Forearm'] = [round(float(x), 5) for x in el]
    print('ELBOW', s, 'upper m', round(float(np.linalg.norm(el - sh)), 3), 'fore m', round(float(np.linalg.norm(wc - el)), 3))
json.dump(d, open(p, 'w'), indent=1)
