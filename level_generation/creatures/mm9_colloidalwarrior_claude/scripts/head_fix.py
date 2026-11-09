"""Close every remaining hole of the head shell with a centroid fan (pinched or non-planar loops too), drop the eye pieces
(the eyes are the shell's almond recesses, painted). Args: <in blend> <out blend>"""
import bpy, bmesh, sys
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
import os
if 'Eyes' in bpy.data.objects and os.environ.get('DROP_EYES'): bpy.data.objects.remove(bpy.data.objects['Eyes'])
f = bpy.data.objects['Face']
bm = bmesh.new(); bm.from_mesh(f.data)
for rnd in range(3):
    bd = [e for e in bm.edges if e.is_boundary]
    if not bd: break
    # boundary components by shared vertices
    left = set(bd); comps = []
    while left:
        e0 = left.pop(); st = [e0]; cc = [e0]
        while st:
            e = st.pop()
            for v in e.verts:
                for e2 in v.link_edges:
                    if e2 in left: left.discard(e2); st.append(e2); cc.append(e2)
        comps.append(cc)
    print('HOLES', rnd, len(comps), sorted((len(c) for c in comps), reverse=True)[:20])
    for cc in comps:
        vs = {v for e in cc for v in e.verts}
        c = sum((v.co for v in vs), Vector()) / len(vs)
        cv = bm.verts.new(c)
        for e in cc:
            # orient each fan triangle against the face already on the edge
            fa = e.link_faces[0]; a, b = e.verts
            loop = next(l for l in fa.loops if l.edge == e)
            if loop.vert == a: a, b = b, a
            try: bm.faces.new((a, b, cv))
            except ValueError: pass
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
print('FIXED boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonman', sum(1 for e in bm.edges if not e.is_manifold))
bm.to_mesh(f.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
