"""Diagnose the rigged mesh for PartUV: per part the connected pieces, degenerate (near zero area) faces, coincident
vertices inside a face, non-manifold and boundary edges; and, if the blend has UVs, the islands under 8 triangles per
part with their surface share. Usage: diag_mesh.py <blend in work/> [object]"""
import bpy, bmesh, os, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0] if a else 'rig_v1.blend'))
ob = bpy.data.objects[a[1] if len(a) > 1 else 'Dillo']
me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
pl = bm.faces.layers.int.get('part')
part = [f[pl] for f in bm.faces]
area = [f.calc_area() for f in bm.faces]
tot = sum(area)
stats = defaultdict(lambda: defaultdict(float))
for f in bm.faces:
    p = part[f.index]
    stats[p]['faces'] += 1; stats[p]['area_pct'] += 100 * area[f.index] / tot
    if area[f.index] < 1e-9: stats[p]['degenerate'] += 1
    vs = [v.co for v in f.verts]
    if min((vs[i] - vs[(i + 1) % len(vs)]).length for i in range(len(vs))) < 1e-5: stats[p]['short_edge'] += 1
for e in bm.edges:
    n = len(e.link_faces)
    if not n: continue
    p = part[e.link_faces[0].index]
    if n == 1: stats[p]['boundary_edges'] += 1
    elif n > 2: stats[p]['nonmanifold_edges'] += 1
# pieces per part
seen = set()
for f in bm.faces:
    if f.index in seen: continue
    st = [f]; seen.add(f.index); n = 0
    while st:
        x = st.pop(); n += 1
        for e in x.edges:
            for g in e.link_faces:
                if g.index not in seen: seen.add(g.index); st.append(g)
    stats[part[f.index]]['pieces'] += 1
for p in sorted(stats):
    print('PART', p, {k: round(v, 3) for k, v in stats[p].items()})
uv = bm.loops.layers.uv.active
if uv:
    # UV islands by shared UV coordinates across edges
    parent = list(range(len(bm.faces)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) != 2: continue
        f, g = lf
        def uvs(face):
            return {l.vert.index: tuple(round(c, 6) for c in l[uv].uv) for l in face.loops}
        uf, ug = uvs(f), uvs(g)
        if all(uf[v.index] == ug[v.index] for v in e.verts):
            parent[find(f.index)] = find(g.index)
    isl = defaultdict(list)
    for f in bm.faces: isl[find(f.index)].append(f.index)
    frag = defaultdict(float); fragn = defaultdict(int)
    for k, fs in isl.items():
        if len(fs) < 8:
            p = part[fs[0]]; frag[p] += 100 * sum(area[i] for i in fs) / tot; fragn[p] += 1
    print('ISLANDS', len(isl), 'FRAGMENTS by part', {p: (fragn[p], round(frag[p], 2)) for p in sorted(frag)})
