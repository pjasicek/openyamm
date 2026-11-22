"""Signed volume of every connected piece of the Guard mesh (negative = inward normals) and open edges."""
import bpy, bmesh, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, a[0] if a else 'work/rig_v1.blend'))
me = bpy.data.objects['Guard'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bl = bm.faces.layers.int['bone']; pl = bm.faces.layers.int['part']
seen = set(); neg = 0; tot = 0
for f in bm.faces:
    if f.index in seen: continue
    comp = [f]; seen.add(f.index); st = [f]
    while st:
        x = st.pop()
        for e in x.edges:
            for g in e.link_faces:
                if g.index not in seen: seen.add(g.index); comp.append(g); st.append(g)
    vol = 0.0
    for g in comp:
        vs = [v.co for v in g.verts]
        for i in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6
    opn = sum(1 for g in comp for e in g.edges if len(e.link_faces) == 1)
    tot += 1
    if vol < 0 or opn:
        neg += vol < 0
        print('PIECE bone', f[bl], 'part', f[pl], 'faces', len(comp), 'vol', round(vol, 5), 'open', opn)
print('PIECES', tot, 'negative', neg)
