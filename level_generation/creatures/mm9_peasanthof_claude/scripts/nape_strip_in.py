"""REVERTED in r8 (2026-11-04): the fixed pull also pinched the jaw corner (user: "deformed right part of the face"); use strip_mirror_in.py.
HOF1: the pale wedge beside the jaw in front views (coordinator pre-screen of r6, 2026-11-04) is the head shell's lowest strip at
the nape sides (export height 1.645-1.665 m, 7 cm behind the neck centre, |x| 7.5-8 cm): it stands out sideways past the neck and
jaw silhouette and faces the key light. Skin-shell vertices (the head component holding the chin) below YTOP and behind the neck
centre (master y > YB, the creature faces -y) move toward the centre line in x by up to K (|x| -> |x| * (1 - K * e), e eased over 1.5 cm
below YTOP and over 2 cm behind YB), so the strip sits inside the jaw/neck silhouette. Positions only; the face front is not touched.
Args: <in blend> <out blend> [ytop 1.668] [yb 0.02] [k 0.22] [export head y 1.697]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
YTOP = float(a[2]) if len(a) > 2 else 1.668; YB = float(a[3]) if len(a) > 3 else 0.02
K = float(a[4]) if len(a) > 4 else 0.22; HEADY = float(a[5]) if len(a) > 5 else 1.697
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent; mw = ob.matrix_world; mwi = mw.inverted()
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
hb = next(b for b in rig.pose.bones if b.name.endswith('Head')); hz = (rig.matrix_world @ hb.head).z; off = HEADY - hz
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
hv = {v.index for f in bm.faces if f[lh] and not f[lk] for v in f.verts}
W = {i: mw @ bm.verts[i].co for i in hv}
seed = min(hv, key=lambda i: W[i].y + 10 * abs(W[i].z - (hz - 0.06)) + 10 * abs(W[i].x))
comp = {seed}; st = [bm.verts[seed]]
while st:
    v = st.pop()
    for e in v.link_edges:
        o = e.other_vert(v)
        if o.index in hv and o.index not in comp: comp.add(o.index); st.append(o)
zt = YTOP - off; n = 0; mx = 0.0
def ss(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
for i in comp:
    p = W[i]
    e = ss((zt - p.z) / 0.015) * ss((p.y - YB) / 0.02)
    if e <= 0: continue
    q = Vector((p.x * (1 - K * e), p.y, p.z)); mx = max(mx, abs(p.x - q.x))
    bm.verts[i].co = mwi @ q; n += 1
bm.to_mesh(ob.data); bm.free(); ob.data.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('NAPESTRIP shell verts', len(comp), 'moved', n, 'max', round(mx * 1000, 1), 'mm')
