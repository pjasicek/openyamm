"""Weight spikes: single vertices whose weights disagree with their neighbours stretch into spikes once a clip moves
the bone they wrongly follow (found by the reduction's surface error, 2026-10-14: a tunic vertex at the right hip
weighted to RightArm/RightForeArm stretched 95 mm in the library Cast; a mantle vertex at the right shoulder carried
a stray RightArm share and stretched its edges to 194 mm).

A vertex is a spike when, at some sampled frame (every 2nd of every clip), the MEDIAN ratio of its edges' posed to
rest length exceeds RATIO (one displaced vertex stretches all of its edges; an opening cloth seam stretches only
some) and its arm-chain weight (Arm, ForeArm, Hand) differs from its neighbours' mean by more than DISAGREE (the
armpit band stretches too, but evenly weighted). Its weights are replaced by the mean of its one-ring
neighbours' weights (normalised, 4 influences). Two rounds. Args: -- <blend in work/>"""
import bpy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

RATIO = 2.5
DISAGREE = 0.15
ARM = ('LeftArm', 'LeftForeArm', 'LeftHand', 'RightArm', 'RightForeArm', 'RightHand')
blend = os.path.join(common.WORK, sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
rig, mesh = bpy.data.objects['Cleric_Rig'], bpy.data.objects['Cleric']
me = mesh.data
E = np.array([e.vertices[:] for e in me.edges])
names = {g.index: g.name for g in mesh.vertex_groups}
nbr = [[] for _ in me.vertices]
for a, b in E:
    nbr[a].append(b); nbr[b].append(a)
inc = [[] for _ in me.vertices]
for k, (a, b) in enumerate(E):
    inc[a].append(k); inc[b].append(k)


def positions():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([v.co[:] for v in m.vertices]); ev.to_mesh_clear(); return P


def rest():
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


rest(); R = positions(); L0 = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1) + 1e-6
for rnd in range(2):
    worst = np.zeros(len(me.vertices)); where = [''] * len(me.vertices)
    for act in [a for a in bpy.data.actions if a.name in ('Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit',
                                                          'Death', 'Dead', 'Fidget')]:
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        f0, f1 = (int(round(x)) for x in act.frame_range)
        for f in range(f0, f1 + 1, 2):
            sc.frame_set(f); P = positions()
            r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / L0
            med = np.array([np.median(r[i]) if i else 0 for i in inc])
            hit = med > worst
            worst[hit] = med[hit]
            for i in np.flatnonzero(hit & (med > RATIO)):
                where[i] = f'{act.name}:{f}'
    armw = np.array([sum(g.weight for g in v.groups if names[g.group] in ARM) for v in me.vertices])
    nb_arm = np.array([np.mean(armw[n]) if n else 0 for n in nbr])
    spikes = [i for i in np.flatnonzero(worst > RATIO) if armw[i] > 0.02 and abs(armw[i] - nb_arm[i]) > DISAGREE]
    print('SPIKES round', rnd, len(spikes), [(int(i), round(float(worst[i]), 2), where[i], round(float(armw[i]), 2),
                                              round(float(nb_arm[i]), 2), [round(float(x), 3) for x in R[i]])
                                             for i in spikes][:12])
    if not spikes:
        break
    for i in spikes:
        acc = {}
        for j in nbr[i]:
            for g in me.vertices[j].groups:
                acc[g.group] = acc.get(g.group, 0.0) + g.weight / len(nbr[i])
        top = sorted(acc.items(), key=lambda x: -x[1])[:4]; s = sum(w for _, w in top)
        for g in list(me.vertices[i].groups):
            mesh.vertex_groups[g.group].remove([int(i)])
        for gi, w in top:
            mesh.vertex_groups[gi].add([int(i)], w / s, 'REPLACE')
    rest()
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=blend)
