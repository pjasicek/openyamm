"""G5: fingers from the mesh by connectivity (the hand has separate fingers; slice tracking mislabelled them).
Thumb: its own cut (first depth with two pieces; it separates far earlier). Hand vertices (within 0.2 m of the wrist, beyond it) are cut at increasing depth along the hand's finger direction;
the thumb is cut first (first depth with two pieces), then the first depth with four more pieces separates the fingers. Each
piece's centreline runs from its base (lowest-depth vertices) along the piece's farthest-point path to its tip;
the base is extended toward the hand by WEB x the piece's length (the webbing hides about a third of the proximal
phalanx). The thumb is the piece nearest the carried source thumb base; the others are ordered from the thumb side
(index) to the pinky. Writes work/fingers_fit.json {side: {name: [[x,y,z] knuckle .. tip]}}. Args: -- <rig blend>"""
import bpy, sys, os, json
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
J = json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))['joints']
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
PV = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', PV)
SKIN = PV == 0                                            # m234: the hands are part of the one stone shell P00
E = np.array([tuple(e.vertices) for e in me.edges])
B = lambda n: np.array(rig.data.bones[n].head_local)
WEB = 0.18
import bmesh
from mathutils import Vector
SKBM = bmesh.new(); SKBM.from_mesh(me); SKBM.transform(body.matrix_world); SKBM.verts.ensure_lookup_table()
bmesh.ops.delete(SKBM, geom=[v for v in SKBM.verts if me.attributes['piece'].data[v.index].value != 0], context='VERTS')


def loop_at(p, n):
    """The skin loop of the plane (p, n) nearest p: (centroid, perimeter) or None."""
    bm = SKBM.copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(p), plane_no=Vector(n))
    edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, best = set(), None
    for v in adj:
        if v in seen:
            continue
        comp, st = [], [v]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); st.extend(adj[x])
        pts = np.array([tuple(x.co) for x in comp])
        per = sum((e.verts[0].co - e.verts[1].co).length for e in edges if e.verts[0] in set(comp))
        c = pts.mean(0)
        if best is None or np.linalg.norm(c - p) < np.linalg.norm(best[0] - p):
            best = (c, per)
    bm.free()
    return best
NPIECES = 5                                                   # thumb + four fingers (Smart Topology gave the goblin a human hand)


def components(mask):
    idx = np.where(mask)[0]; s = set(idx.tolist())
    adj = {i: [] for i in idx}
    for a, b in E:
        if a in s and b in s:
            adj[a].append(b); adj[b].append(a)
    seen, comps = set(), []
    for i in idx:
        if i in seen:
            continue
        st, comp = [i], []
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); st.extend(adj[x])
        comps.append(np.array(comp))
    return comps


def centreline(comp, fdir, wr):
    P = co[comp]; dep = (P - wr) @ fdir
    base = P[dep < dep.min() + 0.006].mean(0)
    far = P[np.argmax(np.linalg.norm(P - base, axis=1))]
    ax = far - base; L = np.linalg.norm(ax); ax /= L
    pts = []
    for t in np.linspace(0, 1, 12):                         # slab centroids along the base->tip line
        q = base + ax * L * t
        m = np.abs((P - q) @ ax) < L / 14
        pts.append(P[m].mean(0) if m.any() else q)
    pts[0] = base; pts[-1] = far
    pts = np.array(pts)
    d0 = pts[1] - pts[0]; d0 /= np.linalg.norm(d0)
    pts = np.vstack([pts[0] - d0 * WEB * L, pts])           # extend into the webbing toward the knuckle
    return pts


out = {}
for side in ('R', 'L'):
    wr = np.array(J[f'{side}_Hand']); fa = np.array(J[f'{side}_Forearm'])
    d = (wr - fa) / np.linalg.norm(wr - fa)
    hand = SKIN & (np.linalg.norm(co - wr, axis=1) < float(os.environ.get('HAND_R', '0.3'))) & ((co - wr) @ d > -0.01) & (np.sign(co[:, 0]) == np.sign(wr[0]))
    # goblin: the cut direction is the forearm's (the carried source finger direction depends on the hand frame that
    # this fit is meant to produce; at first it pointed 60 deg off and no depth split the hand)
    fdir = d
    dep = (co - wr) @ fdir
    # the thumb leaves the palm first: first depth with two pieces, the smaller one
    thumb = None
    # m150: the bracer's wrist ring splits off at depth 0 (a 44-vertex loop); the thumb leaves at ~8 cm, 6-9 cm from
    # the carried source thumb base (THUMB_MIN_CUT, THUMB_NEAR)
    for tcut in np.arange(float(os.environ.get('THUMB_MIN_CUT', '0')), 0.16, 0.0025):
        tc = [c for c in components(hand & (dep > tcut)) if len(c) >= 8]
        # m406: the gauntlet's dorsal plate splits off first (it covers the back of the hand to the knuckles); the
        # thumb is the non-largest piece nearest the rig's carried thumb base, not simply the smallest
        if os.environ.get('FF_DEBUG'):
            print('FFDBG', side, round(tcut, 4), [(len(c), round(float(np.linalg.norm(co[c].mean(0) - B(f'B_{side}_Finger0'))), 3)) for c in tc], flush=True)
        if len(tc) >= 2:
            big = max(tc, key=len); tb = B(f'B_{side}_Finger0')
            cand = [c for c in tc if c is not big and len(c) >= 15]
            near = [c for c in cand if np.linalg.norm(co[c].mean(0) - tb) < float(os.environ.get('THUMB_NEAR', '0.06'))]
            if near:
                small = min(near, key=lambda c: np.linalg.norm(co[c].mean(0) - tb)); tcen = co[small].mean(0)
                thumb = centreline(small, fdir, wr); tcut_used = tcut; break
            continue
        if False:
            small = min(tc, key=len); tcen = co[small].mean(0)
            thumb = centreline(small, fdir, wr); tcut_used = tcut; break
    print('THUMBCUT', side, 'depth cm', round(tcut_used * 100, 1), 'verts', len(small))
    # fingers: a split tree over increasing depth (the index separates far earlier than the pinky, so no single
    # depth shows all four). A finger = the earliest component whose descendants never split again.
    tv = set(small.tolist())
    levels = []
    for cut in np.arange(tcut_used, 0.3, 0.0025):
        mask = hand & (dep > cut); mask[small] = False                 # the thumb is cut out, its base stays palm
        cs_ = [c for c in components(mask) if len(c) >= 8]
        if not cs_:
            break
        levels.append(cs_)
    owner = [{int(v): i for i, c in enumerate(cs_) for v in c} for cs_ in levels]
    kids = [[[j for j, c in enumerate(levels[k + 1]) if owner[k].get(int(c[0])) == i] for i in range(len(levels[k]))]
            for k in range(len(levels) - 1)] + [[[] for _ in levels[-1]]]
    memo = {}
    def is_chain(k, i):
        if (k, i) not in memo:
            ch = kids[k][i]
            memo[(k, i)] = len(ch) <= 1 and (not ch or is_chain(k + 1, ch[0]))
        return memo[(k, i)]
    parent = lambda k, i: next((j for j, ch in enumerate(kids[k - 1]) if i in ch), None) if k else None
    comps = [levels[k][i] for k in range(len(levels)) for i in range(len(levels[k]))
             if is_chain(k, i) and len(levels[k][i]) >= 15 and (k == 0 or parent(k, i) is None or not is_chain(k - 1, parent(k, i)))]
    if len(comps) > NPIECES - 1:                    # m406: the gauntlet's dorsal plate and a medial cuff flap split off
        # too and the "thumb" cut took the plate. The digits are the pieces that reach past 12 cm; with five of them
        # the thumb is the one nearest the carried source thumb's distal joint, the other four are the fingers.
        long_ = [c for c in comps if dep[c].max() > 0.12 and len(c) >= 40]
        if len(long_) == NPIECES:
            td = B(f'B_{side}_Finger02' if side == 'L' else 'B_R_Finger0.002')
            th = min(long_, key=lambda c: np.linalg.norm(co[c].mean(0) - td))
            small = th; tcen = co[th].mean(0); thumb = centreline(th, fdir, wr)
            comps = [c for c in long_ if c is not th]
            print('FINGERFIT', side, 'thumb re-chosen among five long pieces (centre', np.round(tcen, 3).tolist(), ')')
        else:
            comps = sorted(comps, key=lambda c: -dep[c].max())[:NPIECES - 1]
            print('FINGERFIT', side, 'kept the', NPIECES - 1, 'farthest-reaching pieces')
    if len(comps) != NPIECES - 1:
        print('FINGERFIT', side, f'split tree gave {len(comps)} fingers', [len(c) for c in comps]); continue
    cut = tcut_used
    pairs = sorted(((centreline(c, fdir, wr), c) for c in comps), key=lambda lc: np.linalg.norm(lc[0][1] - tcen))
    lines = [l for l, _ in pairs]; pieces = [c for _, c in pairs]   # index nearest the thumb
    # knuckles: deep webbing on this mesh separates the index and pinky late, so their pieces start mid-finger. Walk
    # each finger back along its own axis, slicing the skin perpendicular to it; the knuckle is the last slice whose
    # loop around the axis is still finger-sized (perimeter < 1.45x the finger's own, centroid within 1.2 cm)
    for k, l in enumerate(lines):
        d0 = l[2] - l[1]; d0 /= np.linalg.norm(d0)
        p_ref = []
        for t in (0.25, 0.4, 0.55):
            q = l[0] + (l[-1] - l[0]) * t
            r = loop_at(q, (l[-1] - l[0]))
            if r is not None:
                p_ref.append(r[1])
        if not p_ref:
            continue
        pf = float(np.median(p_ref)); base = l[1]; ext = 0.0
        for step in np.arange(0.004, 0.09, 0.004):
            q = l[1] - d0 * step
            r = loop_at(q, d0)
            if r is None or r[1] > 1.45 * pf or np.linalg.norm(r[0] - q) > 0.012:
                break
            base, ext = q, step
        if ext > 0:
            lines[k] = np.vstack([base, l[1:]])
        print('KNUCKLE', side, k, 'finger perimeter cm', round(pf * 100, 1), 'extended back cm', round(ext * 100, 1))
    res = {'thumb': thumb.tolist()}
    for n, l in zip(['index', 'middle', 'ring', 'pinky'], lines):
        res[n] = l.tolist()
    # the separated pieces themselves (vertex indices of the step1/rig_v1..v4f topology): finger_weights.py assigns
    # every vertex of a piece to that finger (distance to the nearest chain left claw tips and knuckle skin on the hand
    # bone: up to 41x stretch in the fist, gob2 review 1)
    res['verts'] = {'thumb': [int(i) for i in small]}
    for n, c in zip(['index', 'middle', 'ring', 'pinky'], pieces):
        res['verts'][n] = [int(i) for i in c]
    out[side] = res
    print('FINGERFIT', side, 'split at depth cm', round(cut * 100, 1), {n: round(float(np.linalg.norm(np.diff(np.array(v), axis=0), axis=1).sum()) * 100, 1) for n, v in res.items() if n != 'verts'}, 'piece verts', {n: len(v) for n, v in res['verts'].items()})
json.dump(out, open(os.path.join(HERE, 'work', 'fingers_fit.json'), 'w'))
