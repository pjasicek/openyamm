"""Close small holes in the Tunic (skin showed through at the collar points); UVs copied from neighbours."""
import bpy, bmesh, json
m = bpy.data.objects['Peasant']; PARTS = json.loads(bpy.context.scene['pfem_parts'])
bm = bmesh.new(); bm.from_mesh(m.data); bm.faces.ensure_lookup_table()
pl = bm.faces.layers.int.get('part'); uvl = bm.loops.layers.uv.active
T = PARTS.index('Tunic')
edges = [e for e in bm.edges if e.is_boundary and e.link_faces[0][pl] == T]
filled = bmesh.ops.holes_fill(bm, edges=edges, sides=12)['faces']
for f in filled:
    f[pl] = T
    for l in f.loops:
        others = [o for o in l.vert.link_loops if o.face not in filled]
        if others and uvl is not None:
            l[uvl].uv = others[0][uvl].uv.copy()
bmesh.ops.recalc_face_normals(bm, faces=filled)
bm.to_mesh(m.data); bm.free()
print('TUNIC holes filled', len(filled))
bpy.ops.wm.save_mainfile()
