"""The face moves rigidly with the Head (VARIANTS_BRIEF lesson from Kira, user review 2026-11-02: "left cheek/chin
distorted"; mm9_kira_claude/scripts/face_rigid.py). Forad's v3 rig split Head/Neck by a plane through the bottom of the
chin and the nape, so the chin's underside kept 20-45 % Neck (y -0.08..-0.05, z 0.673-0.68).

Weights only (UVs, geometry, paint unchanged), on head-material vertices in front of the jaw angle (y < YB) only, and
the Head share only ever RAISED (the neck blend behind the jaw and under the ears stays Forad's): a boundary that follows
the jaw, z_b = Z0 + SLOPE (y - Y0) + CURVE x^2 (throat corner y -0.045 z 0.664, rising toward the back), Head fraction
t = smoothstep(z - z_b, -LO, HI); new Head share = max(old, t) of the vertex's Head+Neck total.
Args (Blender): <in blend> <out blend> <report json>"""
import bpy, sys, json
import numpy as np
IN, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
Z0, Y0, SLOPE, CURVE, LO, HI, YB = 0.664, -0.045, 0.57, 1.2, 0.010, 0.008, 0.0
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
face = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if hd[p.index] == 1 and hn[p.index] == 0: face[list(p.vertices)] = True
P = np.array([body.matrix_world @ v.co for v in me.vertices])
gi = {g.name: g.index for g in body.vertex_groups}
H, NK = 'Bip01 Head', 'Bip01 Neck'
def sst(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
zb = Z0 + SLOPE * (P[:, 1] - Y0) + CURVE * (P[:, 0] + 0.017) ** 2
T = sst(P[:, 2] - zb, -LO, HI)
changed, before, after = 0, [], []
for i in np.nonzero(face & (P[:, 1] < YB))[0].tolist():
    v = me.vertices[i]
    w = {body.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0}
    tot = w.get(H, 0) + w.get(NK, 0)
    if tot <= 1e-6 or w.get(NK, 0) <= 1e-4: continue
    old = w.get(H, 0) / tot; new = max(old, float(T[i]))
    if new - old < 1e-3: continue
    before.append(old); after.append(new); changed += 1
    body.vertex_groups[gi[H]].add([i], tot * new, 'REPLACE')
    if tot * (1 - new) > 1e-4: body.vertex_groups[gi[NK]].add([i], tot * (1 - new), 'REPLACE')
    else: body.vertex_groups[gi[NK]].remove([i])
low = face & (P[:, 1] < -0.05) & (P[:, 2] > 0.668)
def hs(i):
    w = {body.vertex_groups[g.group].name: g.weight for g in me.vertices[i].groups}
    return w.get(H, 0) / max(1e-9, sum(w.values()))
hw = np.array([hs(i) for i in np.nonzero(low)[0]])
rep = dict(changed=changed, mean_before=round(float(np.mean(before)), 3) if before else None,
           mean_after=round(float(np.mean(after)), 3) if after else None, chin_verts=int(low.sum()),
           chin_head_min=round(float(hw.min()), 3))
json.dump(rep, open(REP, 'w'), indent=1); print('FACERIGID ' + json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
