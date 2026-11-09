"""Close the open top of the head skin (MM8 Pirate): the skin piece is open under the bandanna (a 68-edge boundary loop). At the right temple the opening's rim lies below the bandanna's lower edge, so the bandanna's inside
(and at some angles the background) shows through a wedge above and in front of the right ear, plus a sliver at the
eye corner; the installed model has it. The loop gets a fan cap around its rest-pose centroid, wound against the rim
faces, weights averaged from the rim (all B_Head), every corner at one dark hairline texel of the head set (the cap is
hidden under the bandanna except through that wedge). The new faces are appended after the source faces, so per-face
masks keep their indices. Usage: blender -b -P patch_scalp.py  (work/source_unpatched.blend -> work/source.blend)"""
import os, bpy, bmesh
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source_unpatched.blend'))
o = bpy.data.objects['Body']; me = o.data
UV = (0.5691, 0.1276)  # face 8766, hairline brown (128, 91, 63)
bm = bmesh.new(); bm.from_mesh(me); dl = bm.verts.layers.deform.active; uvl = bm.loops.layers.uv.active
n_faces = len(bm.faces)
edges = [e for e in bm.edges if e.is_boundary]
nxt = {}
for e in edges:
    l = e.link_loops[0]; nxt[l.vert] = (l.link_loop_next.vert, e)   # rim face winding a -> b
loops, seen = [], set()
for a in list(nxt):
    if a in seen:
        continue
    cyc, v = [], a
    while v not in seen and v in nxt:
        seen.add(v); cyc.append(v); v = nxt[v][0]
    if v is a:
        loops.append(cyc)
# the skin's opening is the longest head loop (68 edges); the 43-edge loop is the bandanna's own lower rim: never cap it
caps = [max((c for c in loops if sum(v.co.z for v in c) / len(c) > 1.5), key=len)]
print('LOOPS head', [(len(c), tuple(round(x, 3) for x in sum((v.co for v in c), Vector()) / len(c))) for c in loops if sum(v.co.z for v in c) / len(c) > 1.45])
assert [len(c) for c in caps] == [68], [len(c) for c in caps]
for cyc in caps:
    ctr = bm.verts.new(sum((v.co for v in cyc), Vector()) / len(cyc))
    acc = {}
    for v in cyc:
        for gi, w in v[dl].items():
            acc[gi] = acc.get(gi, 0) + w / len(cyc)
    tot = sum(acc.values())
    for gi, w in acc.items():
        ctr[dl][gi] = w / tot
    for a in cyc:
        b = nxt[a][0]
        f = bm.faces.new((b, a, ctr))
        for l in f.loops:
            l[uvl].uv = UV
bm.normal_update()
print('CAPPED', len(bm.faces) - n_faces, 'faces; open edges', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
