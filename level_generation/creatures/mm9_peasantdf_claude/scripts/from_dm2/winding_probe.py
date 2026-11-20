"""Faces of 'Body' whose winding disagrees with a neighbour across a manifold edge (flipped Meshy faces), and an
optional fix: bmesh recalc_face_normals per connected part of the flagged faces' parts. Args: <blend> [out blend]"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bad = set()
for e in bm.edges:
    if len(e.link_faces) != 2:
        continue
    a, b = e.link_faces
    def dirn(f):
        for l in f.loops:
            if l.edge is e:
                return l.vert is e.verts[0]
    if dirn(a) == dirn(b):
        bad.add(a.index); bad.add(b.index)
pts = [tuple(round(x, 3) for x in bm.faces[i].calc_center_median()) for i in sorted(bad)]
print('INCONSISTENT', len(bad), pts[:20])
if len(argv) > 1 and bad:
    # flip the minority side: grow consistent regions from each bad face's part and recalc normals on those faces' parts
    seen = set(); parts = []
    for i in bad:
        if i in seen:
            continue
        stack = [bm.faces[i]]; comp = []
        seen.add(i)
        while stack:
            f = stack.pop(); comp.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index); stack.append(g)
        parts.append(comp)
    for comp in parts:
        bmesh.ops.recalc_face_normals(bm, faces=comp)
        print('RECALC part faces', len(comp))
    bm.to_mesh(me); me.update()
    bpy.ops.wm.save_as_mainfile(filepath=argv[1])
