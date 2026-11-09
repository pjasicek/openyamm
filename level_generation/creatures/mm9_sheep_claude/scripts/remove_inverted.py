"""Delete the connected parts of 'Body' with a negative signed volume (inside-out bubbles the voxel remesh leaves in
closed cavities) and small stray fragments away from the head and paws (a flat 6-triangle chip under the chest; the
teeth, eyes and claws are in the head or at the paws). The other faces keep their UVs, weights and attributes.
Args: <in blend> <out blend>"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
seen, removed, doomed = set(), [], []
for f in bm.faces:
    if f.index in seen:
        continue
    comp, st = [], [f]; seen.add(f.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.edges:
            for y in e.link_faces:
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
    vol = 0.0
    for x in comp:
        vs = [v.co for v in x.verts]
        for i in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
    c = sum((v.co for x in comp for v in x.verts), comp[0].verts[0].co * 0) / sum(len(x.verts) for x in comp)
    stray = len(comp) < 20 and c.y > -1.2 and c.z > 0.3
    if vol < 0 or stray:
        removed.append((len(comp), round(vol, 6), [round(x, 3) for x in c]))
        doomed += comp
bmesh.ops.delete(bm, geom=doomed, context='FACES')   # after the walk: deleting while iterating skips parts
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.to_mesh(ob.data)
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
print('REMOVED', removed, 'faces now', len(ob.data.polygons))
