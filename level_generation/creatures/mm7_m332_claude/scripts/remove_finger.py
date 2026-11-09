"""m190: Smart Topology modelled six digits per hand (thumb + five fingers; the HD master has four fingers). Removes the
extra outermost finger on each hand shell (P04 left, P05 right): along the forearm direction (work/joints_final.json,
elbow -> wrist), the most posterior (+Y, behind the palm) finger component at the depth where it first separates from
its neighbours is cut 4 mm below that depth, its open ring is capped and the cap's ring smoothed into the knuckle.
Leaves index 17.9 / middle 19.5 / ring 18.5 / pinky 16.9 cm (the removed one was the shortest, 14.5 cm).
Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))['joints']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl = bm.verts.layers.int['piece']
for side, piece in (('L', 2), ('R', 3)):   # m332: hand shells P02 (L) / P03 (R)
    wr = np.array(J[f'{side}_Hand']); fa = np.array(J[f'{side}_Forearm']); d = (wr - fa) / np.linalg.norm(wr - fa)
    hv = [v for v in bm.verts if v[pl] == piece]
    dep = {v: float((np.array(v.co) - wr) @ d) for v in hv}

    def comps(cut):
        s = {v for v in hv if dep[v] > cut}; seen, res = set(), []
        for v in s:
            if v in seen:
                continue
            st, c = [v], []
            while st:
                x = st.pop()
                if x in seen:
                    continue
                seen.add(x); c.append(x); st.extend(e.other_vert(x) for e in x.link_edges if e.other_vert(x) in s)
            if len(c) >= 8:
                res.append(c)
        return res
    sep = back = None
    for cut in np.arange(0.06, 0.2, 0.0025):
        cs = comps(cut)
        cand = [c for c in cs if len(c) < int(os.environ.get('MAXV', '100')) and np.mean([v.co.y for v in c]) - wr[1] > 0.01]   # a small piece behind the palm
        if cand:
            sep = cut; back = max(cand, key=lambda c: np.mean([v.co.y for v in c])); break
    ys = [np.mean([v.co.y for v in c]) for c in comps(sep + 0.015)]          # all fingers apart 1.5 cm deeper
    ys = sorted(ys)
    # grow the finger back below the separation depth: vertices within 4 mm under it that connect to the piece and lie
    # on the posterior side of the gap to the next finger
    cut = sep - 0.004
    yb = np.mean([v.co.y for v in back]); ynext = ys[-2]
    kill = set(back)
    front = list(back)
    while front:
        x = front.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y in kill or y[pl] != piece or dep.get(y, -1) <= cut:
                continue
            if y.co.y > (yb + ynext) / 2:
                kill.add(y); front.append(y)
    ring_before = {e.other_vert(v) for v in kill for e in v.link_edges if e.other_vert(v) not in kill}
    bmesh.ops.delete(bm, geom=list(kill), context='VERTS')
    bnd = [e for e in bm.edges if e.is_boundary and all(v in ring_before for v in e.verts)]
    f = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    capv = list({v for e in bnd for v in e.verts})
    fill_faces = f['faces']
    bmesh.ops.triangulate(bm, faces=fill_faces)
    # round the cap: pull the ring slightly outward along the finger axis and relax it with its neighbours
    for _ in range(4):
        new = {}
        for v in capv:
            nb = [e.other_vert(v).co for e in v.link_edges]
            new[v] = v.co * 0.5 + sum(nb, v.co * 0) / len(nb) * 0.5
        for v, c in new.items():
            v.co = c
    print('FINGERCUT', side, 'separation depth cm', round(sep * 100, 1), 'removed verts', len(kill), 'cap ring', len(capv),
          'finger y cm', round(yb * 100, 1), 'next', round(ynext * 100, 1))
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[bm.faces.layers.int.get('piece')] in (2, 3)] if bm.faces.layers.int.get('piece') else [])
bm.to_mesh(me); bm.free()
print('FINGERCUT tris now', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
