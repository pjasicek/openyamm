"""Skin-weight outliers in the hands of work/source.blend: vertices whose dominant bone carries less than 0.25 total
weight (REA_LIMIT, default 0.25; 0.15 applied) among their edge neighbours (a lone vertex on another finger bone pokes out as a spike once the fingers curl:
the left thumb tip and index tip). REA_FIX=1 sets each outlier's weights to the mean of its neighbours (two passes)
and saves work/source.blend. Positions and faces are unchanged."""
import os, bpy, bmesh
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
o = bpy.data.objects['Body']; me = o.data; names = {g.index: g.name for g in o.vertex_groups}
hand = {i for i, n in names.items() if any(k in n for k in ('_Hand', '_Finger'))}
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
W = [{g.group: g.weight for g in v.groups if names[g.group] != 'ReduceProtect'} for v in me.vertices]
fix = os.environ.get('REA_FIX'); LIMIT = float(os.environ.get('REA_LIMIT', '.25'))
for p in range(2 if fix else 1):
    out = []
    for v in bm.verts:
        w = W[v.index]
        if not w: continue
        dom = max(w, key=w.get)
        if dom not in hand: continue
        nbs = [e.other_vert(v).index for e in v.link_edges]
        share = sum(W[n].get(dom, 0) for n in nbs) / max(len(nbs), 1)
        if share < LIMIT: out.append((v.index, names[dom], round(share, 2)))
    print('PASS', p, 'OUTLIERS', len(out)); [print('  ', *x) for x in out]
    if not fix: break
    for i, _, _ in out:
        nbs = [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges]; acc = {}
        for n in nbs:
            for g, x in W[n].items(): acc[g] = acc.get(g, 0) + x / len(nbs)
        tot = sum(acc.values()); W[i] = {g: x / tot for g, x in acc.items()}
        for g in list(o.vertex_groups):
            if g.name != 'ReduceProtect': g.remove([i])
        for g, x in W[i].items(): o.vertex_groups[g].add([i], x, 'REPLACE')
if fix: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
