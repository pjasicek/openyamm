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
SKIN = PV == 0                                            # bracer/spike shells near the wrist are not hand pieces
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
NPIECES = 4                                                   # three fingers plus thumb, measured on both Gog hands


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
    hand = SKIN & (np.linalg.norm(co - wr, axis=1) < 0.3) & (co[:,2] < wr[2]) & (np.sign(co[:, 0]) == np.sign(wr[0]))
    connected = max(components(hand), key=len)
    hand[:] = False; hand[connected] = True
    # Geodesic depth follows the bent claws; a plane can lose a raised digit before the others separate.
    import heapq
    ids=set(connected.tolist())
    adj={i:[] for i in ids}
    for a,b in E:
        if a in ids and b in ids:
            length=float(np.linalg.norm(co[a]-co[b]))
            adj[a].append((b,length));adj[b].append((a,length))
    dep=np.full(len(co),np.inf)
    seeds=sorted(ids,key=lambda i:np.linalg.norm(co[i]-wr))[:8]
    heap=[]
    for i in seeds:
        dep[i]=0;heapq.heappush(heap,(0,i))
    while heap:
        dist,i=heapq.heappop(heap)
        if dist>dep[i]: continue
        for j,length in adj[i]:
            if dist+length<dep[j]:
                dep[j]=dist+length;heapq.heappush(heap,(dep[j],j))
    levels=[]
    for cut in np.arange(0,float(dep[connected].max()),0.0025):
        cs_=[c for c in components(hand & (dep>cut)) if len(c)>=6]
        if not cs_: break
        levels.append(cs_)
    owner=[{int(v):i for i,c in enumerate(cs_) for v in c} for cs_ in levels]
    kids=[[[j for j,c in enumerate(levels[k+1]) if owner[k].get(int(c[0]))==i]
           for i in range(len(levels[k]))] for k in range(len(levels)-1)]+[[[] for _ in levels[-1]]]
    memo={}
    def is_chain(k,i):
        if (k,i) not in memo:
            ch=kids[k][i]
            memo[k,i]=len(ch)<=1 and (not ch or is_chain(k+1,ch[0]))
        return memo[k,i]
    parent=lambda k,i:next((j for j,ch in enumerate(kids[k-1]) if i in ch),None) if k else None
    comps=[levels[k][i] for k in range(len(levels)) for i in range(len(levels[k]))
           if is_chain(k,i) and len(levels[k][i])>=12 and
           (k==0 or parent(k,i) is None or not is_chain(k-1,parent(k,i)))]
    print('DIGIT_COMPONENTS',side,[(len(c),round(float(dep[c].min()),3),co[c].mean(0).round(3).tolist()) for c in comps])
    assert len(comps)==4,(side,len(comps))
    def geo_line(c):
        ds=dep[c]; lo,hi=ds.min(),ds.max()
        pts=[]
        for t in np.linspace(lo,hi,12):
            selected=c[np.abs(ds-t)<max((hi-lo)/10,0.004)]
            pts.append(co[selected].mean(0) if len(selected) else co[c[np.argmin(abs(ds-t))]])
        pts=np.array(pts)
        for _ in range(2):
            pts[1:-1]=(pts[:-2]+2*pts[1:-1]+pts[2:])/4
        direction=pts[2]-pts[0]
        direction/=max(np.linalg.norm(direction),1e-9)
        pts[0]-=direction*0.022
        return pts
    # On these open, bent hands the raised opposed thumb is the highest branch.
    small=max(comps,key=lambda c:co[c,2].mean())
    thumb=geo_line(small);tcen=thumb[0]
    pairs=sorted(((geo_line(c),c) for c in comps if c is not small),key=lambda lc:np.linalg.norm(lc[0][0]-tcen))
    lines=[l for l,_ in pairs];pieces=[c for _,c in pairs]
    cut=float(dep[small].min())
    res = {'thumb': thumb.tolist()}
    for n, l in zip(['index', 'middle', 'pinky'], lines):
        res[n] = l.tolist()
    # the separated pieces themselves (vertex indices of the step1/rig_v1..v4f topology): finger_weights.py assigns
    # every vertex of a piece to that finger (distance to the nearest chain left claw tips and knuckle skin on the hand
    # bone: up to 41x stretch in the fist, gob2 review 1)
    res['verts'] = {'thumb': [int(i) for i in small]}
    for n, c in zip(['index', 'middle', 'pinky'], pieces):
        res['verts'][n] = [int(i) for i in c]
    res['geodesic_depth']={str(int(i)):float(dep[i]) for i in connected}
    out[side] = res
    print('FINGERFIT', side, 'split at depth cm', round(cut * 100, 1), {n: round(float(np.linalg.norm(np.diff(np.array(v), axis=0), axis=1).sum()) * 100, 1) for n, v in res.items() if n not in ('verts','geodesic_depth')}, 'piece verts', {n: len(v) for n, v in res['verts'].items()})
assert set(out)=={'L','R'}
json.dump(out, open(os.path.join(HERE, 'work', 'fingers_fit.json'), 'w'))
