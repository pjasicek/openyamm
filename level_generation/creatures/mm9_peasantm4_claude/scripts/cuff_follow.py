"""Soft cuffs (PeasantM8, 2026-11-02; sleeve poke gate): Forad's bracers are rigid rings on the forearm, so where MM9 bends
the wrist hard (Dead/Death R 127 deg, Hit R, Talk L) the back of the hand slides through the ring wall (sleeve_poke_gate.py
17-24 mm). PeasantM8 wears a cream linen cuff there, which should follow the hand a little. Per side, rest pose: the
sleeve (non-head, non-hand faces' vertices mostly weighted to that side's Forearm/Hand) projected on the forearm->hand
axis; vertices within BAND of the most distal sleeve vertex take a share of their Forearm weight over to the Hand:
share = MAXS * smoothstep(0..1 over the band toward the rim). Weights only: geometry, UVs and attributes unchanged.
Args (Blender): <in blend> <out blend> <report json> [band 0.03] [max share 0.5]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
BAND = float(a[3]) if len(a) > 3 else 0.03
MAXS = float(a[4]) if len(a) > 4 else 0.5
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world
P = np.array([mw @ v.co for v in me.vertices])
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
gname = {g.index: g.name for g in body.vertex_groups}; gi = {g.name: g.index for g in body.vertex_groups}
W = [{gname[g.group]: g.weight for g in v.groups if g.weight > 0} for v in me.vertices]
handv = set()
for p in me.polygons:
    if hn[p.index] or hd[p.index]: handv.update(p.vertices)
rep = {}
for s in 'LR':
    FA, HA = f'Bip01 {s} Forearm', f'Bip01 {s} Hand'
    j0 = np.array(rig.matrix_world @ rig.data.bones[FA].head_local); j1 = np.array(rig.matrix_world @ rig.data.bones[HA].head_local)
    ax = (j1 - j0) / np.linalg.norm(j1 - j0)
    sleeve = [i for i in range(len(P)) if i not in handv and W[i] and (W[i].get(FA, 0) + W[i].get(HA, 0)) / sum(W[i].values()) > 0.5]
    t = (P[sleeve] - j1) @ ax
    rim = float(t.max())
    n = 0; shares = []
    for i, ti in zip(sleeve, t):
        u = np.clip((ti - (rim - BAND)) / BAND, 0, 1)
        sh = MAXS * u * u * (3 - 2 * u)
        if sh <= 1e-3 or W[i].get(FA, 0) <= 0: continue
        mv = W[i][FA] * sh
        body.vertex_groups[gi[FA]].add([i], W[i][FA] - mv, 'REPLACE')
        if HA not in gi: gi[HA] = body.vertex_groups.new(name=HA).index
        body.vertex_groups[gi[HA]].add([i], W[i].get(HA, 0) + mv, 'REPLACE')
        n += 1; shares.append(sh)
    rep[s] = dict(sleeve_verts=len(sleeve), rim_cm_past_hand_joint=round(rim * 100, 2), changed=n,
                  share_max=round(float(max(shares)), 3) if shares else 0)
json.dump(rep, open(REP, 'w'), indent=1); print('CUFF', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
