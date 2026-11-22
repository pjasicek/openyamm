"""Clay views of selected piece groups of work/clean_v1.blend (pieces sorted by vertex count as prep.py lists them).
Prints per group: vertices, triangles, boundary edges. Usage: piece_views.py <name>=<spec> ...
spec: comma list of piece indices or ranges a-b ('14-' = 14 to the end)."""
import bpy, bmesh, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
src = bpy.data.objects['Dillo']
bm0 = bmesh.new(); bm0.from_mesh(src.data); bm0.verts.ensure_lookup_table()
label = [-1] * len(bm0.verts); pieces = []
for v in bm0.verts:
    if label[v.index] >= 0: continue
    st = [v]; label[v.index] = len(pieces); idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0: label[w.index] = label[v.index]; st.append(w)
    pieces.append(idx)
order = sorted(range(len(pieces)), key=lambda i: -len(pieces[i]))
rank = {p: r for r, p in enumerate(order)}
n = len(pieces)


def parse(spec):
    out = set()
    for part in spec.split(','):
        if '-' in part:
            a, b = part.split('-'); out |= set(range(int(a), int(b) + 1 if b else n))
        else:
            out.add(int(part))
    return out


for arg in args:
    name, spec = arg.split('=')
    want = parse(spec)
    src.name = 'DilloSrc'
    bm = src.data.copy(); ob = bpy.data.objects.new('Dillo', bm)
    b = bmesh.new(); b.from_mesh(bm); b.verts.ensure_lookup_table()
    bmesh.ops.delete(b, geom=[v for v in b.verts if rank[label[v.index]] not in want], context='VERTS')
    bnd = sum(1 for e in b.edges if e.is_boundary); tris = sum(len(f.verts) - 2 for f in b.faces)
    print(f'GROUP {name} verts {len(b.verts)} tris {tris} boundary_edges {bnd}')
    b.to_mesh(bm)
    bpy.context.scene.collection.objects.link(ob)
    for view, (loc, tgt) in {'quarter': ((-2.2, -2.6, 1.6), (0, 0, 0.3)), 'side': ((3, 0, 0.35), (0, 0, 0.35)),
                             'top': ((0, 0, 3), (0, 0, 0)), 'back': ((0, 3, 0.4), (0, 0, 0.35))}.items():
        C.render(loc, tgt, 1.8, os.path.join(HERE, 'review', f'piece_{name}_{view}.png'), res=(600, 480), floor=False)
    bpy.data.objects.remove(ob, do_unlink=True); src.name = 'Dillo'
