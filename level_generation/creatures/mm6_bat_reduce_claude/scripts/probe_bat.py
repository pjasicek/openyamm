"""Bat candidate probe: boundary loops (size, perimeter, centre) and connected pieces (tris, centre, size)."""
import os, bpy, bmesh, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('PB_BLEND', 'ladder.blend')))
o = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_40')]
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
out = {}
for e in bm.edges:
    if e.is_boundary:
        f = e.link_faces[0]; l = next(l for l in f.loops if l.edge is e)
        out.setdefault(l.link_loop_next.vert, []).append(l.vert)
loops = []
while any(out.values()):
    st = next(v for v, lst in out.items() if lst); path = [st]
    while True:
        nxt = out[path[-1]].pop() if out.get(path[-1]) else None
        if nxt is None: break
        if nxt in path:
            i = path.index(nxt); loops.append(path[i:]); path = path[:i + 1]
            if not out.get(path[-1]): break
            continue
        path.append(nxt)
for lp in sorted(loops, key=len):
    c = np.mean([v.co[:] for v in lp], 0); per = sum((lp[i].co - lp[(i + 1) % len(lp)].co).length for i in range(len(lp)))
    print('LOOP', len(lp), 'perimeter_mm', round(per * 1000, 1), 'centre', np.round(c, 3).tolist())
comp = {}; seen = set()
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cv = []
    while st:
        x = st.pop(); cv.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    fs = {f for x in cv for f in x.link_faces}; co = np.array([x.co[:] for x in cv])
    print('PIECE tris', len(fs), 'centre', np.round(co.mean(0), 3).tolist(), 'size', np.round(np.ptp(co, 0), 3).tolist())
