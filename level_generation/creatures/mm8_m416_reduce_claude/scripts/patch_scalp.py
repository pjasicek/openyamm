"""Close the open top of the head skin (MM8 Pirate Crossbowman; copied from the sibling Pirate Warrior,
../mm8_m412_reduce_claude/scripts/patch_scalp.py, where the opening's rim showed below the bandanna at the right
temple). Here the skin piece is open under the bandanna and hair (a 48-edge boundary loop, z 1.64-1.77 m); the
installed model shows no gap, but the cut moves both rims, so the opening is capped first. The loop gets a fan cap
around its rest-pose centroid, wound against the rim faces, weights averaged from the rim (all B_Head), every corner
at one hair-brown texel of the body set (the cap is hidden under the bandanna and hair). The new faces are appended after the source faces, so per-face
masks keep their indices. Usage: blender -b -P patch_scalp.py  (work/source_unpatched.blend -> work/source.blend)"""
import os, bpy, bmesh
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source_unpatched.blend'))
o = bpy.data.objects['Body']; me = o.data
UV = (0.4010, 0.0540)  # hair face 7466, brown (127, 74, 40)
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
# the skin's opening: the longest loop of head-set (u > 0.5) faces above 1.6 m; the bandanna, hair and eye loops
# beside it are body-set or small pieces and stay open
headset = lambda c: all(l[uvl].uv[0] > .5 for v in c for f in v.link_faces for l in f.loops)
print('LOOPS head', [(len(c), headset(c), tuple(round(x, 3) for x in sum((v.co for v in c), Vector()) / len(c))) for c in loops if sum(v.co.z for v in c) / len(c) > 1.45])
caps = [max((c for c in loops if sum(v.co.z for v in c) / len(c) > 1.6 and headset(c)), key=len)]
assert [len(c) for c in caps] == [48], [len(c) for c in caps]
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
