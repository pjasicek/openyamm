"""Cuff clean-up on the master (2026-11-01, Fidget hand close-ups: cream and salmon flaps round both wrists). After
the hand graft the sleeve end kept Meshy's crumpled inner lining ring (skin-painted faces inside the cuff, outside the
graft's 4.5 cm inner radius) and rim faces poking past the cuff.
Inward-facing old faces (normal against the radial direction) from 5 cm before the cuff are the turned-in lining too. On the textured master (the head UV layout is paid
for, so the graft is not re-run): per arm, every old body face (attributes hand = 0, head = 0) whose centroid lies past
(cuff - 1 cm) along the forearm axis within 6 cm of it (the lining), or with a vertex more than 1.2 cm past the cuff,
is deleted; then faces with two or more open edges within 4 cm of the cuff (sliver tips left by the cut) are deleted
twice; loose vertices go. Follow-up 2026-11-02: every old face whose centre is within TRIM (1.5 cm) of the cuff end
goes too (the flared rim showed as cream/salmon flaps), then the new rim is relaxed. Cuff positions from v2/work/hands_v1.json. Args (Blender): <in blend> <out blend> <hands json>"""
import bpy, bmesh, json, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
H = json.load(open(a[2]))
TRIM = float(a[3]) if len(a) > 3 else 0.015   # follow-up 2026-11-02: the outer 1.5 cm of the cuff (its flared rim) goes whole
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world
hand = np.zeros(len(me.polygons), np.int32); head = np.zeros(len(me.polygons), np.int32)
me.attributes['hand'].data.foreach_get('value', hand); me.attributes['head'].data.foreach_get('value', head)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
CO = np.array([tuple(mw @ v.co) for v in bm.verts])
bones = rig.data.bones
rep = {}
dele = set()
sides = {'L': ('Bip01 L Hand', 'Bip01 L Forearm'), 'R': ('Bip01 R Hand', 'Bip01 R Forearm')}
near = {}
for key, (hn, fn) in sides.items():
    W = np.array(rig.matrix_world @ bones[hn].head_local); E = np.array(rig.matrix_world @ bones[fn].head_local)
    d = (W - E) / np.linalg.norm(W - E)
    cuff = H['sides'][key]['cuff_along_m']
    n0 = len(dele)
    for f in bm.faces:
        if hand[f.index] or head[f.index]:
            continue
        P = CO[[v.index for v in f.verts]]
        if np.sign(P[:, 0].mean()) != np.sign(W[0]):
            continue
        rel = P - W; al = rel @ d; rad = np.linalg.norm(rel - np.outer(al, d), axis=1)
        if rad.mean() > 0.16 or al.mean() < -0.15:
            continue
        if al.mean() < -0.06:
            continue
        near.setdefault(key, set()).add(f.index)
        c = P.mean(0); rel_c = c - W; radial = rel_c - (rel_c @ d) * d; radial /= max(np.linalg.norm(radial), 1e-6)
        n = np.array(mw.to_3x3() @ f.normal)
        inward = float(n @ radial) < 0                   # the turned-in lining of Meshy's folded cuff
        if (al.mean() > cuff - 0.05 and inward) or al.mean() > cuff - TRIM or al.max() > cuff + 0.012:
            dele.add(f.index)
    rep[key] = {'cuff_m': cuff, 'deleted_first': len(dele) - n0}
geom = [bm.faces[i] for i in sorted(dele)]
cand = set().union(*near.values()) - dele
bmesh.ops.delete(bm, geom=geom, context='FACES')
bm.faces.ensure_lookup_table()
# sliver tips: map old indices by the remaining faces' original index layer
for it in range(2):
    tips = [f for f in bm.faces if sum(1 for e in f.edges if e.is_boundary) >= 2 and not any(
        bm.faces.layers.int.get('hand') and f[bm.faces.layers.int['hand']] for _ in [0])]
    tips = [f for f in tips if f[bm.faces.layers.int['hand']] == 0 and f[bm.faces.layers.int['head']] == 0
            and min(np.linalg.norm(np.array(tuple(mw @ f.calc_center_median())) - np.array(rig.matrix_world @ bones[sides[k][0]].head_local)) for k in sides) < 0.10]
    rep[f'tips_{it}'] = len(tips)
    bmesh.ops.delete(bm, geom=tips, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# saw-tooth rim (follow-up 2026-11-02, orchestrator: flaps at the cuffs): the open rim of each cuff is relaxed along
# itself (each rim vertex toward the mean of its two rim neighbours, 8 passes of 0.5), so the remaining spikes lie down
# into a smooth edge; only rim vertices of old body faces within 10 cm of a hand joint move; no faces change
hand_l = bm.faces.layers.int['hand']
Wj = [np.array(rig.matrix_world @ bones[sides[k][0]].head_local) for k in sides]
mwi = mw.inverted()
rim = [v for v in bm.verts if any(e.is_boundary for e in v.link_edges) and all(f[hand_l] == 0 for f in v.link_faces)
       and min(np.linalg.norm(np.array(tuple(mw @ v.co)) - w) for w in Wj) < 0.10]
rimset = set(rim)
for _ in range(8):
    new = {}
    for v in rim:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary and e.other_vert(v) in rimset]
        if len(nb) == 2:
            new[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
    for v, c in new.items():
        v.co = c
rep['rim_vertices_relaxed'] = len(rim)
rep['boundary_edges'] = sum(1 for e in bm.edges if e.is_boundary)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('CUFFFIX', json.dumps(rep), 'faces', len(me.polygons))
