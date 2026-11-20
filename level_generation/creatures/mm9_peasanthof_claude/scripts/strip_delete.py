"""HOF1: delete the head shell's neck-strip faces at the nape sides (user review r7, 2026-11-04; the "pale wedge" beside the jaw corner:
faces 9940/9941 of the r7 export, a ray pick: head shell 7 cm behind the neck centre, 1.64-1.66 m, |x| 7 cm, lit side-on). Behind them
the body's own neck/collar surface already closes the view (the pick's next hit is the body at 1.665 m), so they are covering faces,
not the only surface. Skin-shell faces (the head component holding the nose) whose vertices ALL lie below YTOP (export height), behind
ZB (export z) and further than XMIN from the centre plane (nose tip x) are deleted; no vertex moves, the jaw is untouched.
Args: <in blend> <out blend> [ytop 1.664] [zb -0.045] [xmin 0.055] [export head y 1.697]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
YTOP = float(a[2]) if len(a) > 2 else 1.664; ZB = float(a[3]) if len(a) > 3 else -0.045
XMIN = float(a[4]) if len(a) > 4 else 0.055; HEADY = float(a[5]) if len(a) > 5 else 1.697
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent; mw = ob.matrix_world
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
hb = next(b for b in rig.pose.bones if b.name.endswith('Head')); off = HEADY - (rig.matrix_world @ hb.head).z
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
hv = {v.index for f in bm.faces if f[lh] and not f[lk] for v in f.verts}
W = {i: mw @ bm.verts[i].co for i in hv}
fr = [i for i in hv if 1.70 - off < W[i].z < 1.78 - off]
nose = min(fr, key=lambda i: W[i].y)
comp = {nose}; st = [bm.verts[nose]]
while st:
    v = st.pop()
    for e in v.link_edges:
        o = e.other_vert(v)
        if o.index in hv and o.index not in comp: comp.add(o.index); st.append(o)
cx = W[nose].x; zt = YTOP - off
def ok(i): p = W[i]; return p.z < zt and -p.y < ZB and abs(p.x - cx) > XMIN
dead = [f for f in bm.faces if f[lh] and not f[lk] and all(v.index in comp and ok(v.index) for v in f.verts)]
cents = [tuple(round(c, 3) for c in (mw @ f.calc_center_median())) for f in dead]
bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
bm.to_mesh(ob.data); bm.free(); ob.data.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('STRIPDELETE faces', len(dead), 'centres (master)', cents)
