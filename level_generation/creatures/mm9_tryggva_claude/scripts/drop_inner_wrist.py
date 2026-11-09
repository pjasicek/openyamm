"""Delete Meshy's leftover old-wrist skin inside the sleeves (mm9_tryggva, sleeve-poke gate 2026-11-02). graft_hands.py removed
the old hand past the cuff, but small body-material triangles of the old forearm stayed inside the right sleeve 5-9 mm from
the forearm axis; sleeve_poke_gate.py took them as the sleeve's outermost wall and reported the visible wrist (past the
jagged cuff) as 27 mm through the cloth. Per side: body faces (not hand, not head) whose vertices all lie within RIN of the
forearm->hand axis (rest pose) between half the forearm and SPAN past the hand joint are hidden inside the grafted
stub; they are deleted. Args (Blender): -- <in blend> <out blend> [rin 0.013] [rmax 0.02] [hrin 0: also faces with a hand-weighted vertex, centre within HRIN, past 0.8 of the forearm] [vmin 0: also faces with any vertex within VMIN of the axis (the sleeve's closure onto the old forearm)]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
RIN = float(a[2]) if len(a) > 2 else 0.013
SPAN = 0.05
RMAX = float(a[3]) if len(a) > 3 else 0.02
HRIN = float(a[4]) if len(a) > 4 else 0.0
VMIN = float(a[5]) if len(a) > 5 else 0.0
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
hand = np.zeros(len(me.polygons), np.int32); head = np.zeros(len(me.polygons), np.int32)
me.attributes['hand'].data.foreach_get('value', hand); me.attributes['head'].data.foreach_get('value', head)
mw = body.matrix_world
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
drop, rep = [], {}
for s in 'LR':
    fa = rig.matrix_world @ rig.data.bones[f'Bip01 {s} Forearm'].head_local
    hd = rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local
    a0, a1 = np.array(fa), np.array(hd); L = np.linalg.norm(a1 - a0); ax = (a1 - a0) / L
    t = (CO - a0) @ ax
    r = np.linalg.norm(np.cross(CO - a0, ax), axis=1)
    span = (t > 0.5 * L) & (t < L + SPAN)
    def deep(f):
        vi = [v.index for v in f.verts]
        c = CO[vi].mean(0)
        return span[vi].all() and np.linalg.norm(np.cross(c - a0, ax)) < RIN and r[vi].max() < RMAX
    gi = body.vertex_groups[f'Bip01 {s} Hand'].index
    handdom = np.array([max(v.groups, key=lambda g: g.weight).group == gi if len(v.groups) else False for v in me.vertices])
    def handbit(f):     # old-hand remnants on the body material at the wrist (weighted mostly to the hand joint)
        vi = [v.index for v in f.verts]
        c = CO[vi].mean(0)
        return handdom[vi].any() and np.linalg.norm(np.cross(c - a0, ax)) < HRIN and (c - a0) @ ax > 0.8 * L
    fs = [f for f in bm.faces if not hand[f.index] and not head[f.index] and (deep(f) or handbit(f) or (VMIN > 0 and span[[v.index for v in f.verts]].all() and r[[v.index for v in f.verts]].min() < VMIN))]
    rep[s + '_r_min_mm'] = round(float(r[span].min()) * 1000, 1) if span.any() else None
    drop += fs; rep[s] = len(fs)
bmesh.ops.delete(bm, geom=drop, context='FACES')
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('DROP_INNER_WRIST', json.dumps({'faces': rep, 'rin': RIN}))
