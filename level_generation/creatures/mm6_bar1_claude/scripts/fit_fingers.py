"""G5: fingers from the mesh by connectivity (the hand has separate fingers; slice tracking mislabelled them).
Thumb: its own cut (first depth with two pieces; it separates far earlier). Hand vertices (within 0.2 m of the wrist, beyond it) are cut at increasing depth along the hand's finger direction;
the first depth at which the rest splits into >= 5 pieces of >= 8 vertices separates thumb + four fingers. Each
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
E = np.array([tuple(e.vertices) for e in me.edges])
B = lambda n: np.array(rig.data.bones[n].head_local)
WEB = 0.18


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
    hand = (np.linalg.norm(co - wr, axis=1) < 0.2) & ((co - wr) @ d > -0.01) & (np.sign(co[:, 0]) == np.sign(wr[0]))
    fdir = B(f'B_{side}_Finger2') - B(f'B_{side}_Hand'); fdir /= np.linalg.norm(fdir)
    dep = (co - wr) @ fdir
    found = None
    for cut in np.arange(0.02, 0.12, 0.0025):
        comps = [c for c in components(hand & (dep > cut)) if len(c) >= 8]
        if len(comps) >= 5:
            found = (cut, sorted(comps, key=len, reverse=True)[:5]); break
    if not found:
        print('FINGERFIT', side, 'no 5-way split'); continue
    cut, comps = found
    th_src = B(f'B_{side}_Finger0')
    lines = [centreline(c, fdir, wr) for c in comps]
    ti = int(np.argmin([np.linalg.norm(l[1] - th_src) for l in lines]))
    lines.pop(ti)
    # the thumb leaves the palm much earlier than the fingers: its own cut is the first depth with two pieces
    thumb = None
    for tcut in np.arange(-0.01, cut, 0.0025):
        tc = [c for c in components(hand & (dep > tcut)) if len(c) >= 8]
        if len(tc) >= 2:
            small = min(tc, key=len)
            thumb = centreline(small, fdir, wr); tcut_used = tcut; break
    print('THUMBCUT', side, 'depth cm', round(tcut_used * 100, 1))
    tdir = B(f'B_{side}_Finger1') - B(f'B_{side}_Finger4'); tdir /= np.linalg.norm(tdir)
    lines.sort(key=lambda l: -(l[1] - wr) @ tdir)
    res = {'thumb': thumb.tolist()}
    for n, l in zip(['index', 'middle', 'ring', 'pinky'], lines):
        res[n] = l.tolist()
    out[side] = res
    print('FINGERFIT', side, 'split at depth cm', round(cut * 100, 1), {n: round(float(np.linalg.norm(np.diff(np.array(v), axis=0), axis=1).sum()) * 100, 1) for n, v in res.items()})
json.dump(out, open(os.path.join(HERE, 'work', 'fingers_fit.json'), 'w'))
