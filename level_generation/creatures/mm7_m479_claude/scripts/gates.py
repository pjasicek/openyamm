"""Treant clip gates on the animated master (every frame of every clip):
  floor     lowest posed vertex (target >= -0.015 m; the root skirt is planted on Root);
  stretch   largest edge length / rest length, with the worst vertex's dominant bone (Death and Dead are the intended
            burst and collapse: their stretch is reported, not gated);
  limbs     clearance between the six limb chains: smallest distance between bone segments of different sectors
            (and between any limb segment and the Spire), against the same measure in the rest pose; a clip passes
            when no pair comes closer than LIMB_MIN or, if they are closer at rest, than 0.8 x their rest value;
  mouth     closed-mouth check (Standing): the lowest upper-tooth tip must stay behind/below the raised lower lip
            front, reported as the tooth tip height above the lip's top edge at the mouth centre.
Writes work/gates.json. Args: -- <blend>"""
import bpy, sys, os, json, itertools
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
LIMB_MIN = 0.12
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
pa = np.zeros(len(me.vertices), np.int32); me.attributes['part'].data.foreach_get('value', pa)
E = np.array([tuple(e.vertices) for e in me.edges])
rest = np.array([tuple(v.co) for v in me.vertices]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
vn = [g.name for g in body.vertex_groups]
dom = np.array([vn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices])
lip = pv == 15
segs = [b.name for b in rig.pose.bones if b.name.startswith('Limb')] + ['Spire']


def seg_dist(a0, a1, b0, b1):
    best = 1e9
    for t in np.linspace(0, 1, 9):
        p = a0 + (a1 - a0) * t; d = b1 - b0
        u = np.clip((p - b0) @ d / max(d @ d, 1e-9), 0, 1); best = min(best, np.linalg.norm(p - (b0 + d * u)))
    return best


def bone_segs():
    return {n: (np.array(rig.matrix_world @ rig.pose.bones[n].head), np.array(rig.matrix_world @ rig.pose.bones[n].tail))
            for n in segs}


pairs = [(a, b) for a, b in itertools.combinations(segs, 2)
         if a.split('_')[0] != b.split('_')[0]]
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
S0 = bone_segs(); rest_d = {p: seg_dist(*S0[p[0]], *S0[p[1]]) for p in pairs}
report = {}
for act in ('Standing', 'Attack', 'Hit', 'Death', 'Dead'):
    A = bpy.data.actions[act]; rig.animation_data.action = A
    if len(A.slots):
        rig.animation_data.action_slot = A.slots[0]
    f0, f1 = map(int, A.frame_range)
    floor = (9, 0); stretch = (0, 0, ''); limb = (9, None, 0, 0); mouth = None
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
        P = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', P); ev.to_mesh_clear(); P = P.reshape(-1, 3)
        z = float(P[:, 2].min())
        if z < floor[0]:
            floor = (z, f)
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        i = int(np.argmax(r))
        if r[i] > stretch[0]:
            stretch = (float(r[i]), f, dom[E[i, 0]])
        if act not in ('Death', 'Dead'):
            S = bone_segs()
            for p in pairs:
                d = seg_dist(*S[p[0]], *S[p[1]])
                lim = min(LIMB_MIN, 0.8 * rest_d[p])
                margin = d - lim
                if margin < limb[0]:
                    limb = (margin, p, d, rest_d[p])
        if act == 'Standing':
            centre = np.abs(P[:, 0]) < 0.15
            tip = P[(pa == 1) & centre][:, 2].min(); liptop = P[lip & centre][:, 2].max()
            front_lip = P[lip & centre][:, 1].min(); tooth_y = P[(pa == 1) & centre][:, 1].min()
            v = (float(liptop - tip), float(tooth_y - front_lip))
            mouth = v if mouth is None or v[0] < mouth[0] else mouth
    rep = {'frames': f1 - f0 + 1, 'floor_min_z': round(floor[0], 4), 'floor_frame': floor[1],
           'max_edge_stretch': round(stretch[0], 2), 'stretch_frame': stretch[1], 'stretch_bone': stretch[2]}
    if act not in ('Death', 'Dead'):
        rep['limb_clearance_margin'] = round(limb[0], 3)
        rep['limb_closest_pair'] = list(limb[1]) if limb[1] else None
        rep['limb_closest_d'] = round(limb[2], 3); rep['limb_pair_rest_d'] = round(limb[3], 3)
    if mouth:
        rep['closed_mouth_lip_over_tooth_tip_m'] = round(mouth[0], 3); rep['tooth_behind_lip_front_m'] = round(mouth[1], 3)
    report[act] = rep
    print('GATE', act, json.dumps(rep), flush=True)
json.dump(report, open(os.path.join(HERE, 'work', 'gates.json'), 'w'), indent=1)
