"""Winding check of the single foot: per connected piece the signed volume and the share of faces whose normal points
toward the piece's centre-line (inward). Args: -- <blend in work/> <object> [fix]"""
import bpy, bmesh, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
ob = bpy.data.objects[a[1]]
bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
seen = set(); pieces = []
for f in bm.faces:
    if f.index in seen: continue
    st = [f]; seen.add(f.index); comp = []
    while st:
        x = st.pop(); comp.append(x)
        for e in x.edges:
            for g in e.link_faces:
                if g.index not in seen: seen.add(g.index); st.append(g)
    pieces.append(comp)
for i, comp in enumerate(pieces):
    vol = sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co)) for f in comp) / 6
    boundary = sum(1 for f in comp for e in f.edges if len(e.link_faces) == 1)
    nonman = sum(1 for f in comp for e in f.edges if len(e.link_faces) > 2)
    print(f'PIECE {i} faces {len(comp)} volume {vol * 1e6:+.1f} cm3 boundary_edges {boundary} nonmanifold {nonman}')
if len(a) > 2 and a[2] == 'fix':
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
    print('FIXED normals recalculated')
