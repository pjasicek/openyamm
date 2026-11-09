"""Drop the micro loose parts of the body set (mm9_sven, 2026-11-02): Meshy's belt studs are separate 1-4 triangle pieces
that lifted up to 5 mm off the belt in some poses (detached_parts_audit.py) and are micro triangles by the modelling
guidelines; the belt's paint already carries its silver studs. Loose parts with at most MAXV vertices and no head/hand
faces are deleted. Args (Blender): -- <in blend> <out blend> [maxv 4]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; MAXV = int(a[2]) if len(a) > 2 else 4
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
seen, drop, sizes = set(), [], []
for v in bm.verts:
    if v in seen:
        continue
    part, st = {v}, [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in part:
                part.add(y); st.append(y)
    seen |= part
    faces = {f for p in part for f in p.link_faces}
    if len(part) <= MAXV and not any(f[lh] or f[lk] for f in faces):
        drop += list(part); sizes.append(len(faces))
bmesh.ops.delete(bm, geom=drop, context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('DROP_MICRO', {'parts': len(sizes), 'faces': sizes})
