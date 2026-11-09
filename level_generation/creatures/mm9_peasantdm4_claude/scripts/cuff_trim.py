"""Trim the body's toothed cuff remnant over the grafted hands (2026-11-02). graft_hands.py cut the old hand away along
the hand-weight border, so body faces reach 0-5 cm past the hand joint in a toothed rim lying on the MPFB hand; in bent
wrists the teeth stood off the hand as shards, and sleeve_tuck.py (made for real sleeves) took them for a sleeve and
shrank the hand's wrist under them by up to 5 cm. Here body faces (no `head`/`hand` attribute) near the wrist are bisected by the plane s = S_CUT along the forearm -> hand axis
(from the hand joint; a clean ring instead of the toothed one) and the part past it is deleted: the hand's own stub,
conformed by graft_hands.py to the original opening, forms the wrist from there. UVs, weights and attributes of the
remaining faces are unchanged (the paid paints stay valid). Args: -- <in blend> <out blend> [s_cut 0.0] [L=..,R=.. per-side s_cut]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
S_CUT0 = float(a[2]) if len(a) > 2 else 0.0
# PeasantDM4: per-side cuts, e.g. L=-0.015 (a toothed sleeve flap hung below the left wrist before the 1 cm plane)
SIDE_CUT = dict((kv.split('=')[0], float(kv.split('=')[1])) for kv in a[3].split(',')) if len(a) > 3 else {}
RAD = 0.09
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
CO = np.array([tuple(mw @ v.co) for v in bm.verts])
rep = {}
for tok in ('L', 'R'):
    S_CUT = SIDE_CUT.get(tok, S_CUT0)
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    axis = (a1 - a0) / np.linalg.norm(a1 - a0)
    # body faces of this wrist: no head/hand attribute, centroid within RAD of the axis and past S_CUT - 0.04
    near = lambda f: (lambda c: abs((c - a1) @ axis - S_CUT) < 0.06 and np.linalg.norm(c - a1 - ((c - a1) @ axis) * axis) < RAD
                      and np.sign(c[0]) == np.sign(a1[0]))(np.array(tuple(mw @ f.calc_center_median())))
    faces = [f for f in bm.faces if not f[lh] and not f[lk] and near(f)]
    # a clean ring: bisect those faces with the plane s = S_CUT (bmesh interpolates UVs and weights on the new
    # vertices), then delete the body faces past it
    Mi = np.array(mw.inverted())
    co = Mi[:3, :3] @ (a1 + S_CUT * axis) + Mi[:3, 3]
    no = Mi[:3, :3] @ axis
    geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co.tolist(), plane_no=no.tolist(), clear_outer=False, clear_inner=False)
    bm.faces.ensure_lookup_table()
    past = [f for f in bm.faces if not f[lh] and not f[lk]
            and (np.array(tuple(mw @ f.calc_center_median())) - a1) @ axis > S_CUT + 1e-5
            and np.linalg.norm((lambda c: c - a1 - ((c - a1) @ axis) * axis)(np.array(tuple(mw @ f.calc_center_median())))) < RAD
            and np.sign(tuple(mw @ f.calc_center_median())[0]) == np.sign(a1[0])]
    bmesh.ops.delete(bm, geom=past, context='FACES')
    rep[tok] = len(past)
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CUFF_TRIM', json.dumps({'faces': rep, 'loose_verts': len(loose), 's_cut': S_CUT0, 'side_cut': SIDE_CUT}))
