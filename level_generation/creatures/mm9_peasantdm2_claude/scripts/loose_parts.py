"""List (and optionally delete) loose parts of 'Body'. Args: <in blend> [out blend max_verts max_size_m]
Deletes parts with <= max_verts vertices AND bounding diagonal <= max_size_m (stray Meshy fragments), keeps the rest."""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); parts = []
for v in bm.verts:
    if v.index in seen:
        continue
    stack = [v]; comp = []
    seen.add(v.index)
    while stack:
        a = stack.pop(); comp.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen:
                seen.add(b.index); stack.append(b)
    parts.append(comp)
dele = []
for comp in sorted(parts, key=lambda c: -len(c)):
    xs = [body.matrix_world @ a.co for a in comp]
    lo = [min(p[i] for p in xs) for i in range(3)]; hi = [max(p[i] for p in xs) for i in range(3)]
    diag = sum((hi[i] - lo[i]) ** 2 for i in range(3)) ** 0.5
    c = [round((hi[i] + lo[i]) / 2, 3) for i in range(3)]
    print('PART', len(comp), 'diag', round(diag, 4), 'centre', c)
    if len(argv) > 1 and len(comp) <= int(argv[2]) and diag <= float(argv[3]):
        dele += comp
if len(argv) > 1:
    print('DROPPED verts', len(dele))
    bmesh.ops.delete(bm, geom=dele, context='VERTS'); bm.to_mesh(me); me.update()
    bpy.ops.wm.save_as_mainfile(filepath=argv[1])
